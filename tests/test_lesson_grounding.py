
import unittest

from pydantic import ValidationError

from classbuild.models.lesson import (
    LessonContent,
    LessonGrounding,
    LessonSection,
    SourceReference,
)


class LessonGroundingTests(unittest.TestCase):

    def setUp(self):
        self.source = SourceReference(
            chunk_id="chunk_1",
            source_filename="sample.pdf",
            page_number=1,
            chunk_index=0,
            similarity=0.85,
            text="Python variables store values.",
        )

        self.grounding = LessonGrounding(
            document_fingerprint="fingerprint_123",
            source_filename="sample.pdf",
            retrieval_query="Python variables",
            sources=[self.source],
        )

        self.valid_data = {

            "title": "Python Variables",
            "introduction": "Learn about Python variables.",
            "sections": [
                {
                    "heading": "Variables",
                    "explanation": "Variables store values.",
                    "example": 'name = "Malak"',
                    "source_ids": ["chunk_1"],
                },
                {
                    "heading": "Assignment",
                    "explanation": "Assignment gives a value to a variable.",
                    "example": "age = 20",
                    "source_ids": ["chunk_1"],
                },
            ],
            "summary": "Variables store values in Python.",
            "exercises": [
               {
                 "task": "Explain what a variable is.",
                 "hint": "Think about stored values.",
                },
                {
                     "task": "Write a Python variable assignment.",
                     "hint": "Use the equals sign.",
                 },
         ],
            "grounding": self.grounding.model_dump(),
        }

    def test_valid_grounded_lesson_is_accepted(self):
        lesson = LessonContent.model_validate(
            self.valid_data
        )

        self.assertTrue(lesson.is_grounded)
        self.assertEqual(lesson.cited_pages, [1])

    def test_grounded_lesson_without_citations_is_rejected(self):
        data = self.valid_data.copy()
        data["sections"] = [
            {
                "heading": "Variables",
                "explanation": "Variables store values.",
                "example": 'name = "Malak"',
                "source_ids": [],
            },
            {
                "heading": "Assignment",
                "explanation": "Assignment gives a value.",
                "example": "age = 20",
                "source_ids": [],
            },
        ]

        with self.assertRaises(ValidationError):
            LessonContent.model_validate(data)

    def test_unknown_source_id_is_rejected(self):
        data = self.valid_data.copy()
        data["sections"] = [
            {
                "heading": "Variables",
                "explanation": "Variables store values.",
                "example": 'name = "Malak"',
                "source_ids": ["fake_chunk"],
            },
            {
                "heading": "Assignment",
                "explanation": "Assignment gives a value.",
                "example": "age = 20",
                "source_ids": ["chunk_1"],
            },
        ]

        with self.assertRaises(ValidationError):
            LessonContent.model_validate(data)

    def test_unused_source_is_rejected(self):
        data = self.valid_data.copy()

        unused_source = SourceReference(
            chunk_id="chunk_2",
            source_filename="sample.pdf",
            page_number=2,
            chunk_index=1,
            similarity=0.80,
            text="Python data types.",
        )

        grounding = self.grounding.model_copy(
            update={
                "sources": [
                    self.source,
                    unused_source,
                ]
            }
        )

        data["grounding"] = grounding.model_dump()

        with self.assertRaises(ValidationError):
            LessonContent.model_validate(data)

    def test_wrong_fingerprint_is_rejected(self):
        with self.assertRaises(ValidationError):
            LessonContent.model_validate(
                self.valid_data,
                context={
                    "expected_fingerprint": "different_pdf"
                },
            )

    def test_source_not_in_retrieved_evidence_is_rejected(self):
        different_source = self.source.model_copy(
            update={"text": "Different source content."}
        )

        with self.assertRaises(ValidationError):
            LessonContent.model_validate(
                self.valid_data,
                context={
                    "allowed_sources": [different_source]
                },
            )


if __name__ == "__main__":
    unittest.main()
