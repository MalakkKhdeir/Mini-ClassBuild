
from pydantic import ValidationError

from classbuild.models.quiz import Quiz
from classbuild.llm.exceptions import GroqClientError
from classbuild.services.structured_output import (
    request_structured_json,
    StructuredGenerationError,
)


SYSTEM_PROMPT = (
    "You are an educational assessment designer. "
    "Create clear, relevant multiple-choice questions."
)

RETRY_SYSTEM_PROMPT = (
    "You are an educational assessment designer. "
    "Return only valid JSON matching the provided schema. "
    "Generate exactly 5 questions with 4 options each, "
    "one correct answer, and an explanation for every question."
)


class QuizGenerationError(Exception):
    """Raised when a quiz cannot be generated or validated."""


class QuizGenerator:
    """Generate a five-question multiple-choice quiz."""

    def __init__(self, groq_client):
        self.groq_client = groq_client

    def generate(
        self,
        lesson_title: str,
        lesson_content: dict,
        difficulty: str,
        course_topic: str,
    ) -> Quiz:
        prompt = f"""
Create a multiple-choice quiz for the lesson below.

Course topic: {course_topic}
Lesson title: {lesson_title}
Difficulty: {difficulty}

Lesson content:
{lesson_content}

Requirements:
- Generate exactly 5 questions.
- Each question must have exactly 4 distinct answer options.
- Each question must have exactly one correct answer.
- The correct_answer must exactly match one of the options.
- Include an explanation for each correct answer.
- Base questions on the lesson content.
- Match the requested difficulty.
- Return JSON matching the provided schema.
"""

        try:
            data = request_structured_json(
                self.groq_client,
                prompt=prompt,
                schema=Quiz.model_json_schema(),
                schema_name="lesson_quiz",
                system_prompts=[
                    SYSTEM_PROMPT,
                    RETRY_SYSTEM_PROMPT,
                ],
                max_completion_tokens=3000,
                reasoning_effort="low",
                what="lesson quiz",
                advice="Please try generating the quiz again.",
            )

            return Quiz.model_validate(data)

        except (
            ValidationError,
            GroqClientError,
            StructuredGenerationError,
        ) as exc:
            raise QuizGenerationError(
                "Could not generate a valid quiz."
            ) from exc
