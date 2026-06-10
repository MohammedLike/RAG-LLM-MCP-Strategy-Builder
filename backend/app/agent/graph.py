from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import reason_node, tool_call_node, rag_retrieve_node, synthesize_node

def should_continue(state: AgentState):
    """
    Determines the next step after reasoning.
    """
    last_message = state["messages"][-1]
    # If the LLM produced tool calls, go to tool execution
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_call"
    # Otherwise, go to RAG retrieval before synthesizing the final answer
    return "rag_retrieve"

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("reason", reason_node)
    workflow.add_node("tool_call", tool_call_node)
    workflow.add_node("rag_retrieve", rag_retrieve_node)
    workflow.add_node("synthesize", synthesize_node)
    
    workflow.set_entry_point("reason")
    
    workflow.add_conditional_edges(
        "reason",
        should_continue,
        {
            "tool_call": "tool_call",
            "rag_retrieve": "rag_retrieve"
        }
    )
    
    # After tool execution, always get RAG context for the final synthesis
    workflow.add_edge("tool_call", "rag_retrieve")
    workflow.add_edge("rag_retrieve", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()

graph = create_agent_graph()
