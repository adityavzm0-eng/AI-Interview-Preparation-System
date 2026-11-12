"""
Helper functions for password hashing, NLP answer analysis, and JSON parsing.
"""

import json
import re
import hashlib
from typing import Dict, Any, Optional

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


# ==========================================
# Password Security
# ==========================================

def hash_password(password: str) -> str:
    """Hashes a password securely using bcrypt or salt-hashed SHA-256."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    else:
        # Fallback salt-hash
        salt = "PrepAI_SecureSalt_2026"
        return "sha256$" + hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against stored hash."""
    if not plain_password or not hashed_password:
        return False
    
    if hashed_password.startswith("sha256$"):
        salt = "PrepAI_SecureSalt_2026"
        computed = "sha256$" + hashlib.sha256((plain_password + salt).encode("utf-8")).hexdigest()
        return computed == hashed_password
    
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False
    return False


# ==========================================
# Robust JSON Extraction from AI Outputs
# ==========================================

def extract_json_from_text(text: str) -> Optional[Any]:
    """
    Extracts and parses JSON object or array from LLM response.
    Handles markdown code blocks (```json ... ```) or embedded brackets.
    """
    if not text:
        return None
        
    text = text.strip()
    
    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. Extract from markdown code fence
    fence_pattern = r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```"
    match = re.search(fence_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # 3. Find outermost { ... }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 4. Find outermost [ ... ]
    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = text[first_bracket:last_bracket + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None


# ==========================================
# NLP Answer Analysis & Metrics
# ==========================================

def compute_nlp_metrics(answer_text: str) -> Dict[str, Any]:
    """
    Analyzes candidate answer using NLP metrics:
    - Word count & Character count
    - Sentence count
    - Average sentence length
    - Vocabulary richness (Type-Token Ratio)
    - Structural assessment
    """
    if not answer_text:
        return {
            "word_count": 0,
            "char_count": 0,
            "sentence_count": 0,
            "avg_sentence_length": 0,
            "vocab_richness": 0,
            "reading_time_sec": 0,
            "structure_rating": "Incomplete"
        }
    
    clean_text = answer_text.strip()
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", clean_text.lower())
    sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if s.strip()]
    
    word_count = len(words)
    sentence_count = max(1, len(sentences))
    char_count = len(clean_text)
    
    unique_words = set(words)
    vocab_richness = round((len(unique_words) / max(1, word_count)) * 100, 1)
    avg_sentence_len = round(word_count / sentence_count, 1)
    
    # Approx reading time in seconds (average 150 words/min)
    reading_time = round((word_count / 150.0) * 60, 1)
    
    # Structure rating
    if word_count < 15:
        structure = "Very Brief / Concise"
    elif word_count < 40:
        structure = "Moderate / Basic"
    elif word_count < 120:
        structure = "Detailed & Well-Structured"
    else:
        structure = "Comprehensive & In-Depth"
        
    return {
        "word_count": word_count,
        "char_count": char_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sentence_len,
        "vocab_richness": vocab_richness,
        "reading_time_sec": reading_time,
        "structure_rating": structure
    }
