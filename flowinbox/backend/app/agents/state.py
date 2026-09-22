from typing import TypedDict, List, Dict, Any, Optional


class FlowInboxState(TypedDict):
    user_id: str
    request: str
    intent: Optional[str]
    plan: Optional[List[str]]
    messages: List[Dict[str, str]]
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    retrieved_context: List[Dict[str, Any]]
    relevant_threads: List[Dict[str, Any]]
    pending_actions: List[Dict[str, Any]]
    approval_status: str  # "none" | "pending" | "approved" | "rejected"
    final_response: Optional[str]
    errors: List[str]
    task_status: str  # "running" | "waiting_approval" | "completed" | "failed"
