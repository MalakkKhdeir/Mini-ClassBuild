import httpx
import pytest

from groq import Groq

from classbuild.llm.groq_client import GroqClient
from classbuild.llm.exceptions import (
    GroqConnectionError,
    GroqTimeoutError,
    AuthenticationError,
    GroqServerError,
    RateLimitError,
)

from classbuild.llm.exceptions import (
    GroqAPIError,
    AuthenticationError,
    ModelNotFoundError,

)
from classbuild.services.structured_output import (
    request_structured_json,
    StructuredGenerationError,
)
from classbuild.llm.exceptions import InvalidJSONError

from classbuild.llm.exceptions import GroqTimeoutError

from classbuild.config import get_settings

from unittest.mock import patch

def make_groq_client(transport, max_retries=1):
    http_client = httpx.Client(transport=transport)

    def create_client(**kwargs):
        return Groq(
            **kwargs,
            http_client=http_client,
        )

    with patch(
        "classbuild.llm.groq_client.Groq",
        side_effect=create_client,
    ):
        client = GroqClient(
            api_key="test-api-key",
            max_retries=max_retries,
        )

    return client, http_client

def test_retries_temporary_server_error():
    attempts = []

    def handler(request):
        attempts.append(request)

        if len(attempts) == 1:
            return httpx.Response(
                503,
                json={"error": {"message": "Temporary error"}},
            )

        return httpx.Response(
            200,
            json={
                "id": "test-id",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "openai/gpt-oss-20b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Hello!",
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    client, http_client = make_groq_client(
        transport,
        max_retries=1,
    )

    try:
        result = client.chat([
            {"role": "user", "content": "Hello"}
        ])

        assert result == "Hello!"
        assert len(attempts) == 2
    finally:
        http_client.close()

@pytest.mark.parametrize(
    "status_code, expected_error",
    [
        (400, GroqAPIError),
        (401, AuthenticationError),
        (403, AuthenticationError),
        (404, ModelNotFoundError),
    ],
)
def test_client_errors_are_not_retried(
    status_code,
    expected_error,
):
    attempts = []

    def handler(request):
        attempts.append(request)

        return httpx.Response(
            status_code,
            json={
                "error": {
                    "message": "Request failed",
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client, http_client = make_groq_client(
        transport,
        max_retries=3,
    )

    try:
        with pytest.raises(expected_error):
            client.chat([
                {"role": "user", "content": "Hello"}
            ])

        assert len(attempts) == 1
    finally:
        http_client.close()

               
@pytest.mark.parametrize(
    "value, expected",
    [
        (None, 1),
        ("0", 0),
        ("2", 2),
        ("5", 3),
        ("-1", 0),
        ("abc", 1),
    ],
)
def test_groq_max_retries_configuration(
    monkeypatch,
    value,
    expected,
):
    monkeypatch.delenv("GROQ_MAX_RETRIES", raising=False)

    if value is not None:
        monkeypatch.setenv("GROQ_MAX_RETRIES", value)

    settings = get_settings()

    assert settings.max_retries == expected               

def test_json_retry_budget_is_bounded():
    attempts = []

    def handler(request):
        attempts.append(request)

        return httpx.Response(
            200,
            json={
                "id": "test-id",
                "object": "chat.completion",
                "created": 1234567890,
                "model": "openai/gpt-oss-20b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "not valid json",
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    transport = httpx.MockTransport(handler)
    client, http_client = make_groq_client(
        transport,
        max_retries=1,
    )

    try:
        with pytest.raises(StructuredGenerationError):
            request_structured_json(
                client,
                prompt="Create a course",
                schema={"type": "object"},
                schema_name="test_schema",
                system_prompts=[
                    "First attempt",
                    "Retry attempt",
                ],
            )

        assert len(attempts) == 2
    finally:
        http_client.close()

def test_api_error_redacts_groq_key():
    secret = "gsk_testsecret123456789"

    def handler(request):
        return httpx.Response(
            400,
            json={
                "error": {
                    "message": f"Invalid API key: {secret}"
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client, http_client = make_groq_client(
        transport,
        max_retries=1,
    )

    try:
        with pytest.raises(GroqAPIError) as exc:
            client.chat([
                {"role": "user", "content": "Hello"}
            ])

        assert secret not in str(exc.value)
        assert "[REDACTED]" in str(exc.value)

    finally:
        http_client.close()            

def test_timeout_error_is_understandable():
    def handler(request):
        raise httpx.ReadTimeout(
            "simulated timeout",
            request=request,
        )

    transport = httpx.MockTransport(handler)
    client, http_client = make_groq_client(
        transport,
        max_retries=0,
    )

    try:
        with pytest.raises(
            GroqTimeoutError,
            match="timed out",
        ):
            client.chat([
                {"role": "user", "content": "Hello"}
            ])

    finally:
        http_client.close()        