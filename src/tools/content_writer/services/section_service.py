import os
import sys

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from tools.content_writer.utils.llm_utils import chat_with_gpt

def get_doc_section_content(messages, notes, target_document_brief, section_detail, model_type, api_key):
  """
  Given a target section name along with its specs, this function should write out the complete content for the section and return it as output
  """

  input_tokens = 0
  output_tokens = 0

  user_message = f"""
  Now, we need to detail out the section {section_detail['title']}

  Here are some additional specifications about the section
  1. section_length: {section_detail['length']}
  2. section_brief: {section_detail['details']}
  3. section_layout: {section_detail['layout']}

  Make sure that you stick to the word limit defined as per the parameter 'section_length'

  The parameter 'section_layout' gives an idea of how the section is to be formed.

  And here are the notes from where you need to write the content for the section
  ```
  {notes}
  ```

  Keep in mind the the section should also comply with the overall target document brief
  ```
  {target_document_brief}
  ```

  Generate your response as plain text ONLY, without any quotes, and with appropriate line/paragraph breaks and bullets points wherever required.

  Use ONLY unicode symbols to denote formulae. DO NOT use LaTeX or other formats. DO NOT use markdown elements in the text.
  """

  messages.append(HumanMessage(content = user_message))

  try:
    messages, section_content, input_tokens, output_tokens = chat_with_gpt(model_type = model_type, api_key = api_key, messages = messages,temperature = 0.5, max_tokens = 4000)
    section_detail.update({'content': section_content})

  except Exception as e:
    raise Exception(f"An error occurred while trying to write content for section {section_detail['name']}: {e}")

  return messages, section_detail, input_tokens, output_tokens

def get_html_section_content(messages, notes, target_document_brief, section_detail, model_type, api_key):
  """
  Given a target HTML section's details, this function writes the complete content for that section,
  wrapped in appropriate HTML tags, and returns it.
  """

  input_tokens = 0
  output_tokens = 0

  # The user message is updated to specifically request HTML output,
  # emphasizing adherence to the 'layout' guide from the outline.
  user_message = f"""
  Now, you will write the content for the HTML section titled: "{section_detail['title']}".

  Here are the specifications you must follow for this section:
  1.  **section_length**: Write approximately {section_detail['length']} words. Stick closely to this limit.
  2.  **section_brief**: The content must be about: "{section_detail['details']}".
  3.  **section_layout**: You MUST structure your output using this HTML guide: "{section_detail['layout']}".

  Use the following notes to get the information for the content:

  {notes}


  Remember that this section is part of a larger page with the following goal:

  {target_document_brief}


  our task is to generate the complete, ready-to-use HTML block for this section.
  - **Strictly adhere to the HTML tags and structure defined in 'section_layout' (e.g., use <h2>, <p>, <ul>, <strong> as specified).**
  - Generate **ONLY the raw HTML code** for this section.
  - Do not include any surrounding text, explanations, or markdown code fences like ```html or ```.
  """

  messages.append(HumanMessage(content = user_message))

  try:
    messages, section_content, input_tokens, output_tokens = chat_with_gpt(model_type = model_type, api_key = api_key, messages = messages,temperature = 0.5, max_tokens = 4000)

    # The following line simulates the raw HTML output for testing.
    # This example corresponds to the second section from the previous function's example outline.
    # section_content = """
    #   <h2>Core Concepts: Qubits and Superposition</h2>
    #   <p>Unlike classical computers that use bits representing 0 or 1, quantum computers use <strong>qubits</strong>. A qubit is the fundamental unit of quantum information. It can exist as a 0, a 1, or both states simultaneously. This ability to be in multiple states at once is a core principle known as <strong>superposition</strong>.</p>
    #   <p>Imagine a spinning coin. While it's in the air, it's neither heads nor tails—it's in a superposition of both. Only when it lands (is measured) does it settle into a definite state. Qubits work similarly, holding a vast amount of information until they are measured, which unlocks immense computational potential for solving complex problems.</p>
    # """

    # The generated content is added back into the section_detail dictionary.
    section_detail.update({'content': section_content})

  except Exception as e:
    # The error message is updated to use 'title' as that is the key in our dictionary.
    raise Exception(f"An error occurred while trying to write content for section '{section_detail['title']}': {e}")

  return messages, section_detail, input_tokens, output_tokens