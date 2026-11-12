"""
User Authentication module.
Handles user registration, login, logout, and session lifecycle.
"""

import streamlit as st
from database import create_user, get_user_by_email
from utils.helpers import hash_password, verify_password
from utils.validators import validate_registration, validate_email


def init_auth_session():
    """Initializes user authentication keys in session state."""
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False


def login_user(user_dict: dict):
    """Sets authenticated user session."""
    st.session_state["user"] = user_dict
    st.session_state["is_authenticated"] = True


def logout_user():
    """Clears user session and resets interview state."""
    st.session_state["user"] = None
    st.session_state["is_authenticated"] = False
    st.session_state["current_interview"] = None
    st.session_state["interview_state"] = None
    st.rerun()


def render_auth_page():
    """Renders modern login and registration forms."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: #1E3A8A; font-weight: 800; font-size: 2.5rem; margin-bottom: 0.3rem;">PrepAI Studio</h1>
            <p style="color: #4B5563; font-size: 1.1rem;">Your AI-Powered Mock Interviewer & Feedback Engine</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])

        with tab_login:
            st.markdown("### Welcome Back")
            st.caption("Sign in to access your interview simulator and analytics dashboard.")
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email Address", placeholder="e.g. candidate@example.com").strip()
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In to PrepAI", use_container_width=True, type="primary")

                if submitted:
                    valid_email, email_err = validate_email(email)
                    if not valid_email:
                        st.error(email_err)
                    elif not password:
                        st.error("Please enter your password.")
                    else:
                        user = get_user_by_email(email)
                        if not user:
                            st.error("No account found with this email address. Please register.")
                        elif not verify_password(password, user["password_hash"]):
                            st.error("Incorrect password. Please try again.")
                        else:
                            login_user(user)
                            st.success(f"Welcome back, {user['name']}!")
                            st.rerun()

        with tab_register:
            st.markdown("### Join PrepAI")
            st.caption("Create an account to start practicing tailored technical and HR interviews.")
            with st.form("register_form", clear_on_submit=True):
                reg_name = st.text_input("Full Name", placeholder="e.g. John Doe").strip()
                reg_email = st.text_input("Email Address", placeholder="e.g. john@example.com").strip()
                reg_password = st.text_input("Password (min 6 characters)", type="password", placeholder="Create a strong password")
                reg_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                reg_submitted = st.form_submit_button("Create Free Account", use_container_width=True, type="primary")

                if reg_submitted:
                    valid, err = validate_registration(reg_name, reg_email, reg_password, reg_confirm)
                    if not valid:
                        st.error(err)
                    else:
                        existing = get_user_by_email(reg_email)
                        if existing:
                            st.warning("An account with this email already exists. Please sign in.")
                        else:
                            pwd_hash = hash_password(reg_password)
                            new_id = create_user(reg_name, reg_email, pwd_hash)
                            if new_id:
                                st.success("Account created successfully! You can now log in.")
                            else:
                                st.error("Failed to create account. Please try again.")
