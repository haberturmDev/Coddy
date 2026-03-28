from abc import ABC, abstractmethod

from domain.models.conversation import Conversation


class SessionStore(ABC):
    """Port: retrieve and persist conversations keyed by session id."""

    @abstractmethod
    def get_or_create(self, session_id: str) -> Conversation:
        """Return the conversation for this session, creating one if missing."""
        ...

    @abstractmethod
    def save(self, session_id: str, conversation: Conversation) -> None:
        """Persist the conversation for this session (no-op for pure in-memory)."""
        ...
