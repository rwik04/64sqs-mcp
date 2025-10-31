"""
Utility functions for LLM interactions.
"""

import time
import json
import os
import base64
from typing import List
from tqdm import tqdm
from openai import RateLimitError
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from src.tools.data_interpreter.config import Config


def encode_image(image_path):
    """
    Reads a jpeg/png image and returns a base64 encoding of the image
    """
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def cooldown_timer(seconds):
    """Display a progress bar for cooldown periods"""
    for _ in tqdm(range(seconds), desc="Cooldown in progress", ncols=100, bar_format='{l_bar}{bar} | {remaining}s left'):
        time.sleep(1)


def get_annotation_limit():
    """Get the annotation limit from environment variables"""
    value = Config.ANNOTATION_LIMIT
    if value is None:
        raise ValueError("Environment variable annotation_limit is not set.")

    try:
        int_value = int(value)
    except ValueError:
        raise ValueError(f"Environment variable annotation_limit must be an integer, got '{value}'.")

    return int_value


def chat_with_model(model_type, api_key, messages=[], temperature=0, max_tokens=2000, json_schema={}):
    """
    Invokes LLM API to chat with the model.
    """
    try:
        if model_type.startswith('gpt'):
            llm = ChatOpenAI(model=model_type, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        elif model_type.startswith('claude'):
            llm = ChatAnthropic(model=model_type, temperature=temperature, max_tokens=max_tokens, anthropic_api_key=api_key)
        elif model_type.startswith('gemini'):
            llm = ChatGoogleGenerativeAI(model=model_type, temperature=temperature, max_tokens=max_tokens, api_key=api_key)

        if len(json_schema) != 0:
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
        raise e


async def async_chat_with_model(model_type, api_key, messages=[], temperature=0, max_tokens=2000, json_schema={}):
    """
    Asynchronously invokes LLM API to chat with the model.
    """
    try:
        if model_type.startswith('gpt'):
            llm = ChatOpenAI(model=model_type, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        elif model_type.startswith('claude'):
            llm = ChatAnthropic(model=model_type, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        elif model_type.startswith('gemini'):
            llm = ChatGoogleGenerativeAI(model=model_type, temperature=temperature, max_tokens=max_tokens, timeout=None, max_retries=2, api_key=api_key)

        if model_type.startswith('claude'):
            time.sleep(5)

        if len(json_schema) != 0:
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
        raise Exception(f"An error occurred while calling async chat_with_model as {str(e)}")


def chat_with_gemini(model_type, messages=[], temperature=0, max_tokens=2000):
    """
    Invokes Gemini API to chat with the model.
    """
    llm = ChatGoogleGenerativeAI(model=model_type, temperature=temperature, max_tokens=max_tokens, timeout=None, max_retries=2)
    response = llm.invoke(messages)
    messages = messages + [response]
    input_tokens = messages[-1].usage_metadata['input_tokens']
    output_tokens = messages[-1].usage_metadata['output_tokens']
    return messages, response.content, input_tokens, output_tokens


def chat_with_gpt(model_type, api_key, messages=[], temperature=0, max_tokens=2000, json_schema={}):
    """
    Invokes GPT API to chat with the model.
    """
    try:
        llm = ChatOpenAI(model=model_type, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        if len(json_schema) != 0:
            llm = llm.with_structured_output(json_schema, include_raw=True)
            response = llm.invoke(messages)
            messages = messages + [response['raw']]
            input_tokens = response['raw'].usage_metadata['input_tokens']
            output_tokens = response['raw'].usage_metadata['output_tokens']
            response = response['parsed']
        else:
            response = llm.invoke(messages, max_tokens=max_tokens)
            messages = messages + [response]
            input_tokens = response.usage_metadata['input_tokens']
            output_tokens = response.usage_metadata['output_tokens']
            response = response.content

        return messages, response, input_tokens, output_tokens
    except Exception as e:
        raise e


async def async_chat_with_gpt(model_type, api_key, messages=[], temperature=0, max_tokens=2000, json_schema={}):
    """
    Asynchronously invokes GPT API to chat with the model.
    """
    try:
        llm = ChatOpenAI(model=model_type, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        if len(json_schema) != 0:
            llm = llm.with_structured_output(json_schema, include_raw=True)
            response = await llm.ainvoke(messages)
            messages = messages + [response['raw']]
            input_tokens = response['raw'].usage_metadata['input_tokens']
            output_tokens = response['raw'].usage_metadata['output_tokens']
            response = response['parsed']
        else:
            response = await llm.ainvoke(messages)
            messages = messages + [response]
            input_tokens = response.usage_metadata['input_tokens']
            output_tokens = response.usage_metadata['output_tokens']
            response = response.content

        return messages, response, input_tokens, output_tokens
    except Exception as e:
        raise e