"""
Input validation utilities for AI Interview Preparation System.
"""

import re
from typing import Tuple


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> Tuple[bool, str]:
    """Validates email format."""
    if not email or not email.strip():
        return False, "Email address cannot be empty."
    if not EMAIL_REGEX.match(email.strip()):
        return False, "Please enter a valid email address (e.g., candidate@example.com)."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Validates password strength (at least 6 characters)."""
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""


def validate_registration(name: str, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
    """Validates full registration inputs."""
    if not name or len(name.strip()) < 2:
        return False, "Please enter your full name (minimum 2 characters)."
    
    valid_email, email_msg = validate_email(email)
    if not valid_email:
        return False, email_msg
        
    valid_pwd, pwd_msg = validate_password(password)
    if not valid_pwd:
        return False, pwd_msg
        
    if password != confirm_password:
        return False, "Passwords do not match. Please re-enter."
        
    return True, ""


def validate_profile(education: str, skills: str) -> Tuple[bool, str]:
    """Validates profile fields."""
    if not education or len(education.strip()) < 2:
        return False, "Please provide your educational background (e.g., B.Tech in Computer Science)."
    if not skills or len(skills.strip()) < 2:
        return False, "Please provide your technical skills (e.g., Python, SQL, Git)."
    return True, ""


def validate_candidate_answer(answer: str) -> Tuple[bool, str]:
    """Validates submitted candidate answer."""
    if not answer or not answer.strip():
        return False, "Please type your answer before submitting."
    
    words = answer.strip().split()
    if len(words) < 3:
        return False, "Your answer is too short (at least 3 words required for evaluation)."
    
    return True, ""
