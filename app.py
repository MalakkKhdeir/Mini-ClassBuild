import streamlit as st
from pydantic import ValidationError
from pathlib import Path
from classbuild.course_config import CourseConfig
from classbuild.llm import GroqClient
from classbuild.llm.exceptions import GroqClientError
from classbuild.models.quiz import Quiz
from classbuild.models.course import Course
from classbuild.services.course_generator import CourseGenerator, CourseGenerationError
from classbuild.services.lesson_generator import LessonGenerator, LessonGenerationError
from classbuild.services.quiz_generator import QuizGenerator, QuizGenerationError
from classbuild.services.quiz_grader import QuizGrader
from uuid import uuid4
from classbuild.rag.document_state import (
    sync_learning_material,
    attach_material_to_course,
)

from classbuild.services.grounded_lesson_generator import (
    GroundedLessonGenerator,
    InsufficientEvidenceError,
)

from classbuild.rag.search_state import get_or_build_index
from classbuild.rag.document_state import material_for_course
from classbuild.rag.embeddings import EmbeddingService

from classbuild.services.chat_state import (
    valid_thread_keys,
    prune_chats,
    thread_key,
    get_history,
    append_exchange,
    clear_thread,
)
from classbuild.models.lesson import LessonContent
from classbuild.models.chat import ChatMessage
from classbuild.services.lesson_chat import (
    LessonChatService,
    LessonChatContext,
    ChatInputError,
    ChatAnswerError,
    readable_citations,
)


st.set_page_config(
    page_title="ClassBuild | Learn. Practice. Build.",
    layout="wide",
    initial_sidebar_state="expanded",
)

css_path = Path(__file__).parent / "assets" / "style.css"

with open(css_path, encoding="utf-8") as css_file:
    st.markdown(
        f"<style>{css_file.read()}</style>",
        unsafe_allow_html=True,
    )

DEFAULT_STATE = {
    "course_config": None,
    "course_outline": None,
    "selected_lesson": None,
    "lesson_contents": {},
    "quizzes": {},
    "quiz_results": {},
    "quiz_attempts": {},
    "chats": {},
}
for state_key, default_value in DEFAULT_STATE.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value

with st.sidebar:
    st.markdown('<div class="cb-brand">📖 ClassBuild</div>', unsafe_allow_html=True)
    st.markdown('<div class="cb-tagline">Learn. Practice. Build.</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Your learning space")
    st.caption("Create a course, explore lessons, and check your understanding.")
    if st.session_state.course_outline:
        side_outline = st.session_state.course_outline
        side_config = st.session_state.course_config or {}
        st.markdown("---")
        st.markdown("**Current course**")
        st.markdown(f"**{side_outline['title']}**")
        st.caption(f"{side_config.get('difficulty', 'Beginner')} · {len(side_outline['lessons'])} lessons")
        st.progress(1.0 if side_outline["lessons"] else 0.0)
    st.markdown("---")
    st.caption("Small steps build real progress.")

st.markdown(
    """
    <div class="cb-hero">
        <div class="cb-eyebrow">Your AI-powered learning studio</div>
        <h1>Learn something new.</h1>
        <p>Build a structured course, explore clear lessons, and practice with quizzes made for your level.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("⚙️ Course setup", expanded=st.session_state.course_outline is None):
    uploaded_pdf = st.file_uploader(
        "Upload course material (PDF)",
        type=["pdf"],
        key="course_pdf",
    )

    upload_data = (
        (uploaded_pdf.name, uploaded_pdf.getvalue())
        if uploaded_pdf is not None
        else None
    )

    material_status = sync_learning_material(
        st.session_state,
        upload_data,
    )

    if material_status.error:
        st.warning(material_status.error)
    elif material_status.document is not None:
        st.success("PDF course material is ready.")

    with st.form("course_form"):
        topic = st.text_input(
            "Course topic",
            value=(st.session_state.course_config or {}).get("topic", ""),
            placeholder="e.g. Introduction to Python",
        )
        difficulty_options = ["Beginner", "Intermediate", "Advanced"]
        saved_difficulty = (st.session_state.course_config or {}).get("difficulty", "Beginner")
        difficulty = st.selectbox(
            "Difficulty level",
            difficulty_options,
            index=difficulty_options.index(saved_difficulty) if saved_difficulty in difficulty_options else 0,
        )
        saved_count = (st.session_state.course_config or {}).get("lesson_count", 3)
        lesson_count = st.slider("Number of lessons", 2, 5, value=min(5, max(2, saved_count)))
        submitted = st.form_submit_button("✨ Generate course outline", type="primary", use_container_width=True)

if submitted:
    if not topic.strip():
        st.warning("Please enter a course topic before generating a course.")
    else:
        config = CourseConfig(topic=topic.strip(), difficulty=difficulty, lesson_count=lesson_count)
        new_config = config.to_dict()
        same_course = st.session_state.course_config == new_config
        if not same_course:
            st.session_state.course_outline = None
            st.session_state.selected_lesson = None
            st.session_state.lesson_contents = {}
            st.session_state.quizzes = {}
            st.session_state.quiz_results = {}
            st.session_state.quiz_attempts = {}
            st.session_state.chats = {}
        st.session_state.course_config = new_config
        try:
            with st.spinner("Designing your course outline..."):

                course = CourseGenerator(GroqClient()).generate(config)
                st.session_state.course_id = str(uuid4())
                st.session_state.course_outline = course.model_dump()
                attach_material_to_course(st.session_state)



            st.success("Your course outline is ready!")
        except (GroqClientError, CourseGenerationError, ValidationError) as exc:
            st.error("We couldn't generate the course outline. Please try again.")
            with st.expander("Technical details"):
                st.exception(exc)
        except Exception as exc:
            st.error("An unexpected error occurred while generating the course.")
            with st.expander("Technical details"):
                st.exception(exc)

outline = st.session_state.course_outline
course_config = st.session_state.course_config
if outline is None:
    st.markdown(
        '<div class="cb-card"><div class="cb-lesson-title">Your course starts here</div><p>Enter a topic in Course setup, choose your level and lesson count, then generate your personalized outline.</p></div>',
        unsafe_allow_html=True,
    )
    st.stop()

st.markdown('<div class="cb-section-label">Course overview</div>', unsafe_allow_html=True)
st.markdown(f"# {outline['title']}")
st.write(outline["description"])

metric_cols = st.columns(3)
for col, label, value in zip(
    metric_cols,
    ["Difficulty", "Lessons", "Lessons explored"],
    [course_config["difficulty"], len(outline["lessons"]), len(st.session_state.lesson_contents)],
):
    with col:
        st.markdown(
            f'<div class="cb-card"><div class="cb-card-label">{label}</div><div class="cb-card-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

with st.expander("🎯 Learning objectives"):
    for objective in outline["objectives"]:
        st.markdown(f"- {objective}")

st.markdown("## Course lessons")
lesson_titles = [lesson["title"] for lesson in outline["lessons"]]

# Keep only chat threads that still belong to the current course,
# lesson version, and uploaded PDF.
chat_document = material_for_course(st.session_state)
chat_document_fingerprint = (
    chat_document.fingerprint if chat_document is not None else None
)
current_valid_chat_keys = valid_thread_keys(
    course_id=st.session_state.get("course_id", ""),
    lessons=st.session_state.lesson_contents,
    lesson_titles=lesson_titles,
    document_fingerprint=chat_document_fingerprint,
)
prune_chats(st.session_state.chats, current_valid_chat_keys)
for index, lesson in enumerate(outline["lessons"], start=1):
    with st.expander(f"**{index:02d}** · {lesson['title']}"):
        st.write(lesson["summary"])
        st.markdown("**By the end of this lesson, you will be able to:**")
        for objective in lesson["learning_objectives"]:
            st.markdown(f"- {objective}")

st.divider()
st.markdown('<div class="cb-section-label">Learn at your pace</div>', unsafe_allow_html=True)
st.header("Lesson studio")

previous_selected = st.session_state.get("selected_lesson")
selected_index = lesson_titles.index(previous_selected) if previous_selected in lesson_titles else 0
selected_title = st.selectbox("Choose a lesson to study", lesson_titles, index=selected_index, key="lesson_selector")
selected_lesson = next(lesson for lesson in outline["lessons"] if lesson["title"] == selected_title)
st.session_state.selected_lesson = selected_title


cache_key = (
    st.session_state.course_id,
    course_config["topic"],
    course_config["difficulty"],
    course_config["lesson_count"],
    selected_title,
)

lesson_content = st.session_state.lesson_contents.get(cache_key)

lesson_col, info_col = st.columns([1.65, 1], gap="large")
with lesson_col:
    st.markdown(
        f'<div class="cb-card"><div class="cb-section-label">Selected lesson</div><div class="cb-lesson-title">{selected_title}</div><p>{selected_lesson["summary"]}</p></div>',
        unsafe_allow_html=True,
    )
with info_col:
    st.markdown(
        f'<div class="cb-card"><div class="cb-card-label">Learning objectives</div><div class="cb-card-value">{len(selected_lesson["learning_objectives"])}</div><p>Skills covered in this lesson</p></div>',
        unsafe_allow_html=True,
    )

if st.button(
    "✨ Generate lesson content" if lesson_content is None else "✓ Lesson content generated",
    key="generate_lesson",
    type="primary" if lesson_content is None else "secondary",
):
    if lesson_content is not None:
        st.info("This lesson is already saved in this session.")
    else:
        try:
            with st.spinner("Preparing your lesson..."):
                document = material_for_course(st.session_state)

                if document is not None:
                    course = Course.model_validate(outline)
                    embedding_service = EmbeddingService()

                    index = get_or_build_index(
                        st.session_state,
                        document,
                        embedding_service,
                    )

                    generated_lesson = GroundedLessonGenerator(
                        GroqClient(),
                        embedding_service=embedding_service,
                    ).generate_lesson(
                        outline=course,
                        lesson_number=lesson_titles.index(selected_title) + 1,
                        document=document,
                        index=index,
                    )
                else:
                    generated_lesson = LessonGenerator(
                        GroqClient()
                    ).generate(
                        lesson_title=selected_title,
                        learning_objectives=selected_lesson["learning_objectives"],
                        difficulty=course_config["difficulty"],
                        course_topic=course_config["topic"],
                    )

            st.session_state.lesson_contents[cache_key] = generated_lesson.model_dump()
            st.success("Lesson content generated and saved.")
            st.rerun()

        except InsufficientEvidenceError as exc:
            st.warning(
                "The uploaded PDF does not contain enough relevant information "
                "to generate this lesson. Try a lesson topic that matches the PDF."
            )
            with st.expander("Evidence details"):
                st.write(f"Reason: {exc.reason}")
                if exc.passages:
                    st.write("Retrieved PDF passages:")
                    for passage in exc.passages:
                        st.write(
                            f"- Page {passage.page_number}: "
                            f"{passage.source_filename} "
                            f"(similarity: {passage.score:.2f})"
                        )

        except (GroqClientError, LessonGenerationError, ValidationError) as exc:
            st.error("We couldn't generate this lesson. Please try again.")
            with st.expander("Technical details"):
                st.exception(exc)

        except Exception as exc:
            st.error("An unexpected error occurred while generating the lesson.")
            with st.expander("Technical details"):
                st.exception(exc)

lesson_content = st.session_state.lesson_contents.get(cache_key)
if lesson_content is None:
    st.info("Generate this lesson to see its introduction, sections, examples, summary, and exercises.")
    st.stop()

st.markdown(
    f'<div class="cb-card"><div class="cb-section-label">Introduction</div><div class="cb-lesson-title">{lesson_content["title"]}</div><p>{lesson_content["introduction"]}</p></div>',
    unsafe_allow_html=True,
)
for index, section in enumerate(lesson_content["sections"], start=1):
    with st.container(border=True):
        st.markdown(f"### {index}. {section['heading']}")
        st.write(section["explanation"])
        st.markdown("**Example**")
        st.code(section["example"], language="python")

grounding = lesson_content.get("grounding")
if grounding:
    cited_ids = {
        source_id
        for section in lesson_content["sections"]
        for source_id in section.get("source_ids", [])
    }
    cited_sources = [
        source
        for source in grounding.get("sources", [])
        if source.get("chunk_id") in cited_ids
    ]
    if cited_sources:
        with st.expander("📚 PDF sources and citations"):
            for source in cited_sources:
                st.markdown(
                    f"- **Page {source['page_number']}** · "
                    f"{source['source_filename']}"
                )

with st.container(border=True):
    st.markdown("### ✨ Summary")
    st.write(lesson_content["summary"])

st.markdown("## Practice exercises")
exercise_cols = st.columns(2, gap="medium")
for index, exercise in enumerate(lesson_content["exercises"]):
    with exercise_cols[index % 2]:
        with st.container(border=True):
            st.markdown(f"**Exercise {index + 1}**")
            st.write(exercise["task"])
            with st.expander("💡 Show hint"):
                st.write(exercise["hint"])

# Floating ClassBuild Tutor
chat_document = material_for_course(st.session_state)
parsed_lesson_content = LessonContent.model_validate(lesson_content)
chat_lesson_number = lesson_titles.index(selected_title) + 1

with st.popover(" ", icon=":material/smart_toy:", help="Open ClassBuild Tutor"):
    st.markdown(
        """
        <div class="cb-tutor-header">
            <div class="cb-tutor-avatar">✦</div>
            <div>
                <div class="cb-tutor-title">ClassBuild Tutor</div>
                <div class="cb-tutor-subtitle">Your personal learning assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="cb-tutor-lesson">{selected_title}</div>',
        unsafe_allow_html=True,
    )

    use_pdf_chat = False
    if chat_document is not None:
        use_pdf_chat = st.toggle(
            "Use uploaded PDF",
            value=False,
            key=f"floating_pdf_chat_mode_{selected_title}",
            help="Answers will be grounded in retrieved passages from your PDF.",
        )
    else:
        st.caption("Upload a PDF in Course setup to enable PDF-based answers.")

    active_chat_key = thread_key(
        course_id=st.session_state.course_id,
        content=parsed_lesson_content,
        lesson_number=chat_lesson_number,
        document_fingerprint=(
            chat_document.fingerprint
            if use_pdf_chat and chat_document is not None
            else None
        ),
    )
    chat_history = get_history(st.session_state.chats, active_chat_key)

    if chat_history:
        transcript_height = min(280, max(150, 92 * len(chat_history)))
        with st.container(height=transcript_height, border=False):
            for message in chat_history:
                is_assistant = message.role == "assistant"
                with st.chat_message(
                    message.role,
                    avatar=":material/smart_toy:" if is_assistant else ":material/person:",
                ):
                    if is_assistant and message.mode == "pdf":
                        st.markdown(readable_citations(message.content, message.sources))
                        if message.sources:
                            with st.expander("Sources"):
                                for source in message.sources:
                                    st.markdown(
                                        f"- Page {source.page_number} · {source.source_filename}"
                                    )
                    else:
                        st.markdown(message.content)
                    if message.status == "insufficient_evidence":
                        st.info("The uploaded PDF did not provide enough evidence.")

    else:
        st.markdown(
            """
            <div class="cb-tutor-empty">
                <div class="cb-tutor-empty-icon">✦</div>
                <div class="cb-tutor-empty-title">What would you like to learn?</div>
                <div class="cb-tutor-empty-copy">Ask a question about this lesson and I’ll explain it step by step.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.form(
        key=f"floating_tutor_form_{selected_title}_{'pdf' if use_pdf_chat else 'lesson'}",
        clear_on_submit=True,
    ):
        input_col, send_col = st.columns([8, 1], vertical_alignment="center")
        with input_col:
            chat_question = st.text_input(
                "Your question",
                placeholder="Message your tutor...",
                label_visibility="collapsed",
            )
        with send_col:
            send_chat = st.form_submit_button(
                " ",
                icon=":material/arrow_upward:",
                type="primary",
                help="Send",
            )

    if chat_history:
        if st.button(
            "Clear conversation",
            key=f"floating_clear_chat_{selected_title}_{'pdf' if use_pdf_chat else 'lesson'}",
            type="secondary",
        ):
            clear_thread(st.session_state.chats, active_chat_key)
            st.rerun()

    if send_chat and chat_question.strip():
        try:
            user_message = ChatMessage(
                role="user",
                content=chat_question.strip(),
                mode="pdf" if use_pdf_chat else "lesson",
            )
            with st.spinner("Preparing your explanation..."):
                pdf_index = None
                if use_pdf_chat:
                    embedding_service = EmbeddingService()
                    pdf_index = get_or_build_index(
                        st.session_state, chat_document, embedding_service
                    )

                course_model = Course.model_validate(outline)
                chat_context = LessonChatContext.from_course(
                    course=course_model,
                    lesson_number=chat_lesson_number,
                    lesson_content=parsed_lesson_content,
                    topic=course_config["topic"],
                    difficulty=course_config["difficulty"],
                )
                answer_message = LessonChatService().answer(
                    ctx=chat_context,
                    question=chat_question.strip(),
                    history=chat_history,
                    document=chat_document if use_pdf_chat else None,
                    index=pdf_index,
                )

            append_exchange(
                st.session_state.chats, active_chat_key, user_message, answer_message
            )
            st.rerun()
        except ChatInputError as exc:
            st.warning(str(exc))
        except (ChatAnswerError, GroqClientError, ValidationError) as exc:
            st.error("I couldn't answer your question. Please try again.")
            with st.expander("Technical details"):
                st.exception(exc)
        except Exception as exc:
            st.error("An unexpected error occurred in Tutor Chat.")
            with st.expander("Technical details"):
                st.exception(exc)

st.divider()
st.markdown('<div class="cb-section-label">Check your understanding</div>', unsafe_allow_html=True)
st.header("Lesson quiz")
st.caption("Five multiple-choice questions · Your answers and explanations appear after submission.")

quiz_key = cache_key
quiz_data = st.session_state.quizzes.get(quiz_key)
if st.button(
    "✨ Generate quiz" if quiz_data is None else "✓ Quiz ready",
    key=f"generate_quiz_{selected_title}",
    type="primary" if quiz_data is None else "secondary",
):
    if quiz_data is not None:
        st.info("The quiz for this lesson is already saved.")
    else:
        try:
            with st.spinner("Creating questions from this lesson..."):
                quiz = QuizGenerator(GroqClient()).generate(
                    lesson_title=selected_title,
                    lesson_content=lesson_content,
                    difficulty=course_config["difficulty"],
                    course_topic=course_config["topic"],
                )
            st.session_state.quizzes[quiz_key] = quiz.model_dump()
            st.session_state.quiz_results.pop(quiz_key, None)
            st.session_state.quiz_attempts[quiz_key] = 0
            st.success("Your quiz is ready.")
            st.rerun()
        except (GroqClientError, QuizGenerationError, ValidationError) as exc:
            st.error("We couldn't generate the quiz. Please try again.")
            with st.expander("Technical details"):
                st.exception(exc)
        except Exception as exc:
            st.error("An unexpected error occurred while generating the quiz.")
            with st.expander("Technical details"):
                st.exception(exc)

quiz_data = st.session_state.quizzes.get(quiz_key)
if quiz_data is not None:
    attempt_number = st.session_state.quiz_attempts.get(quiz_key, 0)
    if st.session_state.quiz_results.get(quiz_key) is None:
        st.info("Answer all five questions, then submit your quiz to see your score and explanations.")

    with st.form(key=f"quiz_form_{selected_title}_{attempt_number}"):
        answers = []
        for index, question in enumerate(quiz_data["questions"]):
            st.markdown(f"### Question {index + 1} of {len(quiz_data['questions'])}")
            st.write(question["question"])
            answer = st.radio(
                "Choose one answer",
                options=question["options"],
                index=None,
                key=f"answer_{index}_{selected_title}_{attempt_number}",
                label_visibility="collapsed",
            )
            answers.append(answer)
            if index < len(quiz_data["questions"]) - 1:
                st.markdown("---")
        submitted_quiz = st.form_submit_button("Submit quiz", type="primary", use_container_width=True)

    if submitted_quiz:
        if any(answer is None for answer in answers):
            st.warning("Please answer all five questions before submitting.")
        else:
            result = QuizGrader.grade(Quiz.model_validate(quiz_data), answers)
            st.session_state.quiz_results[quiz_key] = result
            st.rerun()

    result = st.session_state.quiz_results.get(quiz_key)
    if result is not None:
        st.markdown("---")
        score_col, note_col = st.columns([1, 2])
        with score_col:
            st.markdown(
                f'<div class="cb-card"><div class="cb-card-label">Your score</div><div class="cb-card-value">{result["score"]} / {result["total"]}</div></div>',
                unsafe_allow_html=True,
            )
        with note_col:
            if result["score"] == result["total"]:
                st.success("Perfect score — beautifully done!")
            elif result["score"] >= 3:
                st.info("Good work! Review the explanations to strengthen your understanding.")
            else:
                st.info("Keep practicing. Review the lesson and try again.")

        st.subheader("Answer review")
        for index, item in enumerate(result["results"], start=1):
            with st.expander(f"Question {index} · {'Correct' if item['is_correct'] else 'Review this answer'}"):
                st.write(item["question"])
                st.write(f"**Your answer:** {item['selected_answer'] or 'No answer'}")
                st.write(f"**Correct answer:** {item['correct_answer']}")
                st.write(f"**Explanation:** {item['explanation']}")
                st.success("Correct") if item["is_correct"] else st.error("Incorrect")

        if st.button("↻ Retake quiz", key=f"retake_quiz_{selected_title}", type="primary"):
            st.session_state.quiz_results.pop(quiz_key, None)
            st.session_state.quiz_attempts[quiz_key] = attempt_number + 1
            st.rerun()

st.markdown('<div class="cb-footer">ClassBuild · Learn. Practice. Build.</div>', unsafe_allow_html=True)
