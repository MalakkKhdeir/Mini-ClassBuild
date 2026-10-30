
from classbuild.models.quiz import Quiz


class QuizGrader:
    """Grade a submitted multiple-choice quiz."""

    @staticmethod
    def grade(quiz: Quiz, answers: list[str | None]) -> dict:
        if len(answers) != len(quiz.questions):
            raise ValueError(
                f"Expected {len(quiz.questions)} answers, "
                f"but received {len(answers)}."
            )

        results = []

        for question, answer in zip(quiz.questions, answers):
            is_correct = answer == question.correct_answer

            results.append({
                "question": question.question,
                "selected_answer": answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "explanation": question.explanation,
            })

        score = sum(
            result["is_correct"] for result in results
        )

        return {
            "score": score,
            "total": len(quiz.questions),
            "results": results,
        }
