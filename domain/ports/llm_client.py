from abc import ABC, abstractmethod
from dataclasses import dataclass

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
    async def generate(self, messages: list[Message]) -> LLMResponse:
        """Send a list of messages and return the assistant's reply and usage."""
        ...
