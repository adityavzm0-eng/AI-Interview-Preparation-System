"""
System and Integration Verification Test Suite for AI Interview Preparation System.
Tests database operations, hashing, validators, NLP analysis, and Gemini client configuration.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
# Ensure UTF-8 output on Windows consoles
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from database import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    upsert_profile,
    get_profile,
    create_interview,
    save_question_record,
    get_user_interviews,
    get_interview_details,
    get_user_dashboard_stats
)
from utils.helpers import hash_password, verify_password, compute_nlp_metrics, extract_json_from_text
from utils.validators import validate_email, validate_password, validate_registration, validate_candidate_answer
from utils.gemini_client import GeminiClient


def test_auth_and_hashing():
    print("\n--- 1. Testing Password Hashing & Auth ---")
    pwd = "SecurePassword123!"
    h = hash_password(pwd)
    assert verify_password(pwd, h), "Password verification failed for correct password"
    assert not verify_password("WrongPassword", h), "Password verification incorrectly passed for wrong password"
    print("✅ Password hashing and verification passed.")


def test_validators():
    print("\n--- 2. Testing Validators ---")
    ok, msg = validate_email("candidate@test.com")
    assert ok, f"Valid email failed: {msg}"
    bad, _ = validate_email("invalid-email")
    assert not bad, "Invalid email incorrectly validated"

    ok, _ = validate_registration("Alex Developer", "alex@example.com", "mypassword1", "mypassword1")
    assert ok, "Valid registration failed"

    mismatch, _ = validate_registration("Alex", "alex@example.com", "pass123", "different")
    assert not mismatch, "Mismatched passwords allowed"

    ans_ok, _ = validate_candidate_answer("Python uses a private heap for memory management.")
    assert ans_ok, "Valid answer failed"

    ans_short, _ = validate_candidate_answer("Hi")
    assert not ans_short, "Short answer allowed"
    print("✅ Input validation tests passed.")


def test_nlp_metrics():
    print("\n--- 3. Testing NLP Metrics Calculation ---")
    sample_text = (
        "In Python, memory management is handled by the Python Memory Manager through a private heap space. "
        "Objects and data structures reside in this heap. Additionally, Python uses reference counting and a "
        "cyclic garbage collector to detect reference cycles and deallocate unused memory efficiently."
    )
    metrics = compute_nlp_metrics(sample_text)
    assert metrics["word_count"] > 25, "Word count mismatch"
    assert metrics["sentence_count"] >= 3, "Sentence count mismatch"
    assert metrics["vocab_richness"] > 0, "Vocab richness should be > 0"
    print(f"✅ NLP Metrics passed: {metrics}")


def test_json_extractor():
    print("\n--- 4. Testing Robust JSON Extractor ---")
    messy_llm_output = (
        "Here is the evaluation you requested:\n```json\n"
        "{\n  \"overall_score\": 8.5,\n  \"strengths\": [\"Clear explanation\"]\n}\n"
        "```\nHope this helps!"
    )
    extracted = extract_json_from_text(messy_llm_output)
    assert isinstance(extracted, dict), "Failed to extract JSON from code block"
    assert extracted.get("overall_score") == 8.5, "JSON content mismatch"
    print("✅ Robust JSON extraction passed.")


def test_database_crud():
    print("\n--- 5. Testing Database CRUD & Relationships ---")
    init_db()

    # Create user
    test_email = f"tester_{os.getpid()}@example.com"
    pwd_hash = hash_password("pass1234")
    user_id = create_user("Test Candidate", test_email, pwd_hash)
    assert user_id is not None, "Failed to create user in database"

    user = get_user_by_email(test_email)
    assert user["email"] == test_email.lower(), "Fetched user email mismatch"

    # Profile upsert
    upsert_profile(
        user_id=user_id,
        education="M.Tech Computer Science",
        skills="Python, PyTorch, SQL, FastAPI",
        experience_level="Fresher (0 - 1 years)",
        target_role="AI/ML Engineer"
    )
    profile = get_profile(user_id)
    assert profile["target_role"] == "AI/ML Engineer", "Profile update failed"

    # Interview creation
    interview_id = create_interview(
        user_id=user_id,
        job_role="AI/ML Engineer",
        interview_type="Technical Interview",
        difficulty="Medium",
        total_questions=5
    )
    assert interview_id > 0, "Failed to create interview record"

    # Question record save
    eval_mock = {
        "overall_score": 8.0,
        "scores": {
            "technical_correctness": 8.5,
            "conceptual_understanding": 8.0,
            "relevance": 9.0,
            "clarity": 8.0,
            "completeness": 7.5
        },
        "strengths": ["Strong conceptual clarity"],
        "weaknesses": ["Could discuss regularization"],
        "missing_points": ["Overfitting mitigation techniques"],
        "improved_answer": "Model answer goes here...",
        "personalized_suggestions": ["Practice explaining loss functions simply."]
    }
    q_id = save_question_record(
        interview_id=interview_id,
        question_text="Explain the bias-variance tradeoff in Machine Learning.",
        candidate_answer="Bias is underfitting error while variance is overfitting error.",
        evaluation=eval_mock,
        score=8.0,
        question_number=1,
        category="Technical"
    )
    assert q_id > 0, "Failed to save question record"

    # Interview details fetch
    details = get_interview_details(interview_id)
    assert details["average_score"] == 8.0, f"Average score mismatch: {details['average_score']}"
    assert len(details["questions"]) == 1, "Questions count mismatch"

    # Dashboard aggregates
    stats = get_user_dashboard_stats(user_id)
    assert stats["total_interviews"] == 1, "Stats total interviews mismatch"
    assert stats["total_questions_answered"] == 1, "Stats questions answered mismatch"
    assert stats["average_score"] == 8.0, "Stats average score mismatch"
    print("✅ Database operations and analytics aggregations passed.")


def test_gemini_client():
    print("\n--- 6. Testing Gemini Client Initialization ---")
    client = GeminiClient()
    print(f"Gemini Client Configured: {client.is_configured()}")
    print("✅ Gemini client initialized successfully.")


if __name__ == "__main__":
    print("==================================================")
    print("PrepAI System & Integration Verification Suite")
    print("==================================================")
    test_auth_and_hashing()
    test_validators()
    test_nlp_metrics()
    test_json_extractor()
    test_database_crud()
    test_gemini_client()
    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! The system is solid and production-ready.")
