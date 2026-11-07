from dataclasses import dataclass

import numpy as np

from classbuild.rag.embeddings import (
    MODEL_NAME,
    EMBEDDING_DIM,
    EmbeddingService,
    InvalidEmbeddingError,
    validate_embedding_matrix,
)
from classbuild.rag.models import ProcessedDocument


DEFAULT_TOP_K = 3


class RetrievalError(Exception):
    """Base exception for retrieval-related errors."""


class EmptyQueryError(RetrievalError):
    """Raised when the search query is empty."""


class NoDocumentError(RetrievalError):
    """Raised when no document is available for searching."""


class IndexMismatchError(RetrievalError):
    """Raised when the search index does not match the document."""


@dataclass(frozen=True)
class DocumentIndex:
    document_fingerprint: str
    model_name: str
    chunk_ids: tuple[str, ...]
    embeddings: np.ndarray

    def __post_init__(self):
        matrix = validate_embedding_matrix(
            self.embeddings,
            expected_rows=len(self.chunk_ids),
            dimension=EMBEDDING_DIM,
        )

        matrix.setflags(write=False)
        object.__setattr__(self, "embeddings", matrix)

    @property
    def size(self) -> int:
        return len(self.chunk_ids)


@dataclass(frozen=True)
class SearchResult:
    rank: int
    chunk_id: str
    source_filename: str
    page_number: int
    chunk_index: int
    text: str
    score: float


def cosine_similarity(
    query: np.ndarray,
    matrix: np.ndarray,
) -> np.ndarray:
    query = np.asarray(query, dtype=np.float32)
    matrix = validate_embedding_matrix(matrix)

    if query.ndim != 1 or query.shape[0] != matrix.shape[1]:
        raise InvalidEmbeddingError(
            "Query embedding has an invalid shape."
        )

    query_norm = np.linalg.norm(query)

    if not np.isfinite(query_norm) or query_norm == 0:
        raise InvalidEmbeddingError(
            "Query embedding must be finite and non-zero."
        )

    matrix_norms = np.linalg.norm(matrix, axis=1)

    similarities = np.dot(matrix, query) / (
        matrix_norms * query_norm
    )

    return similarities


def build_index(
    document: ProcessedDocument,
    service: EmbeddingService,
) -> DocumentIndex:
    if not document.chunks:
        raise NoDocumentError(
            "The document has no chunks to index."
        )

    texts = [chunk.text for chunk in document.chunks]
    embeddings = service.embed_texts(texts)

    return DocumentIndex(
        document_fingerprint=document.fingerprint,
        model_name=MODEL_NAME,
        chunk_ids=tuple(
            chunk.chunk_id for chunk in document.chunks
        ),
        embeddings=embeddings,
    )


def check_index(
    index: DocumentIndex,
    document: ProcessedDocument,
) -> None:
    expected_chunk_ids = tuple(
        chunk.chunk_id for chunk in document.chunks
    )

    if index.document_fingerprint != document.fingerprint:
        raise IndexMismatchError(
            "The search index belongs to a different document."
        )

    if index.chunk_ids != expected_chunk_ids:
        raise IndexMismatchError(
            "The search index does not match the document chunks."
        )


def search(
    index: DocumentIndex,
    document: ProcessedDocument,
    query: str,
    service: EmbeddingService,
    top_k: int = DEFAULT_TOP_K,
) -> list[SearchResult]:
    if not isinstance(query, str) or not query.strip():
        raise EmptyQueryError("Search query cannot be empty.")

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k <= 0
    ):
        raise ValueError("top_k must be a positive integer.")

    check_index(index, document)

    query_embedding = service.embed_query(query)

    scores = cosine_similarity(
        query_embedding,
        index.embeddings,
    )

    ranked_indices = np.argsort(-scores, kind="stable")[:top_k]

    chunks_by_id = {
        chunk.chunk_id: chunk
        for chunk in document.chunks
    }

    results = []

    for rank, position in enumerate(ranked_indices, start=1):
        chunk_id = index.chunk_ids[position]
        chunk = chunks_by_id[chunk_id]

        results.append(
            SearchResult(
                rank=rank,
                chunk_id=chunk.chunk_id,
                source_filename=chunk.source_filename,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                score=float(scores[position]),
            )
        )

    return results
