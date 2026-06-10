from typing import TypedDict, List

class ChatMessage(TypedDict):
    role: str
    content: str
    timestamp: int

class RedisMemory:
    def __init__(self):
        self.memory: dict[str, List[ChatMessage]] = {}

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        return self.memory.get(session_id, [])

    def add_messages(self, session_id: str, messages: List[ChatMessage]):
        if session_id not in self.memory:
            self.memory[session_id] = []
        self.memory[session_id].extend(messages)
        self.memory[session_id] = self.memory[session_id][-20:]

memory = RedisMemory()
