from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage
import json

from ..agent.graph import graph
from ..agent.memory import memory

class ChatRequest(BaseModel):
    message: str
    session_id: str

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Synchronous chat endpoint invoking the LangGraph agent.
    Conversation history is stored in Redis (24h TTL, 20 messages).
    """
    history = await memory.get_history(request.session_id)
    messages = []
    for item in reversed(history):
        if item.get("role") == "user":
            messages.append(HumanMessage(content=item.get("content", "")))
        elif item.get("role") == "assistant":
            messages.append(AIMessage(content=item.get("content", "")))
    messages.append(HumanMessage(content=request.message))

    initial_state = {
        "messages": messages,
        "session_id": request.session_id,
        "tool_calls": [],
        "tool_results": [],
        "retrieved_context": []
    }
    
    try:
        await memory.add_message(request.session_id, "user", request.message)
        result = await graph.ainvoke(initial_state)
        final_message = result["messages"][-1]
        await memory.add_message(request.session_id, "assistant", final_message.content)
        return {"response": final_message.content}
    except Exception as e:
        return {"error": str(e)}

@router.delete("/chat/{session_id}")
async def clear_chat_session(session_id: str):
    await memory.clear(session_id)
    return {"cleared": session_id}

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket streaming endpoint for token-by-token or step-by-step updates.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            message = request_data.get("message")
            session_id = request_data.get("session_id", "default")
            
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "session_id": session_id,
                "tool_calls": [],
                "tool_results": [],
                "retrieved_context": []
            }
            
            # Streaming steps from LangGraph
            async for step in graph.astream(initial_state):
                # Send the entire step result or specific tokens
                # For simplicity, we'll send the latest message after each step
                for node_name, output in step.items():
                    if "messages" in output and output["messages"]:
                        last_msg = output["messages"][-1]
                        await websocket.send_json({
                            "node": node_name,
                            "content": last_msg.content,
                            "is_final": node_name == "synthesize"
                        })
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
