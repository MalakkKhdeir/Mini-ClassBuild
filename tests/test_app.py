from datetime import datetime, timezone
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

from classbuild.models.course import Course
from classbuild.persistence.course_store import (
    CourseStorageError,
    CourseStore,
)
from classbuild.persistence.saved_course import (
    SavedCourse,
    SourceDocument,
    build_saved_course,
    new_course_id,
)


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app.py"


def make_outline():
    return Course(
        title="Python Fundamentals",
        description="An introductory Python course.",
        objectives=[
            "Understand Python basics.",
            "Write simple Python programs.",
        ],
        lessons=[
            {
                "title": "Python Basics",
                "learning_objectives": ["Understand variables."],
                "summary": "Introduction to Python variables.",
            },
            {
                "title": "Python Functions",
                "learning_objectives": ["Understand functions."],
                "summary": "Introduction to Python functions.",
            },
        ],
    )


def make_saved_course(
    *,
    topic="Python",
    course_id=None,
    source_document=None,
):
    course = build_saved_course(
        course_id=course_id or new_course_id(),
        topic=topic,
        difficulty="Beginner",
        outline=make_outline(),
        lesson_contents={},
        quizzes={},
        selected_lesson="Python Basics",
    )
    if source_document is not None:
        course.source_document = source_document
    return course


def run_app(monkeypatch, tmp_path, session_state=None):
    """Run the real Streamlit app against an isolated course directory."""
    monkeypatch.setenv("MINICLASSBUILD_SAVE_DIR", str(tmp_path / "saved_courses"))

    app = AppTest.from_file(str(APP_PATH), default_timeout=30)
    if session_state:
        for key, value in session_state.items():
            app.session_state[key] = value

    return app.run()


def course_session(course_id=None):
    return {
        "course_id": course_id or new_course_id(),
        "course_config": {
            "topic": "Python",
            "difficulty": "Beginner",
            "lesson_count": 2,
        },
        "course_outline": make_outline().model_dump(),
        "selected_lesson": "Python Basics",
        "lesson_contents": {},
        "quizzes": {},
        "quiz_results": {},
        "quiz_attempts": {},
        "chats": {},
        "saved_content_hash": None,
        "saved_source_document": None,
    }


def click_button(app, label):
    matching = [button for button in app.button if button.label == label]
    assert matching, f"Button not found: {label}"
    matching[0].click()
    return app.run()


def test_save_update_and_reopen_course_without_groq(
    monkeypatch,
    tmp_path,
):
    """Saving and reopening a course must not require a Groq API call."""
    state = course_session()
    app = run_app(monkeypatch, tmp_path, state)

    app = click_button(app, "💾 Save current course")

    store = CourseStore(tmp_path / "saved_courses")
    saved = store.load(state["course_id"])
    assert saved.topic == "Python"

    # Update the active course and save it again.
    app.session_state["course_config"] = {
        "topic": "Python Advanced",
        "difficulty": "Advanced",
        "lesson_count": 2,
    }
    app.session_state["saved_content_hash"] = None
    app = app.run()
    app = click_button(app, "💾 Save current course")

    updated = store.load(state["course_id"])
    assert updated.topic == "Python Advanced"
    assert updated.difficulty == "Advanced"

    # A fresh app session can load the saved course without generating it.
    fresh = run_app(monkeypatch, tmp_path)
    fresh = click_button(fresh, "📂 Load selected course")
    assert fresh.session_state["saved_course_id"] == state["course_id"]
    assert fresh.session_state["course_id"] != state["course_id"]
    assert fresh.session_state["course_config"]["topic"] == "Python Advanced"


def test_loading_course_resets_quiz_answers_and_chat_history(
    monkeypatch,
    tmp_path,
):
    store = CourseStore(tmp_path / "saved_courses")
    saved = make_saved_course()
    store.save(saved)

    state = {
        "quiz_results": {"old-quiz": {"score": 1}},
        "quiz_attempts": {"old-quiz": 3},
        "chats": {"old-thread": [{"role": "user", "content": "old message"}]},
        "lesson_contents": {"old-lesson": {"title": "Old lesson"}},
        "quizzes": {"old-quiz": {"questions": []}},
    }
    app = run_app(monkeypatch, tmp_path, state)
    app = click_button(app, "📂 Load selected course")

    assert app.session_state["quiz_results"] == {}
    assert app.session_state["quiz_attempts"] == {}
    assert app.session_state["chats"] == {}
    assert app.session_state["lesson_contents"] == {}
    assert app.session_state["quizzes"] == {}


def test_courses_with_identical_titles_are_listed_separately(
    monkeypatch,
    tmp_path,
):
    store = CourseStore(tmp_path / "saved_courses")
    first = make_saved_course(topic="Python")
    second = make_saved_course(topic="Python")
    store.save(first)
    store.save(second)

    app = run_app(monkeypatch, tmp_path)

    selectors = [
        item for item in app.selectbox
        if item.label == "Load a saved course"
    ]
    assert selectors
    assert len(selectors[0].options) == 2
    assert first.course_id[:8] in selectors[0].options[0] or first.course_id[:8] in selectors[0].options[1]
    assert second.course_id[:8] in selectors[0].options[0] or second.course_id[:8] in selectors[0].options[1]


def test_loaded_pdf_course_preserves_its_original_document_identity(
    monkeypatch,
    tmp_path,
):
    source = SourceDocument(
        filename="original-course.pdf",
        fingerprint="original-fingerprint-123",
    )
    store = CourseStore(tmp_path / "saved_courses")
    saved = make_saved_course(source_document=source)
    store.save(saved)

    app = run_app(monkeypatch, tmp_path)
    app = click_button(app, "📂 Load selected course")

    # Save again without uploading a different PDF.
    app = click_button(app, "💾 Save current course")
    reloaded = store.load(saved.course_id)

    assert reloaded.source_document is not None
    assert reloaded.source_document.filename == "original-course.pdf"
    assert reloaded.source_document.fingerprint == "original-fingerprint-123"


def test_corrupted_saved_course_file_is_reported_in_sidebar(
    monkeypatch,
    tmp_path,
):
    save_dir = tmp_path / "saved_courses"
    save_dir.mkdir(parents=True)
    (save_dir / f"{'a' * 32}.json").write_text(
        "{ this is not valid JSON",
        encoding="utf-8",
    )

    app = run_app(monkeypatch, tmp_path)

    warning_text = "\n".join(item.value for item in app.warning)
    assert "Could not read saved course file" in warning_text


def test_failed_save_is_reported_without_crashing_app(
    monkeypatch,
    tmp_path,
):
    def fail_save(self, course):
        raise CourseStorageError("Simulated disk write failure")

    monkeypatch.setattr(CourseStore, "save", fail_save)

    app = run_app(monkeypatch, tmp_path, course_session())
    app = click_button(app, "💾 Save current course")

    error_text = "\n".join(item.value for item in app.error)
    assert "Could not save course" in error_text
    assert "Simulated disk write failure" in error_text


def test_markdown_export_download_is_offered(
    monkeypatch,
    tmp_path,
):
    app = run_app(monkeypatch, tmp_path, course_session())
    app = click_button(app, "📄 Prepare Markdown export")

    export_path = Path(app.session_state["markdown_export_path"])
    assert export_path.exists()
    assert export_path.suffix == ".md"

    download_buttons = app.get("download_button")
    assert any(item.label == "⬇️ Download Markdown" for item in download_buttons)
