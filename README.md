# Mini ClassBuild 🎓

An AI-powered educational platform that generates personalized courses, structured lessons, and interactive quizzes based on the learner's chosen topic and difficulty level.

##  Project Overview

Mini ClassBuild helps learners create customized learning experiences using Generative AI.

Users can:
- Generate structured course outlines based on a chosen topic.
- Select a difficulty level: Beginner, Intermediate, or Advanced.
- Customize the number of lessons.
- Generate detailed lesson content with explanations and practical examples.
- Practice through interactive multiple-choice quizzes.
- Receive instant grading, scores, and answer explanations.
- Retake quizzes to improve their understanding.

##  Features

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

### 3. Interactive Quiz System
- Five multiple-choice questions per quiz.
- Four answer options per question.
- Automatic grading.
- Score calculation (0–5).
- Explanations for correct answers.
- Quiz retake functionality.

### 4. Structured AI Output
- Pydantic-based data validation.
- JSON Schema support.
- Groq API integration.
- Automatic retry for invalid JSON responses.

##  Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | User interface |
| Groq API | AI-powered content generation |
| Pydantic | Data validation and structured models |
| python-dotenv | Environment variable management |
| Pytest | Automated testing |

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
│   │   └── quiz.py
│   │
│   └── services/
│       ├── structured_output.py
│       ├── course_generator.py
│       ├── lesson_generator.py
│       ├── quiz_generator.py
│       └── quiz_grader.py
│
├── scripts/
│   ├── __init__.py
│   └── test_groq_connection.py
│
└── tests/
    ├── test_course_model.py
    ├── test_lesson_model.py
    ├── test_quiz_model.py
    └── test_structured_output.py
```

##  Installation & Setup

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

##  Testing

The project uses Pytest for automated testing.

Run all tests:

```bash
python -m pytest tests -v
```

The current test suite covers:
- Course model validation.
- Lesson model validation.
- Quiz structure and grading.
- Structured JSON output handling.
- Retry behavior for invalid JSON responses.

##  Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |
| `GROQ_MODEL` | AI model used for generation |
| `GROQ_TIMEOUT_SECONDS` | Request timeout in seconds |

##  Project Goal

The goal of Mini ClassBuild is to demonstrate how Generative AI can be integrated into an educational application through structured output generation, data validation, modular architecture, and an interactive user interface.

---

**Developed as part of the Sahaba AI Engineering Training Program.**