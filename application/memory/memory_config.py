import json
from dataclasses import dataclass, field


DEFAULT_SUMMARIZATION_MODEL = "llama-3.1-8b-instant"
DEFAULT_LAST_N_MESSAGES = 10


@dataclass
class SummarizationParams:
    last_n_messages: int = DEFAULT_LAST_N_MESSAGES
    model: str = DEFAULT_SUMMARIZATION_MODEL


@dataclass
class MemoryStrategies:
    summarization: bool = False


@dataclass
class MemoryConfig:
    """Controls which memory strategies are active and their parameters."""

    strategies: MemoryStrategies = field(default_factory=MemoryStrategies)
    params_summarization: SummarizationParams = field(
        default_factory=SummarizationParams
    )

    def to_json(self) -> str:
        return json.dumps({
            "strategies": {"summarization": self.strategies.summarization},
            "params_summarization": {
                "last_n_messages": self.params_summarization.last_n_messages,
                "model": self.params_summarization.model,
            },
        })

    @classmethod
    def from_json(cls, raw: str) -> "MemoryConfig":
        data = json.loads(raw)
        return cls(
            strategies=MemoryStrategies(
                **data.get("strategies", {})
            ),
            params_summarization=SummarizationParams(
                **data.get("params_summarization", {})
            ),
        )
