from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import reason_node, tool_call_node, rag_retrieve_node, synthesize_node

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool_call"
    return END

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("reason", reason_node)
    workflow.add_node("tool_call", tool_call_node)
    workflow.add_node("synthesize", synthesize_node)
    
    workflow.set_entry_point("reason")
    
    workflow.add_conditional_edges(
        "reason",
        should_continue,
        {
            "tool_call": "tool_call",
            END: END
        }
    )
    workflow.add_edge("tool_call", "synthesize")
    workflow.add_edge("synthesize", END)
    
    return workflow.compile()

graph = create_agent_graph()
