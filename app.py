import streamlit as st
from pydantic import ValidationError
from pathlib import Path
from classbuild.course_config import CourseConfig
from classbuild.llm import GroqClient
from classbuild.llm.exceptions import GroqClientError
from classbuild.models.quiz import Quiz
from classbuild.services.course_generator import CourseGenerator, CourseGenerationError
from classbuild.services.lesson_generator import LessonGenerator, LessonGenerationError
from classbuild.services.quiz_generator import QuizGenerator, QuizGenerationError
from classbuild.services.quiz_grader import QuizGrader


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
        st.session_state.course_config = new_config
        try:
            with st.spinner("Designing your course outline..."):
                course = CourseGenerator(GroqClient()).generate(config)
            st.session_state.course_outline = course.model_dump()
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

cache_key = (course_config["topic"], course_config["difficulty"], course_config["lesson_count"], selected_title)
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
                generated_lesson = LessonGenerator(GroqClient()).generate(
                    lesson_title=selected_title,
                    learning_objectives=selected_lesson["learning_objectives"],
                    difficulty=course_config["difficulty"],
                    course_topic=course_config["topic"],
                )
            st.session_state.lesson_contents[cache_key] = generated_lesson.model_dump()
            st.success("Lesson content generated and saved.")
            st.rerun()
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
