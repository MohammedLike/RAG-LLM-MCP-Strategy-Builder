from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import operator

def add_messages(left: list, right: list):
    return left + right

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    tool_calls: list[Dict[str, Any]]
    tool_results: list[Dict[str, Any]]
    retrieved_context: list[str]
    current_market_data: Optional[Dict[str, Any]]
    session_id: str
