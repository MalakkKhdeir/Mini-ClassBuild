
import hashlib
import json
import re

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from classbuild.models.course import Course
from classbuild.models.lesson import LessonContent
from classbuild.models.quiz import Quiz


SCHEMA_VERSION = 1
APP_NAME = "Mini ClassBuild"

COURSE_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def new_course_id() -> str:
    """Generate a random 32-character course ID."""
    return uuid4().hex


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1)
    fingerprint: str = Field(min_length=1)


class SavedCourse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = SCHEMA_VERSION
    app: str = APP_NAME

    course_id: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    topic: str = Field(min_length=1)
    difficulty: str = Field(min_length=1)

    outline: Course

    lessons: dict[int, LessonContent] = Field(
        default_factory=dict
    )

    quizzes: dict[int, Quiz] = Field(
        default_factory=dict
    )

    source_document: SourceDocument | None = None

    selected_lesson: str | None = None

    @field_validator("course_id")
    @classmethod
    def validate_course_id(cls, value):
        if not COURSE_ID_PATTERN.fullmatch(value):
            raise ValueError(
                "Course ID must contain exactly 32 hexadecimal characters."
            )
        return value

    @model_validator(mode="after")
    def check_consistency(self):
        lesson_count = len(self.outline.lessons)
        valid_numbers = set(range(1, lesson_count + 1))

        # Check lesson numbers.
        if not set(self.lessons).issubset(valid_numbers):
            raise ValueError(
                "Saved lessons must match the course outline."
            )

        # Check lesson titles.
        for number, lesson in self.lessons.items():
            expected_title = self.outline.lessons[number - 1].title

            if lesson.title.strip().casefold() != expected_title.strip().casefold():
                raise ValueError(
                    f"Lesson {number} does not match the course outline."
                )

        # A quiz must have a corresponding lesson.
        if not set(self.quizzes).issubset(set(self.lessons)):
            raise ValueError(
                "Every saved quiz must have a corresponding lesson."
            )

        # Check grounded lessons.
        grounded_lessons = [
            lesson
            for lesson in self.lessons.values()
            if lesson.grounding is not None
        ]

        if grounded_lessons and self.source_document is None:
            raise ValueError(
                "Grounded lessons require a source document."
            )

        for lesson in grounded_lessons:
            grounding = lesson.grounding

            if (
                grounding.document_fingerprint
                != self.source_document.fingerprint
                or grounding.source_filename
                != self.source_document.filename
            ):
                raise ValueError(
                    "Grounded lesson does not match the saved PDF."
                )

        # Check selected lesson.
        if self.selected_lesson is not None:
            valid_titles = {
                lesson.title
                for lesson in self.outline.lessons
            }

            if self.selected_lesson not in valid_titles:
                raise ValueError(
                    "Selected lesson does not exist in the course outline."
                )

        return self

    def lessons_by_number(self) -> dict[int, dict]:
        return {
            number: lesson.model_dump()
            for number, lesson in self.lessons.items()
        }

    def quizzes_by_number(self) -> dict[int, dict]:
        return {
            number: quiz.model_dump()
            for number, quiz in self.quizzes.items()
        }
    

    def content_hash(self) -> str:
        content = self.model_dump(
            mode="json",
            exclude={"created_at", "updated_at"},
        )

        serialized = json.dumps(
            content,
            sort_keys=True,
            ensure_ascii=False,
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()


def build_saved_course(
    *,
    course_id: str,
    topic: str,
    difficulty: str,
    outline: Course | dict,
    lesson_contents: dict,
    quizzes: dict,
    selected_lesson: str | None = None,
    created_at: datetime | None = None,
) -> SavedCourse:
    """Build a validated SavedCourse from the current app data."""

    if not isinstance(outline, Course):
        outline = Course.model_validate(outline)

    # Map lesson titles to their outline numbers.
    title_to_number = {
        lesson.title.strip().casefold(): number
        for number, lesson in enumerate(outline.lessons, start=1)
    }

    def normalize_collection(collection):
        normalized = {}

        for key, value in collection.items():
            if isinstance(key, int) and not isinstance(key, bool):
                number = key

            elif isinstance(key, tuple) and key:
                title = str(key[-1]).strip().casefold()
                number = title_to_number.get(title)

            else:
                title = str(key).strip().casefold()
                number = title_to_number.get(title)

            if number not in title_to_number.values():
                raise ValueError(
                    f"Cannot identify a valid lesson for key: {key}"
                )

            if number in normalized:
                raise ValueError(
                    f"Duplicate saved data for lesson {number}."
                )

            normalized[number] = value

        return normalized

    # Convert lesson data to numbered LessonContent objects.
    normalized_lessons = normalize_collection(lesson_contents)

    saved_lessons = {
        number: (
            value
            if isinstance(value, LessonContent)
            else LessonContent.model_validate(value)
        )
        for number, value in normalized_lessons.items()
    }

    # Convert quiz data to numbered Quiz objects.
    normalized_quizzes = normalize_collection(quizzes)

    saved_quizzes = {
        number: (
            value
            if isinstance(value, Quiz)
            else Quiz.model_validate(value)
        )
        for number, value in normalized_quizzes.items()
    }

    # Collect PDF information from grounded lessons.
    source_documents = {
        (
            lesson.grounding.source_filename,
            lesson.grounding.document_fingerprint,
        )
        for lesson in saved_lessons.values()
        if lesson.grounding is not None
    }

    if len(source_documents) > 1:
        raise ValueError(
            "Saved lessons refer to different source documents."
        )

    source_document = None

    if source_documents:
        filename, fingerprint = next(iter(source_documents))

        source_document = SourceDocument(
            filename=filename,
            fingerprint=fingerprint,
        )

    now = datetime.now(timezone.utc)

    return SavedCourse(
        course_id=course_id,
        created_at=created_at or now,
        updated_at=now,
        topic=topic,
        difficulty=difficulty,
        outline=outline,
        lessons=saved_lessons,
        quizzes=saved_quizzes,
        source_document=source_document,
        selected_lesson=selected_lesson,
    )

