from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FileInfo:
    """Information about a file to be analyzed."""
    filename: str
    displayname: str
    filetype: str
    id: str
    tags_selected: Optional[List[str]] = None


@dataclass
class AnsweringConfig:
    """Configuration for answering queries."""
    client: str
    project_id: str
    filenames: List[FileInfo]
    query: str
    model_type: str
    llm_api_key: str
    emb_api_key: str
    bucket_name: str
    aws_access_key: str
    aws_secret_access_key: str

@dataclass
class Reference:
    """A reference found in a file."""
    reference: str
    confidence: float
    question: Optional[str] = None


@dataclass
class FileResponse:
    """Response generated for a specific file."""
    response: str
    references: List[str]
    pointers: List[str]
    questions: List[str]
    confidence: str
    filedetails: List[Dict[str, str]]


@dataclass
class TagResponse:
    """Response aggregated by tag."""
    response: str
    tag: str
    files_included: List[Dict[str, str]]
    confidence: str


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    # Note: Downstream code constructs plain dict responses. Keep this as dicts to
    # avoid serialization issues when tools return JSON over MCP.
    file_level_responses: List[Dict[str, Any]]
    response_summary: Optional[str] = None
    # tag_level_responses: Dict[str, TagResponse]
    # tag_comparison_summary: str
    token_tracker: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize result to a plain dict for safe JSON transport."""
        return {
            "file_level_responses": self.file_level_responses,
            "response_summary": self.response_summary,
            # "tag_level_responses": {k: asdict(v) for k, v in self.tag_level_responses.items()} if hasattr(self, "tag_level_responses") else {},
            # "tag_comparison_summary": getattr(self, "tag_comparison_summary", ""),
            "token_tracker": self.token_tracker,
        }