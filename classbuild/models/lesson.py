
from pydantic import BaseModel, Field, ConfigDict


class LessonSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    example: str = Field(min_length=1)


class LessonExercise(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    hint: str = Field(min_length=1)


class Lesson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    introduction: str = Field(min_length=1)
    sections: list[LessonSection] = Field(min_length=2, max_length=4)
    summary: str = Field(min_length=1)
    exercises: list[LessonExercise] = Field(min_length=2, max_length=2)
