"""
Dashboard and Interview History module.
Provides interactive Plotly visualizations, aggregate statistics,
and detailed interview history exploration.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_user_dashboard_stats, get_user_interviews, get_interview_details
from modules.interview import render_question_evaluation_card


def render_dashboard_page():
    """Renders high-level performance metrics and Plotly charts."""
    user = st.session_state.get("user")
    if not user:
        st.warning("Please sign in to view your performance dashboard.")
        return

    st.markdown("## 📊 Performance Analytics Dashboard")
    st.markdown("Track your interview preparation velocity, score trajectories, and competency breakdown over time.")

    stats = get_user_dashboard_stats(user["id"])

    # Metric Cards Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Total Interviews</div>
                <div style="color: #1E293B; font-size: 2rem; font-weight: 800; margin-top: 0.2rem;">{stats['total_interviews']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Questions Practiced</div>
                <div style="color: #2563EB; font-size: 2rem; font-weight: 800; margin-top: 0.2rem;">{stats['total_questions_answered']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Average Score</div>
                <div style="color: #059669; font-size: 2rem; font-weight: 800; margin-top: 0.2rem;">{stats['average_score']} <span style="font-size: 1rem; color: #64748B;">/ 10</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            f"""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="color: #64748B; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Best Performance</div>
                <div style="color: #7C3AED; font-size: 2rem; font-weight: 800; margin-top: 0.2rem;">{stats['highest_score']} <span style="font-size: 1rem; color: #64748B;">/ 10</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if stats["total_interviews"] == 0:
        st.info("👋 You haven't completed any mock interviews yet! Go to **Start Interview** in the sidebar to begin your first session.")
        return

    # Visualizations Row 1: Score Progression Over Time
    st.markdown("### 📈 Score Progression & Improvement Trajectory")
    prog_data = stats.get("progression", [])
    if prog_data:
        df_prog = pd.DataFrame(prog_data)
        df_prog["session_num"] = range(1, len(df_prog) + 1)
        df_prog["label"] = df_prog["job_role"] + " (" + df_prog["difficulty"] + ")"

        fig_prog = px.line(
            df_prog,
            x="session_num",
            y="average_score",
            markers=True,
            hover_data=["label", "interview_type", "created_at"],
            labels={"session_num": "Interview Session #", "average_score": "Average Score (/10)"},
            title="Interview Performance Trend"
        )
        fig_prog.update_traces(
            line=dict(color="#2563EB", width=3),
            marker=dict(size=8, color="#1E3A8A")
        )
        fig_prog.update_layout(
            yaxis=dict(range=[0, 10]),
            height=320,
            margin=dict(l=40, r=40, t=40, b=30)
        )
        st.plotly_chart(fig_prog, use_container_width=True)

    # Visualizations Row 2: Technical vs HR and Difficulty Breakdown
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        st.markdown("### 🎙️ Technical vs HR Performance")
        type_data = stats.get("type_breakdown", [])
        if type_data:
            df_type = pd.DataFrame(type_data)
            df_type["avg_score"] = df_type["avg_score"].round(2)
            fig_type = px.bar(
                df_type,
                x="interview_type",
                y="avg_score",
                color="interview_type",
                text="avg_score",
                labels={"interview_type": "Interview Type", "avg_score": "Average Score"},
                color_discrete_sequence=["#3B82F6", "#8B5CF6", "#10B981"]
            )
            fig_type.update_layout(
                yaxis=dict(range=[0, 10]),
                showlegend=False,
                height=300,
                margin=dict(l=30, r=30, t=30, b=30)
            )
            st.plotly_chart(fig_type, use_container_width=True)

    with col_v2:
        st.markdown("### 🎯 Score by Difficulty Level")
        diff_data = stats.get("difficulty_breakdown", [])
        if diff_data:
            df_diff = pd.DataFrame(diff_data)
            df_diff["avg_score"] = df_diff["avg_score"].round(2)
            fig_diff = px.bar(
                df_diff,
                x="difficulty",
                y="avg_score",
                color="difficulty",
                text="avg_score",
                labels={"difficulty": "Difficulty", "avg_score": "Average Score"},
                color_discrete_map={"Easy": "#10B981", "Medium": "#F59E0B", "Hard": "#EF4444"}
            )
            fig_diff.update_layout(
                yaxis=dict(range=[0, 10]),
                showlegend=False,
                height=300,
                margin=dict(l=30, r=30, t=30, b=30)
            )
            st.plotly_chart(fig_diff, use_container_width=True)

    # Recent Interviews Table
    st.markdown("### 🕒 Recent Interview History")
    recent_interviews = get_user_interviews(user["id"])[:5]
    if recent_interviews:
        rec_data = []
        for r in recent_interviews:
            rec_data.append({
                "Date": r["created_at"],
                "Job Role": r["job_role"],
                "Type": r["interview_type"],
                "Difficulty": r["difficulty"],
                "Questions": r["total_questions"],
                "Avg Score (/10)": r["average_score"]
            })
        st.dataframe(pd.DataFrame(rec_data), use_container_width=True, hide_index=True)


# ==========================================
# Interview History Explorer
# ==========================================

def render_history_page():
    """Renders comprehensive history with filtering and deep-dive question reviews."""
    user = st.session_state.get("user")
    if not user:
        st.warning("Please sign in to view your interview history.")
        return

    st.markdown("## 📜 Complete Interview History")
    st.markdown("Review all past interviews, inspect AI evaluations, and analyze model answers for questions you answered.")

    interviews = get_user_interviews(user["id"])
    if not interviews:
        st.info("You haven't completed any mock interviews yet. Launch your first one under **Start Interview**!")
        return

    # Filter controls
    f_col1, f_col2, f_col3 = st.columns(3)
    roles = ["All Roles"] + sorted(list({i["job_role"] for i in interviews}))
    types = ["All Types"] + sorted(list({i["interview_type"] for i in interviews}))
    diffs = ["All Difficulties"] + sorted(list({i["difficulty"] for i in interviews}))

    with f_col1:
        sel_role = st.selectbox("Filter by Role", roles)
    with f_col2:
        sel_type = st.selectbox("Filter by Type", types)
    with f_col3:
        sel_diff = st.selectbox("Filter by Difficulty", diffs)

    filtered = [
        i for i in interviews
        if (sel_role == "All Roles" or i["job_role"] == sel_role)
        and (sel_type == "All Types" or i["interview_type"] == sel_type)
        and (sel_diff == "All Difficulties" or i["difficulty"] == sel_diff)
    ]

    st.caption(f"Showing **{len(filtered)}** of **{len(interviews)}** total recorded sessions.")
    st.markdown("---")

    # Render each interview as a full drilldown card
    for item in filtered:
        item_id = item["id"]
        role = item["job_role"]
        itype = item["interview_type"]
        diff = item["difficulty"]
        score = item["average_score"]
        created = item["created_at"]
        q_cnt = item["total_questions"]

        score_color = "#10B981" if score >= 7.5 else ("#F59E0B" if score >= 5.0 else "#EF4444")

        with st.expander(f"📅 {created} | {role} - {itype} ({diff}) | Score: {score}/10"):
            h_col1, h_col2, h_col3 = st.columns([1, 2, 1])
            with h_col1:
                st.markdown(
                    f"""
                    <div style="background-color: {score_color}20; border-left: 4px solid {score_color}; padding: 0.75rem; border-radius: 4px;">
                        <span style="font-size: 0.8rem; color: #64748B;">Average Score</span>
                        <div style="font-size: 1.5rem; font-weight: 700; color: {score_color};">{score} / 10</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with h_col2:
                st.markdown(f"**Role:** {role}  \n**Type:** {itype}  \n**Difficulty:** {diff}")
            with h_col3:
                st.markdown(f"**Total Questions:** {q_cnt}  \n**Date:** {created[:10]}")

            # Fetch detailed questions
            details = get_interview_details(item_id)
            if details and details.get("questions"):
                st.markdown("#### Questions & AI Evaluations")
                for q in details["questions"]:
                    st.markdown(f"**Question {q['question_number']} ({q.get('category', 'Technical')}):** {q['question_text']}")
                    st.markdown(f"*Your Answer:* {q['candidate_answer']}")
                    
                    eval_obj = q.get("evaluation")
                    if isinstance(eval_obj, dict) and eval_obj:
                        render_question_evaluation_card(eval_obj)
                    else:
                        st.caption(f"Score: {q.get('score', 0)}/10")
                    st.markdown("---")
            else:
                st.caption("No individual question records found for this session.")
