
import pytest
from pydantic import ValidationError

from classbuild.models.course import Course


def make_valid_course_data():
    return {
        "title": "Introduction to Python",
        "description": "A beginner course about Python.",
        "objectives": [
            "Understand Python basics",
        ],
        "lessons": [
            {
                "title": f"Lesson {i}",
                "learning_objectives": [
                    f"Understand concept {i}",
                ],
                "summary": f"Summary for lesson {i}.",
            }
            for i in range(1, 3)
        ],
    }


def test_course_accepts_two_lessons():
    course = Course.model_validate(make_valid_course_data())

    assert len(course.lessons) == 2


def test_course_rejects_fewer_than_two_lessons():
    data = make_valid_course_data()
    data["lessons"] = data["lessons"][:1]

    with pytest.raises(ValidationError):
        Course.model_validate(data)


def test_course_rejects_more_than_five_lessons():
    data = make_valid_course_data()
    data["lessons"] = [
        {
            "title": f"Lesson {i}",
            "learning_objectives": [f"Objective {i}"],
            "summary": f"Summary {i}",
        }
        for i in range(1, 7)
    ]

    with pytest.raises(ValidationError):
        Course.model_validate(data)
