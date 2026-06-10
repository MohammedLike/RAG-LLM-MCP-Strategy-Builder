from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
from ..llm import generate_chat_response
from ..agent.memory import memory
from langchain_core.messages import AIMessage, HumanMessage

class ChatRequest(BaseModel):
    message: str
    session_id: str

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    history = memory.get_messages(request.session_id)
    message_history = []
    for msg in history:
        if hasattr(msg, "type") and msg.type == "human":
            message_history.append({"role": "user", "content": msg.content})
        else:
            message_history.append({"role": "assistant", "content": msg.content})

    response_text = generate_chat_response(request.message, message_history)

    memory.add_messages(request.session_id, [HumanMessage(content=request.message)])
    memory.add_messages(request.session_id, [AIMessage(content=response_text)])

    return {"response": response_text}

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        response = generate_chat_response(data, [])
        await websocket.send_text(response)
