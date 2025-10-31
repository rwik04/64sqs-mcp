import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from itertools import chain

from ..utils.llm_client import create_embedding
from ..utils.text_processing import cosine_similarity_vectors, parse_embedding_string
from ..utils.file_utils import load_nodes_from_file

class SearchService:
    """Service for searching through different types of file indexes."""
    
    def __init__(self, config: Any):
        """
        Initialize the search service.
        
        Args:
            config: Configuration object with API keys and settings
        """
        self.config = config
        
    def find_references(self, query: str, filename: str) -> List[Dict[str, Any]]:
        """
        Find relevant references in a file using multiple search methods.
        
        Args:
            query: Search query
            filename: Name of the file to search
            
        Returns:
            List of relevant references with confidence scores
        """
        # Load nodes from file
        nodes_path = f"{self.config.client}/{self.config.project_id}/uploaded_files/{filename}/nodes_binary"
        nodes = load_nodes_from_file(nodes_path)

        # print(f"Nodes: {nodes}")
        
        if not nodes:
            return []
            
        # Combine text from all nodes
        node_text = "\n".join([node.text for node in nodes])
        
        if len(nodes) <= 1:
            return [{'reference': node_text, 'confidence': 1.0}]
            
        # Search through different indexes
        references_questionnaire = self._search_questionnaire(query, filename)
        references_vectorstore = self._search_vectorstore(query, filename)
        
        # Combine and deduplicate references
        references_combined = list(chain(references_questionnaire, references_vectorstore))
        
        if not references_combined:
            return []
            
        # Deduplicate by keeping highest confidence for each reference
        references_final = {}
        for item in references_combined:
            ref = item['reference']
            conf = item['confidence']
            if ref not in references_final or conf > references_final[ref]['confidence']:
                references_final[ref] = item
                
        return list(references_final.values())
        
    def _search_questionnaire(self, query: str, filename: str) -> List[Dict[str, Any]]:
        """
        Search through questionnaire/list index.
        
        Args:
            query: Search query
            filename: Name of the file
            
        Returns:
            List of relevant references
        """
        local_list_index_path = f"{self.config.bucket_name}/{self.config.client}/{self.config.project_id}/list_index_files/{filename}/"
        possible_references = []
        
        try:
            questionnaire = pd.read_csv(local_list_index_path + 'questionnaire.csv')
        except FileNotFoundError:
            # print(f"Couldn't find questionnaire file: {local_list_index_path}")
            return []
            
        # Create embedding for query
        embedding = create_embedding(text=query, api_key=self.config.emb_api_key)
        
        # Calculate similarities
        questionnaire['similarities'] = questionnaire.embeddings.apply(
            lambda x: cosine_similarity_vectors(parse_embedding_string(x), embedding)
        )
        
        # Filter by similarity threshold and get top results
        questionnaire = questionnaire[questionnaire.similarities >= 0.8]
        questionnaire = questionnaire.sort_values('similarities', ascending=False)
        questionnaire = questionnaire[:3]
        
        if questionnaire.empty:
            return []
            
        # Group by node_id and aggregate
        questionnaire = questionnaire.groupby('node_id').aggregate({
            'questions': lambda x: '; '.join(x), 
            'similarities': 'max'
        }).reset_index()
        
        with open(local_list_index_path + 'docstore.json') as f:
            docstore_data = json.load(f)
            
        for _, row in questionnaire.iterrows():
            node_id = row['node_id']
            question = row['questions']
            similarity = row['similarities']
            
            if node_id in docstore_data.get('docstore/data', {}):
                text = docstore_data['docstore/data'][node_id]['__data__']['text']
                possible_references.append({
                    'reference': text, 
                    'question': question, 
                    'confidence': similarity
                })
            
        return possible_references
        
    def _search_vectorstore(self, query: str, filename: str) -> List[Dict[str, Any]]:
        """
        Search through vector store index.
        
        Args:
            query: Search query
            filename: Name of the file
            
        Returns:
            List of relevant references
        """
        local_vector_index_path = f"{self.config.bucket_name}/{self.config.client}/{self.config.project_id}/vector_index_files/{filename}/"
        possible_references = []
        
        # Import llama-index components
        from llama_index import StorageContext, load_index_from_storage
        from llama_index.retrievers import VectorIndexRetriever
        from llama_index.query_engine import RetrieverQueryEngine
        from llama_index.postprocessor import SimilarityPostprocessor
        
        # Rebuild storage context and load index
        storage_context = StorageContext.from_defaults(persist_dir=local_vector_index_path)
        index = load_index_from_storage(storage_context=storage_context)
        
        # Configure retriever and query engine
        retriever = VectorIndexRetriever(index=index, similarity_top_k=3)
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever, 
            response_mode='no_text', 
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)]
        )
        
        # Get results
        results = query_engine.query(query)
        
        # Extract references
        for r in results.source_nodes:
            possible_references.append({
                'reference': r.node.text, 
                'confidence': r.score
        })
            
        return possible_references 