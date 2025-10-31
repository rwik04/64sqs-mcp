"""
Source processing utilities (decoupled from target.py)
"""

import os
import json
import time
import math
import pandas as pd
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Tuple
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.tools.data_interpreter.utils.db_utils import create_connection
from src.tools.data_interpreter.utils.llm_utils import chat_with_model
from src.tools.data_interpreter.models import STRUCTURED, EXCEL, DB, SNOWFLAKE, Data_Source_Type
from src.tools.data_interpreter.config import Config


def process_single_source(
    user_source, engine, system_prompt_str, user_query_str, model_type, api_key
):
    """
    Processes a single user_source: fetches schema, sample data, calls LLM asynchronously.

    Returns a tuple: (user_source_if_relevant_or_None, input_tokens, output_tokens)
    """
    messages = [SystemMessage(content=system_prompt_str)]
    external_engine = engine  # Default to internal engine if no connection details provided
    data_schema_list_internal = None
    is_temp_source = user_source.get('filetype') == 'temp'
    if user_source.get('source_db_uri') is not None and not is_temp_source:
        source_db_uri = user_source['source_db_uri']
        external_engine = create_connection(source_db_uri)

    try:
        print(f"Process Single Source {user_source}")
        query_schema_for_source = None
        if is_temp_source:
            # Build schema from provided temp rows
            rows = user_source.get('temp_rows') or []
            if rows and isinstance(rows, list) and isinstance(rows[0], dict):
                cols = list({k for r in rows for k in r.keys()})
                data_schema_list_internal = [{ 'name': c, 'description': '' } for c in cols]
        elif user_source.get("filetype") == DB and user_source.get('extid') is not None:
            query_schema_for_source = f"SELECT column_descriptions FROM db_manager WHERE id = {user_source['extid']}"
        elif user_source.get("filetype") == STRUCTURED and user_source.get('extid') is not None:
            query_schema_for_source = f"SELECT column_descriptions FROM csv_file_manager WHERE id = {user_source['extid']}"
        elif user_source.get('filetype') == EXCEL and user_source.get('extid') is not None:
            query_schema_for_source = f"SELECT column_descriptions FROM excel_file_manager WHERE id = {user_source['extid']}"
        else:
            print(f"Async: No schema query available for {user_source.get('displayname')}, skipping schema extraction.")

        if query_schema_for_source:
            result_df_schema = pd.read_sql(query_schema_for_source, engine)  # schema to be extracted from internal db

            if not result_df_schema.empty and 'column_descriptions' in result_df_schema.columns:
                schema_str = result_df_schema['column_descriptions'].iloc[0]
                if isinstance(schema_str, str) and schema_str.strip():
                    try:
                        evaluated_schema = eval(schema_str)
                        if isinstance(evaluated_schema, list):
                            data_schema_list_internal = evaluated_schema
                    except Exception as eval_e:
                        print(f"Async: Error eval-ing schema for {user_source.get('displayname')}: {eval_e}")

    except Exception as e_schema:
        print(f"Async: Error loading schema for {user_source.get('displayname')}: {e_schema}")

    sample_query_str = ''
    schema_text_internal = ''
    try:
        if is_temp_source:
            rows = user_source.get('temp_rows') or []
            sample_result_df = pd.DataFrame(rows[:10]) if rows else pd.DataFrame()
        else:
            sample_query_str = f"SELECT * FROM `{user_source['tablename']}` ORDER BY RAND() LIMIT 10;"
            if user_source.get("db_type", "") == SNOWFLAKE:
                sample_query_str = f"SELECT * FROM {user_source['tablename']} ORDER BY RANDOM() LIMIT 10;"
            sample_result_df = pd.read_sql(sample_query_str, external_engine)
        print(f"PROCESSING SOURCE: {user_source.get('displayname', 'N/A')}\t:\t{data_schema_list_internal}")

        temp_schema_text = ""
        for col_spec in (data_schema_list_internal or []):
            col_name = col_spec.get('name')
            col_desc = col_spec.get('description', '')
            if col_name and col_name in sample_result_df.columns:
                examples = ", ".join([str(item) for item in sample_result_df[col_name].dropna().to_list()])
                temp_schema_text += f"{col_name} | {col_desc} | Example data: {examples}\n"
            elif col_name:
                temp_schema_text += f"{col_name} | {col_desc} | Example data: Not available in sample\n"
        if temp_schema_text.strip():
            schema_text_internal = temp_schema_text

    except Exception as e_sample:
        print(sample_query_str)
        print(f"Async: Error fetching/processing sample data for {user_source.get('displayname')}: {e_sample}")

    schema_prompt_content = f"""
    Here is the schema description of the data source named `{user_source.get('displayname', 'N/A')}`.
    A random sample of up to 10 rows might be provided along with column descriptions.
    Keep in mind that these are just a sample and may not represent the entire data.

    Read it as - `column_name | column_description | Example data (if available)`:
    ```
    {schema_text_internal}
    ```
    """
    messages.append(HumanMessage(content=schema_prompt_content))

    if external_engine != engine and not is_temp_source:
        external_engine.dispose()

    try:
        _, response, in_tokens, out_tokens = chat_with_model(
            model_type, api_key, messages=messages,
            temperature=0, max_tokens=512,
        )

        response = response.replace("```json", "").replace("```", "").strip()
        response = json.loads(response)

        print(f"File name: {user_source['displayname']}: {response['reason']}")

        if response['relevant'].lower() == 'yes':
            return user_source, in_tokens, out_tokens
        else:
            return None, in_tokens, out_tokens

    except Exception as e:
        print(f"Async: LLM call error for {user_source.get('displayname')}: {e}")
        return None, 0, 0


def shortlist_user_sources(user_query, user_sources, model_type, api_key):
    """
    Shortlists user sources: orchestrates the process of shortlisting user_sources
    Returns a list of shortlisted user sources: (list_of_shortlisted_sources, input_tokens, output_tokens)
    """

    print(user_query)
    shortlisted_user_sources_final = []
    system_prompt_content = f"""
    You are a helpful assistant for 'Research and Analysis'
    Your role is to help users get answers to queries by gathering, analyzing, and summarizing information across various data sources provided by them.

    Next, you will be shown the data sources with their summary/schema, one by one.
    You will then need to determine if the provided data source appears relevant for answering the following query or not
    ```
    {user_query}
    ```

    IMPORTANT GUIDELINES
    1. Take note of both the name and the schema description of the data source.
    2. The data-source is to be considered relevant even if just the name of the source or name of a single column appears relevant for answering the query or not.
    3. Sometimes, based on the summary you might feel that data need not directly have the phrase giving out the answer. But it may still be relevant if you think you get to the required answer by reviewing the data and extracting relevant insights
    4. Sometimes, queries may involve triangulating of information from multiple files. In that case, we will need to identify all those files, one by one

    If a file appears to be relevant for answering the query (completely or in part), return a JSON without any extra verbiage of the following format:
    {{
      "relevant": "YES" or "NO",
      "reason": "reason why it is relevant or not relevant"
    }}
    """

    total_input_tokens = 0
    total_output_tokens = 0

    # COMMON DB connection
    engine = create_connection(Config.DB_URI)

    all_results = []
    if user_sources:
        num_workers = min(len(user_sources), 20)

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for source_item in user_sources:
                futures.append(executor.submit(
                    process_single_source,
                    source_item,
                    engine,
                    system_prompt_content,
                    user_query,
                    model_type,
                    api_key
                ))

            for future in futures:
                try:
                    all_results.append(future.result())
                except Exception as e_future:
                    print(f"A thread for source processing raised an exception: {e_future}")
                    all_results.append((None, 0, 0))

    # Process results
    for result_item in all_results:
        if result_item is not None:  # Should always be a tuple now
            relevant_user_source, in_tokens_item, out_tokens_item = result_item
            total_input_tokens += in_tokens_item
            total_output_tokens += out_tokens_item
            if relevant_user_source:
                shortlisted_user_sources_final.append(relevant_user_source)

    if engine:
        engine.dispose()

    return shortlisted_user_sources_final, total_input_tokens, total_output_tokens


def prepare_initial_message_thread(user_query, user_sources, model_type, api_key):
    """
    Attempts to prepare an initial list of messages for the LLM (agent) with initial context about task, tools available and files provided

    Args:
        user_query (str): the query asked by the user
        user_sources (List): the data sources provided by the user from where the answer needs to be searched and returned

    Returns:
        messages (List): A list of messages with initial context about task, tools available and files provided
    """
    engine = create_connection(Config.DB_URI)
    ext_engine = None
    # Define system context message, with details around the task as well as tools available
    messages = [
        SystemMessage(content=f"""
        You are a helpful assistant for 'Research and Analysis'
        Your role is to help users get answers to queries by gathering, analyzing, and summarizing information across various data sources provided by them.

        These data sources can be of the following types
        1. UNSTRUCTURED_TEXT - PDFs, DOCx, TXTs, etc. These documents would be parsed and stored as small chunks of text
        2. STRUCTURED_TABLE - CSVs or Relational DB Tables. CSVs are also parsed and stored as tables in a relational database, with the same name as that of the CSV file

        Besides the above two data source types, there is a third type
        3. STRUCTURED_TABLE_TEMPORARY - Any intermediate data (derived from structured or unstructured data sources) that is created/acquired in the process of answering the user query. Stored as a table as data is acquired.

        You will next be guided (step by step) on how you need to go about answering queries
        Follow the instructions at each step carefully and carry them out to the best of your ability
        """
        ),
        HumanMessage(content=f"""
        To start with, here's the query from the user
        ```
        {user_query}
        ```

        Next up is a list of data sources provided by the user, to be presented one by one
        For each data source, you will be shown a relevant summary (or data schema description) and sample data
        """
        )
    ]

    if len(user_sources) > 0:
        # Describe the shortlisted user_sources
        for i, user_source in enumerate(user_sources):
            # Create connection object
            source_connection_details = user_source.get('source_db_uri')
            ext_engine = create_connection(source_connection_details) if source_connection_details else None
            data_description = ''
            data_schema = None
            sample_data_dict_string = ''
            try:
                query = None
                # TEMP source: build schema from provided rows
                if user_source.get('filetype') == 'temp':
                    rows = user_source.get('temp_rows') or []
                    cols = []
                    if rows and isinstance(rows, list) and isinstance(rows[0], dict):
                        cols = list({k for r in rows for k in r.keys()})
                    data_schema = [{ 'name': c, 'description': '' } for c in cols]
                    data_description = 'Temporary table derived from JSON.'
                else:
                    # load data schema from metadata tables
                    if user_source['filetype'] == STRUCTURED:
                        query = f"select column_descriptions from csv_file_manager where id = {user_source['extid']}"
                    elif user_source['filetype'] == EXCEL:
                        query = f"select column_descriptions from excel_file_manager where id = {user_source['extid']}"
                    elif user_source['filetype'] == DB and user_source.get('extid') is not None:
                        query = f"SELECT column_descriptions FROM db_manager WHERE id = {user_source['extid']}"

                    # Remove timing logic here
                    result = pd.read_sql(query, con=engine)
                    data_schema = eval(result['column_descriptions'][0])
                    print(f"Data schema loaded for {user_source.get('displayname', user_source.get('tablename', 'N/A'))}")

                # load data description
                if user_source.get('filetype') != 'temp':
                    query = ''
                    if user_source['filetype'] == STRUCTURED:
                        query = f"select description from csv_file_manager where id = {user_source['extid']}"
                    elif user_source['filetype'] == EXCEL:
                        query = f"select description from excel_file_manager where id = {user_source['extid']}"
                    elif user_source['filetype'] == DB:
                        query = f"select description from db_manager where id = {user_source['extid']}"

                    result = pd.read_sql(query, con=engine)
                    data_description = result['description'][0]
                    print(f"Column description loaded for {user_source.get('displayname', user_source.get('tablename', 'N/A'))}")

            except Exception as e:
                print(f"An error occured while loading data schema for file {user_source['displayname']}: {e}")

            try:
                if user_source.get('filetype') == 'temp':
                    # Use provided temp rows as sample
                    rows = user_source.get('temp_rows') or []
                    rows = rows[:10]
                    if rows:
                        sample_data_dict_for_json = pd.DataFrame(rows).to_dict(orient='list')
                        sample_data_dict_string = json.dumps(sample_data_dict_for_json, indent=4)
                    else:
                        sample_data_dict_string = "No sample data rows found."
                else:
                    # Load sample data from external source
                    query_sample = f"select * from `{user_source['tablename']}` ORDER BY RAND() limit 10"
                    if user_source.get("db_type") == SNOWFLAKE:
                        query_sample = f"select * from {user_source['tablename']} ORDER BY RANDOM() limit 10"
                    sample_data_df = pd.read_sql(query_sample, con=ext_engine)
                    print(f"Sample data loaded for {user_source.get('displayname', user_source.get('tablename', 'N/A'))}")
                    # Create a serializable version of the sample data
                    # added fix
                    serializable_sample_data = []
                    if not sample_data_df.empty:
                        for record in sample_data_df.to_dict(orient='records'):
                            serializable_record = {}
                            for key, value in record.items():
                                if isinstance(value, pd.Timestamp):
                                    serializable_record[key] = value.isoformat()
                                elif isinstance(value, datetime):
                                    serializable_record[key] = value.isoformat()
                                elif isinstance(value, date):
                                    serializable_record[key] = value.isoformat()
                                elif isinstance(value, float) and math.isnan(value):
                                    serializable_record[key] = None
                                elif pd.isna(value):
                                    serializable_record[key] = None
                                else:
                                    serializable_record[key] = value
                            serializable_sample_data.append(serializable_record)

                        # Convert the list of serializable records to the desired dict format for JSON dump
                        # If you want orient='list' for json.dumps:
                        sample_data_dict_for_json = pd.DataFrame(serializable_sample_data).to_dict(orient='list')
                        sample_data_dict_string = json.dumps(sample_data_dict_for_json, indent=4)
                    else:
                        sample_data_dict_string = "No sample data rows found."

            except Exception as e:
                print(f"An error occured while loading sample data for file {user_source['displayname']}: {e}")

            # convert schema from json to delimiter based string
            schema_text = ""
            for col in (data_schema or []):
                schema_text += f"{col['name']} | {col.get('description', '')}\n"

            # append schema as prompt to the message thread
            schema_prompt = f"""
            Here is the description (including schema details) the data source #{i} - `{user_source['tablename']}`.
            General description:
            ```
            {data_description}
            ```

            Schema details; Read it as - `column_name | column_description`:
            ```
            {schema_text}
            ```
            """
            messages.append(HumanMessage(content=schema_prompt))

            # append sample data as prompt to the message thread
            sample_data_prompt = f"""
            And here are some sample rows from the above data source.
            Use them to get an idea about the data and ACCORDINGLY DECIDE THE TOOLS to be used.
            ```
            {sample_data_dict_string}
            ```
            """
            messages.append(HumanMessage(content=sample_data_prompt))

        question_prompt = """Based on the query and the data description, answer the following questions:

        1. What are the different raw/derived metrics you need to answer the query? Be very specific about the metrics, especially if they have to be derived as well.
        2. ⁠Do you think you can get all of the above metrics via a single SQL task with one or more CTEs… Or will you need to do break it down into more steps? As far as possible you should do the former unless you need to annotate some textual fields.

        Answer both the questions in a concise and complete manner without extra verbiage.
        """
        messages.append(HumanMessage(content=question_prompt))

        output_messages, response, input_tokens, output_tokens = chat_with_model(messages=messages, temperature=0,
                                                                                 max_tokens=4096, model_type=model_type,
                                                                                 api_key=api_key)
        print(f"LLM call completed for {user_source.get('displayname', user_source.get('tablename', 'N/A'))}")
        print(f"Answer to questions: {response}")

        messages.append(AIMessage(content=response))

        # Describe the different tools available to the agent
        tool_descriptions_prompt = """
        1. query_data: To acquire some data from a particular data source (UNSTRUCTURED_TEXT or STRUCTURED_TABLE or STRUCTURED_TABLE_TEMPORARY) using search queries or SQL queries. Any mathematical aggregation/calculations required to answer the query must be done by SQL querying on raw or intermediate tables. SQL queries should be optimised to filter as well as aggregate data to the right level upfront. So create the most efficient query operation using one or more CTEs if required.
        2. annotate_data: To review the acquired or the raw data queried (record by record) and annotate it with one or more fields. This can be used for more investigating/assessing the queried data in a more nuanced way and then tagging it with Yes/No or different labels/categories. Use this when the user asks something which is qualitative and cannot be applied as a filter due to no explicit presence as a column/or its values. This should ONLY be used wrt text fields, since numeric/integer fields can be easily inspected/manipulated/summarised using mathematical operations in tool query_data.
        3. summarise_answer: To go through the final data and create the final response. To be executed once required data has been acquired and if required, annotated. Should not be used to perform mathematical operations/calculations using the acquired data, use only to report the final answer using final data which has all the computations and aggregations done beforehand. Try to do this action in one step unless it is very essential.

        Besides the above tools, there's also a fourth one
        4. __end__: To end the execution when
        --- the goal has been accomplished (i.e. final response done)
        --- or the data sources provided by the user are not relevant
        --- or we are not able to acquire the right intermediate data even though the data sources looked relevant
        """

        # Generate plan of action
        plan_generation_prompt = f"""
        Now, based on the schema and sample-data provided above, generate a plan of action to answer the user query
        The plan of action needs to clearly specify what tool will be invoked at each step, along with a reason for the same

        One important guideline is DO NOT generate an invalid plan. A plan is invalid when the tool summary_answer is required to perform any calculation or mathematical operations on the acquired data as part of its assigned task.
        A valid plan is one which performs all the necessary calculations, computations using query_data tool by SQL on raw or intermediate tables even if it takes one extra step.

        You will have the following tools at your disposal, that you can use to answer the user-query. Use only these tools.
        ```
        {tool_descriptions_prompt}
        ```

        And here is the user query, provided once again for your reference.
        ```
        {user_query}
        ```

        -- Return the plan as a VALID list (i.e. enclosed within square brackets []) of JSONs. Each JSON in the list of JSONs returned must have the following keys:
        ---- 'tool_name': Contains the name of the tool to be executed at that step of the route. Clearly mention the name of the tool without any error as a string, enclosed within double quotes.
        ---- 'reason': Contains the reason for the execution of the tool. Briefly explain how that tool is to be used. Give it as a string enclosed within double quotes.
        ------ If the tool is `query_data`, clearly specify what operations are required to be performed for example, joins, groupings or calculations, etc Try to aggregate data upfront if required using one or more CTEs.
        ------ If the tool is annotate_data, you MUST create a SEPARATE plan step for EACH distinct theme, topic, or question you need to annotate. For example, if the query is "How many employees complain about low pay and how many complain about long hours?", your plan MUST have TWO separate 'annotate_data' steps: one to tag reviews for 'low pay' and a second one to tag reviews for 'long hours'. Do NOT combine multiple annotation tasks into a single step. Annotations is required only for text fields
        ------ If the tool is `summarise_answer`, clearly specify what data is to be summarised and how it is to be performed.
        ---- DO NOT return any other extra text or information in the above json

        IMPORTANT GUIDELINES for creating the plan
        -- The order in which tools are planned to be invoked must be logical, which can be followed step-by-step to accurately answer the given user-query based on the provided data sources.
        -- The tools 'query_data' and 'annotate_data' can be invoked on multiple files. Thus if it is required to acquire or annotate multiple files, it can be done in a single step. The details of how to invoke are different and will be covered later
        -- The tool 'summarise_answer' should ideally be done on a single one file. So if there are multiple datasets, they should be integrated/joined using query_data first before invoking summarisation. Should not be used to perform mathematical operations/calculations using the acquired data.
        -- The tool 'summarise_answer' should not perform any mathematical calculation and therefore any calculation must not be there in it's 'reason'. Any calculation must be done using tool 'query_data' only.
        -- If the files can't be integrated/joined, they may be provided directly to the tool 'summarise_answer' as multiple data sources
        -- If there are multiple datasets over which summarisation needs to be done, integrate the data before invoking this tool by invoking the `query_data` tool.
        -- While creating the plan, ignore any mention of 'creating charts/visualisation' in the query. That will be done separately once we have the answer and the final data
        -- For annotate_data: If the query requires multiple distinct annotations (e.g., tagging multiple themes, conditions, or labels like 'positive team environment', 'good management', 'low pay', or 'long hours'), each annotation MUST result in its own separate column and MUST be performed in a SEPARATE annotate_data step. Do NOT combine multiple annotations into a single step, as this will lead to malformed outputs (e.g., concatenated values in one column). After all annotations, use query_data to create a final table joining or selecting the relevant columns for aggregation/counting.
        -- Example for multi-annotation: If identifying and tagging 5 themes, plan separate annotate_data steps for each theme (creating one column per step), then query_data to combine into a final table for counting/summarization.
        -- For queries involving mutually exclusive groups or combinations of conditions (e.g., 'A but not B', 'B but not A', 'both A and B', 'neither'), ALWAYS plan SEPARATE annotate_data steps for EACH group, treating them as distinct qualitative conditions to create explicit Yes/No columns (e.g., 'mentions_nyquil_not_tylenol: Yes/No' where Yes if text mentions Nyquil AND NOT Tylenol). Do NOT derive combos in query_data—annotate each explicitly so the final table has dedicated columns for each bucket. Use query_data only to merge the columns and count Yes per column for the summary.
        -- In annotation reasons, specify the exact combo logic without assuming derivation (e.g., "Tag Yes if mentions Nyquil AND NOT Tylenol in the text").
        -- For queries requiring identification of top themes/topics from text fields (e.g., top 5 themes from 'Pros'): After an initial query_data to extract the relevant text column, use summarise_answer to analyze the text and explicitly list the top 5 themes (e.g., as a non-calculative summary step). Then, proceed with separate annotate_data steps to tag presence (Y/N) or single lable/category for each identified theme.
        -- A valid plan must have `__end__` as their last step.

        Finally, here are some examples of how a typical execution might look like
          1. 'query_data' --> 'summarise_answer' --> '__end__' : this is the simplest case when the acquired data is ready to be summarised in one go
          2. 'query_data' --> 'annotate_data' --> 'query_data' --> 'summarise_answer' --> '__end__' : a slightly more complex case when the acquired data needs to be inspected (Say if a certain condition is met or not) and then annotated with different lables then again acquired to count the no. of cases with the required label and finally sent for summarising
          3. 'query_data' --> 'annotate_data' --> 'query_data' --> 'annotate_data' --> 'query_data' --> 'summarise_answer' --> '__end__' : an even more complex case where the data needs to be first queried and then marked as per some condition, then checked against the marked condition, then marked again, and then queried and sent for summarisation.
          4. 'query_data' --> 'annotate_data' (for theme1) --> 'annotate_data' (for theme2) --> 'annotate_data' (for theme3) --> 'query_data' (combine columns and count) --> 'summarise_answer' --> '__end__' : For queries needing multiple Y/N tags (e.g., per theme or condition), use separate annotate_data per column, then aggregate.
          5. Data Integration / Joining: For a query that requires combining two tables, like "What are the common 'pros' mentioned for products in the 'Software' category?", assuming you have a reviewstable and aproducts table.
            - Step 1: query_data(to write a SQL query that JOINS thereviewsandproductstables, filters forcategory = 'Software', and selects the relevant 'pros' column).
            - Step 2: summarise_answer (to read the resulting list of 'pros' and identify the common themes).
            - Step 3: end.
            This shows how to first combine data sources before analyzing them.
          6. 'query_data' (extract text) → 'annotate_data' (tag A not B) → 'annotate_data' (tag B not A) → 'annotate_data' (tag both) → 'annotate_data' (tag neither) → 'query_data' (count per column) → 'summarise_answer' (report) → '__end__' : Alternative for explicit combo columns.
          7. 'query_data' (extract text) → 'annotate_data' (tag for A but not B) → 'annotate_data' (tag for B but not A) → 'annotate_data' (tag for both A and B) → 'annotate_data' (tag for neither) → 'query_data' (merge columns and count Yes per combo column) → 'summarise_answer' (report counts with table showing the 4 columns) → '__end__' : For mutual-exclusion queries needing explicit combo columns in the final output (e.g., medicine mentions like Nyquil/Tylenol groups).
          8. 'query_data' (extract relevant text column) → 'annotate_data' (tag mentions_nyquil_not_tylenol: Yes/No) → 'annotate_data' (tag mentions_tylenol_not_nyquil: Yes/No) → 'annotate_data' (tag mentions_both: Yes/No) → 'annotate_data' (tag mentions_neither: Yes/No) → 'query_data' (combine into final table with the 4 columns and count Yes for each) → 'summarise_answer' (report counts and show sample table with the columns) → '__end__' : Explicitly annotate and output each combo as separate columns for direct final table visibility.
        These are just some example cases. You may have more complex cases
        Logically decide a route for the same. DO NOT go into longer, more complex routes unless required like in the cases where performing a calculation like averaging or percentage representaion is required, for these operation, you have to use tool 'query_data' and perform using SQL, if one extra step is required then let it be so.
        While using query_data, try to filter and summarise the data to the right level as much as possible
        """
        messages.append(HumanMessage(plan_generation_prompt))

    else:
        messages.append(HumanMessage(
            content=f"It appears that none of the data sources provided by the user were relevant for answering the query"))
        messages.append(AIMessage(content="[{'tool_name': '__end__', 'reason': 'No relevant sources found'}]"))

    # Close connection objects
    engine.dispose()
    if ext_engine:
        ext_engine.dispose()

    return messages
