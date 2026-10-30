from dataclasses import dataclass

DIFFICULTY_LEVELS = ("Beginner", "Intermediate", "Advanced")

DEFAULT_DIFFICULTY = "Beginner"

MIN_LESSONS = 2
MAX_LESSONS = 5
DEFAULT_LESSONS = 3



@dataclass(frozen=True)
class CourseConfig:
    topic: str
    difficulty: str
    lesson_count: int

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "difficulty": self.difficulty,
            "lesson_count": self.lesson_count,
        }


class CourseConfigError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_course_config(topic, difficulty, lesson_count):
    errors = []

    topic = topic.strip()

    if not topic:
        errors.append("Topic cannot be empty")


    if difficulty not in DIFFICULTY_LEVELS:
        errors.append(
            f"Difficulty must be one of: {', '.join(DIFFICULTY_LEVELS)}"
        )


    if isinstance(lesson_count, bool) or not isinstance(lesson_count, int):
        errors.append("Lesson count must be an integer")
    elif not MIN_LESSONS <= lesson_count <= MAX_LESSONS:
        errors.append(
            f"Lesson count must be between {MIN_LESSONS} and {MAX_LESSONS}"
        )

    if errors:
        raise CourseConfigError(errors)

    return CourseConfig(
        topic=topic,
        difficulty=difficulty,
        lesson_count=lesson_count,
    )
