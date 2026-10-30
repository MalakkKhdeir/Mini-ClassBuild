
import pytest
from pydantic import BaseModel, Field, ValidationError

from classbuild.llm.exceptions import InvalidJSONError
from classbuild.services.structured_output import (
    strict_schema,
    describe_validation_error,
    request_structured_json,
    StructuredGenerationError,
)


class SampleModel(BaseModel):
    name: str = Field(min_length=1)
    items: list[str] = Field(min_length=2)


def test_strict_schema_removes_unsupported_keywords():
    original = SampleModel.model_json_schema()

    cleaned = strict_schema(original)

    assert "minLength" not in cleaned["properties"]["name"]
    assert "minItems" not in cleaned["properties"]["items"]

    # The original schema must remain unchanged.
    assert "minLength" in original["properties"]["name"]


def test_describe_validation_error():
    with pytest.raises(ValidationError) as error:
        SampleModel.model_validate({"name": "", "items": []})

    problems = describe_validation_error(error.value)

    assert len(problems) >= 2
    assert any("name" in problem for problem in problems)
    assert any("items" in problem for problem in problems)


class FakeClient:
    model = "openai/gpt-oss-20b"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_json(self, **kwargs):
        self.calls.append(kwargs)

        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


def test_request_retries_once_after_invalid_json():
    client = FakeClient([
        InvalidJSONError("Invalid JSON", category="invalid_json"),
        {"title": "Python Basics"},
    ])

    result = request_structured_json(
        client,
        prompt="Create a course",
        schema=SampleModel.model_json_schema(),
        schema_name="test_schema",
        system_prompts=["First attempt", "Retry attempt"],
    )

    assert result == {"title": "Python Basics"}
    assert len(client.calls) == 2
    assert client.calls[0]["system_prompt"] == "First attempt"
    assert client.calls[1]["system_prompt"] == "Retry attempt"



def test_request_raises_after_two_invalid_responses():
    client = FakeClient([
        InvalidJSONError(
            "Invalid JSON",
            category="invalid_json",
        ),
        InvalidJSONError(
            "Still invalid",
            category="invalid_json",
        ),
    ])

    with pytest.raises(StructuredGenerationError):
        request_structured_json(
            client,
            prompt="Create a course",
            schema=SampleModel.model_json_schema(),
            schema_name="test_schema",
            system_prompts=["First attempt", "Retry attempt"],
        )

    assert len(client.calls) == 2



def test_request_does_not_retry_other_errors():
    client = FakeClient([
        RuntimeError("Connection failed"),
        {"title": "This should not be used"},
    ])

    with pytest.raises(RuntimeError):
        request_structured_json(
            client,
            prompt="Create a course",
            schema=SampleModel.model_json_schema(),
            schema_name="test_schema",
            system_prompts=["First attempt", "Retry attempt"],
        )

    assert len(client.calls) == 1
