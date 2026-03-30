from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from domain.models.conversation import Message


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMClient(ABC):
    """Port: any LLM provider must implement this interface."""

    @abstractmethod
    async def generate(
        self, messages: list[Message], model: Optional[str] = None
    ) -> LLMResponse:
        """Send a list of messages and return the assistant's reply and usage.

        Args:
            messages: Conversation messages to send.
            model: Optional model override; uses the client's default when None.
        """
        ...
