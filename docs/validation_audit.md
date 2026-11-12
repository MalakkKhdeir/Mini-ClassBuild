# Mini ClassBuild – Validation Audit

## Purpose

This document records the validation and reliability rules
implemented in Mini ClassBuild.

It identifies the rules that were already enforced and the
additional rules introduced during Stage 3.

The evaluation scenarios provide automated tests for these rules.

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

## 7. Automated Evaluation

The offline evaluation suite is implemented using:

- `scripts/evaluation_scenarios.py`
- `scripts/run_evaluation.py`

The evaluation suite checks the implemented rules through
automated test scenarios.

Latest evaluation result:

- Total scenarios: 22
- Passed scenarios: 22
- Failed scenarios: 0
- Pass percentage: 100%

Run the evaluation using:

```bash
python scripts/run_evaluation.py --no-json