# Mini ClassBuild 🎓

An AI-powered educational platform that generates personalized courses, structured lessons, and interactive quizzes based on the learner's chosen topic and difficulty level. It also uses Retrieval-Augmented Generation (RAG) to create source-grounded lessons from uploaded learning materials and provides an interactive AI tutor to support learners.

## Project Overview

Mini ClassBuild helps learners create customized learning experiences using Generative AI.

Users can:
- Generate structured course outlines based on a chosen topic.
- Select a difficulty level: Beginner, Intermediate, or Advanced.
- Customize the number of lessons.
- Generate detailed lesson content with explanations and practical examples.
- Upload PDF learning materials to support lesson generation.
- Generate lessons grounded in retrieved information from uploaded documents.
- Access source references and citations in grounded lessons.
- Interact with an AI tutor through a floating chat interface.
- Practice through interactive multiple-choice quizzes.
- Receive instant grading, scores, and answer explanations.
- Retake quizzes to improve their understanding.

## Features

### 1. AI Course Generation
- Personalized course outlines.
- Configurable difficulty levels.
- Customizable lesson count (2–5).
- Structured learning objectives.

### 2. AI Lesson Generation
- Detailed lesson introductions.
- 2–4 structured learning sections.
- Practical examples.
- Exactly two exercises per lesson, with hints.
- Structured lesson content using validated data models.

### 3. Retrieval-Augmented Generation (RAG)
- Upload PDF learning materials.
- Extract and process document content.
- Split documents into searchable text chunks.
- Generate embeddings for semantic search.
- Retrieve relevant passages based on lesson topics and learning objectives.
- Use retrieved evidence to support lesson generation.
- Maintain document and search state.

### 4. Grounded Lesson Generation
- Generate lessons using retrieved document evidence.
- Include source references for generated lesson sections.
- Validate source IDs against available retrieved passages.
- Check evidence relevance before accepting generated content.
- Retry citation generation when citations are missing or invalid.
- Preserve source traceability in generated lessons.

### 5. AI Tutor Chat
- Floating chat interface accessible throughout the learning experience.
- Interactive conversations with an AI tutor.
- Lesson-aware chat context.
- Conversation thread management.
- Chat state management and validation.

### 6. Interactive Quiz System
- Five multiple-choice questions per quiz.
- Four answer options per question.
- Automatic grading.
- Score calculation (0–5).
- Explanations for correct answers.
- Quiz retake functionality.

### 7. Structured AI Output
- Pydantic-based data validation.
- JSON Schema support.
- Groq API integration.
- Automatic retry for invalid JSON responses.
- Validation of generated courses, lessons, quizzes, and chat data.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | User interface |
| Groq API | AI-powered content generation and chat |
| Pydantic | Data validation and structured models |
| RAG | Evidence-based lesson generation |
| PDF Processing | Extracting learning material from PDF documents |
| Embeddings | Semantic representation of text |
| Pytest | Automated testing |
| python-dotenv | Environment variable management |

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
│   ├── llm/
│   │   ├── exceptions.py
│   │   └── groq_client.py
│   │
│   ├── models/
│   │   ├── course.py
│   │   ├── lesson.py
│   │   ├── quiz.py
│   │   └── chat.py
│   │
│   ├── rag/
│   │   ├── __init__.py
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
├── scripts/
│   ├── test_groq_connection.py
│   ├── test_lesson_generator.py
│   ├── test_quiz_generator.py
│   └── test_quiz_grader.py
│
└── tests/
    ├── __init__.py
    ├── test_chat_model.py
    ├── test_grounded_citations.py
    ├── test_grounded_lessons.py
    ├── test_lesson_grounding.py
    ├── test_lesson_model.py
    └── test_lesson_state.py
```

## Installation & Setup

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd Mini-ClassBuild
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root directory.

Add your Groq API credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
GROQ_TIMEOUT_SECONDS=60
```

You can use `.env.example` as a reference.

**Important:** Never commit your `.env` file or expose your API key.

### 5. Test the Groq connection

```bash
python -m scripts.test_groq_connection
```

### 6. Run the application

```bash
python -m streamlit run app.py
```

The application will open in your browser.

## Testing

The project uses Pytest for automated testing.

Run all tests:

```bash
python -m pytest -q
```

The test suite covers:
- Course and lesson model validation.
- Quiz structure and grading.
- Chat model validation.
- Grounded lesson generation.
- Source citation validation.
- Lesson grounding and evidence handling.
- Lesson state management.
- Structured AI output and retry behavior.

**Latest test result:** 51 tests passed.

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | AI model used for generation |
| `GROQ_TIMEOUT_SECONDS` | Request timeout in seconds |

## Project Goal

The goal of Mini ClassBuild is to demonstrate how Generative AI can be integrated into an educational application through structured content generation, Retrieval-Augmented Generation (RAG), evidence-based learning, data validation, conversational AI, and modular software architecture.

---

**Developed as part of the Sahaba AI Engineering Training Program.**