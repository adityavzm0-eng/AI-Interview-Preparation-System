"""
PrepAI - AI Interview Preparation System
Main Streamlit Application Entrypoint.
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Page configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="PrepAI - AI Interview Preparation System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment & imports
from config import APP_NAME, APP_TAGLINE, APP_VERSION, GEMINI_API_KEY
from database import init_db
from utils.gemini_client import GeminiClient
from modules.authentication import init_auth_session, render_auth_page, logout_user
from modules.profile import render_profile_page
from modules.interview import render_interview_page
from modules.dashboard import render_dashboard_page, render_history_page

# Load custom CSS
css_file = Path(__file__).resolve().parent / "assets" / "style.css"
if css_file.exists():
    with open(css_file, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_gemini_client() -> GeminiClient:
    """Initializes or retrieves cached GeminiClient instance."""
    if "gemini_client" not in st.session_state:
        # Check session key or env
        key = st.session_state.get("custom_api_key", GEMINI_API_KEY)
        st.session_state["gemini_client"] = GeminiClient(api_key=key)
    return st.session_state["gemini_client"]


def render_about_page():
    """Renders comprehensive documentation and platform features."""
    st.markdown("## ℹ️ About PrepAI Studio")
    st.markdown(
        """
        **PrepAI** is an advanced, production-grade AI Interview Simulator and Performance Feedback Engine designed for 
        freshers, college graduates, and experienced software engineers to prepare for technical, HR, and mixed interviews.

        ### 🌟 Core Architectural Features
        1. **Adaptive Question Generation**:
           - Powered by **Google Gemini API** (`gemini-1.5-flash` / `gemini-2.0-flash`).
           - Real-time question synthesis tailored to target role, candidate experience level, and difficulty.
           - Zero question repetition within the same interview cycle.
        
        2. **Multidimensional Answer Evaluation**:
           - Evaluates responses across **5 core industry dimensions**:
             - *Technical Correctness*
             - *Conceptual Understanding*
             - *Relevance & Focus*
             - *Clarity & Communication*
             - *Completeness & Edge Cases*
           - Delivers constructive feedback suitable for freshers including **Strengths**, **Weaknesses**, **Missing Points**, and a **10/10 Model Answer**.

        3. **NLP-Powered Text Analytics**:
           - Local analysis calculating word count, vocabulary richness (Type-Token Ratio), reading time, and sentence structure complexity.

        4. **Interactive Plotly Visualizations**:
           - Radar skill charts, score progression over time, technical vs. HR comparative breakdowns, and difficulty distributions.

        5. **Secure SQLite Architecture**:
           - Full relational schema with cascading foreign keys storing user accounts, candidate profiles, interview sessions, and individual evaluations.

        ---
        ### 🛠️ Technology Stack
        - **Frontend**: Streamlit
        - **Language Model**: Google Gemini API (with optional OpenAI fallback)
        - **NLP & Analysis**: Text preprocessing, Type-Token Ratio, lexical density
        - **Database**: SQLite 3 with context management
        - **Data Visualization**: Plotly Express & Graph Objects
        - **Security**: Salted SHA-256 / Bcrypt password hashing
        """
    )


def main():
    # Initialize SQLite database
    init_db()

    # Initialize user session state
    init_auth_session()

    # Initialize Gemini client
    gemini_client = load_gemini_client()

    # Check authentication
    if not st.session_state.get("is_authenticated"):
        render_auth_page()
        return

    user = st.session_state.get("user")

    # Sidebar Navigation & User Info
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 1rem;">
                <h2 style="color: #1E3A8A; margin: 0; font-size: 1.5rem; font-weight: 800;">🎯 PrepAI</h2>
                <div style="font-size: 0.8rem; color: #64748B;">AI Mock Interview Platform</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(f"👤 Signed in as **{user['name']}**")
        st.caption(f"{user['email']}")

        st.markdown("---")

        # Navigation Options
        pages = ["Dashboard", "Start Interview", "Interview History", "My Profile", "About"]
        
        # Check if programmatic nav was requested
        current_nav = st.session_state.get("nav_selection", "Dashboard")
        default_index = pages.index(current_nav) if current_nav in pages else 0

        selection = st.radio(
            "Navigation",
            pages,
            index=default_index,
            key="sidebar_nav_radio"
        )
        st.session_state["nav_selection"] = selection

        st.markdown("---")

        # Gemini API Key Status & Config
        st.markdown("##### 🤖 AI Model Configuration")
        active_provider = gemini_client.get_provider().upper()
        if gemini_client.is_configured():
            st.success(f"🟢 Provider: {active_provider}")
        else:
            st.info("🟡 Practice Mode (NLP Engine Active)")

        with st.expander("⚙️ Configure API Key", expanded=not gemini_client.is_configured()):
            st.markdown(
                """
                **💡 Recommended: Google Gemini API (100% Free)**
                Get your free API key at [aistudio.google.com](https://aistudio.google.com/app/apikey).
                *(No credit card required).*
                """
            )
            current_val = st.session_state.get("custom_api_key", GEMINI_API_KEY)
            user_key_input = st.text_input(
                "Paste API Key (Gemini or OpenAI)",
                value=current_val,
                type="password",
                placeholder="AIzaSy... or sk-..."
            )
            
            # Show detected provider
            clean_input = user_key_input.strip()
            if clean_input.startswith("AIzaSy"):
                detected = "Google Gemini"
            elif clean_input.startswith("sk-"):
                detected = "OpenAI"
            else:
                detected = "Auto-detect"
            st.caption(f"Detected key type: **{detected}**")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("💾 Save Key", use_container_width=True, type="primary"):
                    if clean_input:
                        st.session_state["custom_api_key"] = clean_input
                        gemini_client.set_api_key(clean_input, provider="auto", persist=True)
                        st.success("API key saved!")
                        st.rerun()
            with btn_col2:
                if st.button("🧪 Test Key", use_container_width=True):
                    if clean_input:
                        gemini_client.set_api_key(clean_input, provider="auto", persist=False)
                        with st.spinner("Testing API connection..."):
                            valid, status_msg = gemini_client.test_connection()
                            if valid:
                                st.success("✅ " + status_msg)
                            else:
                                st.error("❌ " + status_msg)
                    else:
                        st.warning("Please paste an API key first.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()

    # Route Page
    if selection == "Dashboard":
        render_dashboard_page()
    elif selection == "Start Interview":
        render_interview_page(gemini_client)
    elif selection == "Interview History":
        render_history_page()
    elif selection == "My Profile":
        render_profile_page()
    elif selection == "About":
        render_about_page()


if __name__ == "__main__":
    main()
