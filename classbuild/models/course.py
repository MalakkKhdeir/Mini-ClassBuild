
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, PrivateAttr


class OutlineLesson(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    learning_objectives: list[str] = Field(min_length=1)
    summary: str = Field(min_length=1)


class Course(BaseModel):
    model_config = ConfigDict(extra="forbid")

    _course_id: str = PrivateAttr(
        default_factory=lambda: str(uuid4())
    )

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    objectives: list[str] = Field(min_length=1)
    lessons: list[OutlineLesson] = Field(min_length=2, max_length=5)

    @property
    def course_id(self) -> str:
        return self._course_id
