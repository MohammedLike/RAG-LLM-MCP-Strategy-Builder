from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
import time
from ..llm import generate_chat_response
from ..agent.memory import memory

class ChatRequest(BaseModel):
    message: str
    session_id: str

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    history = memory.get_messages(request.session_id)
    response_text = await generate_chat_response(request.message, history)

    timestamp = int(time.time() * 1000)
    memory.add_messages(request.session_id, [
        {"role": "user", "content": request.message, "timestamp": timestamp},
        {"role": "assistant", "content": response_text, "timestamp": timestamp + 1}
    ])

    return {"response": response_text}

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        response = await generate_chat_response(data, [])
        await websocket.send_text(response)
