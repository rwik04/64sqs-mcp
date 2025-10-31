"""
Service for annotation logic (decoupled from target.py)
"""

from typing import Dict, Any
import asyncio
import json
import time
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from langchain_core.messages import HumanMessage, SystemMessage

from src.tools.data_interpreter.models import (
    AgentState,
    Action_Type,
    OutputEntry,
    Data_Source_Type,
    StructuredRecordLimitError,
)
from src.tools.data_interpreter.utils.llm_utils import (
    chat_with_model,
    async_chat_with_model,
    get_annotation_limit,
)
from src.tools.data_interpreter.utils.db_utils import create_connection

class AnnotationService:
    def __init__(self):
        pass

    def tool_annotate_data(self, state: AgentState) -> AgentState:
        action = state['actions'][-1]
        action_details = action['action_details']
        model_type = state['model_type']
        api_key = state['api_key']
        updated_state = self._deepcopy_state(state)
        current_output_log = updated_state.get('output', [])
        total_tool_input_tokens = 0
        total_tool_output_tokens = 0

        if not action_details:
            no_action_entry = OutputEntry(
                step_no=len(current_output_log) + 1,
                planned_action=updated_state['current_step_reason'],
                output={"status": "Skipped - No action details"},
                insight=None
            )
            current_output_log.append(no_action_entry)
            updated_state['output'] = current_output_log
            return updated_state

        for action_detail in action_details:
            instruction = action_detail['instruction']
            try:
                # If already inside an event loop (e.g., server context), run the coroutine in a separate thread
                try:
                    asyncio.get_running_loop()
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        action_result, call_input_tokens, call_output_tokens = executor.submit(
                            lambda: asyncio.run(
                                self.tool_annotate_dataframe_async(
                                    model_type,
                                    api_key,
                                    action_detail,
                                    current_output_log,
                                    updated_state['shortlisted_user_sources']
                                )
                            )
                        ).result()
                except RuntimeError:
                    # No running loop; safe to use asyncio.run directly
                    action_result, call_input_tokens, call_output_tokens = asyncio.run(
                        self.tool_annotate_dataframe_async(
                            model_type,
                            api_key,
                            action_detail,
                            current_output_log,
                            updated_state['shortlisted_user_sources']
                        )
                    )
            except Exception as e:
                action_result = {
                    "status": f"$$FAILED$$ during async execution: {e}",
                    "data_extracted_name": None, "column_name": None, "data": None
                }
                call_input_tokens, call_output_tokens = 0, 0

            updated_state['messages'].append(HumanMessage(content=action_result['status']))
            total_tool_input_tokens += call_input_tokens
            total_tool_output_tokens += call_output_tokens

            output_content_for_log = {
                "status": action_result['status'],
                "data_extracted_name": action_result.get('data_extracted_name'),
                "column_name": action_result.get('column_name'),
            }

            if "$$FAILED$$" in action_result['status']:
                updated_state['retries_remaining'] -= 1
                output_entry = OutputEntry(
                    step_no=len(current_output_log) + 1,
                    planned_action=updated_state['current_step_reason'],
                    executed_action={"action": instruction, "action_type": "TEXT_PROMPT"},
                    output=output_content_for_log,
                    insight=None
                )
                current_output_log.append(output_entry)
                if updated_state['retries_remaining'] >= 0:
                    add_step = {'tool_name': Action_Type.ANNOTATE, 'reason': "Previous annotation failed. Retrying."}
                else:
                    add_step = {'tool_name': Action_Type.END, 'reason': "Annotation failed after max retries."}
                    updated_state['final_response'] = "Answer generation failed due to annotation error."
                updated_state['remaining_steps'].append(add_step)
                updated_state['output'] = current_output_log
                updated_state['token_tracker']['workflow_execution'][model_type]['input_tokens'] += total_tool_input_tokens
                updated_state['token_tracker']['workflow_execution'][model_type]['output_tokens'] += total_tool_output_tokens
                return updated_state
            else:
                if updated_state['retries_remaining'] < updated_state['max_retries']:
                    updated_state['retries_remaining'] += 1
                output_content_for_log["data"] = action_result.get('data_extracted')
                output_entry = OutputEntry(
                    step_no=len(current_output_log) + 1,
                    planned_action=updated_state['current_step_reason'],
                    executed_action={"action": instruction, "action_type": "TEXT_PROMPT"},
                    output=output_content_for_log,
                    insight=None
                )
                current_output_log.append(output_entry)

        updated_state['output'] = current_output_log
        updated_state['token_tracker']['workflow_execution'][model_type]['input_tokens'] += total_tool_input_tokens
        updated_state['token_tracker']['workflow_execution'][model_type]['output_tokens'] += total_tool_output_tokens
        return updated_state

    async def annotate_single_row_async(
        self,
        row_dict_str: str,
        instruction_for_llm_task: str,
        model_type: str,
        api_key: str
    ) -> tuple[str, int, int]:
        annotation_system_message_content = f"""
        The rows of the data in the temp table will be provided row by row in a dictionary format.
        Each row of the dictionary needs to be annotated based on the following instructions.
        ```
        {instruction_for_llm_task}
        ```

        The task at hand might sometimes by subjective/ambiguous (e.g. judging sentiment).

        Still try labelling/tagging to the best of your ability, preferably tagging those ambiguous cases towards what the user wants to search for.

        Provide only the relevant annotation (label/tag) for that row and nothing else.

        All annotations (labels/tags) must be LOGICAL and STRICTLY follow the instructions.

        DO NOT enclose the annotations in `[]`. DO NOT return any other keyword/phrase except a valid label/tag.
        ALWAYS output a SINGLE Yes/No label per row—NEVER phrases like 'mentions_A: No, mentions_B: No' or any extras. If combo, evaluate ONLY the specified combo as Yes/No.
        """

        row_specific_human_prompt_content = f"""
        The following is the data stored in the current row:
        ```
        {row_dict_str}
        ```

        Go through it slowly and carefully and generate the valid label/tag based on the above instructions.
        """

        messages_for_llm_call = [
            SystemMessage(content=annotation_system_message_content),
            HumanMessage(content=row_specific_human_prompt_content)
        ]

        _, actual_llm_response_content, in_tokens, out_tokens = await async_chat_with_model(
            model_type=model_type,
            api_key=api_key,
            messages=messages_for_llm_call,
            temperature=0,
            max_tokens=512,
            json_schema={}
        )

        cleaned_response = actual_llm_response_content.strip()
        cleaned_response = cleaned_response.replace("```python", "").replace("```", "").replace("```json", "").replace("```", "")

        return cleaned_response, in_tokens, out_tokens

    async def tool_annotate_dataframe_async(
        self,
        model_type: str,
        api_key: str,
        action_detail: Dict[str, Any],
        agent_output_log: list,
        shortlisted_user_sources: list
    ) -> tuple[dict, int, int]:
        total_input_tokens_for_tool = 0
        total_output_tokens_for_tool = 0
        action_result: Dict[str, Any] = {}

        if len(action_detail['target_data_sources']) > 1:
            action_result['status'] = "$$FAILED$$ to annotate data. `annotate_data` tool expects a single target data source."
            action_result['data_extracted'], action_result['data_extracted_name'], action_result['column_name'] = None, None, None
            return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool

        target_data_source_info = action_detail['target_data_sources'][0]
        target_data_source_type = target_data_source_info['source_type']
        target_data_source_name = target_data_source_info['source_name']
        instruction_for_llm_task_from_action_detail = action_detail['instruction']
        initial_df = None

        # Ensure source_db_uri is present for TABLE
        if 'source_db_uri' not in target_data_source_info and target_data_source_type == Data_Source_Type.TABLE:
            for user_source in shortlisted_user_sources:
                if user_source['tablename'] == target_data_source_name:
                    target_data_source_info['source_db_uri'] = user_source.get('source_db_uri')
                    target_data_source_info['db_type'] = user_source.get('db_type')
                    break

        # Fetch DataFrame from log or external source
        if target_data_source_type == Data_Source_Type.TEMP_TABLE:
            found_df = False
            for entry in reversed(agent_output_log):
                if entry.get('output') and entry['output'].get('data_extracted_name') == target_data_source_name:
                    if 'data' in entry['output'] and entry['output']['data']:
                        df_data_list = entry['output']['data']
                        try:
                            initial_df = pd.DataFrame(df_data_list)
                            found_df = True
                        except Exception as e:
                            action_result['status'] = f"$$FAILED$$ Could not decode/create DataFrame for '{target_data_source_name}': {e}"
                            return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool
                        break
            if not found_df:
                action_result['status'] = f"$$FAILED$$ Data source '{target_data_source_name}' not found in agent output log for annotation."
                return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool
        elif target_data_source_type == Data_Source_Type.TABLE:
            target_data_source_db_uri = target_data_source_info['source_db_uri']
            engine = create_connection(target_data_source_db_uri)
            initial_df = pd.read_sql_query(f"SELECT * FROM `{target_data_source_name}`", con=engine)
            engine.dispose()

        # Check annotation limit
        annotation_limit = get_annotation_limit()
        if initial_df is not None and len(initial_df) > annotation_limit:
            raise StructuredRecordLimitError(
                f"Encountered data with more than {annotation_limit} rows for annotation. Please contact support if you want to raise your quota")

        if initial_df is None or initial_df.empty:
            action_result['data_extracted'] = json.dumps([])
            action_result['data_extracted_name'] = f"annotate_data_{str(time.time()).replace('.', '_')}"
            action_result['status'] = "Zero records found for annotation. Original data was empty."
            action_result['column_name'] = None
            return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool

        # Async Parallel Annotation
        row_dict_strings_for_llm = [str(row.to_dict()) for _, row in initial_df.iterrows()]
        annotation_tasks = [
            self.annotate_single_row_async(
                row_str,
                instruction_for_llm_task_from_action_detail,
                model_type,
                api_key
            )
            for row_str in row_dict_strings_for_llm
        ]
        results_from_gather = await asyncio.gather(*annotation_tasks, return_exceptions=True)

        annotations_results_ordered = [None] * len(initial_df)
        for i, result_item in enumerate(results_from_gather):
            if isinstance(result_item, Exception):
                annotations_results_ordered[i] = f"ANNOTATION_ERROR: {type(result_item).__name__}"
            else:
                annotation_text, in_tokens, out_tokens = result_item
                annotations_results_ordered[i] = annotation_text
                total_input_tokens_for_tool += in_tokens
                total_output_tokens_for_tool += out_tokens

        # Generate column name
        column_name_prompt = f"""
        Given the annotation instruction:
        ``{instruction_for_llm_task_from_action_detail}``
        Generate a concise, SQL-friendly column name (e.g., using underscores, no spaces) for the annotations.
        The column name should clearly represent the purpose of the annotation.
        Return ONLY the column-name, without any extra verbiage or quotes.
        Ensure the name is unique and not one of these existing column names:
        {str(initial_df.columns.tolist())}
        """
        messages_llm_col = [HumanMessage(content=column_name_prompt)]
        _, col_name_response, in_tokens_col, out_tokens_col = await async_chat_with_model(
            model_type=model_type, api_key=api_key, messages=messages_llm_col,
            temperature=0, max_tokens=64, json_schema={}
        )
        column_name = col_name_response.strip().replace(" ", "_").replace("-", "_")
        original_proposed_col_name = column_name
        count = 1
        while column_name in initial_df.columns:
            column_name = f"{original_proposed_col_name}_{count}"
            count += 1
        total_input_tokens_for_tool += in_tokens_col
        total_output_tokens_for_tool += out_tokens_col

        initial_df[column_name] = annotations_results_ordered

        # Fill missing values
        for col in initial_df.columns:
            if initial_df[col].dtype == 'object':
                initial_df[col] = initial_df[col].fillna('')
            elif np.issubdtype(initial_df[col].dtype, np.number):
                initial_df[col] = initial_df[col].astype(float).where(initial_df[col].notnull(), None)
            elif np.issubdtype(initial_df[col].dtype, np.datetime64):
                initial_df[col] = initial_df[col].where(initial_df[col].notnull(), None)
                initial_df[col] = initial_df[col].apply(lambda x: x.isoformat() if pd.notnull(x) else None)

        data_extracted_list = initial_df.to_dict(orient='records')
        data_id = str(time.time()).replace('.', '_')
        action_result['data_extracted_name'] = f"annotate_data_{data_id}".replace("-", "_")
        action_result['data_extracted'] = data_extracted_list
        action_result['column_name'] = column_name
        action_result['status'] = f"""
        Successfully annotated data (async).
        Annotated data stored in-memory with name {action_result['data_extracted_name']}.
        Annotations in column `{column_name}`.
        """
        return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool

    def _deepcopy_state(self, state: AgentState) -> AgentState:
        import copy as _copy
        return _copy.deepcopy(state)
