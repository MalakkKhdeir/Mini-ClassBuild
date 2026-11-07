
import re

from classbuild.rag.models import DocumentChunk


DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150


def _validate(chunk_size, chunk_overlap):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")


def _find_cut(text, start, end):
    # Prefer paragraph boundaries
    cut = text.rfind("\n\n", start, end)

    if cut > start:
        return cut

    # Then prefer sentence boundaries
    matches = list(re.finditer(r"[.!?؟]\s+", text[start:end]))

    if matches:
        return start + matches[-1].end()

    # Otherwise, prefer a word boundary
    cut = text.rfind(" ", start, end)

    if cut > start:
        return cut

    return end


def _next_start(text, cut, chunk_overlap):
    next_start = max(0, cut - chunk_overlap)

    # Move to a word boundary
    while next_start < cut and text[next_start].isspace():
        next_start += 1

    return next_start


def chunk_text(
    text,
    chunk_size=DEFAULT_CHUNK_SIZE,
    chunk_overlap=DEFAULT_CHUNK_OVERLAP
):
    _validate(chunk_size, chunk_overlap)

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            end = _find_cut(text, start, end)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = _next_start(text, end, chunk_overlap)

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def chunk_pages(
    pages,
    source_filename,
    chunk_size=DEFAULT_CHUNK_SIZE,
    chunk_overlap=DEFAULT_CHUNK_OVERLAP
):
    _validate(chunk_size, chunk_overlap)

    document_chunks = []

    for page in pages:
        page_number = (
            page.page_number
            if hasattr(page, "page_number")
            else page["page_number"]
        )

        text = (
            page.text
            if hasattr(page, "text")
            else page["text"]
        )

        page_chunks = chunk_text(
            text,
            chunk_size,
            chunk_overlap
        )

        for index, chunk in enumerate(page_chunks):
            document_chunk = DocumentChunk(
                chunk_id=f"p{page_number}-c{index + 1}",
                source_filename=source_filename,
                page_number=page_number,
                chunk_index=index,
                text=chunk
            )

            document_chunks.append(document_chunk)

    return document_chunks
