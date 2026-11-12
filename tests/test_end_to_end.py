
import socket
from unittest.mock import patch

import pytest

from classbuild.course_config import CourseConfig
from classbuild.services.course_generator import CourseGenerator
from classbuild.services.lesson_generator import LessonGenerator
from classbuild.services.quiz_generator import QuizGenerator
from classbuild.persistence.saved_course import (
    build_saved_course,
    new_course_id,
)
from classbuild.persistence.course_store import CourseStore
from classbuild.export.markdown_export import export_markdown


class ScriptedGroq:
    """Return predefined JSON responses without calling the Groq API."""

    model = "fake-model"

    def generate_json(self, *, schema_name, **kwargs):
        if schema_name == "course_outline":
            return {
                "title": "Python Fundamentals",
                "description": "An introductory Python course.",
                "objectives": [
                    "Understand Python basics",
                    "Write simple Python programs",
                ],
                "lessons": [
                    {
                        "title": "Python Basics",
                        "learning_objectives": [
                            "Understand variables",
                            "Understand basic data types",
                        ],
                        "summary": "Introduction to Python syntax and variables.",
                    },
                    {
                        "title": "Python Functions",
                        "learning_objectives": [
                            "Understand functions",
                            "Use parameters and return values",
                        ],
                        "summary": "Introduction to reusable Python functions.",
                    },
                ],
            }

        if schema_name == "lesson_content":
            return {
                "title": "Python Basics",
                "introduction": "Python is a beginner-friendly programming language.",
                "sections": [
                    {
                        "heading": "Variables",
                        "explanation": "Variables store values in a program.",
                        "example": "name = 'Malak'",
                    },
                    {
                        "heading": "Data Types",
                        "explanation": "Python supports strings, integers, and floats.",
                        "example": "age = 20",
                    },
                ],
                "summary": "Variables and data types are basic Python concepts.",
                "exercises": [
                    {
                        "task": "Create a variable called name.",
                        "hint": "Use an assignment statement.",
                    },
                    {
                        "task": "Create an integer variable.",
                        "hint": "Assign a whole number to a variable.",
                    },
                ],
            }

        if schema_name == "lesson_quiz":
            return {
                "questions": [
                    {
                        "question": f"Question {number}: Which option is correct?",
                        "options": [
                            "A",
                            "B",
                            "C",
                            "D",
                        ],
                        "correct_answer": "A",
                        "explanation": "Option A is correct.",
                    }
                    for number in range(1, 6)
                ]
            }

        raise AssertionError(
            f"Unexpected schema requested: {schema_name}"
        )


@pytest.fixture
def offline_environment(monkeypatch):
    """Prevent accidental network access during the test."""

    def blocked_connection(*args, **kwargs):
        raise AssertionError(
            "Network access is not allowed in end-to-end tests."
        )

    monkeypatch.setattr(
        socket.socket,
        "connect",
        blocked_connection,
    )
    monkeypatch.setattr(
        socket,
        "create_connection",
        blocked_connection,
    )


def test_complete_course_workflow(tmp_path, offline_environment):
    # 1. Generate a course outline.
    fake_groq = ScriptedGroq()

    config = CourseConfig(
        topic="Python",
        difficulty="Beginner",
        lesson_count=2,
    )

    course = CourseGenerator(fake_groq).generate(config)

    assert course.title == "Python Fundamentals"
    assert len(course.lessons) == 2

    # 2. Generate lesson content.
    first_lesson = course.lessons[0]

    lesson = LessonGenerator(fake_groq).generate(
        lesson_title=first_lesson.title,
        learning_objectives=first_lesson.learning_objectives,
        difficulty=config.difficulty,
        course_topic=config.topic,
    )

    assert lesson.title == first_lesson.title
    assert len(lesson.sections) >= 2
    assert len(lesson.exercises) == 2

    # 3. Generate a quiz from the lesson.
    quiz = QuizGenerator(fake_groq).generate(
        lesson_title=lesson.title,
        lesson_content=lesson.model_dump(),
        difficulty=config.difficulty,
        course_topic=config.topic,
    )

    assert len(quiz.questions) == 5

    # 4. Build and save the course.
    saved_course = build_saved_course(
        course_id=new_course_id(),
        topic=config.topic,
        difficulty=config.difficulty,
        outline=course,
        lesson_contents={1: lesson.model_dump()},
        quizzes={1: quiz.model_dump()},
        selected_lesson=lesson.title,
    )

    store = CourseStore(save_dir=tmp_path / "saved_courses")
    store.save(saved_course)

    # 5. Load the saved course.
    loaded_course = store.load(saved_course.course_id)

    assert loaded_course.course_id == saved_course.course_id
    assert loaded_course.topic == "Python"
    assert 1 in loaded_course.lessons
    assert 1 in loaded_course.quizzes
    assert loaded_course.lessons[1].title == "Python Basics"
    assert len(loaded_course.quizzes[1].questions) == 5

    # 6. Export the course to Markdown.
    export_path = export_markdown(
        outline=loaded_course.outline,
        topic=loaded_course.topic,
        lessons=loaded_course.lessons,
        quizzes=loaded_course.quizzes,
        output_dir=tmp_path / "exports",
    )

    assert export_path.exists()

    exported_content = export_path.read_text(encoding="utf-8")

    assert "# Python" in exported_content
    assert "An introductory Python course." in exported_content
    assert "Python Basics" in exported_content
    assert "Answer Key" in exported_content
