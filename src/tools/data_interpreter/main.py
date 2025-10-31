"""
Main orchestration for data interpreter agent (decoupled from target.py)
"""

import sys
import os
import json
import time
import logging
import pprint
from typing import Dict, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from langgraph.graph import StateGraph, END
from src.tools.data_interpreter.models import AgentState, OutputEntry, Action_Type
from src.tools.data_interpreter.services.agent_service import AgentService
from src.tools.data_interpreter.services.query_service import QueryService
from src.tools.data_interpreter.services.annotation_service import AnnotationService
from src.tools.data_interpreter.services.summarisation_service import SummarisationService
from src.tools.data_interpreter.utils.llm_utils import chat_with_model
from src.tools.data_interpreter.utils.source_utils import shortlist_user_sources, prepare_initial_message_thread
from langchain_core.messages import HumanMessage

class DataInterpreter:
    """Main class that orchestrates the data interpreter agent workflow using LangGraph."""
    
    def __init__(self, client, project_id, filenames, model_type, api_key, query):
        self.client = client
        self.project_id = project_id
        self.filenames = filenames
        self.model_type = model_type
        self.api_key = api_key
        self.query = query
        
        # Initialize services
        self.agent_service = AgentService()
        self.query_service = QueryService()
        self.annotation_service = AnnotationService()
        self.summarisation_service = SummarisationService()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
    def _build_workflow(self):
        """Build the LangGraph workflow."""
        workflow_builder = StateGraph(AgentState)
        
        # Define the nodes
        workflow_builder.add_node("agent", self.agent_service.agent)
        workflow_builder.add_node("query_data", self.query_service.tool_query_data)
        workflow_builder.add_node("annotate_data", self.annotation_service.tool_annotate_data)
        workflow_builder.add_node("summarise_answer", self.summarisation_service.tool_summarise_answer)
        
        # Build graph
        workflow_builder.set_entry_point("agent")
        workflow_builder.add_conditional_edges(
            "agent", 
            self._select_next_action, 
            {
                "query_data": "query_data", 
                "annotate_data": "annotate_data", 
                "summarise_answer": "summarise_answer", 
                END: END
            }
        )
        workflow_builder.add_edge("query_data", "agent")
        workflow_builder.add_edge("annotate_data", "agent")
        workflow_builder.add_edge("summarise_answer", "agent")
        
        # Compile
        return workflow_builder.compile()
    
    def _select_next_action(self, state: AgentState):
        """
        This function checks if the agent was able to identify at least one valid action
        That action could be invoking of a tool or ending of the execution
        It processes the last action object suggested the agent to identify the next action type
        """
        next_action = state['actions'][-1]
        next_action_type = next_action['action_type']
        return next_action_type
    
    def _initialize_state(self) -> AgentState:
        """Initialize the agent state with all required components."""
        token_tracker = {}
        
        # Enrich provided filenames with temp JSON-derived tables if any
        enriched_sources = []
        temp_tables: Dict[str, list] = {}
        for src in (self.filenames or []):
            try:
                if src.get('filetype') == 'temp':
                    jpath = src.get('filename')
                    base = src.get('displayname') or (os.path.splitext(os.path.basename(jpath))[0] + ".csv")
                    rows = []
                    with open(jpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
                        rows = data
                    elif isinstance(data, dict):
                        if all(isinstance(v, list) for v in data.values()):
                            max_len = max((len(v) for v in data.values()), default=0)
                            for i in range(max_len):
                                row = {}
                                for k, v in data.items():
                                    row[k] = v[i] if i < len(v) else None
                                rows.append(row)
                        else:
                            rows = [data]
                    else:
                        rows = [{"value": data}]
                    temp_tables[base] = rows
                    src = {**src, 'displayname': base, 'tablename': base, 'temp_rows': rows}
            except Exception as e:
                print(f"Error loading temp JSON for source {src.get('displayname', src.get('filename'))}: {e}")
            enriched_sources.append(src)

        # Get shortlisted (relevant) user sources - include BOTH normal and temp equally
        shortlisted_filenames = []
        start = time.time()

        shortlisted_all, input_tokens, output_tokens = shortlist_user_sources(
            user_query=self.query,
            user_sources=enriched_sources,
            model_type=self.model_type,
            api_key=self.api_key
        )
        shortlisted_filenames = shortlisted_all
        token_tracker.update({
            "shortlist_user_sources": {
                self.model_type: {"input_tokens": input_tokens, "output_tokens": output_tokens}
            }
        })


        # Ask the agent to create an initial plan/route for accomplishing the task
        remaining_steps = []
        if len(shortlisted_filenames) == 0:
            messages = prepare_initial_message_thread(
                user_query=self.query, 
                user_sources=shortlisted_filenames, 
                model_type=self.model_type, 
                api_key=self.api_key
            )
            remaining_steps = [{"tool_name": "__end__", "reason": "No relevant sources found"}]
            plan = remaining_steps.copy()
            token_tracker.update({
                "prepare_initial_message_thread": {
                    self.model_type: {"input_tokens": 0, "output_tokens": 0}
                }
            })
        else:
            messages = prepare_initial_message_thread(
                user_query=self.query, 
                user_sources=shortlisted_filenames, 
                model_type=self.model_type, 
                api_key=self.api_key
            )
            start2 = time.time()
            messages, response, input_tokens, output_tokens = chat_with_model(
                messages=messages, 
                temperature=0, 
                max_tokens=4096, 
                model_type=self.model_type, 
                api_key=self.api_key
            )

            start = time.time()

            print(f"messages: {messages}")
            print(f"Outer llm call took {time.time() - start} seconds")
            response = response.replace("```python", "").replace("```json", "").replace("```", "")

            remaining_steps = eval(response.strip())
            plan = remaining_steps.copy()
            print(f"Plan: {type(remaining_steps)} - {plan}")
            remaining_steps.reverse()
            token_tracker.update({
                "prepare_initial_message_thread": {
                    self.model_type: {"input_tokens": input_tokens, "output_tokens": output_tokens}
                }
            })

        if len(remaining_steps) == 0:
            remaining_steps = [{"tool_name": "__end__", "reason": "Could not create plan"}]

        print("#######################################################################################")
        print(f"Remaining steps {remaining_steps}")
        print("######################################################################################")
        print(f"Plan of action generated in {time.time() - start} s")

        token_tracker.update({
            "workflow_execution": {
                self.model_type: {"input_tokens": 0, "output_tokens": 0}
            }
        })

        # Prune temp_tables to only shortlisted temp sources
        if temp_tables:
            shortlisted_temp_names = {
                (s.get('displayname') or s.get('tablename')) if s.get('filetype') == 'temp' else None
                for s in shortlisted_filenames if s.get('filetype') == 'temp'
            }
            shortlisted_temp_names.discard(None)
            temp_tables = {k: v for k, v in temp_tables.items() if k in shortlisted_temp_names}

        # Inform the agent about available TEMP tables, their names and inferred columns
        if temp_tables:
            temp_tables_desc_lines = [
                "The following STRUCTURED_TABLE_TEMPORARY sources are available for querying (refer by source_name exactly):"
            ]
            for tname, rows in temp_tables.items():
                cols = []
                if rows and isinstance(rows, list) and isinstance(rows[0], dict):
                    cols = list(rows[0].keys())
                temp_tables_desc_lines.append(f"- {tname} | columns: {', '.join(map(str, cols))}")
            messages.append(HumanMessage(content="\n".join(temp_tables_desc_lines)))

        # Define initial state
        state = AgentState(
            client=self.client,
            project_id=self.project_id,
            model_type=self.model_type,
            api_key=self.api_key,
            token_tracker=token_tracker,
            user_query=self.query,
            original_user_sources=self.filenames,
            shortlisted_user_sources=shortlisted_filenames,
            temp_tables=temp_tables,
            messages=messages,
            plan=plan,
            actions=[],
            retries_remaining=2,
            max_retries=2,
            current_step_reason="",
            remaining_steps=remaining_steps,
            chart={'chartType': "NA"},
            tableData=[{'data': [], 'headers': []}],
            insight=None,
            confidence=None,
            output=[]
        )
        
        return state
    
    def _process_final_response(self, updated_state: AgentState) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Process the final response and return the formatted output."""
        # Process final response
        if updated_state['insight'] is None:
            updated_state['insight'] = "Apologies but your query does not look relevant to any of the selected files. In case you think otherwise, can you try rephrasing it?"
            # Build a minimal shortlist entry; include 'id' only when present
            minimal_shortlist = []
            for filename in self.filenames:
                entry = {
                    'displayname': filename.get('displayname'),
                    'filetype': filename.get('filetype')
                }
                if 'id' in filename:
                    entry['id'] = filename['id']
                minimal_shortlist.append(entry)
            updated_state['shortlisted_user_sources'] = minimal_shortlist
            updated_state['confidence'] = "HIGH"
            updated_state['tableData'] = []
            updated_state['chart'] = {'chartType': "NA", 'highchartsConfig': None}
            # Do not append a fallback OutputEntry to avoid creating a redundant "last step"

        # Prepare final response
        filedetails = []
        table_name_update = []
        print('Shortlisted User Sources Loop!')
        for item in updated_state.get('shortlisted_user_sources', []):
            print(item)
            fd = {
                "displayname": item["displayname"],
                "filetype": item["filetype"]
            }
            if "id" in item:
                fd["id"] = item["id"]
            filedetails.append(fd)
            table_name_update.append({
                "key": item.get("tablename", item["displayname"]),
                "value": item["displayname"]
            })

        for item in updated_state.get('output', []):
            if "executed_action" in item:
                executed_action = item["executed_action"]
                if executed_action and "action" in executed_action:
                    action = executed_action["action"]
                    for subItem in table_name_update:
                        action = action.replace(subItem['key'], subItem["value"])
                    item["executed_action"]['action'] = action

        final_response = {
            'filedetails': filedetails,
            'confidence': updated_state['confidence'],
            'chart': updated_state['chart'],
            'tableData': updated_state.get('tableData', []),
            'output': updated_state.get('output', [])
        }

        return final_response, updated_state['token_tracker']

    def run(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run the data interpreter workflow synchronously.
        
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (final_response, token_tracker)
        """
        start = time.time()
        
        # Initialize state
        state = self._initialize_state()
        
        # Execute workflow
        updated_state = {}
        for output in self.workflow.stream(state):
            for key, value in output.items():
                if key == 'agent':
                    pprint.pprint(f"Output from node '{key}':")
                    pprint.pprint("---")
                    pprint.pprint("Proposed Next Action:\n")
                    pprint.pprint(value['actions'][-1], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                    pprint.pprint("Updated Plan:\n")
                    pprint.pprint(value['remaining_steps'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                    pprint.pprint(f"Retries Remaining:\n{value['retries_remaining']}")
                    pprint.pprint("---")
                    pprint.pprint(f"Tokens Consumed:\n")
                    pprint.pprint(value['token_tracker'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                else:
                    pprint.pprint(f"Output from node '{key}':")
                    pprint.pprint("---")
                    pprint.pprint("Updated Plan:\n")
                    pprint.pprint(value['remaining_steps'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                    pprint.pprint(f"Tokens Consumed:\n")
                    pprint.pprint(value['token_tracker'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                updated_state = value
            pprint.pprint("----------------")
        
        # Process final response
        final_response, token_tracker = self._process_final_response(updated_state)
        
        print(f"Workflow executed in {time.time() - start} seconds")
        
        return final_response, token_tracker
    
    async def arun(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Run the data interpreter workflow asynchronously.
        
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (final_response, token_tracker)
        """
        start = time.time()
        
        # Initialize state
        state = self._initialize_state()
        
        # Execute workflow asynchronously
        updated_state = {}
        async for output in self.workflow.astream(state):
            for key, value in output.items():
                if key == 'agent':
                    pprint.pprint(f"Output from node '{key}':")
                    pprint.pprint("---")
                    pprint.pprint("Proposed Next Action:\n")
                    pprint.pprint(value['actions'][-1], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                    pprint.pprint("Updated Plan:\n")
                    pprint.pprint(value['remaining_steps'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                    pprint.pprint(f"Retries Remaining:\n{value['retries_remaining']}")
                    pprint.pprint("---")
                    pprint.pprint(f"Tokens Consumed:\n")
                    pprint.pprint(value['token_tracker'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                else:
                    pprint.pprint(f"Output from node '{key}':")
                    pprint.pprint("---")
                    pprint.pprint("Updated Plan:\n")
                    pprint.pprint(value['remaining_steps'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                    pprint.pprint(f"Tokens Consumed:\n")
                    pprint.pprint(value['token_tracker'], indent=2, width=80, depth=None)
                    pprint.pprint("---")
                updated_state = value
            pprint.pprint("----------------")
        
        # Process final response
        final_response, token_tracker = self._process_final_response(updated_state)
        
        print(f"Workflow executed in {time.time() - start} seconds")
        
        return final_response, token_tracker


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    model_type = 'gpt-4.1-2025-04-14'
    api_key = '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'
    
    # Mock data for testing (replace with actual data)
    client = '64sqs'  # Replace with actual client
    project_id = "80"
    
    # filenames = [
    # {
    #     'id': 164, # 537, # ----- id from file_manager
    #     'extid': 10, # 150, # ----- ext_id from file_manager
    #     'displayname': 'Nike Quarterly Revenue.xlsx (Sheet1)', # ----- file_name from file_manager
    #     'filename': 'Nike_Quarterly_Revenue_99998538-a86b-11ef-9c86-0242ac120002.xlsx', # ----- internal_name from file_manager
    #     # 'tablename': '99ab18de-a86b-11ef-9c86-0242ac120002', # ----- table_name from csv_file_manager or excel_file_manager
    #     'tablename': '4e858044-1c31-11f0-a635-0242ac120005',
    #     # 'filetype': 'excel', # ----- structured or excel... when file_type in file_manager belongs to ('CSV', 'XLSX')
    #     'filetype': 'structured', # ----- structured or excel... when file_type in file_manager belongs to ('CSV', 'XLSX')
    #     'source_db_uri': 'mysql://root:May_2022@db-docqna.cmgtohlasrf0.ap-southeast-1.rds.amazonaws.com:3306/llmqna-dev'
    # },
    # {
    #     'id': 210, # 537, # ----- id from file_manager
    #     'extid': 2, # 150, # ----- ext_id from file_manager
    #     'displayname': 'Polaris Glassdoor Reviews Sample 20181024.xlsx (Sheet1)', # ----- file_name from file_manager
    #     'filename': 'Polaris_Glassdoor_Reviews_Sample_20181024_f51be548-b524-11ef-9a03-0242ac120002.xlsx', # ----- internal_name from file_manager
    #     # 'tablename': 'f5c2c98a-b524-11ef-9a03-0242ac120002', # ----- table_name from csv_file_manager or excel_file_manager
    #     'tablename': '2da1e630-c770-11ef-99c1-0242ac120005',
    #     'filetype': 'excel', # ----- structured or excel... when file_type in file_manager belongs to ('CSV', 'XLSX')
    #     'source_db_uri': 'mysql://root:May_2022@db-docqna.cmgtohlasrf0.ap-southeast-1.rds.amazonaws.com:3306/llmqna-dev'
    # }
    # ]

    query = "Aggregate the extracted data into a table with one row per interviewee and the following columns: 'Cloud Platforms', 'Recent Challenges Solved', 'Debugging Performance Approaches', 'SQL vs NoSQL Description', and 'Keeping Up with Tech Trends'. Then, analyze for themes and patterns by identifying which cloud platforms are most commonly mentioned, the most common debugging strategies, and what percentage mention open-source as a way of staying up-to-date. Summarize these patterns"
    
    # Use temp JSONs as primary sources via filenames list (minimal fields)
    filenames = [
        {
            'displayname': 'Interviews.csv',
            'filename': '/home/rwik/code/mcp_server/temp/Alice_Johnson_Interview_c635c04c-8d40-11f0-b031-0242ac120004.pdf_flat_8b97c17b.json',
            'filetype': 'temp'
        },
        # {
        #     'displayname': 'Interview_-_Scientist_1_6344cd58-...23b76546.csv',
        #     'filename': '/home/rwik/code/mcp_server/temp/Interview_-_Scientist_1_6344cd58-4dbb-11f0-a9ac-0242ac120005.txt_result_23b76546.json',
        #     'filetype': 'temp'
        # }
    ]

    # Create DataInterpreter instance
    interpreter = DataInterpreter(
        client=client,
        project_id=project_id,
        filenames=filenames,
        model_type=model_type,
        api_key=api_key,
        query=query
    )
    
    # Run the workflow synchronously
    final_response, token_tracker = interpreter.run()
    
    print("\n-------------------\n")
    print("Final Response:")
    print(final_response)
