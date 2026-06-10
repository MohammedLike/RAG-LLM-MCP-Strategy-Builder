import requests
from .config import settings
from .agent.prompts import SYSTEM_PROMPT


class OllamaClient:
    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.session = requests.Session()

    def chat(self, messages: list[dict], temperature: float = 0.2, max_tokens: int = 1024) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = self.session.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("choices"):
            choice = data["choices"][0]
            message = choice.get("message", {})
            return message.get("content", "").strip()

        return str(data)


ollama_client = OllamaClient(settings.OLLAMA_BASE_URL, settings.LLM_MODEL_NAME)


def build_messages(user_message: str, history: list[dict]) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    return messages


def generate_chat_response(user_message: str, history: list[dict]) -> str:
    messages = build_messages(user_message, history)
    try:
        return ollama_client.chat(messages)
    except Exception as exc:
        return f"ERROR: failed to get model response: {exc}"
