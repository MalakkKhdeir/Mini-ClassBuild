
import hashlib
import io
import re
import unicodedata

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from classbuild.rag.chunker import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    chunk_pages,
)

from classbuild.rag.models import (
    PageText,
    ProcessedDocument,
)


# Maximum allowed PDF size
MAX_FILE_SIZE_MB = 10


# =========================
# Custom Exceptions
# =========================

class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""


class InvalidFileError(PDFProcessingError):
    """Raised when the uploaded file is not a valid PDF."""

    pass


class FileTooLargeError(PDFProcessingError):
    """Raised when the PDF exceeds the maximum file size."""

    pass


class EmptyFileError(PDFProcessingError):
    """Raised when the uploaded file is empty."""

    pass


class CorruptedPDFError(PDFProcessingError):
    """Raised when the PDF cannot be read."""

    pass


class EncryptedPDFError(PDFProcessingError):
    """Raised when the PDF is password-protected."""

    pass


class NoExtractableTextError(PDFProcessingError):
    """Raised when no text can be extracted from the PDF."""

    pass


# =========================
# Fingerprint
# =========================

def fingerprint(data: bytes) -> str:
    """Generate a SHA-256 fingerprint for the PDF data."""

    return hashlib.sha256(data).hexdigest()


# =========================
# PDF Upload Validation
# =========================

def validate_pdf_upload(filename: str, data: bytes) -> None:
    """Validate an uploaded PDF file."""

    if not filename.lower().endswith(".pdf"):
        raise InvalidFileError("Only PDF files are allowed.")

    if not data:
        raise EmptyFileError("The uploaded PDF file is empty.")

    max_size = MAX_FILE_SIZE_MB * 1024 * 1024

    if len(data) > max_size:
        raise FileTooLargeError(
            f"PDF file size must not exceed {MAX_FILE_SIZE_MB} MB."
        )

    # Check PDF signature near the beginning of the file
    if b"%PDF-" not in data[:1024]:
        raise InvalidFileError("The uploaded file is not a valid PDF.")


# =========================
# Text Cleaning
# =========================

def clean_text(text: str) -> str:
    """Normalize and clean extracted PDF text."""

    # Normalize Unicode characters
    text = unicodedata.normalize("NFC", text)

    # Unify line breaks
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove control characters except tabs and newlines
    text = "".join(
        char
        for char in text
        if unicodedata.category(char) != "Cc"
        or char in "\n\t"
    )

    # Collapse repeated inline spaces while preserving indentation
    cleaned_lines = []

    for line in text.split("\n"):
        indentation = len(line) - len(line.lstrip(" \t"))

        leading = line[:indentation]
        content = line[indentation:]

        content = re.sub(r"[ \t]{2,}", " ", content)

        cleaned_lines.append(leading + content)

    text = "\n".join(cleaned_lines)

    # Keep at most one blank line between paragraphs
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =========================
# PDF Page Extraction
# =========================

def extract_pages(data: bytes) -> list[PageText]:
    """Extract and clean text from every PDF page."""

    try:
        reader = PdfReader(io.BytesIO(data))

        # Try opening encrypted PDFs with an empty password
        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")

                if not decrypted:
                    raise EncryptedPDFError(
                        "This PDF is password-protected."
                    )

            except EncryptedPDFError:
                raise

            except Exception as exc:
                raise EncryptedPDFError(
                    "Unable to unlock this password-protected PDF."
                ) from exc

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):

            try:
                extracted_text = page.extract_text() or ""
                cleaned_text = clean_text(extracted_text)

            except Exception:
                # Keep the page even if text extraction fails
                cleaned_text = ""

            pages.append(
                PageText(
                    page_number=page_number,
                    text=cleaned_text
                )
            )

        return pages

    except EncryptedPDFError:
        raise

    except (PdfReadError, OSError, ValueError) as exc:
        raise CorruptedPDFError(
            "The PDF file is corrupted or cannot be read."
        ) from exc

    except Exception as exc:
        raise CorruptedPDFError(
            "An error occurred while reading the PDF file."
        ) from exc


# =========================
# Full PDF Processing Pipeline
# =========================

def process_pdf(
    filename: str,
    data: bytes,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> ProcessedDocument:
    """Validate, extract, clean, and chunk an uploaded PDF."""

    # 1. Validate uploaded file
    validate_pdf_upload(filename, data)

    # 2. Extract text from all pages
    pages = extract_pages(data)

    # 3. Check whether any page contains extractable text
    if not any(page.text.strip() for page in pages):
        raise NoExtractableTextError(
            "No extractable text was found in this PDF. "
            "Scanned PDFs without a text layer are not supported."
        )

    # 4. Calculate document statistics
    all_text = "\n".join(page.text for page in pages)

    word_count = len(re.findall(r"\w+", all_text, flags=re.UNICODE))
    char_count = sum(len(page.text) for page in pages)

    # 5. Identify empty pages
    empty_pages = [
        page.page_number
        for page in pages
        if not page.text.strip()
    ]

    # 6. Split pages into DocumentChunk objects
    chunks = chunk_pages(
        pages=pages,
        source_filename=filename,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    # 7. Build the final processed document
    return ProcessedDocument(
        filename=filename,
        fingerprint=fingerprint(data),
        page_count=len(pages),
        word_count=word_count,
        char_count=char_count,
        empty_pages=empty_pages,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunks=chunks
    )
