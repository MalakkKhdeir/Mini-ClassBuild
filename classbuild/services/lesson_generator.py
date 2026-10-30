
from pydantic import ValidationError

from classbuild.models.lesson import Lesson
from classbuild.llm.exceptions import GroqClientError
from classbuild.services.structured_output import (
    request_structured_json,
    StructuredGenerationError,
)


SYSTEM_PROMPT = (
    "You create accurate educational content. "
    "Follow the requested JSON schema exactly. "
    "Return only the requested structured data."
)

RETRY_SYSTEM_PROMPT = (
    "You are an educational content designer. "
    "Return only valid JSON matching the provided schema. "
    "Include all required fields, 2 to 4 sections, "
    "and exactly 2 exercises."
)


class LessonGenerationError(Exception):
    """Raised when lesson content cannot be generated or validated."""


class LessonGenerator:
    """Generate structured content for a selected course lesson."""

    def __init__(self, groq_client):
        self.groq_client = groq_client

    def generate(
        self,
        lesson_title: str,
        learning_objectives: list[str],
        difficulty: str,
        course_topic: str,
    ) -> Lesson:
        objectives_text = "\n".join(
            f"- {objective}" for objective in learning_objectives
        )

        prompt = f"""
Create a complete educational lesson using the information below.

Course topic: {course_topic}
Lesson title: {lesson_title}
Difficulty: {difficulty}

Learning objectives:
{objectives_text}

Return one JSON object with these fields:
- title: a non-empty string
- introduction: a clear introductory paragraph
- sections: a list containing 2 to 4 sections
- summary: a concise paragraph
- exercises: a list containing exactly 2 exercises

Every section must contain:
- heading: a short title
- explanation: a clear explanation
- example: a relevant code example or practical example

Every exercise must contain:
- task: an exercise instruction
- hint: a helpful hint that does not give away the full answer

Additional requirements:
- Match the requested difficulty.
- Keep the lesson relevant to the learning objectives.
- Include valid values for every required field.
- Do not include markdown fences or text outside the JSON object.
"""

        try:
            data = request_structured_json(
                self.groq_client,
                prompt=prompt,
                schema=Lesson.model_json_schema(),
                schema_name="lesson_content",
                system_prompts=[
                    SYSTEM_PROMPT,
                    RETRY_SYSTEM_PROMPT,
                ],
                max_completion_tokens=4000,
                reasoning_effort="low",
                what="lesson content",
                advice="Please try generating the lesson again.",
            )

            return Lesson.model_validate(data)

        except (
            ValidationError,
            GroqClientError,
            StructuredGenerationError,
        ) as exc:
            raise LessonGenerationError(
                "Could not generate valid lesson content."
            ) from exc
