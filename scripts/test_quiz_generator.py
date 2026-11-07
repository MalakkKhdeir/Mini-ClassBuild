
from classbuild.llm import GroqClient
from classbuild.services.quiz_generator import QuizGenerator

lesson_content = {
    "introduction": "Python variables store values.",
    "sections": [
        {
            "heading": "Variables",
            "explanation": "Variables are names assigned to values.",
            "example": "age = 20",
        },
        {
            "heading": "Data Types",
            "explanation": "Python includes integers, strings, floats, and booleans.",
            "example": 'name = "Malak"',
        },
    ],
    "summary": "Variables store values of different data types.",
}

generator = QuizGenerator(GroqClient())

quiz = generator.generate(
    lesson_title="Python Variables and Data Types",
    lesson_content=lesson_content,
    difficulty="Beginner",
    course_topic="Introduction to Python",
)

print("QUESTIONS:", len(quiz.questions))

for index, question in enumerate(quiz.questions, start=1):
    print(f"\nQuestion {index}: {question.question}")
    print("Options:", question.options)
    print("Correct answer:", question.correct_answer)
    print("Explanation:", question.explanation)
