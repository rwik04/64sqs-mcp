"""
Data models and type definitions for the agent system.
"""

from typing import TypedDict, List, Optional, Dict, Any, Sequence, Annotated
from enum import Enum
from langchain_core.messages import BaseMessage


class Data_Source_Type(str, Enum):
    TEXT = "UNSTRUCTURED_TEXT"
    TABLE = "STRUCTURED_TABLE"
    TEMP_TABLE = "STRUCTURED_TABLE_TEMPORARY"


class Action_Type(str, Enum):
    QUERY = "query_data"
    ANNOTATE = "annotate_data"
    SUMMARISE = "summarise"
    SUMMARISE_ANSWER = "summarise_answer"
    END = "__end__"


class Action_Details(TypedDict):
    instruction: str
    target_data_sources: List[dict]  # each dict has 'source_name' and 'source_type'
    args: Optional[List[str]]


class Action(TypedDict):
    action_num: int
    action_type: Action_Type
    action_details: List[Action_Details]


class OutputEntry(TypedDict):
    step_no: int
    planned_action: Optional[str]
    executed_action: Optional[str]
    output: Optional[Dict[str, Any]]
    insight: Optional[str]

class DBDetails(TypedDict):
    """Database connection details"""
    db_type: str
    host: str
    port: int
    user: str
    password: str
    database: str
    schema: Optional[str] = None
    warehouse: Optional[str] = None
    role: Optional[str] = None


class FileDetails(TypedDict):
    """File details for each data source"""
    id: int
    extid: int
    filename: str
    displayname: str
    tablename: str
    filetype: str
    db_connection_details: Optional[DBDetails] = None


class AgentState(TypedDict):
    """State of the agent during execution"""
    client: str
    project_id: int
    model_type: str
    api_key: str
    token_tracker: dict
    db_connection_details: dict
    user_query: str
    original_user_sources: List[FileDetails]
    shortlisted_user_sources: List[FileDetails]
    temp_tables: Dict[str, List[Dict[str, Any]]]
    messages: List[BaseMessage]
    plan: List[dict]
    actions: List[Action]
    max_retries: int
    retries_remaining: int
    current_step_reason: str
    remaining_steps: List[dict]
    chart: dict
    tableData: List[dict]
    insight: str
    confidence: str
    output: List[OutputEntry]


class StructuredRecordLimitError(Exception):
    """Custom Exception raised when a structured record is too long (default > 200 rows)"""
    pass


# Constants
# File type categories
UNSTRUCTURED = "unstructured"
STRUCTURED = "structured"
EXCEL = "excel"
URL = "url"
DB = "db"
AUDIO = "audio"
YOUTUBE = "youtube"
GOOGLE_DRIVE = "google-drive"
COPY_PASTE = "copy-paste"

# Allowed file extensions
ALLOWED_EXTENSIONS = set(["txt", "pdf", "doc", "ppt", "docx", "pptx"])
CSV_ALLOWED_EXTENSIONS = set(["csv"])
EXCEL_ALLOWED_EXTENSIONS = set(["xlsx"])
AUDIO_ALLOWED_EXTENSIONS = set(["m4a", "mp3", "wav", "mp4"])

# GPT Model types
GPT_3 = "gpt-3.5-turbo-1106"
GPT_4 = "gpt-4-1106-preview"
GPT_4O = "gpt-4.1-2025-04-14"
GPT_40MINI = "gpt-4.1-mini-2025-04-14"
GPT_EMBEDDING = "text-embedding-ada-002"

# GEMINI Model types
GEMINI_PRO = "gemini-1.5-pro"
GEMINI_FLASH = "gemini-2.0-flash"

# Claude Model types
CLAUDE_SONNET = "claude-3-7-sonnet-20250219"
CLAUDE_HAIKU = "claude-3-5-haiku-20241022"

# Database types
MYSQL = "mysql"
SNOWFLAKE = "snowflake"