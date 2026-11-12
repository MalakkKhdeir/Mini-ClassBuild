
from datetime import datetime, timezone

import pytest

from classbuild.models.course import Course
from classbuild.models.lesson import (
    LessonContent,
    LessonSection,
    LessonExercise,
)
from classbuild.models.quiz import Quiz, QuizQuestion

from classbuild.persistence.saved_course import (
    SavedCourse,
    SourceDocument,
    new_course_id,
    build_saved_course,
)

from classbuild.persistence.course_store import (
    CourseStore,
    CourseNotFoundError,
    InvalidCourseIdError,
    CourseFileTooLargeError,
    CorruptedCourseFileError,
    UnsupportedSchemaVersionError,
)


from unittest.mock import patch


from classbuild.export.markdown_export import (
    course_to_markdown,
    course_filename,
    export_markdown,
)

from classbuild.models.lesson import (
    LessonContent,
    LessonSection,
    LessonExercise,
    LessonGrounding,
    SourceReference,
)

def make_outline():
    return Course(
        title="Python Course",
        description="A course about Python programming.",
        objectives=[
            "Understand Python basics.",
            "Write simple Python programs.",
        ],
        lessons=[
            {
                "title": "Python Basics",
                "learning_objectives": [
                    "Understand variables.",
                ],
                "summary": "Introduction to Python basics.",
            },
            {
                "title": "Python Functions",
                "learning_objectives": [
                    "Understand functions.",
                ],
                "summary": "Introduction to Python functions.",
            },
        ],
    )


def make_lesson(title="Python Basics"):
    return LessonContent(
        title=title,
        introduction="Introduction to Python programming.",
        sections=[
            {
                "heading": "Variables",
                "explanation": "Variables store values.",
                "example": "name = 'Malak'",
            },
            {
                "heading": "Data Types",
                "explanation": "Python supports different data types.",
                "example": "age = 20",
            },
        ],
        summary="Python uses variables and data types.",
        exercises=[
            {
                "task": "Create a variable named name.",
                "hint": "Use the assignment operator.",
            },
            {
                "task": "Create an integer variable.",
                "hint": "Assign a whole number.",
            },
        ],
    )


def make_quiz():
    return Quiz(
        questions=[
            QuizQuestion(
                question=f"What is the correct Python option? Question {i}",
                options=[
                    "Python",
                    "Java",
                    "C++",
                    "JavaScript",
                ],
                correct_answer="Python",
                explanation="Python is the correct answer.",
            )
            for i in range(1, 6)
        ]
    )


def test_save_and_load_course(tmp_path):
    course_id = new_course_id()

    course = build_saved_course(
        course_id=course_id,
        topic="Python Programming",
        difficulty="Beginner",
        outline=make_outline(),
        lesson_contents={
            1: make_lesson(),
        },
        quizzes={
            1: make_quiz(),
        },
        selected_lesson="Python Basics",
    )

    store = CourseStore(tmp_path)

    # Save the course.
    saved_path = store.save(course)

    assert saved_path.exists()

    # Load the saved course.
    loaded_course = store.load(course_id)

    # Verify the loaded data.
    assert loaded_course.course_id == course_id
    assert loaded_course.topic == "Python Programming"
    assert loaded_course.difficulty == "Beginner"

    assert len(loaded_course.outline.lessons) == 2

    assert 1 in loaded_course.lessons
    assert loaded_course.lessons[1].title == "Python Basics"

    assert 1 in loaded_course.quizzes
    assert len(loaded_course.quizzes[1].questions) == 5

    assert loaded_course.selected_lesson == "Python Basics"



def test_update_course(tmp_path):
    course_id = new_course_id()
    store = CourseStore(tmp_path)

    course = build_saved_course(
        course_id=course_id,
        topic="Python Programming",
        difficulty="Beginner",
        outline=make_outline(),
        lesson_contents={1: make_lesson()},
        quizzes={},
    )

    store.save(course)

    original_created_at = store.load(course_id).created_at

    updated_course = course.model_copy(
        update={
            "topic": "Advanced Python",
            "difficulty": "Advanced",
        }
    )

    store.update(updated_course)

    loaded_course = store.load(course_id)

    assert loaded_course.topic == "Advanced Python"
    assert loaded_course.difficulty == "Advanced"
    assert loaded_course.created_at == original_created_at
    assert loaded_course.updated_at >= original_created_at


def test_list_courses(tmp_path):
    store = CourseStore(tmp_path)

    for topic in ["Python", "Machine Learning"]:
        course = build_saved_course(
            course_id=new_course_id(),
            topic=topic,
            difficulty="Beginner",
            outline=make_outline(),
            lesson_contents={},
            quizzes={},
        )

        store.save(course)

    summaries = store.list_courses()

    assert len(summaries) == 2

    topics = {summary.topic for summary in summaries}

    assert topics == {"Python", "Machine Learning"}

    for summary in summaries:
        assert summary.course_id
        assert summary.lesson_count == 2
        assert summary.difficulty == "Beginner"



def test_delete_course(tmp_path):
    store = CourseStore(tmp_path)
    course_id = new_course_id()

    course = build_saved_course(
        course_id=course_id,
        topic="Python Programming",
        difficulty="Beginner",
        outline=make_outline(),
        lesson_contents={},
        quizzes={},
    )

    store.save(course)

    store.delete(course_id)

    assert not (tmp_path / f"{course_id}.json").exists()

    with pytest.raises(CourseNotFoundError):
        store.load(course_id)



def test_invalid_course_id(tmp_path):
    store = CourseStore(tmp_path)

    with pytest.raises(InvalidCourseIdError):
        store.load("../outside")


def test_load_corrupted_json(tmp_path):
    store = CourseStore(tmp_path)
    course_id = new_course_id()

    corrupted_file = tmp_path / f"{course_id}.json"
    corrupted_file.write_text(
        "{ invalid json content",
        encoding="utf-8",
    )

    with pytest.raises(CorruptedCourseFileError):
        store.load(course_id)


def test_unsupported_schema_version(tmp_path):
    store = CourseStore(tmp_path)
    course_id = new_course_id()

    course_file = tmp_path / f"{course_id}.json"

    course_file.write_text(
        '{"schema_version": 999}',
        encoding="utf-8",
    )

    with pytest.raises(UnsupportedSchemaVersionError):
        store.load(course_id)


def test_load_file_too_large(tmp_path):
    store = CourseStore(tmp_path)
    course_id = new_course_id()

    course_file = tmp_path / f"{course_id}.json"

    course_file.write_bytes(
        b"x" * (2 * 1024 * 1024 + 1)
    )

    with pytest.raises(CourseFileTooLargeError):
        store.load(course_id)



def test_save_file_too_large(tmp_path):
    store = CourseStore(tmp_path)

    course = build_saved_course(
        course_id=new_course_id(),
        topic="Python " + ("A" * (2 * 1024 * 1024)),
        difficulty="Beginner",
        outline=make_outline(),
        lesson_contents={},
        quizzes={},
    )

    with pytest.raises(CourseFileTooLargeError):
        store.save(course)


def test_save_is_atomic(tmp_path):
    store = CourseStore(tmp_path)

    course = build_saved_course(
        course_id=new_course_id(),
        topic="Python Programming",
        difficulty="Beginner",
        outline=make_outline(),
        lesson_contents={},
        quizzes={},
    )

    original_path = store.save(course)
    original_content = original_path.read_bytes()

    updated_course = course.model_copy(
        update={"topic": "Updated Python"},
    )

    with patch(
        "classbuild.persistence.course_store.os.replace",
        side_effect=OSError("Simulated write failure"),
    ):
        with pytest.raises(OSError):
            store.save(updated_course)

    assert original_path.read_bytes() == original_content
    assert not original_path.with_suffix(".tmp").exists()


def test_list_courses_ignores_temp_files(tmp_path):
    store = CourseStore(tmp_path)

    course = build_saved_course(
        course_id=new_course_id(),
        topic="Python Programming",
        difficulty="Beginner",
        outline=make_outline(),
        lesson_contents={},
        quizzes={},
    )

    store.save(course)

    temp_file = tmp_path / "unfinished.tmp"
    temp_file.write_text(
        '{"incomplete": true}',
        encoding="utf-8",
    )

    summaries = store.list_courses()

    assert len(summaries) == 1
    assert summaries[0].course_id == course.course_id



def test_reject_quiz_without_saved_lesson():
    with pytest.raises(ValueError):
        build_saved_course(
            course_id=new_course_id(),
            topic="Python Programming",
            difficulty="Beginner",
            outline=make_outline(),
            lesson_contents={
                1: make_lesson(),
            },
            quizzes={
                2: make_quiz(),
            },
        )



def test_reject_lesson_with_wrong_title():
    with pytest.raises(ValueError):
        build_saved_course(
            course_id=new_course_id(),
            topic="Python Programming",
            difficulty="Beginner",
            outline=make_outline(),
            lesson_contents={
                1: make_lesson(title="Java Basics"),
            },
            quizzes={},
        )




def test_reject_invalid_selected_lesson():
    with pytest.raises(ValueError):
        build_saved_course(
            course_id=new_course_id(),
            topic="Python Programming",
            difficulty="Beginner",
            outline=make_outline(),
            lesson_contents={},
            quizzes={},
            selected_lesson="Java Basics",
        )


def test_markdown_export_contains_course_content():
    outline = make_outline()

    markdown = course_to_markdown(
        outline=outline,
        topic="Python Programming",
        lessons={
            1: make_lesson(),
        },
        quizzes={
            1: make_quiz(),
        },
    )

    assert "# Python Programming" in markdown
    assert "Course Description" in markdown
    assert "Learning Objectives" in markdown

    assert "Lesson 1: Python Basics" in markdown
    assert "Lesson 2: Python Functions" in markdown

    assert "Variables" in markdown
    assert "Data Types" in markdown

    assert "Question 1" in markdown
    assert "Answer Key" in markdown


def test_markdown_missing_lesson_note():
    outline = make_outline()

    markdown = course_to_markdown(
        outline=outline,
        topic="Python",
        lessons={},
        quizzes={},
    )

    assert "This lesson has not been generated yet." in markdown


def test_markdown_answer_key_uses_option_letters():
    outline = make_outline()
    lesson = make_lesson()
    quiz = make_quiz()

    markdown = course_to_markdown(
        outline=outline,
        topic="Python",
        lessons={1: lesson},
        quizzes={1: quiz},
    )

    answer_key = markdown.split("## Answer Key")[-1]

    assert "**A**" in answer_key
    assert "- Lesson 1, Question 1: **A**" in answer_key
    assert "- Explanation:" in answer_key


def test_course_filename_is_safe():
    filename = course_filename("../Python: Basics/Level 1")

    assert "/" not in filename
    assert "\\" not in filename
    assert ":" not in filename
    assert filename.endswith(".md")


def test_export_markdown_creates_file(tmp_path):
    outline = make_outline()

    output_path = export_markdown(
        outline=outline,
        topic="Python",
        lessons={},
        quizzes={},
        output_dir=tmp_path,
    )

    assert output_path.exists()
    assert output_path.suffix == ".md"


def test_markdown_exports_pdf_sources():
    outline = make_outline()
    lesson_data = make_lesson().model_dump()

    lesson_data["grounding"] = {
        "document_fingerprint": "abc123",
        "source_filename": "python.pdf",
        "retrieval_query": "Python basics",
        "sources": [
            {
                "chunk_id": "source-1",
                "chunk_index": 0,
                "source_filename": "python.pdf",
                "page_number": 3,
                "text": "Python is a programming language.",
                "similarity": 0.95,
            }
        ],
    }
    lesson_data["sections"][0]["source_ids"] = ["source-1"]

    lesson = LessonContent.model_validate(lesson_data)

    markdown = course_to_markdown(
        outline=outline,
        topic="Python",
        lessons={1: lesson},
        quizzes={},
    )

    assert "python.pdf" in markdown
    assert "page 3" in markdown