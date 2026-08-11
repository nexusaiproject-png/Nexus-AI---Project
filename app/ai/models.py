from dataclasses import dataclass, field


@dataclass(frozen=True)
class AIMessage:
    role: str
    content: str


@dataclass(frozen=True)
class AIRequest:
    messages: tuple[AIMessage, ...]
    model: str
    temperature: float = 0.2
    max_tokens: int | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AIResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, str] = field(default_factory=dict)
