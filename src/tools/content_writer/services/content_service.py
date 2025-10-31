import os
import sys

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from tools.content_writer.services.outline_service import get_doc_outline, get_html_outline
from tools.content_writer.services.section_service import get_doc_section_content, get_html_section_content
from docx import Document
from docx.shared import RGBColor, Pt

def get_content(notes, target_document_type, target_document_length, target_document_brief, model_type, api_key):
    """
    Given notes and target document specs, this function orchestrates the generation of a content draft.

    1. notes: List of text snippets.
    2. target_document_type: 'doc', or 'html'.
    3. target_document_length: String describing length ('XX slides' or 'XX words').
    4. target_document_brief: String with high-level instructions.

    Returns the final content draft, a draft name, and a token tracking dictionary.
    """
    draft_content = []
    token_tracker = {}

    # 1. Use dictionaries to map document types to their respective functions
    outline_functions = {
        "doc": get_doc_outline,
        "html": get_html_outline,
    }
    content_functions = {
        "doc": get_doc_section_content,
        "html": get_html_section_content,
    }

    # Check for a supported document type
    if target_document_type not in outline_functions:
        raise ValueError(f"Unsupported document type: '{target_document_type}'. Supported types are: {list(outline_functions.keys())}")

    ## STEP 1: Generate an outline for the draft
    try:
        # Select the correct outline function from the dictionary
        outline_func = outline_functions[target_document_type]
        messages, draft_outline, draft_name, input_tokens, output_tokens = outline_func(
            notes=notes,
            target_document_type=target_document_type,
            target_document_length=target_document_length,
            target_document_brief=target_document_brief,
            model_type=model_type,
            api_key=api_key
        )
        token_tracker["get_draft_outline"] = {model_type: {"input_tokens": input_tokens, "output_tokens": output_tokens}}

    except Exception as e:
        raise Exception(f"An error occurred while generating the outline: {e}")

    # Create a summary message to guide the next step
    outline_generation_summary_message = f"""
    The outline for the {target_document_type} is complete. Next, you will generate the content for each section one by one.
    Do not repeat content across sections.
    """
    # This resets the history. For better context,use: messages.append(SystemMessage(...))
    messages = [SystemMessage(content=outline_generation_summary_message)]
    #messages.append(SystemMessage(content = outline_generation_summary_message))

    ## STEP 2: Generate content for each section
    final_input_tokens_section_detailing = 0
    final_output_tokens_section_detailing = 0

    # Select the correct content function from the dictionary
    content_func = content_functions[target_document_type]

    for section_detail in draft_outline:
        print(f"Generating content for section: {section_detail['title']}")
        try:
            messages, section_detail_updated, input_tokens, output_tokens = content_func(
                messages=messages,
                notes=notes,
                target_document_brief=target_document_brief,
                section_detail=section_detail,
                model_type=model_type,
                api_key=api_key
            )
            draft_content.append(section_detail_updated)
            final_input_tokens_section_detailing += input_tokens
            final_output_tokens_section_detailing += output_tokens

        except Exception as e:
            raise Exception(f"An error occurred while generating content for section '{section_detail['title']}': {e}")

    token_tracker.update(
    {
        "get_section_content": {
            model_type: {"input_tokens":  final_input_tokens_section_detailing, "output_tokens": final_output_tokens_section_detailing}
        }
    }
    )

    ## --Storing content for experimentation--
    global glob_content
    glob_content = draft_content
    ##

    return draft_content, draft_name, token_tracker

def create_doc_from_content(draft_content, draft_name, title_font_size=16, text_font_size=11, title_bold=True, title_underline=True):
    doc = Document()

    for item in draft_content:
        title = doc.add_heading(item['title'])
        if title_font_size is not None:
            for run in title.runs:
                run.font.size = Pt(title_font_size)
                run.bold = True
                run.underline = True
                run.font.color.rgb = RGBColor(0, 0, 0)

        text = doc.add_paragraph(item['content'])
        if text_font_size is not None:
            for run in text.runs:
                run.font.size = Pt(text_font_size)

    # Define base path for output files
    base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp")
    os.makedirs(base_path, exist_ok=True)
    output_doc_path = f"{base_path}/{draft_name}.docx"
    doc.save(output_doc_path)

    print("Saved document at ", output_doc_path)

def create_html_from_content(
    draft_content,
    draft_name,
    font_family="'Inter', sans-serif",
    bg_color="#ffffff",
    text_color="#333333",
    primary_color= "#000000", #"#007bff", black/blue
    container_max_width="800px",
    title_font_size="2.5em",
    text_font_size="1.1em",
    title_bold=True
):
    """
    Stitches HTML section content into a single, styled HTML file with customizable typography.

    Args:
        draft_content (list): A list of section dictionaries with 'content' keys.
        draft_name (str): The base name for the output file and the page title.
        base_path (str): The directory where the file will be saved.
        font_family (str): The CSS font-family for the page.
        bg_color (str): The background color of the page.
        text_color (str): The main text color.
        primary_color (str): An accent color for headings.
        container_max_width (str): The maximum width for the content container.
        title_font_size (str): The CSS font-size for the main <h1> title.
        text_font_size (str): The CSS font-size for body text like <p>, <ul>.
        title_bold (bool): Determines if headings should be bold.
    """

    # Combine the HTML content from all sections
    all_sections_html = "\n".join(item['content'] for item in draft_content)

    # Determine font-weight based on the title_bold flag
    title_font_weight = "bold" if title_bold else "normal"

    # Create a complete HTML5 document with embedded CSS for styling
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{draft_name}</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: {bg_color};
                --text-color: {text_color};
                --primary-color: {primary_color};
                --font-family: {font_family};
                --container-width: {container_max_width};
            }}

            body {{
                font-family: var(--font-family);
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: var(--bg-color);
                color: var(--text-color);
                display: flex;
                justify-content: center;
            }}

            .container {{
                width: 100%;
                max-width: var(--container-width);
            }}

            h1, h2, h3 {{
                color: var(--primary-color);
                line-height: 1.2;
                font-weight: {title_font_weight};
            }}

            h1 {{
                font-size: {title_font_size};
            }}

            /* Scaling section and sub-section headers relative to the main title */
            h2 {{
                font-size: calc({title_font_size} * 0.8);
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
                margin-top: 40px;
            }}

            h3 {{
                font-size: calc({title_font_size} * 0.6);
            }}

            p, ul, ol {{
                font-size: {text_font_size};
                margin-bottom: 1em;
            }}

            strong {{
                color: var(--primary-color);
            }}

            blockquote {{
                border-left: 4px solid #eee;
                padding-left: 1em;
                margin-left: 0;
                font-style: italic;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{draft_name}</h1>
            {all_sections_html}
        </div>
    </body>
    </html>
    """

    try:
        # Sanitize the draft_name to make it a valid filename
        safe_filename = "".join(c for c in draft_name if c.isalnum() or c in (' ', '_')).rstrip()
        # Define base path for output files
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp")
        os.makedirs(base_path, exist_ok=True)
        output_html_path = f"{base_path}/{safe_filename}.html"

        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"Saved HTML document at: {output_html_path}")

    except Exception as e:
        raise Exception(f"An error occurred while saving the HTML file: {e}")