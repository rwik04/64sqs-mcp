"""
Service for summarisation logic (decoupled from target.py)
"""

import copy
import json
import time
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from src.tools.data_interpreter.models import AgentState, OutputEntry, Action_Type, Data_Source_Type
from src.tools.data_interpreter.utils.llm_utils import chat_with_model

class SummarisationService:
    def __init__(self):
        pass

    def tool_summarise_answer(self, state: AgentState) -> AgentState:
        action = state['actions'][-1]
        action_details = action['action_details']
        model_type = state['model_type']
        api_key = state['api_key']
        updated_state = copy.deepcopy(state)
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

        last_successful_result = None
        last_successful_df = None
        last_successful_source_name = None
        
        for action_detail in action_details:
            instruction = action_detail['instruction']
            try:
                action_result, call_input_tokens, call_output_tokens, df_data = self._generate_final_answer(
                    model_type,
                    api_key,
                    action_detail,
                    current_output_log,
                    updated_state['shortlisted_user_sources']
                )
            except Exception as e:
                action_result = {
                    "status": f"$$FAILED$$ during summarisation: {e}",
                    "final_answer": None,
                    "chart_type": None,
                    "highcharts_config": None
                }
                call_input_tokens, call_output_tokens = 0, 0
                df_data = None

            updated_state['messages'].append(HumanMessage(content=action_result['status']))
            total_tool_input_tokens += call_input_tokens
            total_tool_output_tokens += call_output_tokens

            output_content_for_log = {
                "status": action_result['status'],
                "final_answer": action_result.get('final_answer'),
                "chart_type": action_result.get('chart_type'),
                "highcharts_config": action_result.get('highcharts_config'),
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
                    add_step = {'tool_name': Action_Type.SUMMARISE_ANSWER, 'reason': "Previous summarisation failed. Retrying."}
                else:
                    add_step = {'tool_name': Action_Type.END, 'reason': "Summarisation failed after max retries."}
                    updated_state['final_response'] = "Answer generation failed due to summarisation error."
                updated_state['remaining_steps'].append(add_step)
                updated_state['output'] = current_output_log
                updated_state['token_tracker']['workflow_execution'][model_type]['input_tokens'] += total_tool_input_tokens
                updated_state['token_tracker']['workflow_execution'][model_type]['output_tokens'] += total_tool_output_tokens
                return updated_state
            else:
                if updated_state['retries_remaining'] < updated_state['max_retries']:
                    updated_state['retries_remaining'] += 1
                output_entry = OutputEntry(
                    step_no=len(current_output_log) + 1,
                    planned_action=updated_state['current_step_reason'],
                    executed_action={"action": instruction, "action_type": "TEXT_PROMPT"},
                    output=output_content_for_log,
                    insight=None
                )
                current_output_log.append(output_entry)
                
                # Store the last successful result for state update
                last_successful_result = action_result
                last_successful_df = df_data
                last_successful_source_name = action_detail['target_data_sources'][0]['source_name'] if action_detail['target_data_sources'] else None

        # Update state with final results from the last successful action
        if last_successful_result:
            updated_state["insight"] = last_successful_result.get('final_answer', '')
            updated_state["confidence"] = 'HIGH'
            updated_state["chart"] = {
                'chartType': last_successful_result.get('chart_type', 'NA'),
                'highchartsConfig': last_successful_result.get('highcharts_config', None)
            }
            
            # Update table data if we have DataFrame data
            if last_successful_df is not None and not last_successful_df.empty:
                updated_state["tableData"] = [{
                    'data_name': last_successful_source_name,
                    'headers': list(last_successful_df.columns),
                    'data': last_successful_df.to_dict(orient='records')
                }]

        updated_state['output'] = current_output_log
        updated_state['token_tracker']['workflow_execution'][model_type]['input_tokens'] += total_tool_input_tokens
        updated_state['token_tracker']['workflow_execution'][model_type]['output_tokens'] += total_tool_output_tokens
        return updated_state

    def _generate_final_answer(
        self,
        model_type: str,
        api_key: str,
        action_detail: Dict[str, Any],
        agent_output_log: list,
        shortlisted_user_sources: list
    ) -> tuple[dict, int, int, Any]:
        total_input_tokens_for_tool = 0
        total_output_tokens_for_tool = 0
        action_result: Dict[str, Any] = {}

        if len(action_detail['target_data_sources']) > 1:
            action_result['status'] = "$$FAILED$$ to summarise answer. `summarise_answer` tool expects a single target data source."
            action_result['final_answer'], action_result['chart_type'] = None, None
            return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool, None

        target_data_source_info = action_detail['target_data_sources'][0]
        target_data_source_type = target_data_source_info['source_type']
        target_data_source_name = target_data_source_info['source_name']
        instruction_for_llm_task_from_action_detail = action_detail['instruction']
        initial_df = None

        # Fetch DataFrame from log
        if target_data_source_type == Data_Source_Type.TEMP_TABLE:
            found_df = False
            print(f"Looking for TEMP_TABLE with name: {target_data_source_name}")
            print(f"Agent output log entries: {len(agent_output_log)}")
            
            for entry in reversed(agent_output_log):
                print(f"Checking entry: {entry.get('output', {}).get('data_extracted_name', 'NO_NAME')}")
                if entry.get('output') and entry['output'].get('data_extracted_name') == target_data_source_name:
                    print(f"Found matching entry with data: {entry['output'].get('data')}")
                    if 'data' in entry['output'] and entry['output']['data']:
                        df_data_list = entry['output']['data']
                        print(f"Data list type: {type(df_data_list)}, length: {len(df_data_list) if df_data_list else 0}")
                        print(f"Data list content: {df_data_list}")
                        try:
                            import pandas as pd
                            initial_df = pd.DataFrame(df_data_list)
                            found_df = True
                            print(f"Successfully created DataFrame with shape: {initial_df.shape}")
                            print(f"DataFrame columns: {list(initial_df.columns)}")
                            print(f"DataFrame head: {initial_df.head()}")
                        except Exception as e:
                            print(f"Error creating DataFrame: {e}")
                            action_result['status'] = f"$$FAILED$$ Could not decode/create DataFrame for '{target_data_source_name}': {e}"
                            return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool, None
                        break
            
            if not found_df:
                print(f"Data source '{target_data_source_name}' not found in agent output log")
                action_result['status'] = f"$$FAILED$$ Data source '{target_data_source_name}' not found in agent output log for summarisation."
                return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool, None

        if initial_df is None or initial_df.empty:
            action_result['final_answer'] = "No data available for summarisation."
            action_result['status'] = "Zero records found for summarisation. Original data was empty."
            action_result['chart_type'] = None
            return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool, initial_df

        # Generate final answer
        summarisation_system_message_content = f"""
        You are an expert data analyst. You have been provided with a dataset and specific instructions to generate a final answer.
        
        The dataset contains the following columns: {list(initial_df.columns)}
        Number of rows: {len(initial_df)}
        
        Your task is to: {instruction_for_llm_task_from_action_detail}
        
        Please provide a comprehensive, well-structured final answer that directly addresses the user's query.
        The answer should be clear, concise, and include relevant insights from the data.
        """

        # Sample data for context
        sample_data = initial_df.head(5).to_dict(orient='records')
        summarisation_human_prompt_content = f"""
        Here is a sample of the data (first 5 rows):
        {json.dumps(sample_data, indent=2)}
        
        Please generate the final answer based on the instructions provided.
        """

        messages_for_llm_call = [
            SystemMessage(content=summarisation_system_message_content),
            HumanMessage(content=summarisation_human_prompt_content)
        ]

        _, actual_llm_response_content, in_tokens, out_tokens = chat_with_model(
            model_type=model_type,
            api_key=api_key,
            messages=messages_for_llm_call,
            temperature=0,
            max_tokens=2000,
            json_schema={}
        )

        total_input_tokens_for_tool += in_tokens
        total_output_tokens_for_tool += out_tokens

        # LLM call for chart type and HighCharts configuration
        chart_type_prompt_messages = [HumanMessage(content=f"""
        You are a data visualization expert. Analyze the user query and determine if they want a chart or graph.

        If they want a chart:
        1. Detect the chart type from: 'bar', 'line', 'scatter', 'pie'
        2. Generate a complete HighCharts configuration object

        Available data columns from analysis: {', '.join(list(initial_df.columns)) if not initial_df.empty else 'No data available'}
        Number of rows: {len(initial_df)}

        Return your response in this exact JSON format:
        {{
          "chartType": "detected_chart_type_or_NA",
          "highchartsConfig": {{
            "chart": {{"type": "chart_type"}},
            "title": {{"text": "Chart Title"}},
            "xAxis": {{"categories": ["category1", "category2"]}},
            "yAxis": {{"title": {{"text": "Y Axis Label"}}}},
            "series": [{{
              "name": "Series Name",
              "data": [1, 2, 3, 4]
            }}]
          }}
        }}

        If no chart is requested, return:
        {{
          "chartType": "NA",
          "highchartsConfig": null
        }}

        Data sample (first 5 rows):
        {json.dumps(initial_df.head(5).to_dict(orient='records'), indent=2) if not initial_df.empty else 'No data available'}
        """)]

        _, chart_response, chart_in_tokens, chart_out_tokens = chat_with_model(
            messages=chart_type_prompt_messages,
            temperature=0,
            max_tokens=1000,  # Increased for full config
            model_type=model_type,
            api_key=api_key
        )

        total_input_tokens_for_tool += chart_in_tokens
        total_output_tokens_for_tool += chart_out_tokens

        # Parse the JSON response
        try:
            chart_data = json.loads(chart_response.strip())
            chart_type = chart_data.get('chartType', 'NA').strip().lower()
            highcharts_config = chart_data.get('highchartsConfig', None)
        except json.JSONDecodeError:
            # Fallback to original behavior if JSON parsing fails
            chart_type = chart_response.strip().lower() if chart_response.strip().lower() in ['bar', 'line', 'scatter', 'pie'] else 'NA'
            highcharts_config = None

        # Validate chart type
        valid_chart_types = ['bar', 'line', 'scatter', 'pie']
        if chart_type not in valid_chart_types:
            chart_type = 'NA'
            highcharts_config = None

        action_result['final_answer'] = actual_llm_response_content.strip()
        action_result['chart_type'] = chart_type
        action_result['highcharts_config'] = highcharts_config
        action_result['status'] = f"""
        Successfully generated final answer.
        Answer: {action_result['final_answer'][:100]}...
        Chart type: {action_result['chart_type']}
        HighCharts config: {'Generated' if highcharts_config else 'None'}
        """
        
        return action_result, total_input_tokens_for_tool, total_output_tokens_for_tool, initial_df
