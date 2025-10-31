import json
from typing import Optional, Dict, Any, List

from fastmcp import Client
from langchain_core.messages import AIMessage


class ToolManager:
    def __init__(self, mcp_url: str = "http://localhost:8000/mcp"):
        self.client = Client(mcp_url)
        # Canonical mappings from fully-qualified MCP tool names to server-exposed names
        self.tool_name_mapping: Dict[str, str] = {
            "mcp_docqna.docs_analysis": "docs_analysis",
            "mcp_docqna.data_interpreter": "data_interpreter",
            "mcp_docqna.content_writer": "content_writer",
            # Additional aliases for robustness (case/format variants)
            "docs_analysis": "docs_analysis",
            "docs-analysis": "docs_analysis",
            "data_interpreter": "data_interpreter",
            "data-interpreter": "data_interpreter",
            # Content writer aliases
            "content_writer": "content_writer",
            "content-writer": "content_writer",
            "contentwriter": "content_writer",
            "writer": "content_writer",
            "mcp_docqna.contentwriter": "content_writer",
            "mcp_docqna.content-writer": "content_writer",
        }

    def _normalize_tool_name(self, raw_tool_name: Optional[str]) -> Optional[str]:
        if raw_tool_name is None:
            return None
        try:
            candidate = str(raw_tool_name).strip()
        except Exception:
            candidate = str(raw_tool_name)

        # Lower-case and harmonize separators for matching
        candidate_lower = candidate.lower().replace("-", "_")

        # Direct map hit
        if candidate_lower in self.tool_name_mapping:
            return self.tool_name_mapping[candidate_lower]

        # Namespaced form like "namespace.tool" → try full, then tail
        if "." in candidate_lower:
            if candidate_lower in self.tool_name_mapping:
                return self.tool_name_mapping[candidate_lower]
            tail = candidate_lower.split(".")[-1]
            if tail in self.tool_name_mapping:
                return self.tool_name_mapping[tail]
            return tail

        return candidate_lower

    def _derive_from_action_plan(self, action_plan: Optional[dict]) -> Dict[str, Any]:
        if not isinstance(action_plan, dict):
            return {"tool": None, "parameters": {}}
        steps = action_plan.get("action_plan") or action_plan.get("steps") or []
        if not isinstance(steps, list) or len(steps) == 0:
            return {"tool": None, "parameters": {}}
        first = steps[0]
        if not isinstance(first, dict):
            return {"tool": None, "parameters": {}}
        raw_tool = first.get("tool") or first.get("target_entity") or first.get("name")
        params = first.get("parameters") or first.get("args") or {}
        return {"tool": raw_tool, "parameters": params}

    def _unwrap_call_result(self, result: Any) -> str:
        # Prefer structured/data payloads, then text content, then str fallback
        try:
            if hasattr(result, "structured_content") and result.structured_content:
                return json.dumps(result.structured_content)
            if hasattr(result, "data") and result.data:
                return json.dumps(result.data)
            if hasattr(result, "content") and result.content is not None:
                rc = result.content
                if isinstance(rc, list):
                    texts: List[str] = []
                    for item in rc:
                        text_val = getattr(item, "text", None)
                        if text_val is None and isinstance(item, dict):
                            text_val = item.get("text")
                        if text_val is not None:
                            texts.append(text_val)
                    if texts:
                        return "\n".join(texts)
                elif isinstance(rc, str):
                    return rc
            if isinstance(result, dict):
                return json.dumps(result)
            if isinstance(result, str):
                return result
            return str(result)
        except Exception:
            return str(result)

    async def call_tool(self, raw_tool_name: Optional[str], params: Dict[str, Any], action_plan: Optional[dict] = None) -> AIMessage:
        # Derive tool name and params when missing
        if raw_tool_name is None:
            derived = self._derive_from_action_plan(action_plan)
            raw_tool_name = derived.get("tool")
            if not params:
                params = derived.get("parameters") or {}

        tool_name = self._normalize_tool_name(raw_tool_name)
        if tool_name is None:
            # Return an empty AIMessage to avoid crashes
            return AIMessage(name="unknown_tool", content="{}")

        try:
            async with self.client:
                result = await self.client.call_tool(tool_name, params)
        except Exception as e:
            error_payload = {"error": str(e), "tool": tool_name, "params": params}
            return AIMessage(name=tool_name, content=json.dumps(error_payload))

        content_text = self._unwrap_call_result(result)
        return AIMessage(name=tool_name, content=content_text)


