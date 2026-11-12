# Mini ClassBuild 

**Mini ClassBuild** is an AI-powered learning platform that helps learners build personalized courses, study structured lessons, and test their understanding through interactive quizzes. It also supports PDF-based learning with Retrieval-Augmented Generation (RAG), source-grounded lesson content, and an interactive AI tutor.

## Overview

Learners can use Mini ClassBuild to:

- Generate a course outline from a topic and selected difficulty.
- Choose a difficulty level: Beginner, Intermediate, or Advanced.
- Customize the number of lessons.
- Generate structured lessons with explanations, examples, summaries, and exercises.
- Upload PDF learning materials and use their content to ground lesson generation.
- View source references associated with grounded lesson sections.
- Ask lesson-related questions through a floating AI tutor.
- Complete multiple-choice quizzes, receive scores and explanations, and retake quizzes.
- Save courses locally and load them in a later session.
- Export course content as a Markdown (`.md`) document.

## Features

### 1. AI Course Generation

- Creates structured course outlines based on the learner's topic.
- Supports Beginner, Intermediate, and Advanced difficulty levels.
- Supports a configurable lesson count (2–5).
- Produces course descriptions and learning objectives.

### 2. AI Lesson Generation

- Generates lesson introductions and structured learning sections.
- Includes explanations and practical examples.
- Provides lesson summaries and exercises with hints.
- Uses validated structured output for generated content.

### 3. PDF-Based Learning with RAG

- Accepts PDF learning materials.
- Extracts text and splits it into searchable chunks.
- Creates embeddings for semantic retrieval.
- Retrieves relevant passages using lesson topics and learning objectives.
- Uses retrieved evidence to support lesson generation.

### 4. Grounded Lessons and Source References

- Generates lesson content using retrieved document evidence.
- Associates lesson sections with source references.
- Validates source IDs against the retrieved passages.
- Checks evidence relevance and handles invalid or missing citations.
- Preserves source traceability, including source filenames and page numbers where available.

### 5. Interactive AI Tutor

- Provides a floating chat interface within the learning experience.
- Supports lesson-aware conversations.
- Maintains chat state and conversation history during the active session.

### 6. Interactive Quizzes

- Generates multiple-choice quizzes for lessons.
- Uses four answer options per question.
- Grades submitted answers automatically.
- Displays scores and explanations.
- Allows learners to retake quizzes.

### 7. Course Storage

- Saves generated course data locally as JSON.
- Lists and loads previously saved courses.
- Preserves available lesson content, quizzes, course details, and source-document metadata.
- Validates saved data and handles invalid, corrupted, oversized, or unsupported course files.
- Uses atomic file replacement when saving course data.

By default, saved courses are stored in the `saved_courses/` directory. The storage location can be changed with `MINICLASSBUILD_SAVE_DIR`.

### 8. Markdown Export

- Exports the course description and learning objectives.
- Includes the course outline and generated lesson content.
- Includes exercises and available quizzes.
- Adds an answer key with explanations when quiz data is available.
- Includes source references for grounded lesson sections when available.

Exports are written to the `exports/` directory.

### 9. Structured Output and Reliability

- Uses Pydantic models to validate generated data.
- Uses structured JSON generation and schema validation.
- Handles API errors, timeouts, and invalid model responses.
- Applies bounded retries for supported temporary or invalid-output cases.
- Redacts secrets from relevant error messages.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
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
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── assets/
│   └── style.css
│
├── classbuild/
│   ├── __init__.py
│   ├── config.py
│   ├── course_config.py
│   │
│   ├── export/
│   │   └── markdown_export.py
│   │
│   ├── llm/
│   │   ├── exceptions.py
│   │   └── groq_client.py
│   │
│   ├── models/
│   │   ├── chat.py
│   │   ├── course.py
│   │   ├── lesson.py
│   │   └── quiz.py
│   │
│   ├── persistence/
│   │   ├── course_store.py
│   │   └── saved_course.py
│   │
│   ├── rag/
│   │   ├── chunker.py
│   │   ├── document_state.py
│   │   ├── embeddings.py
│   │   ├── models.py
│   │   ├── pdf_processor.py
│   │   ├── retriever.py
│   │   └── search_state.py
│   │
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
│
├── docs/
│   ├── how_it_works.md
│   └── validation_audit.md
│
├── scripts/
│   ├── evaluation_scenarios.py
│   ├── final_check.py
│   ├── run_evaluation.py
│   ├── test_groq_connection.py
│   ├── test_lesson_generator.py
│   └── test_quiz_generator.py
│
└── tests/
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

Runtime-generated directories:

- `saved_courses/` — locally saved course JSON files.
- `exports/` — generated Markdown exports.

These directories may be created while the application is running.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/MalakkKhdeir/Mini-ClassBuild.git
cd Mini-ClassBuild
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root directory. You can use `.env.example` as a starting point.

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TIMEOUT_SECONDS=60
GROQ_MAX_RETRIES=1
```

Optional: choose a different directory for locally saved courses:

```env
MINICLASSBUILD_SAVE_DIR=saved_courses
```

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key | Required |
| `GROQ_MODEL` | Model used for generation | `openai/gpt-oss-20b` |
| `GROQ_TIMEOUT_SECONDS` | API request timeout in seconds | `60` |
| `GROQ_MAX_RETRIES` | Maximum retry count (bounded by the application) | `1` |
| `MINICLASSBUILD_SAVE_DIR` | Local course storage directory | `saved_courses` |

**Security:** Never commit your `.env` file or publish your API key. Keep credentials in environment variables or an appropriate secrets manager.

### 5. Run the application

```bash
python -m streamlit run app.py
```

Streamlit will provide a local URL in the terminal. Open it in your browser to use Mini ClassBuild.

## Testing

Run the automated test suite from the project root:

```bash
python -m pytest -q
```

The tests cover areas including:

- Course, lesson, quiz, and chat model validation.
- Lesson generation and grounded lesson behavior.
- Source citation and evidence validation.
- Quiz models and grading-related behavior.
- Course persistence and saved-course validation.
- Structured output and retry handling.
- Reliability and end-to-end workflows.

To run the project's final check script:

```bash
python -m scripts.final_check
```

Test results can vary by environment and code revision. Run the commands above to verify the current checkout; this README intentionally does not state a fixed passing-test count.

## Documentation

Additional project documentation is available in:

- [`docs/how_it_works.md`](docs/how_it_works.md) — application workflow and implementation overview.
- [`docs/validation_audit.md`](docs/validation_audit.md) — validation and reliability notes.

## Project Goal

Mini ClassBuild demonstrates how Generative AI can support personalized learning through structured course generation, PDF-based retrieval, evidence-grounded lessons, conversational assistance, interactive assessment, local persistence, and content export.

---

**Developed as part of the Sahaba AI Engineering Training Program.**
