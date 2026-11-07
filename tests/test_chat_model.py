
import unittest

from pydantic import ValidationError

from classbuild.models.chat import ChatMessage
from classbuild.models.lesson import SourceReference


class ChatMessageTests(unittest.TestCase):

    def setUp(self):
        self.source = SourceReference(
            chunk_id="chunk_1",
            source_filename="sample.pdf",
            page_number=1,
            chunk_index=0,
            similarity=0.85,
            text="Python variables store values.",
        )

    def test_user_message_is_accepted(self):
        message = ChatMessage(
            role="user",
            content="What is a variable?",
            mode="pdf",
        )

        self.assertEqual(message.role, "user")
        self.assertEqual(message.cited_pages, [])

    def test_lesson_answer_without_sources_is_accepted(self):
        message = ChatMessage(
            role="assistant",
            content="A variable stores a value.",
            mode="lesson",
        )

        self.assertEqual(message.mode, "lesson")
        self.assertFalse(message.sources)

    def test_pdf_answer_with_valid_citation_is_accepted(self):
        message = ChatMessage(
            role="assistant",
            content="Variables store values. [p1-c0]",
            mode="pdf",
            status="answered",
            sources=[self.source],
            document_fingerprint="fingerprint_123",
        )

        self.assertEqual(message.cited_pages, [1])

    def test_pdf_answer_without_fingerprint_is_rejected(self):
        with self.assertRaises(ValidationError):
            ChatMessage(
                role="assistant",
                content="Variables store values. [p1-c0]",
                mode="pdf",
                sources=[self.source],
            )

    def test_pdf_answer_without_sources_is_rejected(self):
        with self.assertRaises(ValidationError):
            ChatMessage(
                role="assistant",
                content="Variables store values.",
                mode="pdf",
                document_fingerprint="fingerprint_123",
            )

    def test_unknown_citation_marker_is_rejected(self):
        with self.assertRaises(ValidationError):
            ChatMessage(
                role="assistant",
                content="Variables store values. [p5-c9]",
                mode="pdf",
                sources=[self.source],
                document_fingerprint="fingerprint_123",
            )

    def test_insufficient_evidence_without_sources_is_accepted(self):
        message = ChatMessage(
            role="assistant",
            content="The PDF does not contain enough information.",
            mode="pdf",
            status="insufficient_evidence",
            document_fingerprint="fingerprint_123",
        )

        self.assertEqual(
            message.status,
            "insufficient_evidence",
        )
        self.assertEqual(message.cited_pages, [])


if __name__ == "__main__":
    unittest.main()
