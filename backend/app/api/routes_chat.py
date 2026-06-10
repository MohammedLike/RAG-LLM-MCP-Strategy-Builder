from fastapi import APIRouter
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Synchronous chat endpoint
    """
    from ..agent.graph import graph
    from langchain_core.messages import HumanMessage
    
    # Very basic simulation
    return {"response": f"Mock response to: {request.message}"}

@router.websocket("/ws/chat")
async def websocket_chat(websocket):
    """
    WebSocket streaming endpoint
    """
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
