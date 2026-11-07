
from pydantic import ValidationError
import pytest

from classbuild.models.lesson import Lesson


def make_valid_lesson_data():
    return {
        "title": "Python Variables",
        "introduction": "Variables store values.",
        "sections": [
            {
                "heading": f"Section {i}",
                "explanation": f"Explanation for section {i}.",
                "example": f"value = {i}",
            }
            for i in range(1, 3)
        ],
        "summary": "Variables store values in Python.",
        "exercises": [
            {
                "task": "Create a variable named age.",
                "hint": "Use the assignment operator.",
            },
            {
                "task": "Print the variable.",
                "hint": "Use print().",
            },
        ],
    }


def test_lesson_has_required_sections_and_exercises():
    lesson = Lesson.model_validate(make_valid_lesson_data())

    assert len(lesson.sections) >= 2
    assert len(lesson.exercises) == 2


def test_lesson_rejects_missing_title():
    data = make_valid_lesson_data()
    data.pop("title")

    with pytest.raises(ValidationError):
        Lesson.model_validate(data)

from classbuild.services.lesson_generator import _without_source_fields


def test_ordinary_lesson_schema_excludes_source_ids():
    schema = _without_source_fields(
        Lesson.model_json_schema()
    )

    section_schema = schema["$defs"]["LessonSection"]

    assert "source_ids" not in section_schema["properties"]
    assert "source_ids" not in section_schema.get("required", [])
