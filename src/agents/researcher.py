import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Tuple, List, Any
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from fastmcp import Client
import sys

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agents.tool_manager import ToolManager
from src.agents.prompts import get_system_prompt
from src.agents.context_provider import build_pre_toolcall_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Researcher:
    def __init__(self, instructions: Optional[str] = None, mcp_url: str = "https://04eae89e8eae.ngrok-free.app/mcp"):
        self.instructions = instructions
        self.mcp_url = mcp_url
        
        # Initialize LLM client
        self.model = ChatOpenAI(
            model="gpt-4.1",
            output_version="responses/v1",
            api_key=os.getenv("LLM_API_KEY"),
            timeout=300,  # seconds
            max_retries=3,
        )
        
        # Bind MCP tools to LLM
        self.llm = self.model.bind_tools(
            [
                {
                    "type": "mcp",
                    "server_label": "docqna",
                    "server_url": mcp_url,
                    "require_approval": "never",
                }
            ]
        )
        
        # Initialize components
        self.system_prompt = get_system_prompt(instructions)
        self.tool_manager = ToolManager("http://localhost:8000/mcp")
        
        # Track execution state
        self.execution_history: List[Dict[str, Any]] = []
        self.temp_files: List[str] = []

    def get_action_plan(self, query: str, user_sources: Dict[str, List[str]] = None) -> Tuple[Dict[Any, Any], List[BaseMessage]]:
        """
        Generate an action plan for the given query.
        
        Args:
            query: The research query
            user_sources: Optional categorized user sources for context
        
        Returns:
            Tuple of (action_plan_dict, messages_list)
        """
        logger.info(f"Generating action plan for query: {query[:100]}...")
        
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        # Add context from user sources if provided
        if user_sources:
            logger.info("Adding user source context to action plan generation")
            context_messages = self._build_context_for_sources(user_sources)
            messages.extend(context_messages)
        
        messages.extend([
            HumanMessage(
                content=(
                    f"""
                    Query: {query}
                    
                    Before creating the action plan, answer these two diagnostic questions:
                    1. Is the user asking for a highly structured, targeted analysis to arrive at precise quantitative insights? Or are they looking for open-ended broad analysis to arrive at qualitative insights?
                    2. Based on the query's complexity, how many distinct steps will be needed to fully address it?
                    """
                )
            ),
            HumanMessage(
                content=(
                    f"""
                    Query: {query}
                    Drawing on the full range of advanced analytical tools that are available to you via the MCP server, carefully create a comprehensive and actionable step-by-step action plan to solve the user's query above. 

                    Each step should clearly specify:
                    - Which MCP tool will be used 
                    - Which data source(s) or intermediate results the tool will operate on 
                    - The core reasoning or thought process for choosing the tool and approach

                    Do not include any steps that rely on tools or resources that are not accessible through the MCP server—any such steps will result in your action plan being discarded.

                    Please respond with strictly a JSON action plan that covers all required steps, following the correct format—do not include any explanations, notes, or extra text outside of the JSON.
                    """
                )
            ),
        ])

        try:
            response = self.llm.invoke(messages)
            messages.append(response)
            
            # Extract the clean action plan JSON
            action_plan_json = self._extract_action_plan(response)
            
            logger.info(f"Generated action plan with {len(action_plan_json.get('action_plan', []))} steps")
            # Log the full action plan JSON
            logger.info("Full action plan JSON:\n" + json.dumps(action_plan_json, indent=2, ensure_ascii=False))
            return action_plan_json, messages
            
        except Exception as e:
            logger.error(f"Error generating action plan: {e}")
            return {"action_plan": []}, messages

    def _extract_action_plan(self, response: BaseMessage) -> Dict[Any, Any]:
        """Extract action plan JSON from LLM response."""
        try:
            content = response.content
            
            if isinstance(content, list) and len(content) > 0:
                # Extract from structured content
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        json_text = item['text']
                        return json.loads(json_text)
            elif isinstance(content, str):
                # Try to parse as JSON directly
                return json.loads(content)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
        except Exception as e:
            logger.error(f"Error extracting action plan: {e}")
            
        return {"action_plan": []}

    def _categorize_filenames(self, filenames: List[str]) -> Dict[str, List[str]]:
        """
        Categorize filenames into unstructured and structured sources using heuristics.
        
        Args:
            filenames: List of filenames to categorize
            
        Returns:
            Dictionary with 'unstructured' and 'structured' keys containing categorized filenames
        """
        unstructured_extensions = {'.pdf', '.txt', '.doc', '.docx', '.ppt', '.pptx', '.rtf', '.odt', '.html', '.htm', '.md', '.xml'}
        structured_extensions = {'.csv', '.tsv', '.json', '.jsonl', '.xlsx', '.xls', '.parquet', '.db', '.sqlite', '.sql'}
        
        categorized = {
            'unstructured': [],
            'structured': []
        }
        
        for filename in filenames:
            # Extract file extension
            file_ext = os.path.splitext(filename.lower())[1]
            
            if file_ext in unstructured_extensions:
                categorized['unstructured'].append(filename)
            elif file_ext in structured_extensions:
                categorized['structured'].append(filename)
            else:
                # Default to unstructured for unknown extensions
                logger.warning(f"Unknown file extension '{file_ext}' for file '{filename}', categorizing as unstructured")
                categorized['unstructured'].append(filename)
        
        logger.info(f"Categorized {len(filenames)} files: {len(categorized['unstructured'])} unstructured, {len(categorized['structured'])} structured")
        return categorized

    def get_categorized_sources(self, filenames: List[str]) -> Dict[str, List[str]]:
        """
        Public method to categorize filenames into unstructured and structured sources.
        
        Args:
            filenames: List of filenames to categorize
            
        Returns:
            Dictionary with 'unstructured' and 'structured' keys containing categorized filenames
        """
        return self._categorize_filenames(filenames)

    def _infer_file_type(self, filename: str) -> str:
        """Infer file type from filename extension."""
        ext = os.path.splitext(filename.lower())[1]
        type_mapping = {
            '.csv': 'csv',
            '.tsv': 'csv',
            '.json': 'json',
            '.jsonl': 'json',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.parquet': 'parquet',
            '.db': 'db',
            '.sqlite': 'db',
            '.sql': 'db'
        }
        return type_mapping.get(ext, 'csv')  # Default to csv

    def _convert_to_structured_sources(self, filenames: List[str]) -> List[Dict[str, Any]]:
        """Convert filenames to structured source format for context_provider."""
        structured_sources = []
        for filename in filenames:
            structured_sources.append({
                'filename': filename,
                'filetype': self._infer_file_type(filename),
                'displayname': filename
            })
        return structured_sources

    def _build_context_for_sources(self, user_sources: Dict[str, List[str]]) -> List[BaseMessage]:
        """
        Build context messages for user-provided sources using context_provider.
        
        Args:
            user_sources: Dictionary with 'unstructured' and 'structured' keys
            
        Returns:
            List of HumanMessage objects with context
        """
        if not user_sources:
            return []
        
        structured_sources = self._convert_to_structured_sources(user_sources.get('structured', []))
        
        return build_pre_toolcall_context(
            doc_summary_s3_paths=user_sources.get('unstructured', []),
            structured_sources=structured_sources
        )

    async def execute_actions(self, action_plan: Dict[Any, Any], messages: List[BaseMessage], user_sources: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """
        Execute the action plan dynamically, handling all steps.
        
        Args:
            action_plan: The action plan dictionary
            messages: Initial conversation messages
            user_sources: Dictionary with 'unstructured' and 'structured' keys containing categorized filenames
            
        Returns:
            Final execution results
        """
        logger.info("Starting action plan execution")
        
        steps = action_plan.get("action_plan", [])
        if not steps:
            logger.warning("No steps found in action plan")
            return {"error": "No steps found in action plan"}
        
        logger.info(f"Executing {len(steps)} steps")

        # Log the intermediate action plan JSON at the start of execution
        logger.info("Executing on action plan:\n" + json.dumps(action_plan, indent=2, ensure_ascii=False))

        # Only log the filenames once, if relevant (do not repeat per step)
        if user_sources:
            if user_sources.get('unstructured'):
                logger.info(f"Using {len(user_sources['unstructured'])} unstructured files.")
            if user_sources.get('structured'):
                logger.info(f"Using {len(user_sources['structured'])} structured files.")

        # Initialize execution state
        current_messages = messages.copy()
        execution_results = []
        
        # Build initial context before first tool call if user sources are provided
        if user_sources:
            logger.info("Building initial context from user sources")
            initial_context = self._build_context_for_sources(user_sources)
            current_messages.extend(initial_context)
        
        for step_idx, step in enumerate(steps):
            try:
                logger.info(f"Executing step {step_idx + 1}: {step.get('step_caption', 'Unknown')}")
                
                # Build context for this step
                context_messages = await self._build_step_context(step, execution_results, user_sources)
                
                # Log the intermediate step parameters JSON before passing to tool_manager
                logger.info(f"Generating tool parameters for step {step_idx + 1}: '{step.get('step_caption', '')}'")

                # Generate tool parameters
                tool_params = await self._generate_tool_parameters(
                    step, current_messages, context_messages, step_idx + 1
                )

                # Log generated tool parameters JSON before passing to tool_manager
                if tool_params:
                    logger.info(f"Tool parameters for step {step_idx + 1}:\n{json.dumps(tool_params, indent=2, ensure_ascii=False)}")
                else:
                    logger.error(f"No tool parameters generated for step {step_idx + 1}")

                if not tool_params:
                    logger.error(f"Failed to generate parameters for step {step_idx + 1}")
                    continue
                
                # Execute the tool
                tool_result = await self.tool_manager.call_tool(
                    tool_params.get("tool"), 
                    tool_params.get("parameters", {}), 
                    action_plan
                )
                
                # Track execution
                step_result = {
                    "step_no": step_idx + 1,
                    "step_caption": step.get("step_caption", ""),
                    "tool": tool_params.get("tool"),
                    "parameters": tool_params.get("parameters", {}),
                    "result": tool_result.content,
                    "success": True
                }
                
                execution_results.append(step_result)
                current_messages.append(tool_result)
                
                # Extract temp files if any
                self._extract_temp_files(tool_result.content)
                
                logger.info(f"Step {step_idx + 1} completed successfully")
                
            except Exception as e:
                logger.error(f"Error executing step {step_idx + 1}: {e}")
                step_result = {
                    "step_no": step_idx + 1,
                    "step_caption": step.get("step_caption", ""),
                    "error": str(e),
                    "success": False
                }
                execution_results.append(step_result)
        
        # Generate final synthesis
        final_result = await self._generate_final_synthesis(current_messages, execution_results)
        
        return {
            "action_plan": action_plan,
            "execution_results": execution_results,
            "final_synthesis": final_result,
            "temp_files": self.temp_files
        }

    async def _build_step_context(self, step: Dict[str, Any], execution_results: List[Dict[str, Any]], user_sources: Dict[str, List[str]] = None) -> List[BaseMessage]:
        """Build context messages for the current step using context_provider functions."""
        # Get target data sources
        target_data = step.get("target_data", [])
        
        # Prepare context parameters
        temp_files = []
        structured_sources = []
        doc_summary_paths = []
        
        for data_source in target_data:
            if data_source == "UNSTRUCTURED":
                # Use user-provided unstructured files
                if user_sources and user_sources.get('unstructured'):
                    doc_summary_paths.extend(user_sources['unstructured'])
            elif data_source == "STRUCTURED":
                # Use user-provided structured files
                if user_sources and user_sources.get('structured'):
                    structured_sources.extend(self._convert_to_structured_sources(user_sources['structured']))
            elif data_source.startswith("TEMP_STEP_"):
                # Extract temp files from previous steps
                step_num = int(data_source.split("_")[-1])
                if step_num <= len(execution_results):
                    temp_files.extend(self.temp_files)
        
        # Use the context_provider function to build context
        return build_pre_toolcall_context(
            temp_files=temp_files,
            structured_sources=structured_sources,
            doc_summary_s3_paths=doc_summary_paths
        )

    async def _generate_tool_parameters(
        self, 
        step: Dict[str, Any], 
        current_messages: List[BaseMessage], 
        context_messages: List[BaseMessage],
        step_number: int
    ) -> Optional[Dict[str, Any]]:
        """Generate tool parameters for the current step."""
        try:
            # Prepare messages for parameter generation
            param_messages = current_messages.copy()
            param_messages.extend(context_messages)
            
            param_messages.append(
                HumanMessage(
                    content=f"""
                    Now proceed to Step {step_number} of the action plan: "{step.get('step_caption', '')}"
                    
                    Tool to use: {step.get('target_entity', 'unknown')}
                    Reasoning: {step.get('thoughts', '')}
                    
                    Provide ONLY the tool calling parameters in JSON format:
                    
                    {{
                "tool": "tool_name",
                        "parameters": {{
                            ...
                        }}
                    }}
                    
                    Make sure the parameters are appropriate for the tool and the current context.
                    """
                )
            )
            
            response = self.llm.invoke(param_messages)
            
            # Extract tool parameters
            tool_params = self._extract_tool_parameters(response)
            
            if not tool_params:
                logger.warning(f"Failed to extract tool parameters for step {step_number}")
                return None
                
            return tool_params
            
        except Exception as e:
            logger.error(f"Error generating tool parameters for step {step_number}: {e}")
            return None

    def _extract_tool_parameters(self, response: BaseMessage) -> Optional[Dict[str, Any]]:
        """Extract tool parameters from LLM response."""
        try:
            content = response.content
            
            if isinstance(content, list) and len(content) > 0:
                for item in content:
                    if isinstance(item, dict) and 'text' in item:
                        return json.loads(item['text'])
            elif isinstance(content, str):
                return json.loads(content)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in tool parameters: {e}")
        except Exception as e:
            logger.error(f"Error extracting tool parameters: {e}")
            
        return None

    def _extract_temp_files(self, content: str) -> None:
        """Extract temp file paths from tool results."""
        try:
            if isinstance(content, str):
                # Try to parse as JSON to find temp files
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        temp_file = parsed.get("temp_file")
                        if temp_file and temp_file not in self.temp_files:
                            self.temp_files.append(temp_file)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            logger.error(f"Error extracting temp files: {e}")

    async def _generate_final_synthesis(
        self, 
        messages: List[BaseMessage], 
        execution_results: List[Dict[str, Any]]
    ) -> str:
        """Generate final synthesis of all execution results."""
        try:
            synthesis_messages = messages.copy()
            synthesis_messages.append(
                HumanMessage(
                    content="""
                    Based on all the tool executions and results above, please provide a comprehensive final synthesis that:
                    
                    1. Summarizes the key findings from all steps
                    2. Answers the original user query completely
                    3. Highlights important insights and patterns
                    4. Provides actionable conclusions
                    
                    Format your response as a clear, well-structured summary that directly addresses the user's needs.
                    """
                )
            )
            
            response = self.llm.invoke(synthesis_messages)
            return response.content if isinstance(response.content, str) else str(response.content)
            
        except Exception as e:
            logger.error(f"Error generating final synthesis: {e}")
            return "Error generating final synthesis"

    async def run_research(self, query: str, filenames: List[str] = None) -> Dict[str, Any]:
        """
        Complete research workflow: plan -> execute -> synthesize.
        
        Args:
            query: The research query
            filenames: List of filenames to analyze (will be categorized automatically)
            
        Returns:
            Complete research results
        """
        logger.info(f"Starting research for query: {query[:100]}...")
        
        try:
            # Categorize filenames if provided
            user_sources = None
            if filenames:
                logger.info(f"Categorizing {len(filenames)} input files")
                user_sources = self._categorize_filenames(filenames)
                # Only log the number of files, avoid logging the actual filenames repeatedly
                if user_sources['unstructured']:
                    logger.info(f"Found {len(user_sources['unstructured'])} unstructured files")
                if user_sources['structured']:
                    logger.info(f"Found {len(user_sources['structured'])} structured files")
            
            # Step 1: Generate action plan
            action_plan, messages = self.get_action_plan(query, user_sources)
            
            if not action_plan.get("action_plan"):
                return {"error": "Failed to generate action plan"}
            
            # Step 2: Execute actions
            results = await self.execute_actions(action_plan, messages, user_sources)
            
            logger.info("Research completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in research workflow: {e}")
            return {"error": str(e)}

async def main():
    """Example usage of the Researcher agent."""
    usecase_prompt = """
    Use Case: Interview Analysis & Theme Identification

    Organizations often conduct interviews to gather feedback, opinions, or experiences from participants.
    However, turning raw interview transcripts into actionable insights requires a structured process.

    We want to analyse a lot of interviews to gather insights. The analysis process will look broadly as follows. 
    The execution of different steps would need to be contextualized as per the available data at any given point in time and the original request.

    1. **Information Retrieval** - First, the interview data is scanned to locate answers to a set of predefined research questions. This ensures that only relevant parts of the transcript are considered.
    2. **Theme/Cohort Identification and Analysis** - Each response is then analyzed to check whether specific themes/cohort (mention of a specific tool/skillset) are present or absent. For example, answers might be tagged "Yes" if a theme is expressed and "No" if it is not. If requested by the user, then aggreagted statistics over those themes/cohorts should also be calculated.
    3. **Insight summarization** - Finally, the findings (just the broad information or deep dive into themes) are distilled into a concise 3-4 sentence summary that captures the key patterns, highlights, and implications emerging from the interviews.

    This process transforms unstructured interview data into clear, measurable insights. By combining qualitative theme identification with quantitative breakdowns, decision-makers gain both depth (what people are saying) and breadth (how widespread those views are), enabling more informed strategies and actions.
    """

    researcher = Researcher(instructions=usecase_prompt)

    # Define the filenames
    filenames = [
        "Dr_Anjali_Singh_India_Detailed_Interview_01a9299e-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Anna_Weber_Germany_Detailed_Interview_01a99500-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Arjun_Mehta_India_Detailed_Interview_01aa9662-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Clara_Hoffmann_Germany_Detailed_Interview_01ad35ca-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_David_Thompson_US_Detailed_Interview_01ad10cc-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Emily_Roberts_US_Detailed_Interview_02d6a2e2-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Erik_Vogel_Germany_Detailed_Interview_02d71ccc-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Felix_Schneider_Germany_Detailed_Interview_02d6d17c-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Helena_Brandt_Germany_Detailed_Interview_02d74238-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_James_Miller_US_Detailed_Interview_02d77226-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Jonas_Fischer_Germany_Detailed_Interview_03d35bea-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Kavita_Joshi_India_Detailed_Interview_03d4686e-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Lukas_Meier_Germany_Detailed_Interview_03d8f258-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Michael_Anderson_US_Detailed_Interview_03d9e0d2-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Neha_Reddy_India_Detailed_Interview_03da310e-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Olivia_Davis_US_Detailed_Interview_04e0ac9a-a27b-11f0-95d8-0242ac120004.pdf",
        "Dr_Priya_Sharma_India_Detailed_Interview_04dfdb08-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Ravi_Kumar_India_Detailed_Interview_04e1eeca-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Sarah_Johnson_US_Detailed_Interview_04e2dc4a-a27b-11f0-95d8-0242ac120004.pdf",
        # "Dr_Siddharth_Rao_India_Detailed_Interview_04e5b690-a27b-11f0-95d8-0242ac120004.pdf",
    ]
    
    # Example query using f-string with filenames
    query = f"""Now I have these files: {filenames}
    
    Task: Profession-Based Patterns in COVID-19 Experiences and Practices

    I have a collection of interview transcripts from doctors in the United States, India, and Germany, representing different medical professions — such as general physicians, intensivists, pediatricians, pulmonologists, emergency doctors, and public health specialists.

    I’d like to analyze these transcripts to understand how a doctor’s profession or specialty shaped their experiences, treatment decisions, and perspectives during the COVID-19 pandemic.

    Topics to Analyze

    1. Role-Specific Experiences
    Identify how doctors from different specialties described their day-to-day experiences during the pandemic. Note what challenges or responsibilities were unique to their roles.

    2. Treatment and Decision Patterns
    Summarize how treatment approaches or clinical decisions varied across professions. Capture any mentions of inter-specialty coordination or disagreements in treatment strategies.

    3. Exposure and Risk Differences
    Describe how different types of doctors discussed personal risk, workload, and emotional impact based on their professional roles and patient contact levels.

    4. Communication and Collaboration
    Analyze how specialists interacted with other medical teams, administrators, or public health authorities, and whether their professional background influenced these interactions.

    5. Country-Level Differences by Profession
    Compare how doctors of similar professions across the U.S., India, and Germany described their roles. Highlight differences in infrastructure, autonomy, or decision-making practices linked to their profession.

    Please generate a document in less than 600 words that organizes your findings in a clear, structured format suitable for decision-makers. The output should feature section headings for each area above and use bullet points, summaries, and comparative tables (if appropriate) to present the patterns, similarities, and differences between countries. Conclude the document with a synthesis highlighting the most important actionable insights and recommendations that emerge from this cross-country analysis, emphasizing both clinical lessons and contextual factors that shaped pandemic treatment responses. The document should be accessible to healthcare leaders, researchers, and policymakers seeking evidence-based learnings to inform future crisis planning and medical guidelines.
    """

    try:
        # Run the complete research workflow with filenames
        results = await researcher.run_research(query, filenames=filenames)
        
        # Print results
        print("=" * 80)
        print("RESEARCH RESULTS")
        print("=" * 80)
        
        if "error" in results:
            print(f"Error: {results['error']}")
            return
        
        # Print action plan
        print("\nACTION PLAN:")
        print(json.dumps(results["action_plan"], indent=2))
        
        # Print execution results
        print("\nEXECUTION RESULTS:")
        for step_result in results["execution_results"]:
            print(f"\nStep {step_result['step_no']}: {step_result['step_caption']}")
            print(f"Tool: {step_result.get('tool', 'N/A')}")
            print(f"Success: {step_result['success']}")
            if not step_result['success']:
                print(f"Error: {step_result.get('error', 'Unknown error')}")
        
        # Print final synthesis
        print("\n" + "=" * 80)
        print("FINAL SYNTHESIS")
        print("=" * 80)
        print(results["final_synthesis"])
        
        # Save results to file
        with open("research_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to research_results.json")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())