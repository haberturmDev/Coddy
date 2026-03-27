from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: Role
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {"role": self.role.value, "content": self.content}


@dataclass
class Conversation:
    """Holds the full message history for a session.

    Not yet persisted — ready to be wired to a store later.
    """

    messages: list[Message] = field(default_factory=list)
    system_prompt: str = "You are a helpful assistant."

    def add(self, message: Message) -> None:
        self.messages.append(message)

    def to_llm_messages(self) -> list[Message]:
        system = Message(role=Role.SYSTEM, content=self.system_prompt)
        return [system] + self.messages
