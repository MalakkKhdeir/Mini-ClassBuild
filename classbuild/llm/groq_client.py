
import json

from groq import (
    Groq,
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
)

from classbuild.config import get_settings

from classbuild.llm.exceptions import (
    AuthenticationError,
    EmptyResponseError,
    GroqAPIError,
    GroqConnectionError,
    GroqServerError,
    GroqTimeoutError,
    InvalidJSONError,
    MissingAPIKeyError,
    ModelNotFoundError,
    RateLimitError,
)


STRICT_SCHEMA_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
}

REASONING_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
}


class GroqClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ):
        settings = get_settings()

        api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.request_timeout_seconds
        )

        if not api_key:
            raise MissingAPIKeyError(
                "GROQ_API_KEY is missing. Add it to your .env file."
            )

        self.client = Groq(
            api_key=api_key,
            timeout=timeout,
        )

    def supports_strict_schema(self) -> bool:
        return self.model in STRICT_SCHEMA_MODELS

    def generate(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        response = self._chat(
            messages=[
                {"role": "user", "content": prompt.strip()},
            ],
        )

        return self._extract_text(response)

    def generate_json(
        self,
        prompt: str,
        schema: dict,
        schema_name: str,
        system_prompt: str | None = None,
        max_completion_tokens: int | None = None,
        reasoning_effort: str | None = None,
    ) -> dict:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        if not isinstance(schema, dict):
            raise TypeError("Schema must be a dictionary.")

        if not isinstance(schema_name, str) or not schema_name.strip():
            raise ValueError("Schema name cannot be empty.")

        if self.supports_strict_schema():
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            }
        else:
            response_format = {"type": "json_object"}
            prompt = (
                "Return JSON matching this schema:\n"
                f"{json.dumps(schema)}\n\n"
                f"{prompt.strip()}"
            )

        messages = []

        if system_prompt and system_prompt.strip():
            messages.append(
                {
                    "role": "system",
                    "content": system_prompt.strip(),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt.strip(),
            }
        )

        extra = {}

        if max_completion_tokens is not None:
            extra["max_completion_tokens"] = max_completion_tokens

        if (
            reasoning_effort is not None
            and self.model in REASONING_MODELS
        ):
            extra["reasoning_effort"] = reasoning_effort

        response = self._chat(
            messages,
            response_format=response_format,
            **extra,
        )

        text = self._extract_text(response)
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "length":
            raise InvalidJSONError(
                "Groq response was truncated by the token limit.",
                category="truncated",
                finish_reason=finish_reason,
                failed_generation=text,
            )

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidJSONError(
                f"Groq returned invalid JSON: {exc}",
                category="invalid_json",
                finish_reason=finish_reason,
                failed_generation=text,
            ) from exc

        if not isinstance(data, dict):
            raise InvalidJSONError(
                "Groq returned JSON, but the result was not an object.",
                category="invalid_json",
                finish_reason=finish_reason,
                failed_generation=text,
            )

        return data

    def _extract_text(self, response) -> str:
        if not response.choices:
            raise EmptyResponseError(
                "Groq returned no response choices."
            )

        text = response.choices[0].message.content

        if not text or not text.strip():
            raise EmptyResponseError(
                "Groq returned an empty response."
            )

        return text.strip()

    def _chat(
        self,
        messages: list[dict],
        response_format: dict | None = None,
        **extra,
    ):
        request = {
            "model": self.model,
            "messages": messages,
            **extra,
        }

        if response_format is not None:
            request["response_format"] = response_format

        try:
            return self.client.chat.completions.create(**request)

        except APITimeoutError as exc:
            raise GroqTimeoutError(
                "Groq request timed out."
            ) from exc

        except APIConnectionError as exc:
            raise GroqConnectionError(
                "Could not connect to Groq."
            ) from exc

        except APIStatusError as exc:
            raise self._translate_status_error(exc) from exc

        except APIError as exc:
            raise GroqAPIError(
                f"Groq API error: {exc}"
            ) from exc

    def _translate_status_error(
        self,
        exc: APIStatusError,
    ) -> Exception:
        status_code = exc.status_code

        if status_code in (401, 403):
            return AuthenticationError(
                "Groq rejected the API key or access."
            )

        if status_code == 404:
            return ModelNotFoundError(
                "The configured Groq model was not found."
            )

        if status_code == 429:
            return RateLimitError(
                "Groq rate limit exceeded."
            )

        if 500 <= status_code <= 504:
            return GroqServerError(
                "Groq server encountered an error."
            )

        error_code = self._error_code(exc)

        if (
            status_code == 400
            and error_code == "json_validate_failed"
        ):
            return InvalidJSONError(
                self._error_detail(exc),
                category="schema_validation",
            )

        return GroqAPIError(
            self._error_detail(exc)
        )

    def _error_code(self, exc: APIStatusError) -> str | None:
        body = getattr(exc, "body", None)

        if isinstance(body, dict):
            error = body.get("error", {})

            if isinstance(error, dict):
                code = error.get("code")

                if isinstance(code, str):
                    return code

        return None

    def _error_detail(self, exc: APIStatusError) -> str:
        body = getattr(exc, "body", None)

        if isinstance(body, dict):
            error = body.get("error", {})

            if isinstance(error, dict):
                message = error.get("message")

                if isinstance(message, str) and message.strip():
                    return message

        return str(exc)
