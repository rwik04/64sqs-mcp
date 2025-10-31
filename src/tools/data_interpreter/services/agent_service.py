"""
Service for agent orchestration logic (decoupled from target.py)
"""

import copy
import json
from src.tools.data_interpreter.models import AgentState, Action_Type, OutputEntry
from langchain_core.messages import HumanMessage, AIMessage

class AgentService:
    def __init__(self):
        pass

    def agent(self, state: AgentState):
        total_input_tokens = 0
        total_output_tokens = 0
        current_messages_history = state['messages']
        actions_history = state['actions']
        print(state['output'])

        if not state['remaining_steps']:
            return self._handle_no_remaining_steps(state, actions_history)

        next_tool_in_plan = state['remaining_steps'][-1]['tool_name']
        next_tool_reason_from_plan = state['remaining_steps'][-1]['reason']
        model_type = state['model_type']
        api_key = state['api_key']

        last_created_data_info_for_prompt = self._get_last_created_data_info(state, next_tool_in_plan)

        instruction_prompt_content = self._get_instruction_prompt_content(next_tool_in_plan)
        guidelines_prompt_content = self._get_guidelines_prompt_content(next_tool_in_plan)

        prompt_for_llm = self._build_prompt_for_llm(
            next_tool_in_plan,
            next_tool_reason_from_plan,
            last_created_data_info_for_prompt,
            instruction_prompt_content,
            guidelines_prompt_content
        )

        next_action_response_dict = {}
        response_content_from_llm = ""

        if state["retries_remaining"] >= 0:
            (
                next_action_response_dict,
                response_content_from_llm,
                total_input_tokens,
                total_output_tokens,
                next_tool_in_plan
            ) = self._get_next_action_response(
                state,
                current_messages_history,
                prompt_for_llm,
                model_type,
                api_key,
                total_input_tokens,
                total_output_tokens,
                next_tool_in_plan
            )
        else:
            print("Agent: No global retries remaining. Forcing END.")
            next_tool_in_plan = Action_Type.END
            next_action_response_dict = {
                "action_details": [{"instruction": "Max global retries reached.", "target_data_sources": []}]
            }

        # Final structure checks and fallback
        if isinstance(next_action_response_dict, list) and len(next_action_response_dict) == 1 and isinstance(
                next_action_response_dict[0], dict):
            next_action_response_dict = next_action_response_dict[0]
        elif not isinstance(next_action_response_dict, dict):
            print(f"Agent: Final response structure unexpected, forcing END. Response: {next_action_response_dict}")
            next_tool_in_plan = Action_Type.END
            next_action_response_dict = {
                "action_details": [{"instruction": "Agent final response structure error.", "target_data_sources": []}]
            }

        action_to_append = {
            'action_num': len(actions_history) + 1,
            'action_type': next_tool_in_plan,
            'action_details': next_action_response_dict.get('action_details', [])
        }
        new_actions_history = list(actions_history)
        new_actions_history.append(action_to_append)
        updated_state = copy.deepcopy(state)
        updated_state['current_step_reason'] = next_tool_reason_from_plan
        if updated_state['remaining_steps']:
            updated_state['remaining_steps'].pop()
        updated_messages_history = list(current_messages_history)
        updated_messages_history.append(HumanMessage(content=prompt_for_llm))
        if response_content_from_llm:
            updated_messages_history.append(AIMessage(content=response_content_from_llm))
        updated_state['messages'] = updated_messages_history
        updated_state['actions'] = new_actions_history
        if 'workflow_execution' not in updated_state['token_tracker']:
            updated_state['token_tracker']['workflow_execution'] = {}
        if model_type not in updated_state['token_tracker']['workflow_execution']:
            updated_state['token_tracker']['workflow_execution'][model_type] = {'input_tokens': 0, 'output_tokens': 0}
        updated_state['token_tracker']['workflow_execution'][model_type]['input_tokens'] += total_input_tokens
        updated_state['token_tracker']['workflow_execution'][model_type]['output_tokens'] += total_output_tokens
        return updated_state

    def _handle_no_remaining_steps(self, state, actions_history):
        print("Agent called with no remaining steps. Defaulting to END.")
        action_to_append = {
            'action_num': len(actions_history) + 1,
            'action_type': Action_Type.END,
            'action_details': [{"instruction": "No more steps in plan.", "target_data_sources": []}]
        }
        actions_history.append(action_to_append)
        updated_state = copy.deepcopy(state)
        updated_state['actions'] = actions_history
        return updated_state

    def _get_last_created_data_info(self, state, next_tool_in_plan):
        last_created_data_info_for_prompt = ""
        print(f"Looking for last created data in {len(state.get('output', []))} output entries")
        
        if state.get('output'):
            for entry in reversed(state['output']):
                # Safely compute data length for logging
                output_obj = entry.get('output')
                data_list = output_obj.get('data') if isinstance(output_obj, dict) else None
                safe_data_len = len(data_list) if isinstance(data_list, list) else 0
                name_for_log = output_obj.get('data_extracted_name', 'NO_NAME') if isinstance(output_obj, dict) else 'NO_OUTPUT'
                print(f"Checking entry: {name_for_log} with data length: {safe_data_len}")

                # Check if this entry has output and contains data
                if (isinstance(output_obj, dict) and 
                    output_obj.get('data_extracted_name') and 
                    isinstance(data_list, list) and
                    len(data_list) > 0):  # Ensure data is not empty list
                    
                    # Check if the status indicates success (not failure)
                    status = output_obj.get('status', '')
                    if isinstance(status, str) and "$$FAILED$$" not in status.upper():
                        last_data_name = entry['output']['data_extracted_name']
                        print(f"Found successful data source: {last_data_name}")
                        last_created_data_info_for_prompt = f"""
IMPORTANT CONTEXT FROM PREVIOUS STEP:
The most recent data processing step successfully produced an intermediate dataset.
This dataset is now available as a `STRUCTURED_TABLE_TEMPORARY` under the unique name: `{last_data_name}`.

If the current tool ('{next_tool_in_plan}') needs to use the output of the immediately preceding data generation step,
you MUST use `{last_data_name}` as the `source_name` and `STRUCTURED_TABLE_TEMPORARY` as the `source_type` in the `target_data_sources`.
Do NOT use original table names for this intermediate data.

If the current tool is summary_answer, it may need to use multiple outputs of previous data generation steps, hence according to what the
query needs, use the appropriate table names and source types in the `target_data_sources`.
"""
                        break

        print(f"Built context: {last_created_data_info_for_prompt[:100]}...")
        return last_created_data_info_for_prompt

    def _get_instruction_prompt_content(self, next_tool_in_plan):
        query_prompt_text = (
            "For the tool `query_data` the instruction needs to be a valid SQL or Snowflake query, with CTEs for multi-step calculations. "
            "For `STRUCTURED_TABLE` sources, use their original `tablename` (often a UUID). For `STRUCTURED_TABLE_TEMPORARY` sources, you MUST use the `data_extracted_name` provided in the 'IMPORTANT CONTEXT' section if you are referencing data from a previous step. "
            "All table names and field names in the SQL query should be within `` if they are original DB tables."
        )
        annotate_prompt_text = (
            "For the tool `annotate_data` the instruction needs to be a relevant annotation task for a language AI model... "
            "Ensure the `target_data_sources` refers to a `STRUCTURED_TABLE_TEMPORARY` using its `data_extracted_name` (provided in 'IMPORTANT CONTEXT')."
        )
        summarise_prompt_text = (
            "For the tool `summarise_answer` the instruction needs to be a relevant task (not calculative in nature) for a language AI model... "
            "Ensure the `target_data_sources` refers to the correct `STRUCTURED_TABLE_TEMPORARY` (using its `data_extracted_name` from 'IMPORTANT CONTEXT') and/or original `STRUCTURED_TABLE`s (using their `tablename`)."
        )
        if next_tool_in_plan == Action_Type.QUERY:
            return query_prompt_text
        elif next_tool_in_plan == Action_Type.ANNOTATE:
            return annotate_prompt_text
        elif next_tool_in_plan == Action_Type.SUMMARISE_ANSWER:
            return summarise_prompt_text
        else:
            return ""

    def _get_guidelines_prompt_content(self, next_tool_in_plan):
        if next_tool_in_plan == Action_Type.QUERY:
            return (
                "1. A single action (SQL query) can be executed on multiple `target_data_sources` (e.g. by joining)...\n"
                "2. The job of the query tool should always be to bring data to the right level of conciseness which means that any mathematical calculation (like averaging, percentage calculation) must be performed using this tool...\n"
                "3. So come up with the most efficient query operation..."
            )
        elif next_tool_in_plan == Action_Type.ANNOTATE:
            return (
                "1. A single action can only be executed on a single `target_data_sources` (one `STRUCTURED_TABLE_TEMPORARY`)...\n"
                "2. If you need to annotate multiple data sources or columns, create separate action items if the plan requires multiple annotation steps...\n"
                "3. Annotation should be done only wrt text fields..."
            )
        elif next_tool_in_plan == Action_Type.SUMMARISE_ANSWER:
            return (
                "1. A single action can be executed on multiple `target_data_sources` (e.g. reviewing multiple datasets for the final answer)..."
            )
        else:
            return ""

    def _build_prompt_for_llm(self, next_tool_in_plan, next_tool_reason_from_plan, last_created_data_info_for_prompt, instruction_prompt_content, guidelines_prompt_content):
        return f"""
        As per your initial plan/route, the next tool that needs to be invoked is: {next_tool_in_plan}
        Reason for this tool (from plan): {next_tool_reason_from_plan}

        {last_created_data_info_for_prompt}

        Return the details on the next action(s) that needs to be executed using the tool '{next_tool_in_plan}'.
        Your response MUST be a single, valid JSON object with the following structure:
        {{
        "action_details": [
            {{
            "instruction": "string: Specific instruction for the tool. {instruction_prompt_content}",
            "target_data_sources": [
                {{
                "source_name": "string: Name of the source. If original, use 'tablename' (e.g., UUID). If intermediate, MUST be the 'data_extracted_name' from 'IMPORTANT CONTEXT'.",
                "source_type": "string: `STRUCTURED_TABLE` or `STRUCTURED_TABLE_TEMPORARY`."
                }}
                // ... more target_data_sources if the tool supports multiple
            ]
            }}
            // ... more action_details if the tool invocation involves multiple distinct operations
        ]
        }}

        IMPORTANT GUIDELINES for actions to be executed using the tool '{next_tool_in_plan}': {guidelines_prompt_content}

        Consider if any previous step returned an empty dataset. If processing an empty dataset doesn't make sense, adjust the `instruction` (e.g., for `summarise_answer`, state no data is available).
        If you determine that no further progress can be made or the goal is met and the next step in the plan is `__end__`, or if the current tool is `__end__`, then for the `__end__` tool, provide an empty list for `action_details` like so: `{{"action_details": []}}`.
        """

    def _get_next_action_response(
        self,
        state,
        current_messages_history,
        prompt_for_llm,
        model_type,
        api_key,
        total_input_tokens,
        total_output_tokens,
        next_tool_in_plan
    ):
        from src.tools.data_interpreter.utils.llm_utils import chat_with_model

        messages_for_this_llm_call = list(current_messages_history)
        messages_for_this_llm_call.append(HumanMessage(content=prompt_for_llm))
        _, response_content_from_llm, input_tokens_call, output_tokens_call = chat_with_model(
            model_type=model_type, api_key=api_key, messages=messages_for_this_llm_call,
            temperature=0, max_tokens=2000
        )
        total_input_tokens += input_tokens_call
        total_output_tokens += output_tokens_call
        response_content_clean = response_content_from_llm.replace("```json", "").replace("```", "").strip()
        try:
            next_action_response_dict = json.loads(response_content_clean)
        except json.JSONDecodeError:
            print(f"Agent LLM response was not valid JSON: {response_content_clean}")
            next_action_response_dict = {}

        parsing_retry_count = 0
        max_parsing_retries = 1
        while (not isinstance(next_action_response_dict, dict) or
               next_action_response_dict.get("action_details") is None or
               not isinstance(next_action_response_dict.get("action_details"), list)) and \
                parsing_retry_count < max_parsing_retries and \
                state["retries_remaining"] > 0:
            parsing_retry_count += 1
            print(f"Retrying agent LLM call due to invalid action JSON structure. Attempt {parsing_retry_count} for this agent turn.")
            messages_for_retry_llm_call = list(messages_for_this_llm_call)
            messages_for_retry_llm_call.append(AIMessage(content=response_content_from_llm))
            messages_for_retry_llm_call.append(HumanMessage(
                content="The previous JSON response was malformed or missing the 'action_details' key as a list. Please try again, ensuring a single valid JSON object with an 'action_details' key whose value is a list of objects. Each object in 'action_details' must have 'instruction' (string) and 'target_data_sources' (list of objects)."))
            _, response_content_from_llm, input_tokens_call, output_tokens_call = chat_with_model(
                model_type=model_type, api_key=api_key, messages=messages_for_retry_llm_call,
                temperature=0, max_tokens=2000
            )
            total_input_tokens += input_tokens_call
            total_output_tokens += output_tokens_call
            response_content_clean = response_content_from_llm.replace("```json", "").replace("```", "").strip()
            try:
                next_action_response_dict = json.loads(response_content_clean)
            except json.JSONDecodeError:
                print(f"Agent LLM response (retry {parsing_retry_count}) still not valid JSON: {response_content_clean}")
                next_action_response_dict = {}

        if not isinstance(next_action_response_dict, dict) or \
                next_action_response_dict.get("action_details") is None or \
                not isinstance(next_action_response_dict.get("action_details"), list):
            print(
                "Agent failed to produce valid 'action_details' after retries for this turn. Defaulting to end current plan step.")
            next_tool_in_plan = Action_Type.END
            next_action_response_dict = {
                "action_details": [{"instruction": "Agent parsing/logic error.", "target_data_sources": []}]
            }

        return (
            next_action_response_dict,
            response_content_from_llm,
            total_input_tokens,
            total_output_tokens,
            next_tool_in_plan
        )
