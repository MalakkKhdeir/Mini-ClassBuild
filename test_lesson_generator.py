
from classbuild.llm import GroqClient
from classbuild.services.lesson_generator import LessonGenerator

generator = LessonGenerator(GroqClient())

lesson = generator.generate(
    lesson_title="Python Variables and Data Types",
    learning_objectives=[
        "Understand variables",
        "Identify basic Python data types",
    ],
    difficulty="Beginner",
    course_topic="Introduction to Python",
)

print("TITLE:", lesson.title)
print("SECTIONS:", len(lesson.sections))

for index, section in enumerate(lesson.sections, start=1):
    print(f"\nSection {index}: {section.heading}")
    print("Example:", section.example)

print("\nEXERCISES:", len(lesson.exercises))

for index, exercise in enumerate(lesson.exercises, start=1):
    print(f"{index}. {exercise.task}")
    print("Hint:", exercise.hint)
