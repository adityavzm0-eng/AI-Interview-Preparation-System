"""
Database module for AI Interview Preparation System.
Manages SQLite connections, table schemas, migrations, and CRUD operations.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from config import DATABASE_PATH


@contextmanager
def get_db_connection():
    """Context manager for SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initializes the database schema if tables do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                education TEXT,
                skills TEXT,
                experience_level TEXT,
                target_role TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Interviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                job_role TEXT NOT NULL,
                interview_type TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                total_questions INTEGER NOT NULL,
                average_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)

        # Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                candidate_answer TEXT,
                evaluation TEXT,
                score REAL DEFAULT 0.0,
                question_number INTEGER DEFAULT 1,
                category TEXT DEFAULT 'Technical',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (interview_id) REFERENCES interviews (id) ON DELETE CASCADE
            );
        """)

        # Indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_user ON interviews (user_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_interview ON questions (interview_id);")


# ==========================================
# User CRUD Operations
# ==========================================

def create_user(name: str, email: str, password_hash: str) -> Optional[int]:
    """Inserts a new user record. Returns user_id on success, None on error."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), password_hash)
            )
            user_id = cursor.lastrowid
            
            # Initialize default empty profile
            cursor.execute(
                "INSERT OR IGNORE INTO profiles (user_id, education, skills, experience_level, target_role) VALUES (?, '', '', 'Fresher (0 - 1 years)', 'Python Developer')",
                (user_id,)
            )
            return user_id
    except sqlite3.IntegrityError:
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user by email."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a user by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ==========================================
# Profile CRUD Operations
# ==========================================

def get_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves candidate profile for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def upsert_profile(user_id: int, education: str, skills: str, experience_level: str, target_role: str) -> bool:
    """Creates or updates the candidate profile."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO profiles (user_id, education, skills, experience_level, target_role, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                education = excluded.education,
                skills = excluded.skills,
                experience_level = excluded.experience_level,
                target_role = excluded.target_role,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, education.strip(), skills.strip(), experience_level.strip(), target_role.strip()))
        return True


# ==========================================
# Interview & Questions Operations
# ==========================================

def create_interview(user_id: int, job_role: str, interview_type: str, difficulty: str, total_questions: int) -> int:
    """Creates a new interview session and returns its ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO interviews (user_id, job_role, interview_type, difficulty, total_questions, average_score)
            VALUES (?, ?, ?, ?, ?, 0.0)
        """, (user_id, job_role, interview_type, difficulty, total_questions))
        return cursor.lastrowid


def save_question_record(interview_id: int, question_text: str, candidate_answer: str, evaluation: Dict[str, Any], score: float, question_number: int, category: str = "Technical") -> int:
    """Saves or updates a question with answer and AI evaluation."""
    evaluation_json = json.dumps(evaluation) if isinstance(evaluation, dict) else str(evaluation)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO questions (interview_id, question_text, candidate_answer, evaluation, score, question_number, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (interview_id, question_text, candidate_answer, evaluation_json, score, question_number, category))
        q_id = cursor.lastrowid
        
        # Recalculate average score for this interview
        cursor.execute("""
            SELECT AVG(score) as avg_score FROM questions WHERE interview_id = ?
        """, (interview_id,))
        avg_row = cursor.fetchone()
        new_avg = round(avg_row["avg_score"] or 0.0, 2)
        
        cursor.execute("""
            UPDATE interviews SET average_score = ? WHERE id = ?
        """, (new_avg, interview_id))
        
        return q_id


def get_user_interviews(user_id: int) -> List[Dict[str, Any]]:
    """Gets all interviews completed by a user ordered by date descending."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM interviews WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_interview_details(interview_id: int) -> Optional[Dict[str, Any]]:
    """Gets interview metadata along with all associated questions and evaluations."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
        interview = cursor.fetchone()
        if not interview:
            return None
        
        cursor.execute("""
            SELECT * FROM questions WHERE interview_id = ? ORDER BY question_number ASC
        """, (interview_id,))
        questions = []
        for q in cursor.fetchall():
            q_dict = dict(q)
            try:
                q_dict["evaluation"] = json.loads(q_dict["evaluation"]) if q_dict["evaluation"] else {}
            except Exception:
                pass
            questions.append(q_dict)
        
        result = dict(interview)
        result["questions"] = questions
        return result


def get_user_dashboard_stats(user_id: int) -> Dict[str, Any]:
    """Computes comprehensive metrics and breakdown for user dashboard."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Basic aggregates
        cursor.execute("""
            SELECT 
                COUNT(*) as total_interviews,
                COALESCE(AVG(average_score), 0.0) as overall_avg,
                COALESCE(MAX(average_score), 0.0) as highest_score
            FROM interviews WHERE user_id = ?
        """, (user_id,))
        basic = cursor.fetchone()
        
        # Total questions answered
        cursor.execute("""
            SELECT COUNT(q.id) as total_questions_answered
            FROM questions q
            JOIN interviews i ON q.interview_id = i.id
            WHERE i.user_id = ?
        """, (user_id,))
        q_count = cursor.fetchone()["total_questions_answered"]
        
        # Score by interview type
        cursor.execute("""
            SELECT interview_type, AVG(average_score) as avg_score, COUNT(*) as count
            FROM interviews
            WHERE user_id = ?
            GROUP BY interview_type
        """, (user_id,))
        type_breakdown = [dict(row) for row in cursor.fetchall()]
        
        # Score by difficulty
        cursor.execute("""
            SELECT difficulty, AVG(average_score) as avg_score, COUNT(*) as count
            FROM interviews
            WHERE user_id = ?
            GROUP BY difficulty
        """, (user_id,))
        difficulty_breakdown = [dict(row) for row in cursor.fetchall()]

        # Score by job role
        cursor.execute("""
            SELECT job_role, AVG(average_score) as avg_score, COUNT(*) as count
            FROM interviews
            WHERE user_id = ?
            GROUP BY job_role
        """, (user_id,))
        role_breakdown = [dict(row) for row in cursor.fetchall()]

        # Score progression over time
        cursor.execute("""
            SELECT id, job_role, interview_type, difficulty, average_score, created_at
            FROM interviews
            WHERE user_id = ?
            ORDER BY created_at ASC
        """, (user_id,))
        progression = [dict(row) for row in cursor.fetchall()]
        
        return {
            "total_interviews": basic["total_interviews"],
            "average_score": round(basic["overall_avg"], 2),
            "highest_score": round(basic["highest_score"], 2),
            "total_questions_answered": q_count,
            "type_breakdown": type_breakdown,
            "difficulty_breakdown": difficulty_breakdown,
            "role_breakdown": role_breakdown,
            "progression": progression
        }
