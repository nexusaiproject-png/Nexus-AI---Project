from app.ai.errors import AIConfigurationError
from app.ai.models import AIRequest, AIResponse
from app.ai.provider import AIProvider


class AICore:
    """Provider-neutral orchestration layer for AI requests."""

    def __init__(self, provider: AIProvider) -> None:
        if provider is None:
            raise AIConfigurationError("AI provider is required")
        self.provider = provider

    async def generate(self, request: AIRequest) -> AIResponse:
        self._validate(request)
        try:
            response = await self.provider.generate(request)
        except Exception as exc:
            from app.ai.errors import AIProviderError

            raise AIProviderError(f"AI provider '{self.provider.name}' failed") from exc

        if not response.content.strip():
            raise AIProviderError("AI provider returned an empty response")
        return response

    @staticmethod
    def _validate(request: AIRequest) -> None:
        if not request.model.strip():
            raise AIConfigurationError("AI model is required")
        if not request.messages:
            raise AIConfigurationError("At least one AI message is required")
        if not 0.0 <= request.temperature <= 2.0:
            raise AIConfigurationError("temperature must be between 0 and 2")
        if request.max_tokens is not None and request.max_tokens <= 0:
            raise AIConfigurationError("max_tokens must be positive")
        for message in request.messages:
            if not message.role.strip() or not message.content.strip():
                raise AIConfigurationError("AI messages require non-empty role and content")
