from abc import ABC, abstractmethod
from domain.models.conversation import Message


class LLMClient(ABC):
    """Port: any LLM provider must implement this interface."""

    @abstractmethod
    async def generate(self, messages: list[Message]) -> str:
        """Send a list of messages and return the assistant's reply."""
        ...
