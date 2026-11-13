# Mini ClassBuild

**Mini ClassBuild** is an AI-powered learning platform that helps learners create personalized courses, study structured lessons, and assess their understanding through interactive quizzes. It also supports PDF-based learning with Retrieval-Augmented Generation (RAG), source-grounded lessons, and an interactive AI tutor.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Testing and Evaluation](#testing-and-evaluation)
- [Documentation](#documentation)
- [Project Goal](#project-goal)

## Overview

Mini ClassBuild allows learners to:

- Generate a course outline from a topic and selected difficulty.
- Choose Beginner, Intermediate, or Advanced difficulty.
- Customize the number of lessons (2–5).
- Generate structured lessons with explanations, examples, summaries, and exercises.
- Upload PDF learning materials and use their content as evidence for lesson generation.
- View source references associated with grounded lesson sections.
- Ask lesson-related questions through an interactive AI tutor.
- Complete multiple-choice quizzes, review scores and explanations, and retake quizzes.
- Save courses locally and reopen them in later sessions.
- Export course content as a Markdown (`.md`) document.

## Features

### 1. AI Course Generation

- Generates structured course outlines based on the learner's topic.
- Supports Beginner, Intermediate, and Advanced difficulty levels.
- Supports a configurable lesson count (2–5).
- Produces course descriptions and learning objectives.

### 2. AI Lesson Generation

- Generates lesson introductions and structured learning sections.
- Includes explanations and practical examples.
- Provides lesson summaries and exercises with hints.
- Validates generated content using structured output.

### 3. PDF-Based Learning with RAG

- Accepts PDF learning materials.
- Extracts text and splits it into searchable chunks.
- Creates embeddings for semantic retrieval.
- Retrieves relevant passages using lesson topics and learning objectives.
- Uses retrieved evidence to support lesson generation.

### 4. Grounded Lessons and Source References

- Generates lesson content using retrieved document evidence.
- Associates lesson sections with source references.
- Validates source IDs against retrieved passages.
- Checks evidence relevance and handles invalid or missing citations.
- Preserves source traceability, including source filenames and page numbers where available.

### 5. Interactive AI Tutor

- Provides a floating chat interface within the learning experience.
- Supports lesson-aware conversations.
- Maintains chat state and conversation history during the active session.

### 6. Interactive Quizzes

- Generates multiple-choice quizzes for lessons.
- Provides four answer options per question.
- Grades submitted answers automatically.
- Displays scores and explanations.
- Allows learners to retake quizzes.

### 7. Course Storage

- Saves course data locally as JSON.
- Lists and loads previously saved courses.
- Preserves available lesson content, quizzes, course details, and source-document metadata.
- Supports updating an existing saved course instead of creating a duplicate on every save.
- Validates saved data and handles invalid, corrupted, oversized, or unsupported course files.
- Uses atomic file replacement when saving course data.
- Reports unreadable or damaged saved-course files without preventing the rest of the saved-course list from being displayed.

By default, saved courses are stored in `saved_courses/`. Set `MINICLASSBUILD_SAVE_DIR` to use a different local storage directory.

### 8. Safe Course Restoration and PDF Source Identity

- Restores saved course data into a new active session.
- Assigns a fresh session course ID when reopening a saved course.
- Keeps the persistent saved-course ID separate from the active session ID.
- Resets session-specific quiz answers and chat history when loading another course.
- Preserves saved lesson content and historical source references.

**PDF source safety**

- PDF-based features remain disabled for a restored course until its original source PDF is uploaded again.
- The uploaded document must match the saved source fingerprint.
- A different PDF with the same filename is not treated as the original source.
- Saved grounded lessons and their historical citations remain available when the original PDF is not uploaded.
- PDF-dependent chat and generation features are enabled only when the matching source document is available.

### 9. Markdown Export

- Exports the course description and learning objectives.
- Includes the course outline and generated lesson content.
- Includes exercises and available quizzes.
- Includes an answer key with explanations when quiz data is available.
- Includes source references for grounded lesson sections when available.

Generated exports are written to `exports/`.

### 10. Structured Output and Reliability

- Uses Pydantic models to validate generated data.
- Uses structured JSON generation and schema validation.
- Handles API errors, timeouts, and invalid model responses.
- Applies bounded retries for supported temporary or invalid-output cases.
- Redacts secrets from relevant error messages.
- Preserves the previous course when a new course-generation request fails.

### 11. Validation, Evaluation, and Final Checks

- Maintains a validation audit describing application safeguards and tests.
- Runs evaluation scenarios and verifies that each required test is found, executed, and passed.
- Includes offline tests that use fakes or test doubles instead of requiring live Groq requests.
- Provides a final verification script that checks the Python version, dependencies, unit tests, evaluation scenarios, and end-to-end workflow.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Core programming language |
| Streamlit | Web application and user interface |
| Groq API | AI-powered course, lesson, quiz, and chat generation |
| Pydantic | Data models and validation |
| Sentence Transformers | Text embeddings |
| NumPy | Numerical operations for retrieval |
| pypdf | PDF text extraction |
| python-dotenv | Environment variable loading |
| Pytest | Automated testing |
| HTTPX | HTTP client testing and mocked API requests |

## Project Structure

```text
Mini-ClassBuild/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── assets/
│   └── style.css
├── classbuild/
│   ├── __init__.py
│   ├── config.py
│   ├── course_config.py
│   ├── export/
│   │   ├── __init__.py
│   │   └── markdown_export.py
│   ├── llm/
│   │   ├── __init__.py
│   │   └── exceptions.py
│   │   └── groq_client.py
│   ├── models/
│   │   ├── chat.py
│   │   ├── course.py
│   │   ├── lesson.py
│   │   └── quiz.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── course_store.py
│   │   └── saved_course.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   ├── document_state.py
│   │   ├── embeddings.py
│   │   ├── models.py
│   │   ├── pdf_processor.py
│   │   ├── retriever.py
│   │   └── search_state.py
│   └── services/
│       ├── chat_state.py
│       ├── course_generator.py
│       ├── grounded_lesson_generator.py
│       ├── lesson_chat.py
│       ├── lesson_generator.py
│       ├── lesson_state.py
│       ├── quiz_generator.py
│       ├── quiz_grader.py
│       └── structured_output.py
├── docs/
│   ├── how_it_works.md
│   └── validation_audit.md
├── scripts/
│   ├── __init__.py
│   ├── evaluation_scenarios.py
│   ├── final_check.py
│   ├── run_evaluation.py
│   ├── test_groq_connection.py
│   ├── test_lesson_generator.py
│   └── test_quiz_generator.py
└── tests/
    ├── __init__.py
    ├── test_app.py
    ├── test_chat_model.py
    ├── test_course_model.py
    ├── test_end_to_end.py
    ├── test_grounded_citations.py
    ├── test_grounded_lessons.py
    ├── test_lesson_grounding.py
    ├── test_lesson_model.py
    ├── test_lesson_state.py
    ├── test_persistence.py
    ├── test_quiz_model.py
    ├── test_reliability.py
    └── test_structured_output.py
```

**Runtime-generated directories** (created when needed and not committed to the repository):

- `saved_courses/` — locally saved course JSON files.
- `exports/` — generated Markdown exports.
- `evaluation_results/` — generated evaluation reports.

## Installation and Setup

### Prerequisites

- Python 3.11 or newer.
- A Groq API key for live AI generation.
- Git (to clone the repository).

### 1. Clone the repository

```bash
git clone https://github.com/MalakkKhdeir/Mini-ClassBuild.git
cd Mini-ClassBuild
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root. Use `.env.example` as a starting point, then add your Groq API key.

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TIMEOUT_SECONDS=60
GROQ_MAX_RETRIES=1
```

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key; required for live AI generation | No default |
| `GROQ_MODEL` | Model used for generation | `openai/gpt-oss-20b` |
| `GROQ_TIMEOUT_SECONDS` | API request timeout in seconds | `60` |
| `GROQ_MAX_RETRIES` | Maximum retry count, bounded by the application | `1` |
| `MINICLASSBUILD_SAVE_DIR` | Local course storage directory | `saved_courses` |

`MINICLASSBUILD_SAVE_DIR` is optional. For example:

```env
MINICLASSBUILD_SAVE_DIR=saved_courses
```

**Security:** Never commit your `.env` file or publish your API key. Keep credentials in environment variables or an appropriate secrets manager.

## Running the Application

From the project root, with the virtual environment activated, run:

```bash
python -m streamlit run app.py
```

Streamlit will display a local URL in the terminal. Open that URL in your browser to use Mini ClassBuild.

## Testing and Evaluation

Run the complete automated test suite:

```bash
python -m pytest -q
```

The tests cover areas including:

- Course, lesson, quiz, and chat model validation.
- Lesson generation and grounded lesson behavior.
- Source citation and evidence validation.
- Quiz models and grading-related behavior.
- Course persistence, save/update/load behavior, and saved-course validation.
- App-level course restoration, session reset, and PDF source identity safety.
- Structured output and retry handling.
- Reliability and end-to-end workflows.

Tests are designed to run offline using fakes or test doubles for external services where applicable. Live AI generation in the application requires a valid Groq API key.

### Stage 3 Evaluation

Run the evaluation scenarios independently:

```bash
python -m scripts.run_evaluation --no-json
```

### Final Verification

Run the complete project verification:

```bash
python scripts/final_check.py
```

The final verification checks the Python version, dependencies, Python syntax, unit tests, evaluation scenarios, and end-to-end workflow. It reports success only when all included checks pass.

Test results can vary by environment and code revision. Run the commands above on the current checkout to verify its status; this README does not claim a fixed passing-test count.

## Documentation

Additional project documentation:

- [`docs/how_it_works.md`](docs/how_it_works.md) — application workflow and implementation overview.
- [`docs/validation_audit.md`](docs/validation_audit.md) — validation and reliability notes.

## Project Goal

Mini ClassBuild demonstrates how Generative AI can support personalized learning through structured course generation, PDF-based retrieval, evidence-grounded lessons, conversational assistance, interactive assessment, local persistence, and content export.

---

**Developed as part of the Sahaba AI Engineering Training Program.**
