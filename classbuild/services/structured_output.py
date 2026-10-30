
import logging
from copy import deepcopy

from pydantic import ValidationError

from classbuild.llm.exceptions import InvalidJSONError


MAX_ATTEMPTS = 2
LOG_PREVIEW_CHARS = 200

_UNSENT_KEYWORDS = {
    "minItems",
    "maxItems",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
}


class StructuredGenerationError(Exception):
    """Raised when structured JSON generation fails after retries."""


def _clean_schema(node):
    """Remove schema keywords that should be enforced by Pydantic."""

    if isinstance(node, dict):
        cleaned = {}

        for key, value in node.items():
            if key in _UNSENT_KEYWORDS:
                continue

            cleaned[key] = _clean_schema(value)

        return cleaned

    if isinstance(node, list):
        return [_clean_schema(item) for item in node]

    return node


def strict_schema(schema: dict) -> dict:
    """Return a cleaned copy of a Pydantic JSON schema."""

    return _clean_schema(deepcopy(schema))


def describe_validation_error(exc: ValidationError) -> list[str]:
    """Convert Pydantic errors into readable messages."""

    problems = []

    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"])
        message = error["msg"]

        problems.append(f"{location}: {message}")

    return problems


def _log_structured_failure(
    logger,
    model: str,
    attempt: int,
    exc: Exception,
):
    """Log a safe preview of a structured generation failure."""

    preview = str(
        getattr(exc, "failed_generation", "")
    )[:LOG_PREVIEW_CHARS]

    category = getattr(exc, "category", "unknown")

    logger.warning(
        "Structured generation failed | model=%s | "
        "attempt=%s/%s | category=%s | preview=%r",
        model,
        attempt,
        MAX_ATTEMPTS,
        category,
        preview,
    )


def request_structured_json(
    client,
    *,
    prompt: str,
    schema: dict,
    schema_name: str,
    system_prompts: list[str],
    max_completion_tokens: int | None = None,
    reasoning_effort: str | None = None,
    logger=None,
    what: str = "structured content",
    advice: str = "Please try again.",
) -> dict:
    """Request structured JSON, retrying once if the JSON is invalid."""

    logger = logger or logging.getLogger(__name__)

    if len(system_prompts) < MAX_ATTEMPTS:
        raise ValueError(
            "system_prompts must contain at least two prompts."
        )

    cleaned_schema = strict_schema(schema)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return client.generate_json(
                prompt=prompt,
                schema=cleaned_schema,
                schema_name=schema_name,
                system_prompt=system_prompts[attempt - 1],
                max_completion_tokens=max_completion_tokens,
                reasoning_effort=reasoning_effort,
            )

        except InvalidJSONError as exc:
            _log_structured_failure(
                logger,
                client.model,
                attempt,
                exc,
            )

            if attempt == MAX_ATTEMPTS:
                raise StructuredGenerationError(
                    f"The AI couldn't produce valid {what} "
                    f"after {MAX_ATTEMPTS} attempts. {advice}"
                ) from exc

        except Exception:
            raise

    raise StructuredGenerationError(
        f"Failed to generate {what}. {advice}"
    )
