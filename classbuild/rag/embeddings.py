from functools import lru_cache
from typing import Protocol

import numpy as np


# Model configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
DEVICE = "cpu"
BATCH_SIZE = 32


# Base exception
class EmbeddingError(Exception):
    """Base exception for embedding-related errors."""


class EmbeddingInputError(EmbeddingError):
    """Raised when the input texts are invalid."""


class EmbeddingModelUnavailableError(EmbeddingError):
    """Raised when the embedding model cannot be loaded."""


class EmbeddingResourceError(EmbeddingError):
    """Raised when model resources are unavailable."""


class InvalidEmbeddingError(EmbeddingError):
    """Raised when generated embeddings are invalid."""


class TextEncoder(Protocol):
    def encode(
        self,
        sentences: list[str],
        batch_size: int = BATCH_SIZE,
        show_progress_bar: bool = False,
        convert_to_numpy: bool = True,
    ) -> np.ndarray:
        ...

@lru_cache(maxsize=2)
def load_model(
    model_name: str = MODEL_NAME,
    device: str = DEVICE,
) -> TextEncoder:
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(
            model_name,
            device=device,
        )

        dimension = model.get_sentence_embedding_dimension()

        if dimension != EMBEDDING_DIM:
            raise InvalidEmbeddingError(
                f"Expected {EMBEDDING_DIM} dimensions, "
                f"but the model returned {dimension}."
            )

        return model

    except InvalidEmbeddingError:
        raise

    except MemoryError as exc:
        raise EmbeddingResourceError(
            "Not enough memory to load the embedding model."
        ) from exc

    except Exception as exc:
        raise EmbeddingModelUnavailableError(
            "The embedding model could not be loaded. "
            "Check your internet connection and try again."
        ) from exc


def validate_embedding_matrix(
    matrix,
    expected_rows: int | None = None,
    dimension: int = EMBEDDING_DIM,
) -> np.ndarray:

    try:
        matrix = np.asarray(matrix, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise InvalidEmbeddingError(
            "Embedding matrix must contain valid numeric values."
        ) from exc

    if matrix.ndim != 2:
        raise InvalidEmbeddingError(
            "Embedding matrix must be two-dimensional."
        )

    if matrix.shape[1] != dimension:
        raise InvalidEmbeddingError(
            f"Expected {dimension} dimensions, "
            f"but received {matrix.shape[1]}."
        )

    if expected_rows is not None and matrix.shape[0] != expected_rows:
        raise InvalidEmbeddingError(
            f"Expected {expected_rows} rows, "
            f"but received {matrix.shape[0]}."
        )

    if not np.isfinite(matrix).all():
        raise InvalidEmbeddingError(
            "Embedding matrix contains invalid numeric values."
        )

    if np.any(np.linalg.norm(matrix, axis=1) == 0):
        raise InvalidEmbeddingError(
            "Embedding matrix contains a zero-length vector."
        )

    return matrix

class EmbeddingService:

    def __init__(self, model: TextEncoder | None = None):
        self.model = model if model is not None else load_model()

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            raise EmbeddingInputError(
                "At least one text is required."
            )

        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise EmbeddingInputError(
                "All texts must be non-empty strings."
            )

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=BATCH_SIZE,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

        except MemoryError as exc:
            raise EmbeddingResourceError(
                "Not enough memory to generate embeddings."
            ) from exc

        except Exception as exc:
            raise EmbeddingModelUnavailableError(
                "Failed to generate text embeddings."
            ) from exc

        return validate_embedding_matrix(
            embeddings,
            expected_rows=len(texts),
        )

    def embed_query(self, query: str) -> np.ndarray:
        if not isinstance(query, str) or not query.strip():
            raise EmbeddingInputError(
                "The search query cannot be empty."
            )

        embeddings = self.embed_texts([query])

        return embeddings[0]