import os
from typing import Optional


import httpx
import structlog
from domain.models.conversation import Message
from domain.ports.llm_client import LLMClient, LLMResponse

log = structlog.get_logger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Adjust to any available Groq model; see https://console.groq.com/docs/models
DEFAULT_MODEL = "llama-3.1-8b-instant"


class GroqClient(LLMClient):
    """Adapter: calls the Groq Chat Completions API."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> None:
        self._api_key = api_key or os.environ["GROQ_API_KEY"]
        self._model = model

    async def generate(
        self, messages: list[Message], model: Optional[str] = None
    ) -> LLMResponse:
        resolved_model = model or self._model
        payload = {
            "model": resolved_model,
            "messages": [m.to_dict() for m in messages],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        headers_for_log = {
            "Authorization": "Bearer [REDACTED]",
            "Content-Type": "application/json",
        }

        log.info(
            "http.outbound.request",
            method="POST",
            url=GROQ_API_URL,
            model=resolved_model,
            message_count=len(messages),
            headers=headers_for_log,
            body=payload,
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            status = response.status_code
            log.info(
                "http.outbound.response",
                method="POST",
                url=str(response.request.url),
                status_code=status,
                body=response.text or "",
            )
            response.raise_for_status()

        data = response.json()
        usage = data.get("usage") or {}
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            completion_tokens=int(usage.get("completion_tokens") or 0),
            total_tokens=int(usage.get("total_tokens") or 0),
        )
