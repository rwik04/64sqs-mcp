import os
import sys
import json

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from tools.content_writer.utils.llm_utils import chat_with_gpt

def get_doc_outline(notes, target_document_type, target_document_length, target_document_brief, model_type, api_key):
    """
    Given a bunch of notes and the specs for the target 'doc', this function should generate an outline and return it as a list of json objects
    Each json represents a unique section... and should contain the name of different sections, a one-line description, section type (doc/slide), and section length (#words)
    """   

    draft_outline = {}
    input_tokens = 0
    output_tokens = 0

    system_message = """
    You will be provided with a bunch of notes (text snippets enclosed in square brackets []), and some high level details about a target document (word doc) that needs to be created from those notes
    You need to come up with an outline (list of logical sections) for that target document, keeping both the notes and the target documents in mind.

    This outline should be provided strictly as a list of structured JSON objects, each object representing details about a specific section
    An example of the output structure is provided below:
    [
      {
        'title': "Name of the 1st Section"
        'details': "A one line description of what will be contained in this section",
        'length': "Approximately how many words should be devoted to writing this section",
        'layout': "How this section is to be structured?",
      },
      {
        'title': "Name of the 2nd section"
        'details': "A one line description of what will be contained in this section",
        'length': "Approximately how many words should be devoted to writing this section",
        'layout': "How this section is to be structured?",
      },
      ...
    ]

    Keep the following in mind for the section 'length'
    - You will be given max target document length in terms of #words. You need to ensure that #words across all sections doesn't exceed target document length.
    - And the #sections can be logically derived based on the content of the notes and what the target document is going to be about.

    The layout key contains a one-liner about how that section is to be structured. Keep it very brief and precise.
    """

    user_message = f"""
    Next, here are the notes which need to be compiled into a document
    ```
    {notes}
    ```

    And here are the specifications of the target document
    1. target_document_type: {target_document_type}
    2. target_document_length: {target_document_length}
    3. target_document_brief: {target_document_brief}

    Go ahead and generate the outline as requested
    """

    messages = [
      SystemMessage(content = system_message),
      HumanMessage(content = user_message)
    ]

    try:
      messages, draft_outline, input_tokens, output_tokens = chat_with_gpt(model_type = model_type, api_key = api_key, messages = messages,temperature = 0.5, max_tokens = 4000)
      draft_outline = draft_outline.replace("```json", "").replace("```", "")
      draft_outline = json.loads(draft_outline)
    except Exception as e:
      raise Exception(f"An error occurred while trying to generate an outline for the new draft: {e}")
    except json.JSONDecodeError:
      raise Exception(f"Failed to decode outline JSON created using LLM. Response returned from LLM was: {draft_outline}")

    user_message = f"""
    Finally, can you come up with a logical name (in 3 to 4 words) for this doc file
    Return only the name as plain text, without any quotes (i.e. '') or other phrases
    """

    messages.append(HumanMessage(content = user_message))

    try:
      messages, draft_name, input_tokens, output_tokens = chat_with_gpt(model_type = model_type, api_key = api_key, messages = messages, temperature = 0.5, max_tokens = 2000)
      draft_name = draft_name.replace("```json", "").replace("```", "").replace("```python", "")
    except Exception as e:
      raise Exception(f"An error occurred while trying to come up with the name for the new draft: {e}")

    return messages, draft_outline, draft_name, input_tokens, output_tokens

def get_html_outline(notes, target_document_type, target_document_length, target_document_brief, model_type, api_key):
    """
    Given a bunch of notes and the specs for a target 'html' page, this function should generate an outline and return it as a list of json objects.
    Each json represents a unique section... and should contain the name of different sections, a one-line description, section type, section length (#words),
    and HTML-specific layout details.
    """

    draft_outline = {}
    input_tokens = 0
    output_tokens = 0

    # The system message is updated to ask for HTML-specific details in the outline.
    system_message = """
    You will be provided with a bunch of notes (text snippets enclosed in square brackets []), and some high level details about a target HTML page that needs to be created from those notes.
    You need to come up with an outline (list of logical sections) for that target HTML page, keeping both the notes and the target page in mind.

    This outline should be provided strictly as a list of structured JSON objects, each object representing details about a specific section.
    An example of the output structure is provided below:
    [
      {
        'title': "Name of the 1st Section",
        'details': "A one line description of what will be contained in this section.",
        'length': "Approximately how many words should be devoted to writing this section.",
        'layout': "Suggest the HTML structure. For e.g., 'Main heading as <h2>, followed by two <p> paragraphs. Use an <ul> for key points.'",
      },
      {
        'title': "Name of the 2nd Section",
        'details': "A one line description of what will be contained in this section.",
        'length': "Approximately how many words should be devoted to writing this section.",
        'layout': "Suggest the HTML structure. For e.g., 'Sub-heading as <h3> with font-size: 1.5em. Content within a styled <div> with a light gray background.'",
      },
      ...
    ]

    Keep the following in mind for the section 'length':
    - You will be given a max target document length in terms of #words. You need to ensure that #words across all sections doesn't exceed the target document length.
    - The number of sections should be logically derived from the content of the notes and the purpose of the target HTML page.

    The 'layout' key is crucial. It must contain a one-liner about how that section is to be structured using HTML. Be specific about header tags (<h1>, <h2>, <h3> etc.), content tags (<p>, <ul>, <ol>, <blockquote>), and any simple styling suggestions (like font size or bolding with <strong>) that would enhance the visual hierarchy.
    """

    user_message = f"""
    Next, here are the notes which need to be compiled into an HTML page:

    {notes}


    And here are the specifications of the target HTML page:
    1. target_document_type: {target_document_type}
    2. target_document_length: {target_document_length} words
    3. target_document_brief: {target_document_brief}

    Go ahead and generate the HTML outline as requested.
    """

    messages = [
      SystemMessage(content = system_message),
      HumanMessage(content = user_message)
    ]

    try:
      messages, draft_outline, input_tokens, output_tokens = chat_with_gpt(model_type = model_type, api_key = api_key, messages = messages,temperature = 0.5, max_tokens = 4000)

    # The following lines simulate the raw output from the LLM for demonstration.
    # In a real scenario, the output would come from the 'chat_with_gpt' call.
    # draft_outline = """
    # ```json
    # [
    #   {
    #     "title": "Introduction to Quantum Computing",
    #     "details": "A high-level overview of what quantum computing is and why it's a significant leap from classical computing.",
    #     "length": "150",
    #     "layout": "Main page title as <h1>. A brief introductory paragraph using <p>."
    #   },
    #   {
    #     "title": "Core Concepts: Qubits and Superposition",
    #     "details": "Explaining the fundamental building block of quantum computers, the qubit, and the principle of superposition.",
    #     "length": "250",
    #     "layout": "Section header as <h2>. Two <p> tags to explain the concepts. Key terms 'qubit' and 'superposition' in <strong> tags."
    #   },
    #   {
    #     "title": "The Power of Entanglement",
    #     "details": "Describing the counter-intuitive phenomenon of quantum entanglement and its role in processing power.",
    #     "length": "200",
    #     "layout": "Section header as <h2>. A blockquote <blockquote> to feature a famous quote about entanglement, followed by a <p> tag for explanation."
    #   }
    # ]
    # ```
    # """

      draft_outline = draft_outline.replace("```json", "").replace("```", "")
      draft_outline = json.loads(draft_outline)

    except Exception as e:
      raise Exception(f"An error occurred while trying to generate an outline for the new draft: {e}")
    except json.JSONDecodeError:
      raise Exception(f"Failed to decode outline JSON created using LLM. Response returned from LLM was: {draft_outline}")

    # The prompt for the name is updated to be more relevant for an HTML page title (SEO-friendly).
    user_message = f"""
    Finally, can you come up with a logical and SEO-friendly title (in 5 to 7 words) for this HTML page? This will be used in the <title> tag.
    Return only the title as plain text, without any quotes (i.e. '') or other phrases.
    """

    messages.append(HumanMessage(content = user_message))

    try:
      messages, draft_name, input_tokens, output_tokens = chat_with_gpt(model_type = model_type, api_key = api_key, messages = messages, temperature = 0.5, max_tokens = 2000)
      #Sample line to test
      #draft_name = "An Introduction to Quantum Computing Concepts"

      draft_name = draft_name.replace("```json", "").replace("```", "").replace("```python", "")
    except Exception as e:
      raise Exception(f"An error occurred while trying to come up with the name for the new draft: {e}")

    return messages, draft_outline, draft_name, input_tokens, output_tokens