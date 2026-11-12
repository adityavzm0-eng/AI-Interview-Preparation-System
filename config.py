"""
Configuration module for AI Interview Preparation System.
Loads environment variables and holds application constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Define base directories
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH)

# Application Metadata
APP_NAME = "PrepAI - AI Interview Preparation System"
APP_TAGLINE = "Master Your Next Technical & HR Interview with Adaptive AI"
APP_VERSION = "1.0.0"

# Gemini & AI Configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

# Database Configuration
DATABASE_NAME = "ai_interview_system.db"
DATABASE_PATH = BASE_DIR / DATABASE_NAME

# Job Roles
JOB_ROLES = [
    "Python Developer",
    "Data Analyst",
    "Data Scientist",
    "Machine Learning Engineer",
    "AI/ML Engineer",
    "Java Developer",
    "Full Stack Developer",
    "SQL Developer",
    "Software Engineer"
]

# Interview Types
INTERVIEW_TYPES = [
    "Technical Interview",
    "HR Interview",
    "Mixed Interview"
]

# Difficulty Levels
DIFFICULTY_LEVELS = [
    "Easy",
    "Medium",
    "Hard"
]

# Question Count Options
QUESTION_COUNT_OPTIONS = [5, 10, 15, 20]

# Experience Levels
EXPERIENCE_LEVELS = [
    "Fresher (0 - 1 years)",
    "Experienced (1 - 3 years)",
    "Experienced (3+ years)"
]

# Evaluation Dimensions & Maximum Scores
EVALUATION_CRITERIA = [
    {"key": "technical_correctness", "label": "Technical Correctness", "max": 10},
    {"key": "conceptual_understanding", "label": "Conceptual Understanding", "max": 10},
    {"key": "relevance", "label": "Relevance & Focus", "max": 10},
    {"key": "clarity", "label": "Clarity & Structure", "max": 10},
    {"key": "completeness", "label": "Completeness & Depth", "max": 10}
]
