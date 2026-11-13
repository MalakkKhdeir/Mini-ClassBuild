
# Mini ClassBuild – Validation Audit

## Purpose

This document records the validation, reliability, and persistence
rules implemented in Mini ClassBuild.

It identifies the rules enforced by the application and the
additional safeguards introduced during Stage 3.

The automated evaluation suite checks these rules through
offline test scenarios.

## Status

- **Already enforced:** The rule was implemented before Stage 3.
- **Fixed in Stage 3:** The rule was added or improved during Stage 3.

## 1. Course Validation

| Rule | Enforcement | Status |
|---|---|---|
| A course must contain at least two lessons. | Course model validation | Already enforced |
| A course must contain no more than five lessons. | Course model validation | Already enforced |
| Lesson titles must be unique. | `check_unique_lesson_titles()` and model validator | Fixed in Stage 3 |

## 2. Lesson Validation

| Rule | Enforcement | Status |
|---|---|---|
| Lessons must contain the required sections and exercises. | Lesson model validation | Already enforced |
| Lesson titles are required. | Lesson model validation | Already enforced |
| Grounded lessons must use valid source IDs. | Grounded lesson validation | Already enforced |
| Grounded lessons must not mention uncited page numbers. | `uncited_page_mentions()` | Fixed in Stage 3 |

## 3. Structured Output Validation

| Rule | Enforcement | Status |
|---|---|---|
| Generated JSON must match the expected schema. | Structured output validation | Already enforced |
| Unsupported schema keywords are removed. | Strict schema preparation | Already enforced |
| Invalid JSON responses are retried within a bounded limit. | `request_structured_json()` | Already enforced |
| Other errors are not retried as invalid JSON. | Structured generation error handling | Already enforced |
| API secrets must not appear in logged error previews. | `redact_secrets()` | Fixed in Stage 3 |

## 4. Retrieval-Augmented Generation (RAG)

| Rule | Enforcement | Status |
|---|---|---|
| Only relevant passages are selected. | Evidence selection | Already enforced |
| Retrieved evidence must meet the similarity threshold. | Evidence retrieval | Already enforced |
| Grounded lessons must cite valid source IDs. | Citation validation | Already enforced |
| Sources from another PDF must be rejected. | Source fingerprint validation | Already enforced |
| Modified or tampered source text must be rejected. | Citation validation | Already enforced |
| Unknown citation IDs must be rejected. | Citation validation | Already enforced |
| Page mentions must match cited pages. | `uncited_page_mentions()` | Fixed in Stage 3 |

## 5. Chatbot Validation

| Rule | Enforcement | Status |
|---|---|---|
| User messages must contain valid content. | Chat message model | Already enforced |
| PDF answers must contain valid source information. | Chat message validation | Already enforced |
| Unknown citation markers must be rejected. | PDF answer validation | Already enforced |
| PDF answers without a valid fingerprint must be rejected. | PDF answer validation | Already enforced |

## 6. Reliability and Error Handling

| Rule | Enforcement | Status |
|---|---|---|
| Temporary Groq errors use bounded retries. | Groq SDK configuration | Fixed in Stage 3 |
| Client errors (400, 401, 403, 404) are not retried. | Groq SDK retry configuration | Fixed in Stage 3 |
| Maximum retries are configurable and clamped. | `GROQ_MAX_RETRIES` | Fixed in Stage 3 |
| Timeout errors must be understandable. | Groq client error handling | Fixed in Stage 3 |
| API secrets must be redacted from error messages. | `redact_secrets()` | Fixed in Stage 3 |
| Structured JSON retries must remain within a fixed request budget. | Structured output retry handling | Fixed in Stage 3 |

## 7. Saved Course Persistence

| Rule | Enforcement | Status |
|---|---|---|
| Saved courses must follow the supported schema. | `SavedCourse` model validation | Fixed in Stage 3 |
| Course content must be saved and loaded consistently. | `CourseStore` | Fixed in Stage 3 |
| Updating a course must preserve its identity. | Course update operation | Fixed in Stage 3 |
| Invalid course IDs must be rejected. | Course ID validation | Fixed in Stage 3 |
| Corrupted or unsupported course files must be reported. | Course loading and listing validation | Fixed in Stage 3 |
| Oversized course files must be rejected. | File-size validation | Fixed in Stage 3 |
| Saving must use atomic file replacement. | Atomic save operation | Fixed in Stage 3 |
| Temporary files must not appear as saved courses. | Course listing logic | Fixed in Stage 3 |
| Saved course content must not include API secrets, chat history, or vector indexes. | Saved course serialization | Fixed in Stage 3 |

## 8. Automated Evaluation

The offline evaluation suite is implemented using:

- `scripts/evaluation_scenarios.py`
- `scripts/run_evaluation.py`

The scenarios cover validation, reliability, retrieval, persistence,
and other application workflows.

Each scenario is considered successful only when all its required
tests are found, executed, and passed. Missing or skipped tests
must not be counted as successful.

Run the evaluation using:

```bash
python scripts/run_evaluation.py --no-json
```

The command prints the current number of scenarios, passed scenarios,
failed scenarios, and the pass percentage.

Do not treat a previously recorded result as the current result.
Always run the command to obtain the latest evaluation status.

## 9. Final Verification

Run the final project verification using:

```bash
python scripts/final_check.py
```

The final verification checks the project environment, dependencies,
syntax, unit tests, offline evaluation, and end-to-end tests.

The final result should report success only when all required checks pass.
