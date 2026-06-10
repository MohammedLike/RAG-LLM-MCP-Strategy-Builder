import json
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from .state import AgentState
from ..mcp.server import server

async def reason_node(state: AgentState):
    """
    Decides if tool call needed, selects tool
    """
    # In a full setup, invoke LLM here.
    return {"messages": state["messages"]}

async def tool_call_node(state: AgentState):
    """
    Executes MCP tool call
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_results = []
        messages = []
        for tool_call in last_message.tool_calls:
            result = await server.execute_tool(tool_call["name"], tool_call["args"])
            tool_results.append(result)
            messages.append(ToolMessage(content=json.dumps(result), tool_call_id=tool_call["id"]))
        return {"messages": messages, "tool_results": tool_results}
    return {}

async def rag_retrieve_node(state: AgentState):
    """
    Retrieves relevant strategy context
    """
    return {"retrieved_context": []}

async def synthesize_node(state: AgentState):
    """
    Combines tool results + RAG context + model reasoning
    """
    return {"messages": []}
