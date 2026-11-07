from classbuild.services.lesson_state import (
    stale_grounded_lessons,
    remove_stale_grounded_lessons,
)


def test_stale_grounded_lessons():
    lessons = {
        "lesson_1": {
            "grounding": {
                "document_fingerprint": "old_pdf"
            }
        },
        "lesson_2": {
            "grounding": {
                "document_fingerprint": "current_pdf"
            }
        },
        "lesson_3": {
            "grounding": None
        },
    }

    stale = stale_grounded_lessons(
        lessons,
        "current_pdf",
    )

    assert stale == ["lesson_1"]


def test_remove_stale_grounded_lessons():
    lessons = {
        "lesson_1": {
            "grounding": {
                "document_fingerprint": "old_pdf"
            }
        },
        "lesson_2": {
            "grounding": None
        },
    }

    quizzes = {"lesson_1": {}, "lesson_2": {}}
    results = {"lesson_1": {}, "lesson_2": {}}
    attempts = {"lesson_1": 2, "lesson_2": 1}

    removed = remove_stale_grounded_lessons(
        lessons,
        "current_pdf",
        quizzes,
        results,
        attempts,
    )

    assert removed == ["lesson_1"]
    assert "lesson_1" not in lessons
    assert "lesson_1" not in quizzes
    assert "lesson_1" not in results
    assert "lesson_1" not in attempts

    assert "lesson_2" in lessons
    assert "lesson_2" in quizzes
    assert "lesson_2" in results
    assert "lesson_2" in attempts