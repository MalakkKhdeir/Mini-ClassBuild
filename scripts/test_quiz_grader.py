
from classbuild.models.quiz import Quiz
from classbuild.services.quiz_grader import QuizGrader

data = {
    "questions": [
        {
            "question": f"Question {i}",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "A is the correct answer.",
        }
        for i in range(1, 6)
    ]
}

quiz = Quiz.model_validate(data)

# Three correct answers and two incorrect answers.
answers = ["A", "B", "A", "C", "A"]

result = QuizGrader.grade(quiz, answers)

print("SCORE:", result["score"])
print("TOTAL:", result["total"])
print("CORRECT:", sum(r["is_correct"] for r in result["results"]))
print("FIRST EXPLANATION:", result["results"][0]["explanation"])
