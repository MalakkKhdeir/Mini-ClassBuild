
class GroqClientError(Exception):
    """Base exception for all Groq client errors."""


class MissingAPIKeyError(GroqClientError):
    """Raised when GROQ_API_KEY is missing."""


class AuthenticationError(GroqClientError):
    """Raised when Groq rejects the API key or access."""


class ModelNotFoundError(GroqClientError):
    """Raised when the configured Groq model does not exist."""


class RateLimitError(GroqClientError):
    """Raised when Groq rate limits a request."""


class GroqTimeoutError(GroqClientError):
    """Raised when a Groq request exceeds the configured timeout."""


class GroqConnectionError(GroqClientError):
    """Raised when Groq cannot be reached."""


class GroqServerError(GroqClientError):
    """Raised when Groq's server encounters an error."""


class EmptyResponseError(GroqClientError):
    """Raised when Groq returns no text in its response."""


class InvalidJSONError(GroqClientError):
    """Raised when generated JSON is invalid or fails validation."""

    def __init__(
        self,
        message: str,
        category: str,
        finish_reason: str | None = None,
        failed_generation: str | None = None,
    ):
        self.category = category
        self.finish_reason = finish_reason
        self.failed_generation = failed_generation
        super().__init__(message)


class GroqAPIError(GroqClientError):
    """Raised for other Groq API errors."""

