import uuid
from dataclasses import dataclass
from typing import Optional

from application.memory.memory_config import MemoryConfig
from application.memory.memory_manager import MemoryManager
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

    def __init__(
        self,
        llm: LLMClient,
        session_store: SessionStore,
        memory_manager: Optional[MemoryManager] = None,
    ) -> None:
        self._llm = llm
        self._session_store = session_store
        self._memory_manager = memory_manager

    async def execute(
        self,
        user_message: str,
        session_id: Optional[str] = None,
        memory_config: Optional[MemoryConfig] = None,
    ) -> ChatResult:
        if session_id is None:
            session_id = str(uuid.uuid4())

        conversation = self._session_store.get_or_create(session_id)
        current_message = Message(role=Role.USER, content=user_message)

        # Resolve effective memory config:
        #   1. Request-provided config takes priority and is persisted for the session.
        #   2. Fall back to the config stored from a previous request in this session.
        #   3. If neither exists, no memory strategy is applied.
        effective_config: Optional[MemoryConfig] = None
        if memory_config is not None:
            effective_config = memory_config
            conversation.memory_config_json = memory_config.to_json()
        elif conversation.memory_config_json:
            effective_config = MemoryConfig.from_json(conversation.memory_config_json)

        if self._memory_manager is not None and effective_config is not None:
            llm_messages, new_summary = await self._memory_manager.build_context(
                conversation, current_message, effective_config
            )
            if new_summary is not None:
                conversation.summary = new_summary
        else:
            llm_messages = conversation.to_llm_messages() + [current_message]

        llm_response = await self._llm.generate(llm_messages)

        conversation.add(current_message)
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
