"""
Database utility functions.
"""

import os
import time
import json
import pandas as pd
import numpy as np
from typing import Union, Dict, List, Optional, Tuple
from sqlalchemy import create_engine
from pandasql import sqldf
from src.tools.data_interpreter.models import DBDetails, SNOWFLAKE
from src.tools.data_interpreter.utils.llm_utils import chat_with_model


def get_db_hash(db_connection_details: DBDetails) -> str:
    """
    Generates a hash for the database connection details.
    This is used to identify the database connection in the agent state.
    """
    db_hash = f"{db_connection_details['db_type']}_{db_connection_details['host']}_{db_connection_details['port']}_{db_connection_details['database']}"
    if db_connection_details.get('schema'):
        db_hash += f"_{db_connection_details['schema']}"
    if db_connection_details.get('warehouse'):
        db_hash += f"_{db_connection_details['warehouse']}"
    if db_connection_details.get('role'):
        db_hash += f"_{db_connection_details['role']}"

    return db_hash


def create_connection(db_uri) -> Union[None, 'sqlalchemy.engine.Engine']:
    """
    Creates a connection to the database
    If only `db_details` is provided, assumes data is uploaded on internal db, thus returns same engine.
    If `internal_db_details` and `external_db_details` are provided, creates a connection to the internal db as well as external db.
    """
    try:
        return create_engine(db_uri)
    except Exception as e:
        print(f"Error creating database connection: {e}")
        raise e


def tool_fetch_from_external_db(
        source_name_in_db: str,
        source_db_uri: dict,
        db_type: str
) -> tuple[Optional[str], Optional[List[str]], str]:
    """Fetches a single table from the external database."""
    try:
        engine = create_connection(source_db_uri)
        # source_name_in_db is assumed to be the correct table name
        query = f"SELECT * FROM `{source_name_in_db}`"
        if db_type == SNOWFLAKE:
            query = query.replace("`", "")
        df = pd.read_sql_query(query, con=engine)
        column_names = df.columns.tolist()

        # Fill missing values for consistent JSON serialization
        for col_name in df.columns:
            if df[col_name].dtype == 'object':
                df[col_name] = df[col_name].fillna('')
            elif np.issubdtype(df[col_name].dtype, np.number):
                df[col_name] = df[col_name].astype(float).where(df[col_name].notnull(), None)
            elif np.issubdtype(df[col_name].dtype, np.datetime64):
                df[col_name] = df[col_name].where(df[col_name].notnull(), None)
                df[col_name] = df[col_name].apply(lambda x: x.isoformat() if pd.notnull(x) else None)

        data_list = df.to_dict(orient='records')
        return data_list, column_names, "success"

    except Exception as e:
        error_message = f"$$FAILED$$ Could not load table '{source_name_in_db}' from database: {e}"
        print(error_message)
        return None, None, error_message
    finally:
        if engine:
            engine.dispose()


def tool_execute_pandasql_query(
        sql_instruction: str,
        dataframes_env: Dict[str, pd.DataFrame]  # Dict of { 'clean_name': DataFrame }
) -> tuple[Optional[str], Optional[List[str]], str]:  # (json_data, column_names, status)
    """Executes a pandasql query on a given environment of DataFrames."""
    try:
        # Ensure table names in sql_instruction match keys in dataframes_env
        queried_df = sqldf(sql_instruction, env=dataframes_env)

        if queried_df is None:
            return None, None, "$$FAILED$$ pandasql query returned None. SQL: " + sql_instruction

        column_names = queried_df.columns.tolist()

        # Fill missing values
        for col_name in queried_df.columns:
            if queried_df[col_name].dtype == 'object':
                queried_df[col_name] = queried_df[col_name].fillna('')
            elif np.issubdtype(queried_df[col_name].dtype, np.number):
                queried_df[col_name] = queried_df[col_name].astype(float).where(queried_df[col_name].notnull(), None)
            elif np.issubdtype(queried_df[col_name].dtype, np.datetime64):
                queried_df[col_name] = queried_df[col_name].where(queried_df[col_name].notnull(), None)
                queried_df[col_name] = queried_df[col_name].apply(lambda x: x.isoformat() if pd.notnull(x) else None)

        data_list = queried_df.to_dict(orient='records')
        return data_list, column_names, "success_pandasql"

    except Exception as e:
        error_message = f"$$FAILED$$ Error during pandasql execution: {e}. SQL: {sql_instruction}"
        print(error_message)
        return None, None, error_message


def modify_query_for_snowflake(query, model_type, api_key):
    """
    Modify the query to be compatible with Snowflake if needed.
    This is a placeholder for any specific modifications required.
    """
    from langchain_core.messages import SystemMessage, HumanMessage
    
    prompt = """You are provided with a SQL query that needs to be modified to be compatible with Snowflake.
        Make the necessary changes to ensure it runs correctly in a Snowflake environment.
        The query is:
        ```
        {query}
        ```
        Return the modified query as a string."""
    
    messages = [
        SystemMessage(content="Return your response as a valid JSON with keys 'thinking' and 'response'"),
        HumanMessage(content=prompt.format(query=query))
    ]
    
    _, response, _, _ = chat_with_model(
        messages=messages, 
        temperature=0, 
        max_tokens=2000,
        model_type=model_type, 
        api_key=api_key
    )
    
    query = json.loads(response.replace("```json", "").replace("```sql", "").replace("```", ""))['response']
    return query.strip()