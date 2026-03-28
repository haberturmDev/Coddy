import uuid
from typing import Optional, Tuple

from domain.models.conversation import Message, Role
from domain.ports.llm_client import LLMClient
from domain.ports.session_store import SessionStore


class ChatUseCase:
    """Orchestrates chat turns with optional session-scoped history."""

    def __init__(self, llm: LLMClient, session_store: SessionStore) -> None:
        self._llm = llm
        self._session_store = session_store

    async def execute(
        self, user_message: str, session_id: Optional[str] = None
    ) -> Tuple[str, str]:
        if session_id is None:
            session_id = str(uuid.uuid4())

        conversation = self._session_store.get_or_create(session_id)
        conversation.add(Message(role=Role.USER, content=user_message))

        reply = await self._llm.generate(conversation.to_llm_messages())

        conversation.add(Message(role=Role.ASSISTANT, content=reply))
        self._session_store.save(session_id, conversation)

        return reply, session_id
