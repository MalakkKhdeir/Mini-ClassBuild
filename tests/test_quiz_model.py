
import pytest
from pydantic import ValidationError

from classbuild.models.quiz import Quiz


def make_valid_quiz_data():
    return {
        "questions": [
            {
                "question": f"Question {i}: Which option is correct?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "Option A is correct for this example.",
            }
            for i in range(1, 6)
        ]
    }


def test_quiz_has_five_questions():
    quiz = Quiz.model_validate(make_valid_quiz_data())

    assert len(quiz.questions) == 5


def test_each_question_has_four_options():
    quiz = Quiz.model_validate(make_valid_quiz_data())

    assert all(len(question.options) == 4 for question in quiz.questions)


def test_correct_answer_matches_an_option():
    quiz = Quiz.model_validate(make_valid_quiz_data())

    assert all(
        question.correct_answer in question.options
        for question in quiz.questions
    )


def test_quiz_rejects_fewer_than_five_questions():
    data = make_valid_quiz_data()
    data["questions"] = data["questions"][:4]

    with pytest.raises(ValidationError):
        Quiz.model_validate(data)


from classbuild.services.quiz_grader import QuizGrader


def test_quiz_grader_scores_three_out_of_five():
    quiz = Quiz.model_validate(make_valid_quiz_data())

    answers = ["A", "B", "A", "C", "A"]
    result = QuizGrader.grade(quiz, answers)

    assert result["score"] == 3
    assert result["total"] == 5
    assert sum(
        item["is_correct"] for item in result["results"]
    ) == 3
