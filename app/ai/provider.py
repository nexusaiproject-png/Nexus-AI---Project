from typing import Protocol

from app.ai.models import AIRequest, AIResponse


class AIProvider(Protocol):
    name: str

    async def generate(self, request: AIRequest) -> AIResponse:
        """Generate a response for an AI request."""
        ...
