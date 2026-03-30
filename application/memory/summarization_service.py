import structlog

from domain.models.conversation import Message, Role
from domain.ports.llm_client import LLMClient

log = structlog.get_logger(__name__)

_SUMMARIZATION_SYSTEM_PROMPT = """\
You are a conversation summarizer. Your job is to compress the provided \
conversation history into a concise, information-dense summary.

Preserve:
- User intent and goals
- Key decisions and conclusions
- Constraints and requirements mentioned
- Technical context (languages, frameworks, data structures, APIs, etc.)

Remove:
- Repetition and restated information
- Small talk and pleasantries
- Clarification back-and-forth that was already resolved
- Irrelevant tangents

Output a structured, factual summary. Use bullet points or short paragraphs. \
Be as concise as possible while losing no meaningful context."""

_SUMMARIZATION_USER_TEMPLATE = """\
Summarize the following conversation history:

{conversation}"""


class SummarizationService:
    """Application service that produces a text summary of a message list.

    Uses the LLMClient port so the underlying provider remains swappable.
    """

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def summarize(self, messages: list[Message], model: str) -> str:
        """Return a condensed summary of *messages* using *model*.

        The call uses a dedicated summarization prompt so the LLM focuses
        only on compression rather than continuing the conversation.
        """
        conversation_text = "\n".join(
            f"{msg.role.value.upper()}: {msg.content}" for msg in messages
        )

        summarization_messages = [
            Message(role=Role.SYSTEM, content=_SUMMARIZATION_SYSTEM_PROMPT),
            Message(
                role=Role.USER,
                content=_SUMMARIZATION_USER_TEMPLATE.format(
                    conversation=conversation_text
                ),
            ),
        ]

        log.info(
            "summarization.start",
            model=model,
            message_count=len(messages),
        )

        response = await self._llm.generate(summarization_messages, model=model)

        log.info(
            "summarization.complete",
            model=model,
            summary_length=len(response.content),
            tokens_used=response.total_tokens,
        )

        return response.content
