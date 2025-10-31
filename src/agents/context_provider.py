import os
import json
import math
import random
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

import sys
# Ensure project root is on sys.path so `src.*` imports work when running this file directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

# Optional imports from existing utils for richer context where available
try:
    from src.tools.data_interpreter.utils.db_utils import create_connection
    from src.tools.data_interpreter.models import STRUCTURED, EXCEL, DB, SNOWFLAKE
    from src.tools.data_interpreter.config import Config as DataInterpreterConfig
except Exception:
    create_connection = None  # type: ignore
    STRUCTURED = "STRUCTURED_TABLE"  # fallback constant names
    EXCEL = "EXCEL"
    DB = "DB"
    SNOWFLAKE = "SNOWFLAKE"
    DataInterpreterConfig = None  # type: ignore


from src.tools.docs_analyser.utils.file_utils import load_summary_file
from src.tools.docs_analyser.config import Config as DocsAnalyserConfig

def _serialize_value(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def _df_to_sample_dict(df: pd.DataFrame, limit: int = 10) -> Dict[str, List[Any]]:
    if df is None or df.empty:
        return {}
    limited = df.head(limit)
    serializable_records: List[Dict[str, Any]] = []
    for record in limited.to_dict(orient="records"):
        serializable_records.append({k: _serialize_value(v) for k, v in record.items()})
    return pd.DataFrame(serializable_records).to_dict(orient="list") if serializable_records else {}


def _infer_schema_from_df(df: pd.DataFrame) -> List[Dict[str, Any]]:
    schema: List[Dict[str, Any]] = []
    if df is None or df.empty:
        return schema
    for col in df.columns:
        dtype = str(df[col].dtype)
        schema.append({"name": col, "description": f"dtype: {dtype}"})
    return schema


def _read_local_tabular(path: str, nrows: int = 10) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".csv", ".tsv"]:
        sep = "," if ext == ".csv" else "\t"
        return pd.read_csv(path, nrows=nrows, sep=sep)
    if ext in [".json", ".jsonl"]:
        try:
            return pd.read_json(path, lines=(ext == ".jsonl"), nrows=nrows)
        except TypeError:
            # pandas < 2 may not support nrows for json; fallback
            return pd.read_json(path, lines=(ext == ".jsonl"))
    if ext in [".parquet"]:
        return pd.read_parquet(path, engine="pyarrow")
    if ext in [".xlsx", ".xls"]:
        try:
            return pd.read_excel(path, nrows=nrows)
        except TypeError:
            return pd.read_excel(path)
    return pd.DataFrame()


def build_context_from_temp_files(temp_files: List[str]) -> List[HumanMessage]:
    """
    Build HumanMessage blocks containing schema and sample rows for local temporary files
    recently created by previous tool steps. Supports CSV/TSV/JSON/JSONL/Parquet.

    Args:
        temp_files: list of absolute or relative file paths

    Returns:
        List[HumanMessage] to prepend before tool-call parameter generation
    """
    messages: List[HumanMessage] = []
    blocks: List[str] = []
    for path in (temp_files or []):
        try:
            if not isinstance(path, str) or not os.path.exists(path):
                continue
            df = _read_local_tabular(path, nrows=50)
            sample = _df_to_sample_dict(df, limit=10)
            schema = _infer_schema_from_df(df)
            schema_text = "\n".join([f"{c['name']} | {c.get('description','')}" for c in schema])
            sample_text = json.dumps(sample, indent=4) if sample else "No sample data rows found."
            blocks.append(
                f"Dataset: `\nSchema (name | description):\n```\n{schema_text}\n```\nSample (JSON orient='list'):\n```\n{sample_text}\n```"
            )
        except Exception:
            continue
    if blocks:
        messages.append(HumanMessage(content="\n\n".join(blocks)))
    return messages


def get_temp_context(paths: List[str] = None) -> Dict[str, Dict[str, Any]]:
    """Simple helper to read local tabular files and return schema+sample."""
    result: Dict[str, Dict[str, Any]] = {}
    for path in (paths or []):
        try:
            if not isinstance(path, str) or not os.path.exists(path):
                continue
            df = _read_local_tabular(path, nrows=50)
            sample = _df_to_sample_dict(df, limit=10)
            schema = _infer_schema_from_df(df)
            result[path] = {"schema": schema, "sample": sample}
        except Exception:
            continue
    return result


def build_context_from_structured_sources(user_sources: List[Dict[str, Any]]) -> List[HumanMessage]:
    """
    Build context messages (schema + sample) for structured sources using internal metadata
    and, when available, external DB connections—mirroring logic in source_utils.
    """
    messages: List[HumanMessage] = []
    if not user_sources:
        return messages

    engine = None
    ext_engine = None
    try:
        # Prefer environment variable over config import for DB URI
        db_uri = os.environ.get("DB_URI")
        if not db_uri and DataInterpreterConfig:
            db_uri = getattr(DataInterpreterConfig, "DB_URI", None)
        if create_connection and db_uri:
            engine = create_connection(db_uri)
        for source in user_sources:
            try:
                data_schema = None
                data_description = ""
                sample_data_dict_string = ""

                # Build schema
                if source.get("filetype") == "temp":
                    rows = source.get("temp_rows") or []
                    cols = []
                    if rows and isinstance(rows, list) and isinstance(rows[0], dict):
                        cols = list({k for r in rows for k in r.keys()})
                    data_schema = [{"name": c, "description": ""} for c in cols]
                    data_description = "Temporary table derived from JSON."
                else:
                    if engine is not None:
                        query = None
                        if source.get("filetype") == STRUCTURED:
                            query = f"select column_descriptions from csv_file_manager where id = {source['extid']}"
                        elif source.get("filetype") == EXCEL:
                            query = f"select column_descriptions from excel_file_manager where id = {source['extid']}"
                        elif source.get("filetype") == DB and source.get("extid") is not None:
                            query = f"SELECT column_descriptions FROM db_manager WHERE id = {source['extid']}"
                        if query:
                            result = pd.read_sql(query, con=engine)
                            data_schema = eval(result['column_descriptions'][0]) if not result.empty else None

                    # Description
                    if engine is not None and source.get("filetype") != "temp":
                        qd = None
                        if source.get("filetype") == STRUCTURED:
                            qd = f"select description from csv_file_manager where id = {source['extid']}"
                        elif source.get("filetype") == EXCEL:
                            qd = f"select description from excel_file_manager where id = {source['extid']}"
                        elif source.get("filetype") == DB:
                            qd = f"select description from db_manager where id = {source['extid']}"
                        if qd:
                            result = pd.read_sql(qd, con=engine)
                            data_description = result['description'][0] if not result.empty else ""

                # Sample data
                if source.get("filetype") == "temp":
                    rows = source.get("temp_rows") or []
                    rows = rows[:10]
                    if rows:
                        sample_data_dict_for_json = pd.DataFrame(rows).to_dict(orient='list')
                        sample_data_dict_string = json.dumps(sample_data_dict_for_json, indent=4)
                    else:
                        sample_data_dict_string = "No sample data rows found."
                else:
                    ext_engine = None
                    # Prefer explicit URI
                    if create_connection and source.get("source_db_uri"):
                        ext_engine = create_connection(source.get("source_db_uri"))
                    # Fallback: construct MySQL URI from connection details if provided
                    elif create_connection and source.get("db_connection_details"):
                        try:
                            details = source.get("db_connection_details", {})
                            db_type_val = str(details.get("db_type", "mysql")).lower()
                            if db_type_val == "mysql":
                                user = details.get("user", "")
                                password = details.get("password", "")
                                host = details.get("host", "localhost")
                                port = details.get("port", 3306)
                                database = details.get("database", "")
                                uri = f"mysql://{user}:{password}@{host}:{port}/{database}"
                                ext_engine = create_connection(uri)
                            # For Snowflake, expect a full URI in source['source_db_uri']
                        except Exception:
                            ext_engine = None
                    if ext_engine is not None:
                        qsample = f"select * from `{source['tablename']}` ORDER BY RAND() limit 10"
                        if source.get("db_type") == SNOWFLAKE:
                            qsample = f"select * from {source['tablename']} ORDER BY RANDOM() limit 10"
                        sample_df = pd.read_sql(qsample, con=ext_engine)
                        sample_dict = _df_to_sample_dict(sample_df, limit=10)
                        sample_data_dict_string = json.dumps(sample_dict, indent=4) if sample_dict else "No sample data rows found."
                    else:
                        sample_data_dict_string = "No external DB connection available for sampling."

                schema_text = "\n".join([f"{col['name']} | {col.get('description','')}" for col in (data_schema or [])])
                prompt = f"""
                Here is the description (including schema details) for the structured data source:
                General description:
                ```
                {data_description}
                ```

                Schema details; Read it as - `column_name | column_description`:
                ```
                {schema_text}
                ```

                Sample rows (JSON with orient='list'):
                ```
                {sample_data_dict_string}
                ```
                """
                messages.append(HumanMessage(content=prompt))
            except Exception:
                continue
    finally:
        try:
            if engine is not None:
                engine.dispose()
        except Exception:
            pass
        try:
            if 'ext_engine' in locals() and ext_engine is not None:
                ext_engine.dispose()
        except Exception:
            pass

    return messages


def get_doc_context(filenames: List[str] = None, *, max_samples: int = 25, sample_threshold: int = 30, random_seed: int = 42) -> Dict[str, str]:
    config = DocsAnalyserConfig()
    from concurrent.futures import ThreadPoolExecutor

    def _get_summary(filename: str) -> str:
        return load_summary_file(
            s3_path=f"{config.AWS_CLIENT_ID}/{config.AWS_PROJECT_ID}/summary_files/{filename}/summary.md"
        )

    filenames = filenames or []
    # Randomly sample when too many filenames to avoid context bloat
    selected: List[str] = filenames
    try:
        if len(filenames) > sample_threshold:
            random.seed(random_seed)
            k = min(max_samples, len(filenames))
            selected = random.sample(filenames, k)
    except Exception:
        selected = filenames

    if not selected:
        return {}

    with ThreadPoolExecutor() as executor:
        summaries = list(executor.map(_get_summary, selected))
    return {fname: summary for fname, summary in zip(selected, summaries) if summary}


def build_pre_toolcall_context(
    temp_files: List[str] = None,
    structured_sources: List[Dict[str, Any]] = None,
    doc_summary_s3_paths: List[str] = None,
) -> List[HumanMessage]:
    """
    High-level helper to compose all applicable context messages to be sent to the LLM
    right before requesting the parameters for the next tool call.
    """
    messages: List[HumanMessage] = []
    if temp_files:
        messages.extend(build_context_from_temp_files(temp_files))
    if structured_sources:
        messages.extend(build_context_from_structured_sources(structured_sources))
    if doc_summary_s3_paths:
        print("Building doc summary context for filenames:", doc_summary_s3_paths)
        filename_to_summary = get_doc_context(doc_summary_s3_paths)
        if filename_to_summary:
            blocks: List[str] = [
                "Here are precomputed document summaries to inform tool selection and parameters."
            ]
            for fname, summary in filename_to_summary.items():
                blocks.append(
                    f"Filename: `{fname}`\n```\n{summary}\n```"
                )
            messages.append(HumanMessage(content="\n\n".join(blocks)))
    return messages

if __name__=="__main__":
    print(build_pre_toolcall_context(temp_files=["/home/rwik/code/mcp_server/temp/Alice_Johnson_Varied_Interview_80e450a2-8e1d-11f0-9435-0242ac120004.pdf_flat_5ff9326b.csv"]))