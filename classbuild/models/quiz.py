
from pydantic import BaseModel, Field, ConfigDict, model_validator


class QuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_answer: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_correct_answer(self):
        if self.correct_answer not in self.options:
            raise ValueError(
                "The correct answer must match one of the four options."
            )
        return self


class Quiz(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[QuizQuestion] = Field(min_length=5, max_length=5)
