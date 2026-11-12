from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    number: int
    name: str
    category: str
    checks: str
    tests: list[str]


T = "tests."


SCENARIOS: list[Scenario] = [
    Scenario(
        number=1,
        name="Course accepts valid lesson count",
        category="outlines",
        checks="A course accepts between two and five lessons.",
        tests=[
            T + "test_course_model.test_course_accepts_two_lessons",
            T + "test_course_model.test_course_rejects_fewer_than_two_lessons",
            T + "test_course_model.test_course_rejects_more_than_five_lessons",
        ],
    ),
    Scenario(
        number=2,
        name="Course lesson titles are unique",
        category="outlines",
        checks="A course rejects duplicate lesson titles.",
        tests=[
            T + "test_course_model.test_course_rejects_duplicate_lesson_titles",
            T + "test_course_model.test_course_accepts_different_lesson_titles",
        ],
    ),
        Scenario(
        number=3,
        name="Lesson structure validation",
        category="lessons",
        checks="A lesson must contain the required sections and a valid title.",
        tests=[
            T + "test_lesson_model.test_lesson_has_required_sections_and_exercises",
            T + "test_lesson_model.test_lesson_rejects_missing_title",
        ],
    ),
    Scenario(
        number=4,
        name="Structured output handles invalid JSON",
        category="structured_output",
        checks="Invalid JSON is retried once, then rejected if still invalid.",
        tests=[
            T + "test_structured_output.test_request_retries_once_after_invalid_json",
            T + "test_structured_output.test_request_raises_after_two_invalid_responses",
            T + "test_structured_output.test_request_does_not_retry_other_errors",
        ],
    ),
    Scenario(
        number=5,
        name="Structured output schema validation",
        category="structured_output",
        checks="The structured output schema is compatible and validation errors are described.",
        tests=[
            T + "test_structured_output.test_strict_schema_removes_unsupported_keywords",
            T + "test_structured_output.test_describe_validation_error",
        ],
    ),
        Scenario(
        number=6,
        name="Grounded citations validation",
        category="rag_citations",
        checks="Only known and valid source IDs are accepted.",
        tests=[
            T + "test_grounded_citations.GroundedCitationTests.test_valid_source_ids_are_accepted",
            T + "test_grounded_citations.GroundedCitationTests.test_unknown_source_ids_are_rejected",
        ],
    ),
    Scenario(
        number=7,
        name="Grounded lesson source validation",
        category="rag_citations",
        checks="Grounded lessons must use valid sources from the retrieved evidence.",
        tests=[
            T + "test_lesson_grounding.LessonGroundingTests.test_valid_grounded_lesson_is_accepted",
            T + "test_lesson_grounding.LessonGroundingTests.test_source_not_in_retrieved_evidence_is_rejected",
            T + "test_lesson_grounding.LessonGroundingTests.test_unknown_source_id_is_rejected",
            T + "test_lesson_grounding.LessonGroundingTests.test_unused_source_is_rejected",
            T + "test_lesson_grounding.LessonGroundingTests.test_wrong_fingerprint_is_rejected",
        ],
    ),
    Scenario(
        number=8,
        name="Grounded lesson retrieval and citations",
        category="rag_citations",
        checks="Evidence retrieval and citation validation work correctly.",
        tests=[
            T + "test_grounded_lessons.TestSelectEvidence.test_accepts_passage_at_threshold",
            T + "test_grounded_lessons.TestSelectEvidence.test_keeps_only_relevant_passages",
            T + "test_grounded_lessons.TestBuildRetrievalQuery.test_includes_course_and_lesson_context",
            T + "test_grounded_lessons.TestBuildGroundedPrompt.test_includes_retrieved_passages",
            T + "test_grounded_lessons.TestCitationValidation.test_rejects_source_from_another_pdf",
            T + "test_grounded_lessons.TestCitationValidation.test_rejects_tampered_source_text",
            T + "test_grounded_lessons.TestCitationValidation.test_rejects_unknown_source_id",
        ],
    ),
        Scenario(
        number=9,
        name="Grounded lesson generation",
        category="lessons",
        checks="Grounded lesson generation uses valid retrieval evidence.",
        tests=[
            T + "test_grounded_lessons.TestDraftToLesson.test_sources_use_real_retrieval_data",
            T + "test_grounded_lessons.TestFormatReferencePassages.test_formats_passage_metadata",
            T + "test_grounded_lessons.TestFormatReferencePassages.test_prevents_passage_tag_injection",
            T + "test_grounded_lessons.TestCachedIndexReuse.test_reuses_cached_index",
        ],
    ),
    Scenario(
        number=10,
        name="Grounded lesson rejects weak or irrelevant evidence",
        category="lessons",
        checks="Lesson generation stops when evidence is insufficient or irrelevant.",
        tests=[
            T + "test_grounded_lessons.TestLowSimilarity.test_stops_before_groq_when_similarity_is_low",
            T + "test_grounded_lessons.TestNotRelevant.test_rejects_irrelevant_evidence",
            T + "test_grounded_lessons.TestNoCitations.test_raises_no_citations_after_retry",
        ],
    ),
    Scenario(
        number=11,
        name="Grounded lesson retry limits",
        category="errors_and_retries",
        checks="Invalid responses and citations are retried only within the configured limit.",
        tests=[
            T + "test_grounded_lessons.TestCitationRetrySecurity.test_rejects_unknown_id_during_regeneration",
            T + "test_grounded_lessons.TestSuccessfulCitationRetry.test_accepts_lesson_after_successful_citation_retry",
            T + "test_grounded_lessons.TestRetryLimits.test_stops_after_two_invalid_json_attempts",
        ],
    ),
        Scenario(
        number=12,
        name="Chat message validation",
        category="chatbot",
        checks="User messages and lesson answers are accepted with valid content.",
        tests=[
            T + "test_chat_model.ChatMessageTests.test_user_message_is_accepted",
            T + "test_chat_model.ChatMessageTests.test_lesson_answer_without_sources_is_accepted",
            T + "test_chat_model.ChatMessageTests.test_insufficient_evidence_without_sources_is_accepted",
        ],
    ),
    Scenario(
        number=13,
        name="PDF answer citation validation",
        category="chatbot",
        checks="PDF answers require valid source fingerprints and citation markers.",
        tests=[
            T + "test_chat_model.ChatMessageTests.test_pdf_answer_with_valid_citation_is_accepted",
            T + "test_chat_model.ChatMessageTests.test_pdf_answer_without_fingerprint_is_rejected",
            T + "test_chat_model.ChatMessageTests.test_pdf_answer_without_sources_is_rejected",
            T + "test_chat_model.ChatMessageTests.test_unknown_citation_marker_is_rejected",
        ],
    ),
    Scenario(
        number=14,
        name="Page mention validation",
        category="rag_citations",
        checks="Page references are detected and uncited page mentions are identified.",
        tests=[
            T + "test_grounded_lessons.TestPageMentions.test_finds_page_number_formats",
            T + "test_grounded_lessons.TestPageMentions.test_finds_uncited_pages",
        ],
    ),
        Scenario(
        number=15,
        name="Quiz validation and grading",
        category="quizzes",
        checks="Quizzes contain five questions, four options per question, and valid answers.",
        tests=[
            T + "test_quiz_model.test_quiz_has_five_questions",
            T + "test_quiz_model.test_each_question_has_four_options",
            T + "test_quiz_model.test_correct_answer_matches_an_option",
            T + "test_quiz_model.test_quiz_rejects_fewer_than_five_questions",
            T + "test_quiz_model.test_quiz_grader_scores_three_out_of_five",
        ],
    ),
    Scenario(
        number=16,
        name="Lesson state management",
        category="state",
        checks="Stale grounded lessons are detected and can be removed.",
        tests=[
            T + "test_lesson_state.test_stale_grounded_lessons",
            T + "test_lesson_state.test_remove_stale_grounded_lessons",
        ],
    ),
        Scenario(
        number=17,
        name="Lesson schema boundaries",
        category="lessons",
        checks="Lesson schemas enforce the correct fields and exclude source IDs from ordinary lessons.",
        tests=[
            T + "test_grounded_lessons.TestGroundedLessonSchema.test_schema_restricts_title_and_source_ids",
            T + "test_lesson_model.test_ordinary_lesson_schema_excludes_source_ids",
        ],
    ),
        Scenario(
        number=18,
        name="Secret redaction",
        category="errors_and_retries",
        checks="API keys and bearer tokens are redacted from error messages.",
        tests=[
            T + "test_structured_output.test_redact_api_key",
            T + "test_structured_output.test_redact_bearer_token",
            T + "test_structured_output.test_redact_groq_api_key",
        ],
    ),
        Scenario(
        number=19,
        name="Groq temporary error retry",
        category="errors_and_retries",
        checks="Temporary server errors are retried within the configured limit.",
        tests=[
            T + "test_reliability.test_retries_temporary_server_error",
        ],
    ),
    Scenario(
        number=20,
        name="Structured JSON retry budget",
        category="errors_and_retries",
        checks="Structured JSON generation stays within its retry budget.",
        tests=[
            T + "test_reliability.test_json_retry_budget_is_bounded",
        ],
    ),
    Scenario(
        number=21,
        name="Groq API error secret protection",
        category="errors_and_retries",
        checks="API keys are removed from Groq error messages.",
        tests=[
            T + "test_reliability.test_api_error_redacts_groq_key",
        ],
    ),
    Scenario(
        number=22,
        name="Groq timeout handling",
        category="errors_and_retries",
        checks="Timeout errors are converted into understandable application errors.",
        tests=[
            T + "test_reliability.test_timeout_error_is_understandable",
        ],
    ),
]