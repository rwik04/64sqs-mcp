import ast
import numpy as np
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity


def cosine_similarity_vectors(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score
    """
    return cosine_similarity([vec1], [vec2])[0][0]


def confidence_string(confidence_score: float) -> str:
    """
    Convert confidence score to string representation.
    
    Args:
        confidence_score: Confidence score (0-1)
        
    Returns:
        Confidence string (LOW, MEDIUM, HIGH)
    """
    if confidence_score >= 0.8:
        return "HIGH"
    elif confidence_score >= 0.6:
        return "MEDIUM"
    else:
        return "LOW"


def clean_text(text: str) -> str:
    """
    Clean and normalize text for processing.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    import re
    text = re.sub(r'\s+', ' ', text)
    text = text.replace("\n", " ")
    text = text.strip()
    return text if text else ""


def extract_questions_from_csv(questionnaire_data: List[Dict[str, Any]]) -> List[str]:
    """
    Extract questions from questionnaire data.
    
    Args:
        questionnaire_data: List of questionnaire entries
        
    Returns:
        List of questions
    """
    questions = []
    for entry in questionnaire_data:
        if 'questions' in entry:
            questions.extend(entry['questions'].split('; '))
    return questions


def parse_embedding_string(embedding_str: str) -> List[float]:
    """
    Parse embedding string from CSV to list of floats.
    
    Args:
        embedding_str: String representation of embedding
        
    Returns:
        List of float values
    """
    try:
        return ast.literal_eval(embedding_str)
    except (ValueError, SyntaxError):
        return [] 