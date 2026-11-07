import logging
from copy import deepcopy
from typing import Callable, Any

from pydantic import ValidationError

from classbuild.llm.exceptions import InvalidJSONError


MAX_ATTEMPTS = 2
LOG_PREVIEW_CHARS = 200

_UNSENT_KEYWORDS = {
    "minItems", "maxItems", "minLength", "maxLength", "minimum", "maximum",
}


class StructuredGenerationError(Exception):
    """Raised when structured JSON generation fails after retries."""


def _clean_schema(node):
    """Remove schema keywords that should be enforced by Pydantic."""
    if isinstance(node, dict):
        return {
            key: _clean_schema(value)
            for key, value in node.items()
            if key not in _UNSENT_KEYWORDS
        }
    if isinstance(node, list):
        return [_clean_schema(item) for item in node]
    return node


def strict_schema(schema: dict) -> dict:
    return _clean_schema(deepcopy(schema))


def describe_validation_error(exc: ValidationError) -> list[str]:
    problems = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error["loc"])
        problems.append(f"{location}: {error['msg']}")
    return problems


def _log_structured_failure(logger, model: str, attempt: int, exc: Exception):
    preview = str(getattr(exc, "failed_generation", ""))[:LOG_PREVIEW_CHARS]
    category = getattr(exc, "category", "unknown")
    logger.warning(
        "Structured generation failed | model=%s | attempt=%s/%s | category=%s | preview=%r",
        model, attempt, MAX_ATTEMPTS, category, preview,
    )


def _retry_guidance(exc: ValidationError) -> str:
    """Add targeted repair instructions for common list-size failures."""
    guidance = []
    for error in exc.errors():
        location = error.get("loc", ())
        error_type = error.get("type", "")
        if location and location[0] == "sections" and error_type == "too_short":
            guidance.append(
                "The sections list must contain at least 2 distinct, "
                "source-supported sections. Do not return only one section, "
                "do not duplicate a section, and do not invent a topic."
            )
        elif location and location[0] == "exercises" and error_type == "too_short":
            guidance.append(
                "The exercises list must contain exactly 2 complete exercises, "
                "each based only on the supplied source passages."
            )
    if not guidance:
        guidance.append(
            "Return every required field with complete, non-empty content. "
            "Do not return empty strings or empty lists where content is required."
        )
    return "\n- ".join(guidance)


def request_structured_json(
    client,
    *,
    prompt: str,
    schema: dict,
    schema_name: str,
    system_prompts: list[str],
    max_completion_tokens: int | None = None,
    reasoning_effort: str | None = None,
    history: list[dict] | None = None,
    validator: Callable[[dict], Any] | None = None,
    logger=None,
    what: str = "structured content",
    advice: str = "Please try again.",
) -> dict:
    """Request JSON and retry once for invalid JSON or failed validation."""
    logger = logger or logging.getLogger(__name__)
    if len(system_prompts) < MAX_ATTEMPTS:
        raise ValueError("system_prompts must contain at least two prompts.")

    cleaned_schema = strict_schema(schema)
    current_prompt = prompt
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            data = client.generate_json(
                prompt=current_prompt,
                schema=cleaned_schema,
                schema_name=schema_name,
                system_prompt=system_prompts[attempt - 1],
                max_completion_tokens=max_completion_tokens,
                reasoning_effort=reasoning_effort,
                history=history,
            )
            if validator is not None:
                validator(data)
            return data

        except InvalidJSONError as exc:
            last_error = exc
            _log_structured_failure(logger, getattr(client, "model", "unknown"), attempt, exc)
            if attempt < MAX_ATTEMPTS:
                current_prompt = (
                    prompt
                    + "\n\nThe previous response was not valid JSON. "
                    "Return one complete JSON object matching the schema."
                )

        except ValidationError as exc:
            last_error = exc
            problems = describe_validation_error(exc)
            logger.warning(
                "Structured response validation failed | model=%s | attempt=%s/%s | problems=%s",
                getattr(client, "model", "unknown"), attempt, MAX_ATTEMPTS,
                "; ".join(problems),
            )
            if attempt < MAX_ATTEMPTS:
                targeted = _retry_guidance(exc)
                current_prompt = (
                    prompt
                    + "\n\nYour previous JSON failed Pydantic validation. "
                    "Regenerate the ENTIRE object, not a partial patch. "
                    "Correct these validation problems:\n- "
                    + "\n- ".join(problems)
                    + "\nAdditional requirements:\n- "
                    + targeted
                    + "\nDo not weaken requirements, omit fields, or invent unsupported source content."
                )

    if isinstance(last_error, ValidationError):
        detail = "; ".join(describe_validation_error(last_error))
        message = (
            f"The AI returned incomplete or invalid {what} after "
            f"{MAX_ATTEMPTS} attempts ({detail}). {advice}"
        )
    else:
        message = (
            f"The AI couldn't produce valid {what} after "
            f"{MAX_ATTEMPTS} attempts. {advice}"
        )
    raise StructuredGenerationError(message) from last_error
