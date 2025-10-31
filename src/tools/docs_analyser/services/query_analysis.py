import copy
import sys
import os
from typing import Dict, Any, Tuple, List
from langchain.schema import HumanMessage, SystemMessage

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from tools.docs_analyser.utils.llm_client import chat_with_model
from tools.docs_analyser.utils.file_utils import load_summary_file, file_exists
from tools.docs_analyser.prompts.docs_analyzer import (
    QUERY_RELEVANCE_CONTEXT_PROMPT,
    QUERY_RELEVANCE_INSTRUCTIONS_PROMPT,
    QUERY_REWRITING_PROMPT
)

from tools.docs_analyser.config import Config

class QueryAnalysisService:
    """Service for analyzing queries and determining file relevance."""
    
    def __init__(self, config: Any):
        """
        Initialize the service.
        
        Args:
            config: Configuration object with API keys and settings
        """
        self.config = config
        
    def analyze_query_relevance(
        self, 
        query: str, 
        messages: List, 
        filename: str
    ) -> Tuple[Dict[str, Any], int, int]:
        """
        Analyze if a file is relevant for answering a query.
        
        Args:
            query: User query
            messages: Conversation messages
            filename: Name of the file to analyze
            
        Returns:
            Tuple of (analysis_result, input_tokens, output_tokens)
        """
        try:
            # print(f"[analyze_query_relevance] Loading summary for file: {filename}")
            # Try to load summary file
            summary_text = self._load_file_summary(filename)
            # print(f"[analyze_query_relevance] Loaded summary text: {summary_text[:200]}...")  # Print first 200 chars
            
            # Add context messages
            # print(f"[analyze_query_relevance] Adding context messages for filename: {filename}")
            messages.extend([
                HumanMessage(
                    content=QUERY_RELEVANCE_CONTEXT_PROMPT.format(
                        filename=filename,
                        summary_text=summary_text
                    )
                ),
                HumanMessage(
                    content=QUERY_RELEVANCE_INSTRUCTIONS_PROMPT
                )
            ])

            # Get LLM response
            # print(f"[analyze_query_relevance] Calling chat_with_model with {len(messages)} messages")
            messages, response, input_tokens, output_tokens = chat_with_model(
                messages=messages,
                temperature=0, 
                max_tokens=4096, 
                model_type=self.config.model_type, 
                api_key=self.config.llm_api_key
            )
            # print(f"[analyze_query_relevance] Raw LLM response: {response}")

            # Parse response
            response = response.replace("```json", "").replace("```", "")
            # print(f"[analyze_query_relevance] Cleaned LLM response: {response}")
            response = eval(response)
            # print(f"[analyze_query_relevance] Parsed response dict: {response}")

            response['relevance_flag'] = response['relevance_flag'].lower()
            # print(f"[analyze_query_relevance] relevance_flag after lower(): {response['relevance_flag']}")

            if response['relevance_flag'] == "''":
                response['relevance_flag'] = ""
                # print(f"[analyze_query_relevance] relevance_flag was empty string, set to ''")

            if 'yes' in response['relevance_flag']:
                response['relevance_flag'] = "yes"
                # print(f"[analyze_query_relevance] relevance_flag contains 'yes', set to 'yes'")

            # print(f"[analyze_query_relevance] Final response: {response}, input_tokens: {input_tokens}, output_tokens: {output_tokens}")
            return response, input_tokens, output_tokens

        except Exception as e:
            # print(f"[analyze_query_relevance] Exception occurred: {str(e)}")
            raise Exception(f"An error occurred while trying to shortlist from the provided filenames for answering query using LLM: {str(e)}")

    def rewrite_query(self, query: str) -> Tuple[str, int, int]:
        """
        Rewrite/modify a query to improve search results.
        
        Args:
            query: Original query
            
        Returns:
            Tuple of (rewritten_query, input_tokens, output_tokens)
        """
        # print(f"[rewrite_query] Received query: {query}")
        query_prompt = QUERY_REWRITING_PROMPT.format(query=query)
        # print(f"[rewrite_query] Formatted query prompt: {query_prompt}")
        messages = [HumanMessage(content=query_prompt)]
        
        # print(f"[rewrite_query] Calling chat_with_model for query rewriting")
        messages, response, input_tokens, output_tokens = chat_with_model(
            messages=messages,  
            temperature=0.4, 
            max_tokens=2000, 
            model_type=self.config.model_type, 
            api_key=self.config.llm_api_key
        )
        # print(f"[rewrite_query] LLM rewritten query: {response}")
        # print(f"[rewrite_query] input_tokens: {input_tokens}, output_tokens: {output_tokens}")

        return response, input_tokens, output_tokens

    def _load_file_summary(self, filename: str) -> str:
        """
        Load summary content for a file.
        
        Args:
            filename: Name of the file
            
        Returns:
            Summary content as string
        """
        # S3 path structure: bucket-name/client-name/project-id/summary_files/filename/summary.md or summary.txt
        summary_paths = [
            f"{self.config.client}/{self.config.project_id}/summary_files/{filename}/summary.md",
            f"{self.config.client}/{self.config.project_id}/summary_files/{filename}/summary.txt"
        ]
        # print(f"[_load_file_summary] Checking summary paths for file: {filename}")
        for path in summary_paths:
            # print(f"[_load_file_summary] Checking if file exists: {path}")
            if file_exists(path):
                # print(f"[_load_file_summary] File exists: {path}, loading summary file.")
                summary = load_summary_file(path)
                # print(f"[_load_file_summary] Loaded summary (first 200 chars): {summary[:200]}...")
                return summary
        
        # print(f"[_load_file_summary] No summary file found for {filename}. Returning default message.")
        return "No summary available for this file." 