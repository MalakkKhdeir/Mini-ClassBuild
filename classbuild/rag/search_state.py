
from dataclasses import dataclass

from classbuild.rag.document_state import (
    DOC_KEY,
    INDEX_KEY,
    SEARCH_KEY,
)

from classbuild.rag.embeddings import (
    EmbeddingService,
    MODEL_NAME,
)

from classbuild.rag.models import ProcessedDocument

from classbuild.rag.retriever import (
    DEFAULT_TOP_K,
    DocumentIndex,
    SearchResult,
    NoDocumentError,
    EmptyQueryError,
    build_index,
    check_index,
    search,
)

@dataclass
class SearchOutcome:
    query: str
    results: list[SearchResult]
    index_built_now: bool

def has_current_index(
    state: dict,
    document: ProcessedDocument,
    service: EmbeddingService,
) -> bool:

    index = state.get(INDEX_KEY)

    if not isinstance(index, DocumentIndex):
        return False

    expected_chunk_ids = tuple(
        chunk.chunk_id for chunk in document.chunks
    )

    service_model_name = getattr(service, "model_name", MODEL_NAME)

    if index.document_fingerprint != document.fingerprint:
        return False

    if index.chunk_ids != expected_chunk_ids:
        return False

    if index.model_name != service_model_name:
        return False

    return True

def get_or_build_index(
    state: dict,
    document: ProcessedDocument,
    service: EmbeddingService,
) -> DocumentIndex:

    if has_current_index(state, document, service):
        return state[INDEX_KEY]

    index = build_index(document, service)

    state[INDEX_KEY] = index
    state.pop(SEARCH_KEY, None)

    return index

def run_search(
    state: dict,
    query: str,
    service: EmbeddingService | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> SearchOutcome:

    state.pop(SEARCH_KEY, None)

    document = state.get(DOC_KEY)

    if document is None:
        raise NoDocumentError(
            "Upload a PDF before searching."
        )

    if not isinstance(query, str) or not query.strip():
        raise EmptyQueryError(
            "Search query cannot be empty."
        )

    if service is None:
        service = EmbeddingService()

    had_current_index = has_current_index(
        state,
        document,
        service,
    )

    index = get_or_build_index(
        state,
        document,
        service,
    )

    results = search(
        index=index,
        document=document,
        query=query,
        service=service,
        top_k=top_k,
    )

    outcome = SearchOutcome(
        query=query.strip(),
        results=results,
        index_built_now=not had_current_index,
    )

    state[SEARCH_KEY] = {
        "fingerprint": document.fingerprint,
        "outcome": outcome,
    }

    return outcome

def current_results(state: dict) -> SearchOutcome | None:

    saved_search = state.get(SEARCH_KEY)

    if not isinstance(saved_search, dict):
        return None

    document = state.get(DOC_KEY)

    if document is None:
        return None

    if saved_search.get("fingerprint") != document.fingerprint:
        return None

    outcome = saved_search.get("outcome")

    if not isinstance(outcome, SearchOutcome):
        return None

    return outcome
