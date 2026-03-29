import uuid
from dataclasses import dataclass
from typing import Optional

from domain.models.conversation import Message, Role
from domain.ports.llm_client import LLMClient
from domain.ports.session_store import SessionStore


@dataclass(frozen=True)
class ChatUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class ChatResult:
    reply: str
    session_id: str
    usage: ChatUsage


class ChatUseCase:
    """Orchestrates chat turns with optional session-scoped history."""

    def __init__(self, llm: LLMClient, session_store: SessionStore) -> None:
        self._llm = llm
        self._session_store = session_store

    async def execute(
        self, user_message: str, session_id: Optional[str] = None
    ) -> ChatResult:
        if session_id is None:
            session_id = str(uuid.uuid4())

        conversation = self._session_store.get_or_create(session_id)
        conversation.add(Message(role=Role.USER, content=user_message))

        llm_response = await self._llm.generate(conversation.to_llm_messages())

        conversation.add(Message(role=Role.ASSISTANT, content=llm_response.content))
        self._session_store.save(session_id, conversation)

        usage = ChatUsage(
            prompt_tokens=llm_response.prompt_tokens,
            completion_tokens=llm_response.completion_tokens,
            total_tokens=llm_response.total_tokens,
        )
        return ChatResult(
            reply=llm_response.content,
            session_id=session_id,
            usage=usage,
        )
