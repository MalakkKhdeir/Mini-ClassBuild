
from pydantic import BaseModel, Field, computed_field, model_validator


class PageText(BaseModel):
    page_number: int = Field(ge=1)
    text: str


class DocumentChunk(BaseModel):
    chunk_id: str
    source_filename: str
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str

    @computed_field
    @property
    def char_count(self) -> int:
        return len(self.text)


class ProcessedDocument(BaseModel):
    filename: str
    fingerprint: str

    page_count: int = Field(ge=1)
    word_count: int = Field(ge=0)
    char_count: int = Field(ge=0)

    empty_pages: list[int] = Field(default_factory=list)

    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)

    chunks: list[DocumentChunk]

    @computed_field
    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @model_validator(mode="after")
    def check_consistency(self):

        chunk_ids = [chunk.chunk_id for chunk in self.chunks]

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("Duplicate chunk IDs are not allowed.")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size.")

        if any(page > self.page_count for page in self.empty_pages):
            raise ValueError("Empty page number exceeds total pages.")

        return self

    def get_chunk(self, chunk_id: str):
        for chunk in self.chunks:
            if chunk.chunk_id == chunk_id:
                return chunk

        return None
