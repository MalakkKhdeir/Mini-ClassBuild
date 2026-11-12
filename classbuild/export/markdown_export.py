
import re

from pathlib import Path

from classbuild.models.course import Course
from classbuild.models.lesson import LessonContent
from classbuild.models.quiz import Quiz


OPTION_LETTERS = ["A", "B", "C", "D"]

INVALID_FILENAME_CHARS = re.compile(
    r'[<>:"/\\|?*\x00-\x1f]'
)


def _one_line(text: str) -> str:
    """Convert text into a single line."""
    return " ".join(text.split())


def course_filename(topic: str) -> str:
    """Create a safe filename from a course topic."""

    filename = INVALID_FILENAME_CHARS.sub("-", topic)
    filename = filename.strip(" .-_")
    filename = filename[:80].rstrip(" .-_")

    if not filename:
        filename = "course"

    return f"{filename}.md"


def _sources_line(section, lesson: LessonContent) -> str:
    """Build a source citation line for a lesson section."""

    if lesson.grounding is None or not section.source_ids:
        return ""

    sources_by_id = {
        source.chunk_id: source
        for source in lesson.grounding.sources
    }

    citations = []

    for source_id in section.source_ids:
        source = sources_by_id.get(source_id)

        if source is None:
            continue

        citation = (
            f"{source.source_filename}, "
            f"page {source.page_number}"
        )

        if citation not in citations:
            citations.append(citation)

    if not citations:
        return ""

    return "**Sources:** " + "; ".join(citations)


def course_to_markdown(
    outline: Course,
    topic: str,
    lessons: dict[int, LessonContent],
    quizzes: dict[int, Quiz],
) -> str:
    """Convert course content into a Markdown document."""

    lines = []
    answer_key = []

    # Course information.
    lines.extend([
        f"# {topic}",
        "",
        "## Course Description",
        "",
        _one_line(outline.description),
        "",
        "## Learning Objectives",
        "",
    ])

    for objective in outline.objectives:
        lines.append(f"- {_one_line(objective)}")

    # Course outline.
    lines.extend([
        "",
        "## Course Outline",
        "",
    ])

    for number, outline_lesson in enumerate(
        outline.lessons,
        start=1,
    ):
        lines.append(
            f"### Lesson {number}: {outline_lesson.title}"
        )

        for objective in outline_lesson.learning_objectives:
            lines.append(f"- {_one_line(objective)}")

        lines.extend([
            "",
            _one_line(outline_lesson.summary),
            "",
        ])

    # Generated lessons.
    lines.extend([
        "## Lessons",
        "",
    ])

    for number, outline_lesson in enumerate(
        outline.lessons,
        start=1,
    ):
        lesson = lessons.get(number)

        lines.extend([
            f"### Lesson {number}: {outline_lesson.title}",
            "",
        ])

        if lesson is None:
            lines.extend([
                "*This lesson has not been generated yet.*",
                "",
            ])
            continue

        lines.extend([
            _one_line(lesson.introduction),
            "",
        ])

        for section in lesson.sections:
            lines.extend([
                f"#### {section.heading}",
                "",
                _one_line(section.explanation),
                "",
                f"**Example:** {_one_line(section.example)}",
                "",
            ])

            sources_line = _sources_line(section, lesson)

            if sources_line:
                lines.extend([
                    sources_line,
                    "",
                ])

        lines.extend([
            "#### Summary",
            "",
            _one_line(lesson.summary),
            "",
            "#### Exercises",
            "",
        ])

        for index, exercise in enumerate(
            lesson.exercises,
            start=1,
        ):
            lines.append(
                f"{index}. {_one_line(exercise.task)}"
            )
            lines.append(
                f"   - Hint: {_one_line(exercise.hint)}"
            )

        lines.append("")

    # Quizzes.
    lines.extend([
        "## Quizzes",
        "",
    ])

    for number, outline_lesson in enumerate(
        outline.lessons,
        start=1,
    ):
        quiz = quizzes.get(number)

        if quiz is None:
            continue

        lines.extend([
            f"### Quiz: Lesson {number} - {outline_lesson.title}",
            "",
        ])

        for index, question in enumerate(
            quiz.questions,
            start=1,
        ):
            lines.extend([
                f"#### Question {index}",
                "",
                _one_line(question.question),
                "",
            ])

            for letter, option in zip(
                OPTION_LETTERS,
                question.options,
            ):
                lines.append(
                    f"- **{letter}.** {_one_line(option)}"
                )

            lines.append("")

            correct_index = question.options.index(
                question.correct_answer
            )

            correct_letter = OPTION_LETTERS[correct_index]

            answer_key.append(
                f"- Lesson {number}, Question {index}: "
                f"**{correct_letter}**"
            )

            answer_key.append(
                f"  - Explanation: {_one_line(question.explanation)}"
            )

    # Separate answer key.
    if answer_key:
        lines.extend([
            "## Answer Key",
            "",
            *answer_key,
            "",
        ])

    return "\n".join(lines)


def export_markdown(
    outline: Course,
    topic: str,
    lessons: dict[int, LessonContent],
    quizzes: dict[int, Quiz],
    output_dir: Path | str,
) -> Path:
    """Export course content to a Markdown file."""

    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / course_filename(topic)

    content = course_to_markdown(
        outline=outline,
        topic=topic,
        lessons=lessons,
        quizzes=quizzes,
    )

    output_path.write_text(
        content,
        encoding="utf-8",
    )

    return output_path
