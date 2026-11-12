"""
Candidate Profile module.
Allows users to view and update their educational background, technical skills,
experience level, and target job role.
"""

import streamlit as st
from config import JOB_ROLES, EXPERIENCE_LEVELS
from database import get_profile, upsert_profile, get_user_by_id
from utils.validators import validate_profile


def render_profile_page():
    """Renders candidate profile view and edit interface."""
    user = st.session_state.get("user")
    if not user:
        st.warning("Please log in to manage your profile.")
        return

    user_id = user["id"]
    current_user = get_user_by_id(user_id) or user
    profile = get_profile(user_id) or {}

    st.markdown("## 👤 Candidate Profile")
    st.markdown("Customize your profile so Gemini AI generates questions accurately matched to your skill set and background.")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); color: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                <div style="font-size: 2.5rem; text-align: center; margin-bottom: 0.5rem;">👨‍💻</div>
                <h3 style="text-align: center; margin: 0; color: white;">{current_user.get('name', 'Candidate')}</h3>
                <p style="text-align: center; opacity: 0.85; font-size: 0.9rem; margin-top: 0.2rem;">{current_user.get('email', '')}</p>
                <hr style="border-color: rgba(255,255,255,0.2); margin: 1rem 0;">
                <p style="margin: 0.3rem 0; font-size: 0.9rem;"><strong>Target Role:</strong><br>{profile.get('target_role') or 'Not Set'}</p>
                <p style="margin: 0.3rem 0; font-size: 0.9rem;"><strong>Experience:</strong><br>{profile.get('experience_level') or 'Fresher'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 **Pro Tip**: Keep your technical skills up-to-date. The question generator uses these to personalize interview questions and evaluation depth.")

    with col2:
        with st.form("profile_form"):
            st.markdown("#### Edit Profile Details")

            # Name and Email display
            st.text_input("Full Name", value=current_user.get("name", ""), disabled=True)
            st.text_input("Email", value=current_user.get("email", ""), disabled=True)

            # Target Role
            default_role_idx = 0
            if profile.get("target_role") in JOB_ROLES:
                default_role_idx = JOB_ROLES.index(profile["target_role"])
            target_role = st.selectbox("Target Job Role", JOB_ROLES, index=default_role_idx)

            # Experience Level
            default_exp_idx = 0
            if profile.get("experience_level") in EXPERIENCE_LEVELS:
                default_exp_idx = EXPERIENCE_LEVELS.index(profile["experience_level"])
            experience_level = st.selectbox("Experience Level", EXPERIENCE_LEVELS, index=default_exp_idx)

            # Education
            education = st.text_input(
                "Education / Degree",
                value=profile.get("education", ""),
                placeholder="e.g. B.Tech in Computer Science & Engineering (2025)"
            )

            # Skills
            skills = st.text_area(
                "Technical Skills & Tools (comma-separated)",
                value=profile.get("skills", ""),
                placeholder="e.g. Python, SQL, Pandas, Scikit-Learn, Git, FastAPI, Docker",
                help="List languages, frameworks, databases, and core concepts you are proficient in."
            )

            save_submitted = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

            if save_submitted:
                valid, msg = validate_profile(education, skills)
                if not valid:
                    st.error(msg)
                else:
                    success = upsert_profile(
                        user_id=user_id,
                        education=education,
                        skills=skills,
                        experience_level=experience_level,
                        target_role=target_role
                    )
                    if success:
                        st.success("Profile updated successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to update profile. Please try again.")
