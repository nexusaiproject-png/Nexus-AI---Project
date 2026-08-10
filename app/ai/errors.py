class AIError(Exception):
    """Base exception for AI core failures."""


class AIConfigurationError(AIError):
    """Raised when the AI core or provider is misconfigured."""


class AIProviderError(AIError):
    """Raised when an AI provider fails to fulfill a request."""
