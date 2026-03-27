import os
import httpx
from typing import Optional
from domain.models.conversation import Message
from domain.ports.llm_client import LLMClient

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Adjust to any available Groq model; see https://console.groq.com/docs/models
DEFAULT_MODEL = "llama-3.1-8b-instant"


class GroqClient(LLMClient):
    """Adapter: calls the Groq Chat Completions API."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> None:
        self._api_key = api_key or os.environ["GROQ_API_KEY"]
        self._model = model

    async def generate(self, messages: list[Message]) -> str:
        payload = {
            "model": self._model,
            "messages": [m.to_dict() for m in messages],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]
