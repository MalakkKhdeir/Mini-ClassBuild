
from pydantic import ValidationError

from classbuild.models.course import Course
from classbuild.course_config import CourseConfig
from classbuild.llm.exceptions import GroqClientError
from classbuild.services.structured_output import (
    request_structured_json,
    StructuredGenerationError,
)


SYSTEM_PROMPT = (
    "You are an educational course designer. "
    "Create clear and structured course outlines."
)

RETRY_SYSTEM_PROMPT = (
    "You are an educational course designer. "
    "Return only valid JSON matching the provided schema. "
    "Follow every required field and lesson count exactly."
)


class CourseGenerationError(Exception):
    """Raised when a course outline cannot be generated or validated."""


class CourseGenerator:
    """Generate and validate structured course outlines."""

    def __init__(self, groq_client):
        self.groq_client = groq_client

    def generate(self, config: CourseConfig) -> Course:
        prompt = f"""
Create a structured course outline.

Topic: {config.topic}
Difficulty: {config.difficulty}
Required number of lessons: {config.lesson_count}

Requirements:
- Create a clear course title and short description.
- Provide meaningful course learning objectives.
- Generate exactly {config.lesson_count} lessons.
- Each lesson must have a title, learning_objectives, and summary.
- Arrange lessons in a logical order.
- Match the requested difficulty.
- Return JSON matching the provided schema.
"""

        try:
            data = request_structured_json(
                self.groq_client,
                prompt=prompt,
                schema=Course.model_json_schema(),
                schema_name="course_outline",
                system_prompts=[
                    SYSTEM_PROMPT,
                    RETRY_SYSTEM_PROMPT,
                ],
                max_completion_tokens=3000,
                reasoning_effort="low",
                what="course outline",
                advice="Please try generating the course again.",
            )

            course = Course.model_validate(data)

        except (
            ValidationError,
            GroqClientError,
            StructuredGenerationError,
        ) as exc:
            raise CourseGenerationError(
                "The generated course outline could not be validated."
            ) from exc

        if len(course.lessons) != config.lesson_count:
            raise CourseGenerationError(
                f"Expected {config.lesson_count} lessons, "
                f"but received {len(course.lessons)}."
            )

        return course
