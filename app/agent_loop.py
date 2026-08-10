from dataclasses import dataclass
from typing import Any, Protocol

from app.tools import ToolRegistry


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class AgentStepResult:
    call_id: str
    name: str
    result: Any


class ModelAdapter(Protocol):
    async def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any: ...


class AgentLoop:
    def __init__(self, model: ModelAdapter, tools: ToolRegistry, max_steps: int = 5) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    async def run(self, messages: list[dict[str, Any]], subject_id: str) -> Any:
        history = list(messages)
        for _ in range(self.max_steps):
            response = await self.model.complete(history, self._tool_schemas())
            calls = list(getattr(response, "tool_calls", []) or [])
            if not calls:
                content = getattr(response, "content", None) or ""
                return content, history + [{"role": "assistant", "content": content}]

            history.append({
                "role": "assistant",
                "content": getattr(response, "content", None),
                "tool_calls": [
                    {"id": call.call_id, "name": call.name, "arguments": call.arguments}
                    for call in calls
                ],
            })
            results = await self._execute_calls(calls, subject_id)
            history.extend(
                {
                    "role": "tool",
                    "tool_call_id": result.call_id,
                    "name": result.name,
                    "content": result.result,
                }
                for result in results
            )
        return "Agent stopped after reaching the maximum tool steps.", history

    def _tool_schemas(self) -> list[dict[str, Any]]:
        return [{"name": name} for name in self.tools.names()]

    async def _execute_calls(self, calls: list[ToolCall], subject_id: str) -> list[AgentStepResult]:
        import asyncio

        results = await asyncio.gather(
            *(self.tools.execute(call.name, call.arguments, subject_id=subject_id) for call in calls)
        )
        return [
            AgentStepResult(call_id=call.call_id, name=call.name, result=result)
            for call, result in zip(calls, results, strict=True)
        ]
