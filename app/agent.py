import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.tools import ToolRegistry


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: str | None = None


@dataclass(frozen=True)
class ModelResponse:
    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()


class AgentModel(Protocol):
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse: ...


@dataclass(frozen=True)
class ToolResult:
    call_id: str | None
    name: str
    result: Any


@dataclass
class AgentState:
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


class Agent:
    def __init__(self, model: AgentModel, tools: ToolRegistry, max_steps: int = 5) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    async def run(self, user_message: str, subject_id: str) -> AgentState:
        state = AgentState(messages=[{"role": "user", "content": user_message}])

        for _ in range(self.max_steps):
            response = await self.model.complete(
                state.messages,
                [{"name": name} for name in self.tools.names()],
            )

            if not response.tool_calls:
                state.messages.append(
                    {"role": "assistant", "content": response.content or ""}
                )
                return state

            state.messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {
                            "name": call.name,
                            "arguments": call.arguments,
                            "call_id": call.call_id,
                        }
                        for call in response.tool_calls
                    ],
                }
            )

            results = await asyncio.gather(
                *(
                    self.tools.execute(
                        call.name,
                        call.arguments,
                        subject_id=subject_id,
                    )
                    for call in response.tool_calls
                )
            )

            for call, result in zip(response.tool_calls, results, strict=True):
                tool_result = ToolResult(call.call_id, call.name, result)
                state.tool_results.append(tool_result)
                state.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.call_id,
                        "tool_name": call.name,
                        "content": result,
                    }
                )

        state.messages.append(
            {"role": "assistant", "content": "Agent stopped after reaching the maximum steps."}
        )
        return state
