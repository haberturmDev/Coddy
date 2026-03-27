from domain.models.conversation import Conversation, Message, Role
from domain.ports.llm_client import LLMClient


class ChatUseCase:
    """Orchestrates a single chat turn.

    Designed to later accept a Conversation object (for history/sessions)
    instead of a plain string, and to support tool calling or RAG hooks.
    """

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def execute(self, user_message: str) -> str:
        # Single-turn for now; swap in a persisted Conversation for sessions.
        conversation = Conversation()
        conversation.add(Message(role=Role.USER, content=user_message))

        reply = await self._llm.generate(conversation.to_llm_messages())

        # Hook point: persist assistant reply, run tools, summarize, etc.
        conversation.add(Message(role=Role.ASSISTANT, content=reply))

        return reply
