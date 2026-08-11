import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.agent_errors import ToolExecutionError
from app.memory import MemoryStore
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
    result: Any = None
    error: ToolExecutionError | None = None

    def as_message(self) -> dict[str, Any]:
        if self.error is not None:
            return self.error.as_message()
        return {
            "role": "tool",
            "tool_call_id": self.call_id,
            "tool_name": self.name,
            "content": self.result,
        }


@dataclass
class AgentState:
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


class Agent:
    def __init__(
        self,
        model: AgentModel,
        tools: ToolRegistry,
        max_steps: int = 5,
        memory: MemoryStore | None = None,
        memory_limit: int = 20,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        if memory_limit < 1:
            raise ValueError("memory_limit must be at least 1")
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.memory = memory
        self.memory_limit = memory_limit

    async def run(self, user_message: str, subject_id: str) -> AgentState:
        state = AgentState()

        if self.memory is not None:
            state.messages.extend(
                {
                    "role": item.role,
                    "content": item.content,
                }
                for item in await self.memory.recent(subject_id, self.memory_limit)
            )

        user = {"role": "user", "content": user_message}
        state.messages.append(user)
        if self.memory is not None:
            await self.memory.add(subject_id, "user", user_message)

        for _ in range(self.max_steps):
            response = await self.model.complete(
                state.messages,
                [{"name": name} for name in self.tools.names()],
            )

            if not response.tool_calls:
                assistant = {"role": "assistant", "content": response.content or ""}
                state.messages.append(assistant)
                if self.memory is not None:
                    await self.memory.add(subject_id, "assistant", assistant["content"])
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
                ),
                return_exceptions=True,
            )

            for call, result in zip(response.tool_calls, results, strict=True):
                if isinstance(result, BaseException):
                    tool_result = ToolResult(
                        call_id=call.call_id,
                        name=call.name,
                        error=ToolExecutionError(
                            call_id=call.call_id or "",
                            name=call.name,
                            error_type=type(result).__name__,
                            message=str(result),
                        ),
                    )
                else:
                    tool_result = ToolResult(call.call_id, call.name, result=result)

                state.tool_results.append(tool_result)
                state.messages.append(tool_result.as_message())

        terminal = {
            "role": "assistant",
            "content": "Agent stopped after reaching the maximum steps.",
        }
        state.messages.append(terminal)
        if self.memory is not None:
            await self.memory.add(subject_id, "assistant", terminal["content"])
        return state
