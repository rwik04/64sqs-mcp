"""
Service for query data logic (decoupled from target.py)
"""

import time
import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage

from src.tools.data_interpreter.models import (
    AgentState,
    Action_Type,
    OutputEntry,
    Data_Source_Type,
    SNOWFLAKE,
)
from src.tools.data_interpreter.utils.db_utils import (
    create_connection,
    tool_fetch_from_external_db,
    tool_execute_pandasql_query,
    modify_query_for_snowflake,
)
from src.tools.data_interpreter.config import Config


class QueryService:
    def __init__(self):
        pass

    def tool_query_data(self, state: AgentState) -> AgentState:
        action = state['actions'][-1]
        action_details_list = action['action_details']
        agent_output_log = state.get('output', [])
        updated_state = self._deepcopy_state(state)
        current_output_log_for_state = updated_state.get('output', [])

        if not action_details_list:
            no_action_entry = OutputEntry(
                step_no=len(current_output_log_for_state) + 1,
                output={"status": "Skipped - No action details"},
                insight=None
            )
            current_output_log_for_state.append(no_action_entry)
            updated_state['output'] = current_output_log_for_state
            return updated_state

        for action_detail_item in action_details_list:
            llm_sql_instruction = action_detail_item['instruction']
            target_data_sources_info = action_detail_item['target_data_sources']

            action_result_status = ""
            final_json_data = None
            executed_sql_for_log = llm_sql_instruction

            # Resolve source connection info from shortlisted sources if missing
            for s in target_data_sources_info:
                if 'source_db_uri' not in s and s['source_type'] == Data_Source_Type.TABLE:
                    for user_source in updated_state['shortlisted_user_sources']:
                        if user_source['tablename'] == s['source_name']:
                            s['source_db_uri'] = user_source.get('source_db_uri')
                            s['db_type'] = user_source.get('db_type')
                            break

            # Group by DB URI
            db_connections: Dict[str, List[dict]] = {}
            for s in target_data_sources_info:
                if 'source_db_uri' in s:
                    db_hash = s['source_db_uri']
                else:
                    db_hash = Config.DB_URI
                if db_hash not in db_connections:
                    db_connections[db_hash] = []
                db_connections[db_hash].append(s)

            source_types_in_query = {s['source_type'] for s in target_data_sources_info}

            if len(source_types_in_query) == 1 and Data_Source_Type.TABLE in source_types_in_query:
                executed_sql_for_log = llm_sql_instruction
                for _, sources in db_connections.items():
                    engine = None
                    try:
                        start = time.time()
                        source_db_uri = sources[0].get('source_db_uri')
                        source_db_type = sources[0].get('db_type')
                        engine = create_connection(source_db_uri)
                        if source_db_type == SNOWFLAKE:
                            llm_sql_instruction = modify_query_for_snowflake(llm_sql_instruction, updated_state['model_type'], updated_state['api_key'])
                            llm_sql_instruction = llm_sql_instruction.replace("`", "")
                        if '%' in llm_sql_instruction:
                            llm_sql_instruction = llm_sql_instruction.replace('%', '%%')
                        queried_df_from_db = pd.read_sql_query(llm_sql_instruction, con=engine)
                        # Fill missing values
                        for col_name in queried_df_from_db.columns:
                            if queried_df_from_db[col_name].dtype == 'object':
                                queried_df_from_db[col_name] = queried_df_from_db[col_name].fillna('')
                            elif np.issubdtype(queried_df_from_db[col_name].dtype, np.number):
                                queried_df_from_db[col_name] = queried_df_from_db[col_name].astype(float).where(
                                    queried_df_from_db[col_name].notnull(), None)
                            elif np.issubdtype(queried_df_from_db[col_name].dtype, np.datetime64):
                                queried_df_from_db[col_name] = queried_df_from_db[col_name].where(queried_df_from_db[col_name].notnull(), None)
                                queried_df_from_db[col_name] = queried_df_from_db[col_name].apply(
                                    lambda x: x.isoformat() if pd.notnull(x) else None)
                        final_json_data = queried_df_from_db.to_dict(orient='records')
                        action_result_status = "success_external_db"
                    except Exception as e:
                        action_result_status = f"$$FAILED$$ Error querying external DB: {e}. SQL: {llm_sql_instruction}"
                        print(action_result_status)
                    finally:
                        if engine:
                            engine.dispose()
            else:
                # pandasql path with possible TEMP_TABLEs
                dataframes_for_pandasql_env: Dict[str, pd.DataFrame] = {}
                all_sources_loaded_successfully = True
                modified_sql_for_pandasql = llm_sql_instruction
                source_load_status_for_log = ""

                import re as _re
                for source_info in target_data_sources_info:
                    original_name = source_info['source_name']
                    source_type = source_info['source_type']
                    source_db_uri = source_info.get('source_db_uri')
                    db_type = source_info.get('db_type')
                    # Sanitize to a SQLite/pandasql-safe identifier: letters, digits, underscore only
                    clean_df_name = _re.sub(r"[^A-Za-z0-9_]", "_", original_name.replace(".csv", ""))
                    df_to_add = None

                    if source_type == Data_Source_Type.TABLE:
                        data_db, _, status_db = tool_fetch_from_external_db(original_name, source_db_uri, db_type)
                        if "$$FAILED$$" in status_db:
                            all_sources_loaded_successfully = False
                            source_load_status_for_log = status_db
                            break
                        if data_db:
                            df_to_add = pd.DataFrame(data_db)

                    elif source_type == Data_Source_Type.TEMP_TABLE:
                        found = False
                        # 1) Check new temp_tables in state (JSON→CSV ingestion)
                        if 'temp_tables' in updated_state and original_name in updated_state['temp_tables']:
                            df = updated_state['temp_tables'][original_name]
                            df_to_add = pd.DataFrame(df)
                            found = True
                        # 1b) Also check if any shortlisted sources carried inline temp rows
                        if not found:
                            for us in updated_state.get('shortlisted_user_sources', []):
                                if us.get('filetype') == 'temp' and us.get('tablename') == original_name and us.get('temp_rows'):
                                    df_to_add = pd.DataFrame(us['temp_rows'])
                                    found = True
                                    break
                        # 2) Fallback to previously extracted query_data entries
                        if not found:
                            for entry in reversed(agent_output_log):
                                if entry['output'] and entry['output'].get('data_extracted_name') == original_name:
                                    if 'data' in entry['output'] and entry['output']['data']:
                                        df = entry['output']['data']
                                        df_to_add = pd.DataFrame(df)
                                        found = True
                                        break
                        if not found:
                            all_sources_loaded_successfully = False
                            source_load_status_for_log = f"$$FAILED$$ Intermediate source '{original_name}' not found."
                            break
                    else:
                        all_sources_loaded_successfully = False
                        source_load_status_for_log = f"$$FAILED$$ Unsupported source type '{source_type}' for '{original_name}'."
                        break

                    if df_to_add is not None:
                        # Normalize unsupported SQLite cell types by JSON-encoding lists/dicts; replace NaN with None
                        def _normalize_cell(value):
                            if isinstance(value, (list, dict)):
                                try:
                                    return json.dumps(value, ensure_ascii=False)
                                except Exception:
                                    return str(value)
                            return value
                        for _col in df_to_add.columns:
                            df_to_add[_col] = df_to_add[_col].map(_normalize_cell)
                        df_to_add = df_to_add.where(pd.notnull(df_to_add), None)
                        dataframes_for_pandasql_env[clean_df_name] = df_to_add
                        # Replace occurrences in SQL for backtick, double-quoted and bare names
                        modified_sql_for_pandasql = modified_sql_for_pandasql.replace(f"`{original_name}`", clean_df_name)
                        modified_sql_for_pandasql = modified_sql_for_pandasql.replace(f'"{original_name}"', clean_df_name)
                        modified_sql_for_pandasql = modified_sql_for_pandasql.replace(original_name, clean_df_name)
                    else:
                        if not (source_load_status_for_log and "$$FAILED$$" in source_load_status_for_log):
                            source_load_status_for_log = f"$$WARNING$$ Source '{original_name}' yielded no data."
                        all_sources_loaded_successfully = False
                        break

                executed_sql_for_log = modified_sql_for_pandasql
                if all_sources_loaded_successfully:
                    start = time.time()
                    final_json_data, _, action_result_status = tool_execute_pandasql_query(
                        modified_sql_for_pandasql,
                        dataframes_for_pandasql_env
                    )
                else:
                    action_result_status = source_load_status_for_log

            # Common logging and state update
            updated_state['messages'].append(HumanMessage(content=action_result_status))
            output_content_for_log_entry = {
                "status": action_result_status,
                "data_extracted_name": None,
                "data": None
            }

            if "$$FAILED$$" in action_result_status:
                updated_state['retries_remaining'] -= 1
                if updated_state['retries_remaining'] >= 0:
                    add_step = {'tool_name': Action_Type.QUERY, 'reason': "Previous query op failed. Retrying."}
                else:
                    add_step = {'tool_name': Action_Type.END, 'reason': "Query op failed after max retries."}
                    updated_state['final_response'] = "Answer generation failed: query error."
                updated_state['remaining_steps'].append(add_step)

                output_entry = OutputEntry(
                    step_no=len(current_output_log_for_state) + 1,
                    planned_action=updated_state['current_step_reason'],
                    executed_action={"action": llm_sql_instruction, "action_type": "SQL_QUERY"},
                    output=output_content_for_log_entry,
                    insight=None
                )
                current_output_log_for_state.append(output_entry)
                updated_state['output'] = current_output_log_for_state
                return updated_state
            else:
                if updated_state['retries_remaining'] < updated_state['max_retries']:
                    updated_state['retries_remaining'] += 1
                data_id = str(time.time()).replace('.', '_')
                new_data_extracted_name = f"query_data_{data_id}".replace("-", "_")
                output_content_for_log_entry["data_extracted_name"] = new_data_extracted_name
                output_content_for_log_entry["data"] = final_json_data
                
                print(f"Storing query result with name: {new_data_extracted_name}")
                print(f"Data structure: {type(final_json_data)} with length: {len(final_json_data) if final_json_data else 0}")
                print(f"First few data items: {final_json_data[:2] if final_json_data else 'None'}")
                
                if final_json_data is not None and final_json_data == []:
                    output_content_for_log_entry["status"] = f"Received empty dataset (Zero records). Result name: {new_data_extracted_name}"
                elif final_json_data is not None:
                    output_content_for_log_entry["status"] = f"Successfully queried data. Result name: {new_data_extracted_name}."
                output_entry = OutputEntry(
                    step_no=len(current_output_log_for_state) + 1,
                    planned_action=updated_state['current_step_reason'],
                    executed_action={"action": llm_sql_instruction, "action_type": "SQL_QUERY"},
                    output=output_content_for_log_entry,
                )
                current_output_log_for_state.append(output_entry)

        updated_state['output'] = current_output_log_for_state
        return updated_state

    def _deepcopy_state(self, state: AgentState) -> AgentState:
        # shallow copy of known top-level keys + deep copy of nested lists
        import copy as _copy
        return _copy.deepcopy(state)
