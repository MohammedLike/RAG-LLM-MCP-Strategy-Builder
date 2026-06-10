import json
from langchain_core.messages import BaseMessage, messages_from_dict

class RedisMemory:
    def __init__(self):
        self.memory = {}

    def get_messages(self, session_id: str) -> list[BaseMessage]:
        return self.memory.get(session_id, [])

    def add_messages(self, session_id: str, messages: list[BaseMessage]):
        if session_id not in self.memory:
            self.memory[session_id] = []
        self.memory[session_id].extend(messages)
        # Keep last 20
        self.memory[session_id] = self.memory[session_id][-20:]

memory = RedisMemory()
