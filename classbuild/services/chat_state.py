import hashlib
import json
from typing import NamedTuple

from classbuild.models.chat import ChatMessage
from classbuild.models.lesson import LessonContent


class ChatThreadKey(NamedTuple):
    course_id: str
    lesson_number: int
    lesson_fingerprint: str
    document_fingerprint: str | None

    @property
    def is_pdf(self) -> bool:
        return self.document_fingerprint is not None


def lesson_fingerprint(content: LessonContent | dict) -> str:
    """Return a stable fingerprint for the lesson content."""

    if isinstance(content, LessonContent):
        data = content.model_dump(mode="json")
    else:
        data = content

    serialized = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()[:16]


def thread_key(
    course_id: str,
    content: LessonContent | dict,
    lesson_number: int,
    document_fingerprint: str | None = None,
) -> ChatThreadKey:
    """Build a unique key for one lesson conversation."""

    return ChatThreadKey(
        course_id=course_id,
        lesson_number=lesson_number,
        lesson_fingerprint=lesson_fingerprint(content),
        document_fingerprint=document_fingerprint,
    )


def get_history(
    chats: dict,
    key: ChatThreadKey,
) -> list[ChatMessage]:
    """Return a copy of the selected conversation."""

    return list(chats.get(key, []))


def append_exchange(
    chats: dict,
    key: ChatThreadKey,
    question: ChatMessage,
    answer: ChatMessage,
) -> None:
    """Append a complete question and answer together."""

    if question.role != "user":
        raise ValueError("Question must be a user message.")

    if answer.role != "assistant":
        raise ValueError("Answer must be an assistant message.")

    history = list(chats.get(key, []))
    history.extend([question, answer])

    chats[key] = history


def clear_thread(
    chats: dict,
    key: ChatThreadKey,
) -> None:
    """Delete one conversation."""

    chats.pop(key, None)


def valid_thread_keys(
    course_id: str,
    lessons: dict,
    lesson_titles: list[str],
    document_fingerprint: str | None = None,
) -> set[ChatThreadKey]:
    """Build valid keys for lesson and PDF conversations."""

    valid_keys = set()

    for cache_key, content in lessons.items():
        if not isinstance(cache_key, tuple) or len(cache_key) < 5:
            continue

        lesson_title = cache_key[4]

        if lesson_title not in lesson_titles:
            continue

        lesson_number = lesson_titles.index(lesson_title) + 1

        try:
            parsed_lesson = LessonContent.model_validate(content)
        except Exception:
            continue

        # Lesson Chat: always valid while the lesson exists
        valid_keys.add(
            thread_key(
                course_id=course_id,
                content=parsed_lesson,
                lesson_number=lesson_number,
            )
        )

        # PDF Chat: valid only for grounded lessons
        # that belong to the currently uploaded PDF.
        if (
            parsed_lesson.is_grounded
            and document_fingerprint is not None
            and parsed_lesson.grounding.document_fingerprint
            == document_fingerprint
        ):
            valid_keys.add(
                thread_key(
                    course_id=course_id,
                    content=parsed_lesson,
                    lesson_number=lesson_number,
                    document_fingerprint=document_fingerprint,
                )
            )

    return valid_keys


def prune_chats(
    chats: dict,
    valid_keys: set[ChatThreadKey],
) -> None:
    """Remove conversations whose lesson or PDF is no longer valid."""

    stale_keys = [
        key
        for key in chats
        if key not in valid_keys
    ]

    for key in stale_keys:
        chats.pop(key, None)