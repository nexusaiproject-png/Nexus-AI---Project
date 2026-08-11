import pytest

from app.ai import AICore, AIMessage, AIRequest, AIResponse
from app.ai.errors import AIConfigurationError, AIProviderError


class FakeProvider:
    name = "fake"

    def __init__(self, response: AIResponse | None = None, error: Exception | None = None):
        self.response = response
        self.error = error

    async def generate(self, request: AIRequest) -> AIResponse:
        if self.error:
            raise self.error
        assert request.model == "test-model"
        return self.response or AIResponse(
            content="hello",
            model=request.model,
            provider=self.name,
        )


def request() -> AIRequest:
    return AIRequest(
        messages=(AIMessage(role="user", content="hello"),),
        model="test-model",
    )


@pytest.mark.asyncio
async def test_ai_core_delegates_to_provider():
    response = await AICore(FakeProvider()).generate(request())
    assert response.content == "hello"
    assert response.provider == "fake"


@pytest.mark.asyncio
async def test_ai_core_wraps_provider_failure():
    with pytest.raises(AIProviderError, match="provider 'fake' failed"):
        await AICore(FakeProvider(error=RuntimeError("boom"))).generate(request())


@pytest.mark.asyncio
async def test_ai_core_rejects_empty_messages():
    invalid = AIRequest(messages=(), model="test-model")
    with pytest.raises(AIConfigurationError, match="At least one AI message"):
        await AICore(FakeProvider()).generate(invalid)


@pytest.mark.asyncio
async def test_ai_core_rejects_invalid_temperature():
    invalid = AIRequest(
        messages=(AIMessage(role="user", content="hello"),),
        model="test-model",
        temperature=3.0,
    )
    with pytest.raises(AIConfigurationError, match="temperature"):
        await AICore(FakeProvider()).generate(invalid)


@pytest.mark.asyncio
async def test_ai_core_rejects_empty_provider_response():
    response = AIResponse(content="   ", model="test-model", provider="fake")
    with pytest.raises(AIProviderError, match="empty response"):
        await AICore(FakeProvider(response=response)).generate(request())
