from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass(frozen=True, slots=True)
class AgentMessage:
    role: Literal["user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class GenerationResult:
    content: str
    provider: str
    model: str
    usage: dict[str, Any] = field(default_factory=dict)


class ChatProvider(Protocol):
    async def generate(
        self, *, system_prompt: str, messages: list[AgentMessage]
    ) -> GenerationResult: ...


class GenerationProviderError(RuntimeError):
    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(message)

