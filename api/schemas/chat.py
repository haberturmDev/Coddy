from typing import Optional

from pydantic import BaseModel, Field

from application.memory.memory_config import (
    MemoryConfig,
    MemoryStrategies,
    SummarizationParams,
)


class SummarizationParamsSchema(BaseModel):
    last_n_messages: int = Field(
        default=10,
        ge=1,
        description="Number of recent messages to keep verbatim",
    )
    model: str = Field(
        default="llama-3.1-8b-instant",
        description="LLM model to use for summarization",
    )


class MemoryStrategiesSchema(BaseModel):
    summarization: bool = Field(
        default=False,
        description="Enable conversation summarization",
    )


class MemoryParamsSchema(BaseModel):
    summarization: SummarizationParamsSchema = Field(
        default_factory=SummarizationParamsSchema
    )


class MemoryConfigSchema(BaseModel):
    strategies: MemoryStrategiesSchema = Field(
        default_factory=MemoryStrategiesSchema
    )
    params: MemoryParamsSchema = Field(default_factory=MemoryParamsSchema)

    def to_memory_config(self) -> MemoryConfig:
        return MemoryConfig(
            strategies=MemoryStrategies(
                summarization=self.strategies.summarization,
            ),
            params_summarization=SummarizationParams(
                last_n_messages=self.params.summarization.last_n_messages,
                model=self.params.summarization.model,
            ),
        )


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(
        default=None,
        description="Existing chat session id; omit to start a new session",
    )
    memory_config: Optional[MemoryConfigSchema] = Field(
        default=None,
        description="Optional memory strategy configuration",
    )


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    response: str = Field(..., description="Assistant reply")
    session_id: str = Field(..., description="Chat session id for follow-up turns")
    usage: TokenUsage
