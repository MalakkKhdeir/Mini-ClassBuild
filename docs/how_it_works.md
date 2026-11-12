
# Mini ClassBuild – How It Works

## 1. Project Overview

Mini ClassBuild is an AI-powered educational platform that generates personalized courses, lessons, and quizzes.

Users can choose a topic, difficulty level, and number of lessons. They can also upload PDF learning materials to generate lessons grounded in document evidence.

The application uses Streamlit for its interface and Groq for AI-powered content generation.

## 2. Main Application Workflow

The application follows this workflow:

1. The user enters a course topic.
2. The user selects a difficulty level.
3. The user selects the number of lessons.
4. The application validates the course configuration.
5. The Course Generator creates a structured course outline.
6. The user selects a lesson.
7. The Lesson Generator creates the lesson content.
8. The Quiz Generator creates a five-question quiz.
9. The user can study the lesson and practice using the quiz.

## 3. Course Generation

The course configuration is represented by `CourseConfig`.

`CourseGenerator` sends the requested topic, difficulty, and lesson count to the Groq client.

The returned JSON is validated using the Pydantic `Course` model.

The course contains:
- A title.
- A description.
- Learning objectives.
- An ordered list of lessons.

## 4. Lesson Generation

`LessonGenerator` creates structured lesson content.

Each lesson contains:
- A title.
- An introduction.
- Two to four sections.
- A summary.
- Exactly two exercises with hints.

The generated JSON is validated using the lesson models.

## 5. PDF Processing and RAG

Users can upload PDF learning materials.

The PDF processing pipeline:
1. Validates the uploaded file.
2. Extracts text from PDF pages.
3. Cleans the extracted text.
4. Splits the text into searchable chunks.
5. Generates embeddings for semantic retrieval.

The retriever searches for passages relevant to the selected lesson.

The grounded lesson generator uses the retrieved passages to generate lessons with source references and page citations.

Grounding validation checks that citations refer to the retrieved source material.

## 6. AI Tutor

The AI Tutor provides lesson-aware assistance.

It uses the lesson context and conversation history to answer learner questions.

Chat messages and citation references are validated before being used.

## 7. Quiz Generation and Grading

`QuizGenerator` creates five multiple-choice questions.

Each question contains:
- A question.
- Four answer options.
- One correct answer.
- An explanation.

The quiz grader checks the learner's answers and calculates the score.

## 8. Structured Output and Reliability

AI responses are requested as structured JSON.

The application uses:
- Pydantic validation.
- JSON schema constraints.
- Bounded retries for invalid structured output.
- Clear application-level errors.
- Secret redaction in error logging.
- Configurable Groq request retries.

## 9. Saving and Loading Courses

Saved courses are represented by the `SavedCourse` model.

The persistence layer stores:
- Course configuration.
- Course outline.
- Generated lessons.
- Generated quizzes.
- Selected lesson.
- Source PDF filename and fingerprint when available.

The storage layer uses JSON files and validates course IDs and saved data.

Files are written atomically to reduce the risk of partial saves.

Temporary quiz answers, chat history, API keys, and embedding data are not included in saved courses.

## 10. Markdown Export

Users can export a course as a Markdown file.

The export includes:
- Course information.
- Course objectives.
- Lessons in their original order.
- Lesson sections and examples.
- Exercises and hints.
- Quiz questions.
- A separate answer key.
- PDF source references when available.

The export layer creates a safe filename based on the course topic.

## 11. Testing Strategy

The project uses Pytest for automated testing.

Tests cover:
- Course and lesson validation.
- Structured output.
- PDF grounding and citations.
- Chat validation.
- Quiz generation and grading.
- State management.
- API error handling and retries.
- Persistence and storage safety.
- Markdown export.
- End-to-end course workflow.

End-to-end tests use fake AI responses so they do not require a real Groq API request.

## 12. Main Technologies

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | User interface |
| Groq API | AI generation |
| Pydantic | Data validation |
| Pytest | Automated testing |
| PyPDF | PDF text extraction |
| Sentence Transformers | Text embeddings |
| NumPy | Embedding operations |
| JSON | Course persistence |
| Markdown | Course export |
