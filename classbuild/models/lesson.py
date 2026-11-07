
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
    ValidationInfo,
)


class LessonSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    example: str = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)

    @field_validator("source_ids")
    @classmethod
    def no_duplicate_ids(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("Duplicate source IDs are not allowed.")
        return value


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


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    chunk_id: str = Field(min_length=1)
    source_filename: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    similarity: float = Field(ge=-1.0, le=1.0)
    text: str = Field(min_length=1)


class LessonGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    document_fingerprint: str = Field(min_length=1)
    source_filename: str = Field(min_length=1)
    retrieval_query: str = Field(min_length=1)
    sources: list[SourceReference] = Field(min_length=1)

    @model_validator(mode="after")
    def no_duplicate_sources(self):
        source_ids = [source.chunk_id for source in self.sources]

        if len(source_ids) != len(set(source_ids)):
            raise ValueError(
                "Duplicate source references are not allowed."
            )

        if any(
            source.source_filename != self.source_filename
            for source in self.sources
        ):
            raise ValueError(
                "All sources must belong to the same PDF."
            )

        return self


class LessonContent(Lesson):
    grounding: LessonGrounding | None = None

    @property
    def is_grounded(self) -> bool:
        return self.grounding is not None

    @property
    def cited_pages(self) -> list[int]:
        if self.grounding is None:
            return []

        cited_ids = {
            source_id
            for section in self.sections
            for source_id in section.source_ids
        }

        return sorted({
            source.page_number
            for source in self.grounding.sources
            if source.chunk_id in cited_ids
        })

    @model_validator(mode="after")
    def check_citations(self, info: ValidationInfo):

        grounding = self.grounding

        all_source_ids = [
            source_id
            for section in self.sections
            for source_id in section.source_ids
        ]

        # Ordinary lessons cannot contain PDF citations
        if grounding is None:
            if all_source_ids:
                raise ValueError(
                    "Ordinary lessons cannot contain PDF citations."
                )
            return self

        # Grounded lessons must cite at least one source
        if not all_source_ids:
            raise ValueError(
                "Grounded lessons must cite at least one source."
            )

        available_sources = {
            source.chunk_id: source
            for source in grounding.sources
        }

        cited_ids = set(all_source_ids)
        available_ids = set(available_sources)

        # Every citation must exist
        if not cited_ids.issubset(available_ids):
            raise ValueError(
                "Unknown source ID was cited."
            )

        # Every listed source must be used
        if cited_ids != available_ids:
            raise ValueError(
                "Unused sources are not allowed."
            )

        context = info.context or {}

        # Check the current PDF fingerprint
        expected_fingerprint = context.get(
            "expected_fingerprint"
        )

        if (
            expected_fingerprint is not None
            and grounding.document_fingerprint != expected_fingerprint
        ):
            raise ValueError(
                "Lesson sources belong to a different PDF."
            )

        # Check sources against actual retrieved passages
        allowed_sources = context.get("allowed_sources")

        if allowed_sources is not None:
            allowed_by_id = {
                source.chunk_id: source
                for source in allowed_sources
            }

            for source in grounding.sources:
                allowed_source = allowed_by_id.get(source.chunk_id)

                if (
                    allowed_source is None
                    or source != allowed_source
                ):
                    raise ValueError(
                        "Lesson source does not match retrieved evidence."
                    )

        return self


def validate_lesson(
    data: dict,
    expected_lesson_number: int | None = None,
    expected_title: str | None = None,
    allowed_sources: list[SourceReference] | None = None,
    expected_fingerprint: str | None = None,
) -> LessonContent:

    context = {
        "expected_lesson_number": expected_lesson_number,
        "expected_title": expected_title,
        "allowed_sources": allowed_sources,
        "expected_fingerprint": expected_fingerprint,
    }

    lesson = LessonContent.model_validate(
        data,
        context=context,
    )

    if expected_title is not None:
        if lesson.title.strip().casefold() != expected_title.strip().casefold():
            raise ValueError(
                "Generated lesson title does not match the expected title."
            )

    return lesson
