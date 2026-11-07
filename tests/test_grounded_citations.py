
import unittest

from pydantic import ValidationError

from classbuild.models.lesson import LessonExercise
from classbuild.services.grounded_lesson_generator import (
    GroundedLessonDraft,
)


class GroundedCitationTests(unittest.TestCase):

    def setUp(self):
        # Create valid exercise objects for the draft.
        self.exercises = [
            LessonExercise.model_construct(),
            LessonExercise.model_construct(),
        ]

        # IDs returned by the RAG retrieval process.
        self.allowed_ids = [
            "chunk_1",
            "chunk_2",
        ]

    def make_draft(self, source_ids):
        """Build a valid grounded lesson draft."""

        return {
            "title": "Introduction to Python",
            "introduction": "Learn Python fundamentals.",
            "sections": [
                {
                    "source_ids": source_ids,
                    "heading": "Variables",
                    "explanation": "Variables store values in Python.",
                    "example": 'name = "Malak"',
                },
                {
                    "source_ids": ["chunk_2"],
                    "heading": "Data Types",
                    "explanation": "Python supports different data types.",
                    "example": "age = 20",
                },
            ],
            "summary": "Python uses variables and data types.",
            "exercises": self.exercises,
            "evidence_relevant": True,
        }

    def test_valid_source_ids_are_accepted(self):
        """The validator should accept IDs found in retrieved passages."""

        data = self.make_draft(["chunk_1"])

        draft = GroundedLessonDraft.model_validate(
            data,
            context={"allowed_ids": self.allowed_ids},
        )

        self.assertEqual(
            draft.sections[0].source_ids,
            ["chunk_1"],
        )

    def test_unknown_source_ids_are_rejected(self):
        """The validator should reject IDs not found in retrieved passages."""

        data = self.make_draft(["fake_chunk_99"])

        with self.assertRaises(ValidationError):
            GroundedLessonDraft.model_validate(
                data,
                context={"allowed_ids": self.allowed_ids},
            )


if __name__ == "__main__":
    unittest.main()
