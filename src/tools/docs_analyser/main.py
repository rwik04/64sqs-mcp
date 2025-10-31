import copy
import traceback
import time
import sys
import os
from typing import List, Dict, Any, Tuple, Optional
from langchain.schema import SystemMessage, HumanMessage

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from tools.docs_analyser.models import FileInfo, AnsweringConfig, AnalysisResult
from tools.docs_analyser.services.query_analysis import QueryAnalysisService
from tools.docs_analyser.services.search_service import SearchService
from tools.docs_analyser.services.response_generation import ResponseGenerationService
from tools.docs_analyser.utils.llm_client import chat_with_model
from tools.docs_analyser.prompts.docs_analyzer import (
    RESPONSE_SUMMARY_SYSTEM_PROMPT,
    RESPONSE_SUMMARY_REFERENCE_PROMPT,
    CONTEXT_SYSTEM_MESSAGE,
    CONTEXT_HUMAN_MESSAGE
)

from tools.docs_analyser.config import Config

import threading

class DocsAnalyzer:
    """Main class that orchestrates document analysis and response generation."""
    
    def __init__(self, filenames: list[FileInfo], query: str):
        """
        Initialize the docs analyzer.
        
        Args:
            filenames: List of FileInfo objects
            query: Query to analyze
        """
        self.config = AnsweringConfig(
            client=Config.AWS_CLIENT_ID,
            project_id=Config.AWS_PROJECT_ID,
            filenames=filenames,
            query=query,
            model_type="gpt-4.1",
            llm_api_key=Config.LLM_API_KEY,
            emb_api_key=Config.EMBEDDING_API_KEY,
            bucket_name=Config.AWS_BUCKET_NAME,
            aws_access_key=Config.AWS_ACCESS_KEY,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
        )
        self.query_analysis_service = QueryAnalysisService(self.config)
        self.search_service = SearchService(self.config)
        self.response_generation_service = ResponseGenerationService(self.config)
        
    def analyze_files(self) -> AnalysisResult:
        """
        Analyze all files and generate responses.
        
        Returns:
            Complete analysis result
        """
        token_tracker = {}
        possible_responses = []
        response_summary = None
        # Analyze each file in parallel
        import concurrent.futures

        def process_file(file_info):
            thread_id = threading.get_ident()
            print(f"[DEBUG] Starting processing for file: {file_info.displayname} (Thread ID: {thread_id})")
            response, token_usage = self.file_worker(file_info)
            print(f"[DEBUG] Finished processing for file: {file_info.displayname} (Thread ID: {thread_id})")
            return file_info, response, token_usage

        print("[DEBUG] Submitting file processing tasks to ThreadPoolExecutor with max_workers=20...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(process_file, file_info) for file_info in self.config.filenames]
            for future in concurrent.futures.as_completed(futures):
                print(f"[DEBUG] Future completed: {future}")
                file_info, response, token_usage = future.result()
                print(f"[DEBUG] Result received for file: {file_info.displayname}")
                if response:
                    print(f"[DEBUG] Appending response for file: {file_info.displayname}")
                    possible_responses.append(response)
                # Track tokens
                token_tracker.update({
                    f'file_{file_info.filename}': {
                        'input_tokens': token_usage['input_tokens'],
                        'output_tokens': token_usage['output_tokens']
                    }
                })
        print("[DEBUG] All file processing tasks completed.")

        # If no responses found, create a default message
        if len(possible_responses) == 0:
            # No relevant responses found
            print("[DEBUG] No relevant responses found, creating no-response-found message.")
            possible_responses = [self._create_no_response_found()]
        else:
            try:
                response_summary, token_usage = self._generate_response_summary(possible_responses)
            except Exception as e:
                print(f"[DEBUG] _generate_response_summary: Exception occurred: {e}. Retrying after 10 seconds.")
                time.sleep(10)
                response_summary, token_usage = self._generate_response_summary(possible_responses)
            
        # Handle tag-level responses
        # tag_results = self._handle_tag_level_responses(possible_responses)
        # if tag_results:
        #     token_tracker['tag_level_responses'] = tag_results['token_usage']
            
        print("[DEBUG] Returning AnalysisResult.")
        return AnalysisResult(
            file_level_responses=possible_responses,
            response_summary=response_summary,
            # tag_level_responses=tag_results.get('tag_responses', {}),
            # tag_comparison_summary=tag_results.get('tag_comparison_summary', ''),
            token_tracker=token_tracker
        )
        
    def file_worker(self, file_info: FileInfo) -> Tuple[Optional[Dict], Dict[str, int]]:
        """
        Analyze a single file for relevance and generate response.
        
        Args:
            file_info: Information about the file
            
        Returns:
            Tuple of (response_data, token_usage)
        """
        input_token_count = 0
        output_token_count = 0
        
        # Check if file is relevant
        print(f"[DEBUG] file_worker: Analyzing file: {file_info.displayname}")

        context_messages = self._get_context_messages()

        # Analyzing query relevance for file: {file_info.displayname}
        print(f"[DEBUG] file_worker: Checking query relevance for file: {file_info.displayname}")

        response, input_tokens, output_tokens = self.query_analysis_service.analyze_query_relevance(
            query=self.config.query,
            messages=copy.deepcopy(context_messages),
            filename=file_info.filename
        )
        input_token_count += input_tokens
        output_token_count += output_tokens
        
        if "yes" not in response['relevance_flag'].lower():
            print(f"[DEBUG] file_worker: File {file_info.displayname} not relevant.")
            return None, {'input_tokens': input_token_count, 'output_tokens': output_token_count}
            
        # Generate search query and find references
        sub_query = response['search_query']
        possible_queries = [sub_query]
        print(f"[DEBUG] file_worker: Finding references for file: {file_info.displayname}")
        references = self.search_service.find_references(sub_query, file_info.filename)
        
        # Try query rewriting if no references found
        if not references:
            print(f"[DEBUG] file_worker: No references found for {file_info.displayname}, trying query rewriting.")
            references, possible_queries = self._try_query_rewriting(sub_query)
            if references:
                input_token_count += sum(q['tokens'] for q in possible_queries[1:])
                output_token_count += sum(q['tokens'] for q in possible_queries[1:])
                
        if not references:
            print(f"[DEBUG] file_worker: Still no references found for {file_info.displayname} after rewriting.")
            return None, {'input_tokens': input_token_count, 'output_tokens': output_token_count}
            
        # Generate response
        print(f"[DEBUG] file_worker: Generating response for file: {file_info.displayname}")
        possible_response, input_tokens, output_tokens = self.response_generation_service.generate_response(
            references=references,
            queries=possible_queries,
            original_query=self.config.query,
            messages=copy.deepcopy(context_messages[:1]),
            filename=file_info.filename
        )
        input_token_count += input_tokens
        output_token_count += output_tokens
        
        if 'NOT ANSWERABLE' not in possible_response['response']:
            print(f"[DEBUG] file_worker: Response generated for file: {file_info.displayname}")
            possible_response.update({'filedetails': [{"displayname": file_info.displayname}]})
            return possible_response, {'input_tokens': input_token_count, 'output_tokens': output_token_count}
            
        print(f"[DEBUG] file_worker: Response for file {file_info.displayname} was NOT ANSWERABLE.")
        return None, {'input_tokens': input_token_count, 'output_tokens': output_token_count}
        
    def _try_query_rewriting(self, original_query: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Try rewriting the query to find references.
        
        Args:
            original_query: Original search query
            
        Returns:
            Tuple of (references, queries_with_tokens)
        """
        references = []
        queries_with_tokens = [{'query': original_query, 'tokens': 0}]
        
        for attempt in range(3):
            if references:
                break
            print(f"[DEBUG] _try_query_rewriting: Attempt {attempt+1} for query: {original_query}")
            rewritten_query, input_tokens, output_tokens = self.query_analysis_service.rewrite_query(original_query)
            references = self.search_service.find_references(rewritten_query, self.config.filenames[0].filename)
            
            queries_with_tokens.append({
                'query': rewritten_query,
                'tokens': input_tokens + output_tokens
            })
            
            if references:
                possible_queries = [q['query'] for q in queries_with_tokens]
                print(f"[DEBUG] _try_query_rewriting: Found references with rewritten query: {rewritten_query}")
                break
            else:
                print(f"[DEBUG] _try_query_rewriting: No references found with rewritten query: {rewritten_query}")
                
        return references, queries_with_tokens
        
    def _generate_response_summary(self, possible_responses: List[Dict]) -> Tuple[str, Dict[str, int]]:
        """
        Generate a summary of multiple file responses.
        
        Args:
            possible_responses: List of file responses
            
        Returns:
            Tuple of (summary, token_usage)
        """
        print(f"[DEBUG] _generate_response_summary: Generating summary for {len(possible_responses)} responses.")
        system_message = SystemMessage(
            content=RESPONSE_SUMMARY_SYSTEM_PROMPT.format(query=self.config.query)
        )
        messages = [system_message]

        for i, response in enumerate(possible_responses):
            reference_message = HumanMessage(
                content=RESPONSE_SUMMARY_REFERENCE_PROMPT.format(
                    response_index=i,
                    displayname=response['filedetails'][0]['displayname'],
                    response=response['response']
                )
            )
            messages.append(reference_message)

        try:
            messages, result, input_tokens, output_tokens = chat_with_model(
                messages=messages, 
                temperature=0, 
                max_tokens=2048,
                model_type=self.config.model_type, 
                api_key=self.config.llm_api_key
            )
        except Exception as e:
            print(f"[DEBUG] _generate_response_summary: Exception occurred: {e}. Retrying after 10 seconds.")
            time.sleep(10)
            try:
                messages, result, input_tokens, output_tokens = chat_with_model(
                    messages=messages, 
                    temperature=0, 
                    max_tokens=2048, 
                    model_type=self.config.model_type, 
                    api_key=self.config.llm_api_key
                )
            except Exception as e:
                print(f"[DEBUG] _generate_response_summary: Second exception occurred: {e}. Raising exception.")
                raise Exception(f"An error occurred while generating response summary: {str(e)}")

        print(f"[DEBUG] _generate_response_summary: Summary generated.")
        return result, {'input_tokens': input_tokens, 'output_tokens': output_tokens}
        
    def _get_context_messages(self) -> List:
        """Get initial context messages for the conversation."""
        return [
            SystemMessage(
                content=CONTEXT_SYSTEM_MESSAGE
            ),
            HumanMessage(
                content=CONTEXT_HUMAN_MESSAGE.format(query=self.config.query)
            )
        ]
        
    def _create_no_response_found(self) -> Dict:
        """Create a response when no relevant information is found."""
        print("[DEBUG] _create_no_response_found: Creating no-response-found message.")
        return {
            'response': 'Apologies but your query does not look relevant to any of the selected files. In case you think otherwise, can you try rephrasing it?',
            'references': [],
            'pointers': [],
            'questions': [],
            'confidence': 'HIGH',
            'filedetails': [{'displayname': f.displayname, 'filetype': f.filetype} for f in self.config.filenames]
        }

if __name__ == "__main__":
    # Create FileInfo objects for the new set of interview PDFs
    # Use the filenames from file_context_0 to create FileInfo objects
    filenames_list = [
        'Alice_Johnson_Varied_Interview_80e450a2-8e1d-11f0-9435-0242ac120004.pdf',
        'Bob_Smith_Varied_Interview_80e63214-8e1d-11f0-9435-0242ac120004.pdf',
        'Charlie_Nguyen_Varied_Interview_80e4d6c6-8e1d-11f0-9435-0242ac120004.pdf',
        'Diana_Patel_Varied_Interview_80e4fe80-8e1d-11f0-9435-0242ac120004.pdf',
        'Ethan_Brown_Varied_Interview_80e65802-8e1d-11f0-9435-0242ac120004.pdf',
        'Fiona_Lee_Varied_Interview_821b5290-8e1d-11f0-9435-0242ac120004.pdf',
        'George_Martin_Varied_Interview_82205d62-8e1d-11f0-9435-0242ac120004.pdf',
        'Hannah_Wilson_Varied_Interview_8221d5f2-8e1d-11f0-9435-0242ac120004.pdf',
        'Ian_Clark_Varied_Interview_8222ea46-8e1d-11f0-9435-0242ac120004.pdf',
        'Jasmine_Wright_Varied_Interview_82233744-8e1d-11f0-9435-0242ac120004.pdf',
        'Kevin_Lewis_Varied_Interview_8314fcf0-8e1d-11f0-9435-0242ac120004.pdf',
        'Laura_Adams_Varied_Interview_831529be-8e1d-11f0-9435-0242ac120004.pdf',
        'Michael_Scott_Varied_Interview_831b7f8a-8e1d-11f0-9435-0242ac120004.pdf',
        'Nina_Torres_Varied_Interview_831c2958-8e1d-11f0-9435-0242ac120004.pdf',
        'Oscar_Davis_Varied_Interview_831d8230-8e1d-11f0-9435-0242ac120004.pdf',
        'Priya_Sharma_Varied_Interview_8410637e-8e1d-11f0-9435-0242ac120004.pdf',
        'Quentin_Zhao_Varied_Interview_84165b76-8e1d-11f0-9435-0242ac120004.pdf',
        'Rachel_Kim_Varied_Interview_841794d2-8e1d-11f0-9435-0242ac120004.pdf',
        'Samir_Hassan_Varied_Interview_84121598-8e1d-11f0-9435-0242ac120004.pdf',
        'Tina_Lopez_Varied_Interview_84168240-8e1d-11f0-9435-0242ac120004.pdf',
    ]

    filenames = [
        FileInfo(
            filename=fn,
            displayname=fn.replace('_Varied_Interview_', ' ').replace('.pdf', '').replace('_', ' '),
            filetype='pdf',
            id=str(idx + 1)
        )
        for idx, fn in enumerate(filenames_list)
    ]

    print("[DEBUG] Instantiating DocsAnalyzer...")
    docs_analyzer = DocsAnalyzer(
        filenames=filenames,
        query="I have transcripts of software engineer interviews. Can you analyze them and give me a summary of the main themes?",
    )

    print("[DEBUG] Starting analysis of files...")
    results = docs_analyzer.analyze_files()

    print("[DEBUG] Analysis complete. Results:")
    print(results)
