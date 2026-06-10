import json
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from .state import AgentState
from ..mcp.server import server

def reason_node(state: AgentState):
    """
    Decides if tool call needed, selects tool
    """
    # For now, it's a simple mock that returns the messages.
    # In a full LangGraph setup, we'd invoke the LLM with tools bound.
    return {"messages": state["messages"]}

def tool_call_node(state: AgentState):
    """
    Executes MCP tool call
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_results = []
        messages = []
        for tool_call in last_message.tool_calls:
            result = server.execute_tool(tool_call["name"], tool_call["args"])
            tool_results.append(result)
            messages.append(ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"]))
        return {"messages": messages, "tool_results": tool_results}
    return {}

def rag_retrieve_node(state: AgentState):
    """
    Retrieves relevant strategy context
    """
    return {"retrieved_context": []}

def synthesize_node(state: AgentState):
    """
    Combines tool results + RAG context + model reasoning
    """
    return {"messages": []}
