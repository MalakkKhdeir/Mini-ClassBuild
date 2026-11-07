
from dataclasses import dataclass
from typing import Callable

from classbuild.rag.models import ProcessedDocument

from classbuild.rag.pdf_processor import (
    process_pdf,
    fingerprint,
    PDFProcessingError,
)
from classbuild.services.lesson_state import (
    remove_stale_grounded_lessons,
)


DOC_KEY = "rag_document"
DOC_STATUS_KEY = "rag_document_status"

COURSE_MATERIAL_KEY = "course_material_fingerprint"

INDEX_KEY = "rag_search_index"
SEARCH_KEY = "rag_search_results"


@dataclass
class MaterialStatus:
    document: ProcessedDocument | None = None
    error: str | None = None
    processed_now: bool = False


def sync_learning_material(
    state: dict,
    upload: tuple[str, bytes] | None,
    processor: Callable | None = None,
) -> MaterialStatus:
    """Synchronize the uploaded PDF with the session state."""

    # No file uploaded
    if upload is None:
        clear_learning_material(state)
        return MaterialStatus()

    filename, data = upload

    # Identify the uploaded file
    file_fingerprint = fingerprint(data)
    identity = (filename, file_fingerprint)

    # Check whether this is the same file
    current_document = state.get(DOC_KEY)
    current_identity = state.get("_rag_document_identity")

    if current_identity == identity:
        return MaterialStatus(
            document=current_document,
            error=state.get(DOC_STATUS_KEY),
            processed_now=False,
        )

    # Remove previous document and its derived data
    clear_learning_material(state)

    # Use the real processor unless another one was injected
    if processor is None:
        processor = process_pdf

    try:
        document = processor(filename, data)

        remove_stale_grounded_lessons(

             state.get("lesson_contents", {}),
            document.fingerprint,
            state.get("quizzes", {}),
            state.get("quiz_results", {}),
            state.get("quiz_attempts", {}),
        )

        state[DOC_KEY] = document
        state[DOC_STATUS_KEY] = None
        state["_rag_document_identity"] = identity

        return MaterialStatus(
            document=document,
            error=None,
            processed_now=True,
        )

    except PDFProcessingError as exc:
        error_message = str(exc)

    except Exception:
        error_message = "An unexpected error occurred while processing the PDF."

    state[DOC_KEY] = None
    state[DOC_STATUS_KEY] = error_message
    state["_rag_document_identity"] = identity

    return MaterialStatus(
        document=None,
        error=error_message,
        processed_now=True,
    )


def clear_learning_material(state: dict) -> None:
    """Remove the loaded document and all data derived from it."""

    state.pop(DOC_KEY, None)
    state.pop(DOC_STATUS_KEY, None)
    state.pop("_rag_document_identity", None)

    state.pop(COURSE_MATERIAL_KEY, None)
    state.pop(INDEX_KEY, None)
    state.pop(SEARCH_KEY, None)


def attach_material_to_course(state: dict) -> None:
    """Attach the currently loaded PDF to the generated course."""

    document = state.get(DOC_KEY)

    if document is None:
        state.pop(COURSE_MATERIAL_KEY, None)
        return

    state[COURSE_MATERIAL_KEY] = document.fingerprint


def material_for_course(state: dict) -> ProcessedDocument | None:
    """Return the PDF only if it matches the course fingerprint."""

    document = state.get(DOC_KEY)
    course_fingerprint = state.get(COURSE_MATERIAL_KEY)

    if document is None or course_fingerprint is None:
        return None

    if document.fingerprint != course_fingerprint:
        return None

    return document
