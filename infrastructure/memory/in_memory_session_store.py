from domain.models.conversation import Conversation
from domain.ports.session_store import SessionStore


class InMemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self._sessions: dict[str, Conversation] = {}

    def get_or_create(self, session_id: str) -> Conversation:
        if session_id not in self._sessions:
            self._sessions[session_id] = Conversation()
        return self._sessions[session_id]

    def save(self, session_id: str, conversation: Conversation) -> None:
        self._sessions[session_id] = conversation
