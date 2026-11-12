"""
Interview Simulation Module.
Handles interview configuration, state machine, live question presentation,
answer submission, real-time Gemini evaluation, previous answer review,
and final interview completion report.
"""

import streamlit as st
import plotly.graph_objects as go
from config import JOB_ROLES, INTERVIEW_TYPES, DIFFICULTY_LEVELS, QUESTION_COUNT_OPTIONS
from database import create_interview, save_question_record, get_profile
from modules.question_generator import QuestionGenerator
from modules.answer_evaluator import AnswerEvaluator
from utils.gemini_client import GeminiClient
from utils.validators import validate_candidate_answer


def init_interview_state():
    """Initializes session state variables for interview workflow."""
    if "interview_active" not in st.session_state:
        st.session_state["interview_active"] = False
    if "interview_id" not in st.session_state:
        st.session_state["interview_id"] = None
    if "questions_list" not in st.session_state:
        st.session_state["questions_list"] = []
    if "current_question_index" not in st.session_state:
        st.session_state["current_question_index"] = 0
    if "evaluations_cache" not in st.session_state:
        st.session_state["evaluations_cache"] = {}
    if "interview_completed" not in st.session_state:
        st.session_state["interview_completed"] = False
    if "interview_config" not in st.session_state:
        st.session_state["interview_config"] = {}


def reset_interview():
    """Resets interview state to configuration screen."""
    st.session_state["interview_active"] = False
    st.session_state["interview_id"] = None
    st.session_state["questions_list"] = []
    st.session_state["current_question_index"] = 0
    st.session_state["evaluations_cache"] = {}
    st.session_state["interview_completed"] = False
    st.session_state["interview_config"] = {}


def render_interview_page(gemini_client: GeminiClient):
    """Main interview router rendering either Setup, Active Session, or Completion Report."""
    init_interview_state()

    user = st.session_state.get("user")
    if not user:
        st.warning("Please sign in or register to launch an interview session.")
        return

    # Check API key status banner
    if not gemini_client.is_configured():
        st.info(
            "💡 **Practice Mode Active**: You can practice with industry-curated interview questions. "
            "To enable live Gemini AI generation, add your free key in the sidebar at **⚙️ Configure API Key**."
        )

    if st.session_state["interview_completed"]:
        render_completion_report()
    elif st.session_state["interview_active"]:
        render_active_interview(gemini_client, user)
    else:
        render_interview_setup(gemini_client, user)


# ==========================================
# 1. Interview Setup & Configuration
# ==========================================

def render_interview_setup(gemini_client: GeminiClient, user: dict):
    """Renders the interview configuration screen."""
    st.markdown("## 🎯 Start New AI Mock Interview")
    st.markdown("Configure your custom interview session. Gemini AI will generate tailored questions based on your selections.")

    profile = get_profile(user["id"]) or {}
    default_role = profile.get("target_role", JOB_ROLES[0])
    if default_role not in JOB_ROLES:
        default_role = JOB_ROLES[0]

    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            job_role = st.selectbox(
                "💼 Target Job Role",
                options=JOB_ROLES,
                index=JOB_ROLES.index(default_role),
                help="Questions will be customized according to typical technical requirements for this role."
            )

            interview_type = st.selectbox(
                "🎙️ Interview Type",
                options=INTERVIEW_TYPES,
                index=0,
                help="Choose Technical (coding/system concepts), HR (behavioral/cultural), or a balanced Mixed format."
            )

        with col2:
            difficulty = st.selectbox(
                "📈 Difficulty Level",
                options=DIFFICULTY_LEVELS,
                index=1,
                help="Easy (Foundational/Freshers), Medium (Practical scenarios), Hard (Complex architecture/Edge cases)."
            )

            num_questions = st.selectbox(
                "🔢 Number of Questions",
                options=QUESTION_COUNT_OPTIONS,
                index=0,
                help="Select session length. 5 questions is ideal for a focused 15-minute quick sprint."
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Profile context indicator
        exp = profile.get("experience_level", "Fresher (0 - 1 years)")
        skills = profile.get("skills", "Python, SQL")
        st.caption(f"ℹ️ **Current Candidate Context**: {exp} | Skills: {skills if skills else 'None added'}")

        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            start_clicked = st.button("🚀 Generate Interview & Begin", type="primary", use_container_width=True)

        if start_clicked:
            loading_msg = "🤖 Google Gemini is crafting your custom interview questions..." if gemini_client.is_configured() else "📋 Preparing curated interview questions..."
            with st.spinner(loading_msg):
                q_generator = QuestionGenerator(gemini_client)
                success, questions, error_msg = q_generator.generate_interview_questions(
                    job_role=job_role,
                    interview_type=interview_type,
                    difficulty=difficulty,
                    total_questions=num_questions,
                    candidate_profile=profile
                )

                if not success or not questions:
                    st.error(f"Failed to generate questions: {error_msg}")
                    return
                    return

                # Create interview in SQLite
                interview_id = create_interview(
                    user_id=user["id"],
                    job_role=job_role,
                    interview_type=interview_type,
                    difficulty=difficulty,
                    total_questions=len(questions)
                )

                # Update session state
                st.session_state["interview_active"] = True
                st.session_state["interview_id"] = interview_id
                st.session_state["questions_list"] = questions
                st.session_state["current_question_index"] = 0
                st.session_state["evaluations_cache"] = {}
                st.session_state["interview_completed"] = False
                st.session_state["interview_config"] = {
                    "job_role": job_role,
                    "interview_type": interview_type,
                    "difficulty": difficulty,
                    "total_questions": len(questions)
                }
                st.rerun()


# ==========================================
# 2. Active Interview Session
# ==========================================

def render_active_interview(gemini_client: GeminiClient, user: dict):
    """Renders active question, submission area, real-time AI evaluation, and navigation."""
    questions = st.session_state["questions_list"]
    idx = st.session_state["current_question_index"]
    total = len(questions)

    if idx >= total:
        st.session_state["interview_completed"] = True
        st.rerun()
        return

    q_data = questions[idx]
    q_num = idx + 1
    config = st.session_state.get("interview_config", {})

    # Header & Progress Bar
    progress_val = (idx) / total
    st.progress(progress_val)

    hdr_col1, hdr_col2 = st.columns([3, 1])
    with hdr_col1:
        st.markdown(f"### 📝 Question {q_num} of {total}")
        st.caption(f"Role: **{config.get('job_role', 'Technical')}** | Type: **{config.get('interview_type')}** | Difficulty: **{q_data.get('difficulty')}**")
    with hdr_col2:
        category = q_data.get("category", "Technical")
        cat_badge = "#2563EB" if category == "Technical" else ("#7C3AED" if category == "HR" else "#059669")
        st.markdown(
            f"""<div style="text-align: right; margin-top: 0.5rem;">
                <span style="background-color: {cat_badge}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;">{category}</span>
            </div>""",
            unsafe_allow_html=True
        )

    # Question Box
    st.markdown(
        f"""
        <div style="background-color: #F8FAFC; border-left: 5px solid #2563EB; padding: 1.25rem; border-radius: 8px; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 1.15rem; font-weight: 600; color: #1E293B; line-height: 1.5;">
                {q_data.get('question_text')}
            </div>
            <div style="margin-top: 0.75rem; font-size: 0.85rem; color: #64748B;">
                🎯 <strong>Key Topic:</strong> {q_data.get('core_concept', 'General Competency')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fresher Hint Accordion
    with st.expander("💡 View Fresher Guidance & Answering Tips"):
        st.info(q_data.get("hint_for_fresher", "Structure your answer using concrete examples, principles, and trade-offs."))
        if q_data.get("expected_points"):
            st.markdown("**Interviewer Expectations:**")
            for pt in q_data.get("expected_points", []):
                st.markdown(f"- {pt}")

    # Answer input
    current_eval = st.session_state["evaluations_cache"].get(q_num)
    saved_answer = current_eval["candidate_answer"] if current_eval else ""

    candidate_answer = st.text_area(
        "✍️ Your Answer:",
        value=saved_answer,
        height=180,
        placeholder="Type your structured answer here. Include definitions, practical scenarios, examples, and trade-offs...",
        key=f"answer_input_{q_num}",
        disabled=bool(current_eval)
    )

    # Word count helper
    words = len(candidate_answer.strip().split()) if candidate_answer.strip() else 0
    st.caption(f"Word count: **{words}** words")

    # Action Buttons
    col_sub, col_next, col_abort = st.columns([2, 2, 1])

    with col_sub:
        if not current_eval:
            submit_clicked = st.button("✅ Submit Answer & Get AI Feedback", type="primary", use_container_width=True)
            if submit_clicked:
                valid, msg = validate_candidate_answer(candidate_answer)
                if not valid:
                    st.error(msg)
                else:
                    with st.spinner("🤖 Gemini AI is analyzing your answer across 5 dimensions..."):
                        profile = get_profile(user["id"]) or {}
                        evaluator = AnswerEvaluator(gemini_client)
                        success, eval_dict, error = evaluator.evaluate_answer(
                            question_data=q_data,
                            candidate_answer=candidate_answer,
                            job_role=config.get("job_role", "Developer"),
                            experience_level=profile.get("experience_level", "Fresher")
                        )

                        if not success:
                            st.error(f"Evaluation failed: {error}")
                        else:
                            # Save to SQLite
                            save_question_record(
                                interview_id=st.session_state["interview_id"],
                                question_text=q_data.get("question_text"),
                                candidate_answer=candidate_answer,
                                evaluation=eval_dict,
                                score=eval_dict["overall_score"],
                                question_number=q_num,
                                category=q_data.get("category", "Technical")
                            )

                            # Save to cache
                            st.session_state["evaluations_cache"][q_num] = {
                                "candidate_answer": candidate_answer,
                                "evaluation": eval_dict,
                                "question_data": q_data
                            }
                            st.rerun()

    with col_next:
        if current_eval:
            btn_label = "🏁 Finish & View Final Report" if q_num == total else "➡️ Next Question"
            if st.button(btn_label, type="primary", use_container_width=True):
                st.session_state["current_question_index"] += 1
                st.rerun()

    with col_abort:
        if st.button("⏹️ Quit Interview", help="Abandon current interview session"):
            reset_interview()
            st.rerun()

    # Display Evaluation Results if answered
    if current_eval:
        st.markdown("---")
        render_question_evaluation_card(current_eval["evaluation"])

    # Review Previous Answers Section
    render_previous_answers_expander()


# ==========================================
# 3. Question Evaluation Card
# ==========================================

def render_question_evaluation_card(evaluation: dict):
    """Renders the multidimensional evaluation card for a single question."""
    st.markdown("### 📊 AI Evaluation & Scoring")

    overall = evaluation.get("overall_score", 0.0)
    score_color = "#10B981" if overall >= 7.5 else ("#F59E0B" if overall >= 5.0 else "#EF4444")

    # Header metric
    m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1])
    with m1:
        st.markdown(
            f"""
            <div style="background-color: {score_color}; color: white; padding: 1rem; border-radius: 8px; text-align: center;">
                <div style="font-size: 0.85rem; font-weight: 500; text-transform: uppercase;">Overall Score</div>
                <div style="font-size: 2.2rem; font-weight: 800;">{overall} / 10</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    nlp = evaluation.get("nlp_metrics", {})
    with m2:
        st.metric("Words Analyzed", nlp.get("word_count", 0))
    with m3:
        st.metric("Vocab Richness", f"{nlp.get('vocab_richness', 0)}%")
    with m4:
        st.metric("Structure", nlp.get("structure_rating", "Standard"))

    # Dimension scores breakdown
    st.markdown("#### Dimension Breakdown")
    scores = evaluation.get("scores", {})
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Technical", f"{scores.get('technical_correctness', 0)}/10")
    c2.metric("Conceptual", f"{scores.get('conceptual_understanding', 0)}/10")
    c3.metric("Relevance", f"{scores.get('relevance', 0)}/10")
    c4.metric("Clarity", f"{scores.get('clarity', 0)}/10")
    c5.metric("Completeness", f"{scores.get('completeness', 0)}/10")

    # Radar Chart
    categories = ['Technical', 'Conceptual', 'Relevance', 'Clarity', 'Completeness']
    vals = [
        scores.get('technical_correctness', 0),
        scores.get('conceptual_understanding', 0),
        scores.get('relevance', 0),
        scores.get('clarity', 0),
        scores.get('completeness', 0)
    ]

    fig = go.Figure(data=go.Scatterpolar(
        r=vals + [vals[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.25)',
        line=dict(color='#2563EB', width=2)
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=10)),
        ),
        showlegend=False,
        height=280,
        margin=dict(l=40, r=40, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Strengths & Weaknesses
    col_str, col_weak = st.columns(2)
    with col_str:
        st.markdown("##### 🌟 What You Did Well")
        for s in evaluation.get("strengths", []):
            st.markdown(f"- ✅ {s}")

    with col_weak:
        st.markdown("##### ⚠️ Areas for Improvement")
        for w in evaluation.get("weaknesses", []):
            st.markdown(f"- 🔸 {w}")

    # Missing important points
    missing = evaluation.get("missing_points", [])
    if missing:
        st.markdown("##### 🔍 Important Points You Missed")
        for m in missing:
            st.markdown(f"- ⭕ {m}")

    # Model / Improved Answer
    improved = evaluation.get("improved_answer")
    if improved and improved != "N/A":
        with st.expander("📖 View Model 10/10 Answer"):
            st.markdown(
                f"""
                <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 1rem; color: #166534; font-size: 0.95rem; line-height: 1.6;">
                    {improved}
                </div>
                """,
                unsafe_allow_html=True
            )

    # Personalized Suggestions for freshers
    suggs = evaluation.get("personalized_suggestions", [])
    if suggs:
        st.markdown("##### 💡 Freshers Interview Tips for this Question")
        for tip in suggs:
            st.markdown(f"- 📌 {tip}")


# ==========================================
# 4. Review Previous Answers Accordion
# ==========================================

def render_previous_answers_expander():
    """Shows previously submitted answers in an expandable drawer."""
    cache = st.session_state.get("evaluations_cache", {})
    if not cache:
        return

    with st.expander(f"📑 Review Previously Completed Questions ({len(cache)} answered)"):
        for q_num, data in sorted(cache.items()):
            st.markdown(f"**Question {q_num}:** {data['question_data'].get('question_text')}")
            st.markdown(f"*Your Answer:* {data['candidate_answer']}")
            score = data['evaluation'].get('overall_score', 0)
            st.caption(f"Score: **{score}/10**")
            st.markdown("---")


# ==========================================
# 5. Interview Completion Report
# ==========================================

def render_completion_report():
    """Renders comprehensive final report with charts and download option."""
    st.markdown("## 🏆 Interview Completed!")
    st.markdown("Congratulations! You have completed all questions in this session. Here is your holistic performance report.")

    cache = st.session_state.get("evaluations_cache", {})
    config = st.session_state.get("interview_config", {})

    if not cache:
        st.warning("No answers found in this session.")
        if st.button("Start New Session"):
            reset_interview()
            st.rerun()
        return

    # Calculate overall average
    scores = [item["evaluation"].get("overall_score", 0.0) for item in cache.values()]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

    # Determine Tier
    if avg_score >= 8.5:
        tier_title = "Exceptional - Strong Hire"
        tier_color = "#10B981"
        tier_desc = "You demonstrated deep conceptual mastery, precise industry terminology, and thorough completeness."
    elif avg_score >= 7.0:
        tier_title = "Proficient - Hire Ready"
        tier_color = "#3B82F6"
        tier_desc = "Good technical grasp with solid foundational explanations. Refining edge cases and depth will elevate you to the top 5%."
    elif avg_score >= 5.0:
        tier_title = "Developing - Practice Recommended"
        tier_color = "#F59E0B"
        tier_desc = "Solid basic intuition, but answers need more technical depth, structure, and relevant industry terminology."
    else:
        tier_title = "Needs Focus - Fundamental Review"
        tier_color = "#EF4444"
        tier_desc = "Recommend revisiting fundamental topics, standard syntax, and practicing with real-world scenarios."

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, {tier_color}15 0%, {tier_color}30 100%); border: 2px solid {tier_color}; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; text-align: center;">
            <div style="font-size: 0.9rem; text-transform: uppercase; font-weight: 700; color: {tier_color}; letter-spacing: 1px;">Overall Performance Tier</div>
            <h2 style="color: {tier_color}; margin: 0.3rem 0; font-size: 2.2rem;">{tier_title}</h2>
            <div style="font-size: 3rem; font-weight: 900; color: #1E293B;">{avg_score} <span style="font-size: 1.5rem; font-weight: 500; color: #64748B;">/ 10</span></div>
            <p style="color: #475569; max-width: 600px; margin: 0.5rem auto 0 auto; font-size: 1rem;">{tier_desc}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Question by Question Score Progression
    q_labels = [f"Q{q_num}" for q_num in sorted(cache.keys())]
    q_scores = [cache[q]["evaluation"].get("overall_score", 0.0) for q in sorted(cache.keys())]

    fig_bar = go.Figure(data=[
        go.Bar(
            x=q_labels,
            y=q_scores,
            marker_color='#3B82F6',
            text=[f"{s}/10" for s in q_scores],
            textposition='auto',
        )
    ])
    fig_bar.update_layout(
        title="Score per Question",
        yaxis=dict(range=[0, 10], title="Score (out of 10)"),
        xaxis=dict(title="Question Number"),
        height=320,
        margin=dict(l=40, r=40, t=40, b=30)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Detailed Accordion of Questions and Feedback
    st.markdown("### 📋 Full Session Review & Improved Answers")
    for q_num, data in sorted(cache.items()):
        q_text = data["question_data"].get("question_text")
        eval_data = data["evaluation"]
        sc = eval_data.get("overall_score", 0)

        with st.expander(f"Question {q_num} (Score: {sc}/10) - {q_text[:70]}..."):
            st.markdown(f"**Full Question:** {q_text}")
            st.markdown(f"**Your Answer:**\n> {data['candidate_answer']}")
            render_question_evaluation_card(eval_data)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 Start Another Interview", type="primary", use_container_width=True):
            reset_interview()
            st.rerun()
    with c2:
        if st.button("📊 Go to Performance Dashboard", use_container_width=True):
            reset_interview()
            st.session_state["nav_selection"] = "Dashboard"
            st.rerun()
