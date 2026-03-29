from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(
        default=None,
        description="Existing chat session id; omit to start a new session",
    )


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant reply")
    session_id: str = Field(..., description="Chat session id for follow-up turns")
    usage: TokenUsage
