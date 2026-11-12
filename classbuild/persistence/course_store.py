
import json
import os

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from classbuild.persistence.saved_course import (
    APP_NAME,
    COURSE_ID_PATTERN,
    SCHEMA_VERSION,
    SavedCourse,
)


DEFAULT_SAVE_DIR = Path("saved_courses")
SAVE_DIR_ENV = "MINICLASSBUILD_SAVE_DIR"
MAX_COURSE_FILE_BYTES = 2 * 1024 * 1024


class CourseStorageError(Exception):
    """Base exception for course storage errors."""


class InvalidCourseIdError(CourseStorageError):
    """Raised when a course ID is invalid."""


class CourseNotFoundError(CourseStorageError):
    """Raised when a saved course does not exist."""


class CourseFileTooLargeError(CourseStorageError):
    """Raised when a course file exceeds the size limit."""


class CorruptedCourseFileError(CourseStorageError):
    """Raised when a saved course file is corrupted or invalid."""


class UnsupportedSchemaVersionError(CourseStorageError):
    """Raised when a saved course uses an unsupported schema version."""


@dataclass(frozen=True)
class SavedCourseSummary:
    course_id: str
    topic: str
    difficulty: str
    lesson_count: int
    created_at: datetime
    updated_at: datetime
    source_filename: str | None = None


class CourseStore:
    def __init__(self, save_dir: Path | str | None = None):
        if save_dir is None:
            save_dir = os.getenv(
                SAVE_DIR_ENV,
                str(DEFAULT_SAVE_DIR),
            )

        self.save_dir = Path(save_dir).expanduser().resolve()
        self.save_dir.mkdir(parents=True, exist_ok=True)


    def _course_path(self, course_id: str) -> Path:
        if not isinstance(course_id, str):
            raise InvalidCourseIdError("Course ID must be a string.")

        if not COURSE_ID_PATTERN.fullmatch(course_id):
            raise InvalidCourseIdError("Invalid course ID.")

        path = (self.save_dir / f"{course_id}.json").resolve()

        if path.parent != self.save_dir:
            raise InvalidCourseIdError(
                "Course path must stay inside the save directory."
            )

        return path

    
    def save(self, course: SavedCourse) -> Path:
        if not isinstance(course, SavedCourse):
            raise TypeError("Expected a SavedCourse object.")

        path = self._course_path(course.course_id)

        data = course.model_dump_json(
            indent=2,
        )

        encoded_data = data.encode("utf-8")

        if len(encoded_data) > MAX_COURSE_FILE_BYTES:
            raise CourseFileTooLargeError(
                "Course file exceeds the 2 MB size limit."
            )

        temp_path = path.with_suffix(".tmp")

        try:
            with temp_path.open("wb") as file:
                file.write(encoded_data)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, path)

        finally:
            if temp_path.exists():
                temp_path.unlink()

        return path

    
    def load(self, course_id: str) -> SavedCourse:
        path = self._course_path(course_id)

        if not path.exists():
            raise CourseNotFoundError(
                f"Course not found: {course_id}"
            )

        try:
            file_size = path.stat().st_size

            if file_size > MAX_COURSE_FILE_BYTES:
                raise CourseFileTooLargeError(
                    "Course file exceeds the 2 MB size limit."
                )

            data = json.loads(path.read_text(encoding="utf-8"))

            if not isinstance(data, dict):
                raise CorruptedCourseFileError(
                    "Course file must contain a JSON object."
                )

            schema_version = data.get("schema_version")

            if schema_version != SCHEMA_VERSION:
                raise UnsupportedSchemaVersionError(
                    f"Unsupported schema version: {schema_version}"
                )

            course = SavedCourse.model_validate(data)

            if course.course_id != course_id:
                raise CorruptedCourseFileError(
                    "Course ID does not match the filename."
                )

            return course

        except (
            CourseFileTooLargeError,
            UnsupportedSchemaVersionError,
            CorruptedCourseFileError,
        ):
            raise

        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError) as exc:
            raise CorruptedCourseFileError(
                "Course file is corrupted or contains invalid data."
            ) from exc

        except OSError as exc:
            raise CorruptedCourseFileError(
                "Could not read the saved course file."
            ) from exc


    def update(self, course: SavedCourse) -> Path:
        if not isinstance(course, SavedCourse):
            raise TypeError("Expected a SavedCourse object.")

        existing_course = self.load(course.course_id)

        updated_course = course.model_copy(
            update={
                "created_at": existing_course.created_at,
                "updated_at": datetime.now().astimezone(),
            }
        )

        updated_course.check_consistency()

        return self.save(updated_course)


    def list_courses(self) -> list[SavedCourseSummary]:
        summaries = []

        for path in sorted(self.save_dir.glob("*.json")):
            course_id = path.stem

            try:
                course = self.load(course_id)
            except CourseStorageError:
                continue

            summaries.append(
                SavedCourseSummary(
                    course_id=course.course_id,
                    topic=course.topic,
                    difficulty=course.difficulty,
                    lesson_count=len(course.outline.lessons),
                    created_at=course.created_at,
                    updated_at=course.updated_at,
                    source_filename=(
                        course.source_document.filename
                        if course.source_document
                        else None
                    ),
                )
            )

        return summaries


    def delete(self, course_id: str) -> None:
        path = self._course_path(course_id)

        if not path.exists():
            raise CourseNotFoundError(
                f"Course not found: {course_id}"
            )

        try:
            path.unlink()
        except OSError as exc:
            raise CourseStorageError(
                "Could not delete the saved course."
            ) from exc

        





