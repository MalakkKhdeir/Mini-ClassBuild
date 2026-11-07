import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from classbuild.models.lesson import SourceReference


CITATION_MARKER = re.compile(r"\[p(\d+)-c(\d+)\]")

class ChatMessage(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    mode: Literal["lesson", "pdf"]
    status: Literal["answered", "insufficient_evidence"] = "answered"
    sources: list[SourceReference] = Field(default_factory=list)
    document_fingerprint: str | None = None
    truncated: bool = False

    @property
    def cited_pages(self) -> list[int]:
        return sorted({
            source.page_number
            for source in self.sources
        })

    @model_validator(mode="after")
    def check_sources(self):
        # User messages cannot contain citations.
        if self.role == "user":
            if self.sources:
                raise ValueError(
                    "User messages cannot contain sources."
                )
            if self.document_fingerprint is not None:
                raise ValueError(
                    "User messages cannot contain a PDF fingerprint."
                )
            if self.status != "answered":
                raise ValueError(
                    "User messages must have answered status."
                )
            return self

        # Lesson-mode answers cannot contain PDF citations.
        if self.mode == "lesson":
            if self.sources:
                raise ValueError(
                    "Lesson-mode answers cannot contain PDF sources."
                )
            if self.document_fingerprint is not None:
                raise ValueError(
                    "Lesson-mode answers cannot contain a PDF fingerprint."
                )
            if self.status != "answered":
                raise ValueError(
                    "Lesson-mode answers must have answered status."
                )
            return self

        # PDF-mode assistant answers must identify their document.
        if not self.document_fingerprint:
            raise ValueError(
                "PDF-mode answers must include a document fingerprint."
            )

        # Insufficient-evidence replies must not cite sources.
        if self.status == "insufficient_evidence":
            if self.sources:
                raise ValueError(
                    "Insufficient-evidence answers cannot cite sources."
                )
            return self

        # Answered PDF messages must cite at least one source.
        if not self.sources:
            raise ValueError(
                "Answered PDF messages must cite at least one source."
            )

        source_ids = [
            source.chunk_id
            for source in self.sources
        ]

        if len(source_ids) != len(set(source_ids)):
            raise ValueError(
                "Duplicate sources are not allowed."
            )

        # Every inline citation must match a listed source.
        allowed_markers = {
            f"[p{source.page_number}-c{source.chunk_index}]"
            for source in self.sources
        }

        found_markers = set(
            CITATION_MARKER.findall(self.content)
        )

        actual_markers = {
            f"[p{page}-c{chunk}]"
            for page, chunk in found_markers
        }

        if not actual_markers.issubset(allowed_markers):
            raise ValueError(
                "Answer contains an unknown citation marker."
            )

        return self
