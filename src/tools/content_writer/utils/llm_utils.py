import os
import sys

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from langchain_openai import ChatOpenAI

def chat_with_gpt(model_type, api_key, messages = [],temperature = 0, max_tokens = 2000):
  """
  Invokes GPT API to chat with the model.
  """
  llm = ChatOpenAI(model = model_type, temperature = 0, max_tokens = max_tokens, api_key = api_key)
  response = llm.invoke(messages)
  messages = messages + [response]
  input_tokens = messages[-1].usage_metadata['input_tokens']
  output_tokens = messages[-1].usage_metadata['output_tokens']
  return messages, response.content, input_tokens, output_tokens