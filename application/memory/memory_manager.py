from typing import Optional

import structlog

from application.memory.memory_config import MemoryConfig
from application.memory.summarization_service import SummarizationService
from domain.models.conversation import Conversation, Message, Role

log = structlog.get_logger(__name__)


class MemoryManager:
    """Orchestrates memory strategies and builds the final LLM context.

    This is the central extension point for all memory strategies.
    To add a new strategy (sliding window, sticky facts, branching, etc.),
    add a method here and dispatch it from ``build_context``.

    Returns:
        A tuple of (messages_for_llm, updated_summary_or_none).
        The use case is responsible for persisting the summary back to the
        conversation and session store.
    """

    def __init__(self, summarization_service: SummarizationService) -> None:
        self._summarization_service = summarization_service

    async def build_context(
        self,
        conversation: Conversation,
        current_message: Message,
        config: MemoryConfig,
    ) -> tuple[list[Message], Optional[str]]:
        """Build the message list to send to the LLM.

        Args:
            conversation: Full session history loaded from the store
                          (does NOT yet include *current_message*).
            current_message: The new user message for this turn.
            config: Active memory configuration for this request.

        Returns:
            (llm_messages, new_summary):
                - llm_messages: ordered list ready to pass to LLMClient.generate()
                - new_summary: updated summary text if generated, else None
                  (None means the caller should not overwrite the existing one)
        """
        if config.strategies.summarization:
            return await self._apply_summarization(
                conversation, current_message, config
            )

        # No active strategy — return the full history unchanged.
        return conversation.to_llm_messages() + [current_message], None

    # ------------------------------------------------------------------
    # Private strategy implementations
    # ------------------------------------------------------------------

    async def _apply_summarization(
        self,
        conversation: Conversation,
        current_message: Message,
        config: MemoryConfig,
    ) -> tuple[list[Message], Optional[str]]:
        params = config.params_summarization
        n = params.last_n_messages
        history = conversation.messages

        if len(history) > n:
            old_messages = history[:-n]
            recent_messages = history[-n:]
        else:
            old_messages = []
            recent_messages = history

        new_summary: Optional[str] = None

        if old_messages:
            log.info(
                "memory.summarization.triggered",
                old_message_count=len(old_messages),
                recent_message_count=len(recent_messages),
                model=params.model,
            )
            new_summary = await self._summarization_service.summarize(
                old_messages, model=params.model
            )

        # Use either the freshly generated summary or the one already stored.
        effective_summary = new_summary if new_summary is not None else conversation.summary

        system_msg = Message(role=Role.SYSTEM, content=conversation.system_prompt)
        messages: list[Message] = [system_msg]

        if effective_summary:
            messages.append(
                Message(
                    role=Role.SYSTEM,
                    content=f"Previous conversation summary:\n{effective_summary}",
                )
            )

        messages.extend(recent_messages)
        messages.append(current_message)

        return messages, new_summary
