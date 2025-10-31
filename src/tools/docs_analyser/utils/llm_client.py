import time
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage, BaseMessage
from openai import RateLimitError


def create_llm_client(model_type: str, api_key: str, temperature: float = 0, max_tokens: int = 2000):
    """
    Creates an LLM client based on the model type.
    
    Args:
        model_type: Type of model (gpt, claude, gemini)
        api_key: API key for the model
        temperature: Temperature for generation
        max_tokens: Maximum tokens for generation
        
    Returns:
        Configured LLM client
    """
    if model_type.startswith('gpt'):
        return ChatOpenAI(
            model=model_type, 
            temperature=temperature, 
            max_tokens=max_tokens, 
            api_key=api_key
        )
    elif model_type.startswith('claude'):
        return ChatAnthropic(
            model=model_type, 
            temperature=temperature, 
            max_tokens=max_tokens, 
            api_key=api_key
        )
    elif model_type.startswith('gemini'):
        return ChatGoogleGenerativeAI(
            model=model_type, 
            temperature=temperature, 
            max_tokens=max_tokens, 
            api_key=api_key
        )
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


def chat_with_model(
    messages: List[BaseMessage] = [],
    temperature: float = 0, 
    max_tokens: int = None, 
    model_type: str = None, 
    api_key: str = None,
    json_schema: Dict[str, Any] = {}
):
    """
    Invokes LLM API to chat with the model.
    
    Args:
        model_type: Type of model to use
        api_key: API key for the model
        messages: List of messages to send
        temperature: Temperature for generation
        max_tokens: Maximum tokens for generation
        json_schema: JSON schema for structured output
        
    Returns:
        Tuple of (messages, response, input_tokens, output_tokens)
    """
    try:
        # Calculate optimal max_tokens if not provided
        if max_tokens is None:
            max_tokens = calculate_optimal_max_tokens(messages, model_type)
        
        llm = create_llm_client(model_type, api_key, temperature, max_tokens)
        
        if json_schema:
            # Validate JSON schema format for structured output
            if not isinstance(json_schema, dict):
                raise ValueError("JSON schema must be a dictionary")
            
            # Check if schema has required title and description for OpenAI compatibility
            if not json_schema.get('title') or not json_schema.get('description'):
                raise ValueError("JSON schema must have 'title' and 'description' keys for structured output compatibility")
            
            if model_type.startswith('claude'):
                time.sleep(5)
            llm = llm.with_structured_output(json_schema, include_raw=True)
            response = llm.invoke(messages)
            messages = messages + [response['raw']]
            input_tokens = response['raw'].usage_metadata['input_tokens']
            output_tokens = response['raw'].usage_metadata['output_tokens']
            response = response['parsed']
        else:
            if model_type.startswith('claude'):
                time.sleep(5)
            response = llm.invoke(messages)
            messages = messages + [response]
            input_tokens = response.usage_metadata['input_tokens']
            output_tokens = response.usage_metadata['output_tokens']
            response = response.content

        return messages, response, input_tokens, output_tokens
        
    except RateLimitError as e:
        raise e
    except Exception as e:
        # Check if it's a token limit error
        if "length limit was reached" in str(e) or "token limit" in str(e).lower():
            error_msg = f"Token limit exceeded. Current max_tokens: {max_tokens}. "
            error_msg += "Try reducing max_tokens or shortening the input messages. "
            error_msg += f"Error details: {str(e)}"
            raise Exception(error_msg)
        
        # Provide more context about the error, especially for structured output issues
        if json_schema:
            raise Exception(f"Error in chat_with_model with structured output (schema: {json_schema}): {str(e)}")
        else:
            raise Exception(f"Error in chat_with_model: {str(e)}")


async def async_chat_with_model(
    model_type: str, 
    api_key: str, 
    messages: List[BaseMessage] = [],
    temperature: float = 0, 
    max_tokens: int = None, 
    json_schema: Dict[str, Any] = {}
):
    """
    Async version of chat_with_model.
    
    Args:
        model_type: Type of model to use
        api_key: API key for the model
        messages: List of messages to send
        temperature: Temperature for generation
        max_tokens: Maximum tokens for generation
        json_schema: JSON schema for structured output
        
    Returns:
        Tuple of (messages, response, input_tokens, output_tokens)
    """
    try:
        # Calculate optimal max_tokens if not provided
        if max_tokens is None:
            max_tokens = calculate_optimal_max_tokens(messages, model_type)
        
        llm = create_llm_client(model_type, api_key, temperature, max_tokens)
        
        if model_type.startswith('claude'):
            time.sleep(5)

        if json_schema:
            # Validate JSON schema format for structured output
            if not isinstance(json_schema, dict):
                raise ValueError("JSON schema must be a dictionary")
            
            # Check if schema has required title and description for OpenAI compatibility
            if not json_schema.get('title') or not json_schema.get('description'):
                raise ValueError("JSON schema must have 'title' and 'description' keys for structured output compatibility")
            
            llm = llm.with_structured_output(json_schema, include_raw=True)
            response = await llm.ainvoke(messages)
            messages = messages + [response['raw']]
            input_tokens = response['raw'].usage_metadata['input_tokens']
            output_tokens = response['raw'].usage_metadata['output_tokens']
            response = response['parsed']
        else:
            response = await llm.ainvoke(messages)
            messages = messages + [response]
            input_tokens = response.usage_metadata["input_tokens"]
            output_tokens = response.usage_metadata["output_tokens"]
            response = response.content

        return messages, response, input_tokens, output_tokens
        
    except RateLimitError as e:
        raise e
    except Exception as e:
        # Check if it's a token limit error
        if "length limit was reached" in str(e) or "token limit" in str(e).lower():
            error_msg = f"Token limit exceeded. Current max_tokens: {max_tokens}. "
            error_msg += "Try reducing max_tokens or shortening the input messages. "
            error_msg += f"Error details: {str(e)}"
            raise Exception(error_msg)
        
        raise Exception(f"An error occurred while calling async chat_with_model: {str(e)}")


def calculate_optimal_max_tokens(messages: List[BaseMessage], model_type: str) -> int:
    """
    Calculate optimal max_tokens based on input message length and model capabilities.
    
    Args:
        messages: List of input messages
        model_type: Type of model being used
        
    Returns:
        Optimal max_tokens value
    """
    # Estimate input tokens (rough approximation: 1 token ≈ 4 characters)
    total_chars = sum(len(str(msg.content)) for msg in messages)
    estimated_input_tokens = total_chars // 4
    
    # Model-specific token limits
    if model_type.startswith('gpt'):
        # GPT models typically have 128k context window
        max_context = 128000
        # Reserve some tokens for input, use remaining for output
        optimal_output = min(2048, max_context - estimated_input_tokens - 1000)
        return max(512, optimal_output)  # Minimum 512 tokens
    elif model_type.startswith('claude'):
        # Claude models typically have 200k context window
        max_context = 200000
        optimal_output = min(2048, max_context - estimated_input_tokens - 1000)
        return max(512, optimal_output)
    elif model_type.startswith('gemini'):
        # Gemini models typically have 1M context window
        max_context = 1000000
        optimal_output = min(2048, max_context - estimated_input_tokens - 1000)
        return max(512, optimal_output)
    else:
        # Default fallback
        return 1024


def create_embedding(text: str, api_key: str, model: str = "text-embedding-ada-002"):
    """
    Creates an embedding vector representation for the text.
    
    Args:
        text: Text to embed
        api_key: OpenAI API key
        model: Embedding model to use
        
    Returns:
        Embedding vector
    """
    import re
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key)
    text = re.sub(r'\s+', ' ', text)
    text = text.replace("\n", " ")
    text = text.strip()
    
    if text is None:
        text = ""
        
    try:
        embedding = client.embeddings.create(input=[text], model=model).data[0].embedding
        return embedding
    except Exception as e:
        # print(f"Error in creating embedding for text: {text}")
        raise Exception(f"Error in creating embedding for text: {str(e)}") 