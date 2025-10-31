import copy
import traceback
import time
from typing import List, Dict, Any, Tuple
from langchain.schema import HumanMessage, SystemMessage

from ..utils.llm_client import chat_with_model
from ..utils.text_processing import confidence_string
from prompts.docs_analyzer import (
    RESPONSE_GENERATION_CONTEXT_PROMPT,
    RESPONSE_GENERATION_REFERENCE_PROMPT,
    RESPONSE_GENERATION_FINAL_INSTRUCTIONS
)

class ResponseGenerationService:
    """Service for generating responses from file references."""
    
    def __init__(self, config: Any):
        """
        Initialize the response generation service.
        
        Args:
            config: Configuration object with API keys and settings
        """
        self.config = config
        
    def generate_response(
        self, 
        references: List[Dict[str, Any]], 
        queries: List[str],
        original_query: str, 
        messages: List, 
        filename: str
    ) -> Tuple[Dict[str, Any], int, int]:
        """
        Generate a response based on file references.
        
        Args:
            references: List of relevant references
            queries: Search queries used
            original_query: Original user query
            messages: Conversation messages
            filename: Name of the file
            
        Returns:
            Tuple of (response_data, input_tokens, output_tokens)
        """
        # Define response schema
        response_json_schema = {
            "title": "ResponseSchema",
            "description": "Schema for structured response with answer and reference pointers",
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "The generated response to the user's query"
                },
                "pointers": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "List of reference pointers or citations"
                }
            },
            "required": ["response", "pointers"]
        }
        
        # Add context message
        context_message = HumanMessage(
            content=RESPONSE_GENERATION_CONTEXT_PROMPT.format(filename=filename)
        )
        messages.append(context_message)

        # Add reference texts
        for i, reference in enumerate(references):
            reference_message = HumanMessage(
                content=RESPONSE_GENERATION_REFERENCE_PROMPT.format(
                    reference_index=i,
                    reference=reference['reference']
                )
            )
            messages.append(reference_message)

        # Add final instructions
        final_instructions_message = HumanMessage(
            content=RESPONSE_GENERATION_FINAL_INSTRUCTIONS.format(
                original_query=original_query,
                queries='...OR...'.join(queries)
            )
        )
        messages.append(final_instructions_message)

        try:
            messages, result, input_tokens, output_tokens = chat_with_model(
                messages=messages, 
                temperature=0, 
                max_tokens=2048,
                model_type=self.config.model_type, 
                api_key=self.config.llm_api_key,
                json_schema=response_json_schema
            )
            
            response = result['response']
            pointers = result['pointers']

        except Exception as e:
            # traceback.print_exc()
            # print("sleep for 10sec")
            time.sleep(10)
            try:
                messages, result, input_tokens, output_tokens = chat_with_model(
                    messages=messages, 
                    temperature=0,
                    max_tokens=2048, 
                    model_type=self.config.model_type,
                    api_key=self.config.llm_api_key,
                    json_schema=response_json_schema
                )
                response = result['response']
                pointers = result['pointers']
            except Exception as e:
                raise Exception(f"An error occurred while trying to generate response using LLM: {str(e)}")

        if 'NOT ANSWERABLE' in response:
            possible_response = {
                'response': response,
                'references': [],
                'pointers': [],
                'questions': [],
                'confidence': 'NA'
            }
        else:
            reference_texts = []
            questions = []
            confidences = []

            for reference in references:
                questions.append(reference.get('question', ''))
                reference_texts.append(reference['reference'])

            # Calculate confidence based on query-pointer similarity
            from ..utils.llm_client import create_embedding
            from ..utils.text_processing import cosine_similarity_vectors
            
            embedding_queries = [create_embedding(text=query, api_key=self.config.emb_api_key) for query in queries]
            embedding_pointers = [create_embedding(text=pointer, api_key=self.config.emb_api_key) for pointer in pointers]
            
            # Compute cosine similarity for all combinations
            similarity_matrix = [
                [cosine_similarity_vectors(q, p) for p in embedding_pointers] 
                for q in embedding_queries
            ]
            
            max_similarity = max(max(row) for row in similarity_matrix) if similarity_matrix else 0

            possible_response = {
                'response': response,
                'references': reference_texts,
                'pointers': pointers,
                'questions': questions,
                'confidence': confidence_string(max_similarity)
            }

        return possible_response, input_tokens, output_tokens 