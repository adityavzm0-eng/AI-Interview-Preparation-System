"""
Question Generator module.
Uses Google Gemini API to generate tailored, scenario-based interview questions
based on candidate profile, target job role, difficulty, and interview type.
Includes rich offline curated repositories as fail-safe fallback.
"""

import json
from typing import List, Dict, Any, Tuple
from utils.gemini_client import GeminiClient

# ==========================================
# Curated Industry Questions Fallback Bank
# ==========================================
CURATED_QUESTIONS = {
    "Python Developer": {
        "Technical": [
            {
                "question_text": "Explain Python's Memory Management, GIL (Global Interpreter Lock), and how reference counting with cyclic garbage collection works in real-world applications.",
                "category": "Technical",
                "core_concept": "Python Internal Memory & GIL",
                "expected_points": ["Private heap space", "Reference counting mechanism", "Cyclic garbage collector for self-referential cycles", "GIL impact on multi-threading vs multi-processing"],
                "hint_for_fresher": "Explain the difference between multi-threading (I/O bound) and multiprocessing (CPU bound) and how Python manages heap memory."
            },
            {
                "question_text": "You are processing a 10GB log file on a server with only 4GB of RAM. How would you design a Python script to parse, filter, and extract summary metrics efficiently without running out of memory?",
                "category": "Scenario-Based",
                "core_concept": "Generators & Memory Optimization",
                "expected_points": ["Using generators with yield instead of loading whole file into list", "Iterating line by line", "Using itertools / chunking", "Avoiding memory leaks"],
                "hint_for_fresher": "Think about lazy evaluation and generator expressions vs standard list comprehensions."
            },
            {
                "question_text": "What are Python Decorators? Write or describe how you would implement a custom '@timing_decorator' that measures execution time of any function.",
                "category": "Technical",
                "core_concept": "Decorators & First-Class Functions",
                "expected_points": ["Functions as first-class citizens", "Inner wrapper function", "*args and **kwargs forwarding", "functools.wraps to preserve function metadata"],
                "hint_for_fresher": "Explain that decorators take a function as input, wrap behavior around it, and return the modified callable."
            },
            {
                "question_text": "Explain the differences between deepcopy, shallow copy, and normal assignment in Python with mutable objects like nested dictionaries and lists.",
                "category": "Technical",
                "core_concept": "Object Mutability & Copying",
                "expected_points": ["Assignment creates new reference to same object", "Shallow copy copies container but retains references to nested objects", "Deepcopy recursively clones all nested objects", "Using the copy module"],
                "hint_for_fresher": "Provide a quick example with a list containing a sub-list [1, [2, 3]] and what happens when you modify the inner list."
            },
            {
                "question_text": "How do Python Dunder (magic) methods work? Give examples of __init__, __str__, __repr__, and __enter__/__exit__ for Context Managers.",
                "category": "Technical",
                "core_concept": "OOP & Context Managers",
                "expected_points": ["__repr__ for developers vs __str__ for end users", "__enter__ and __exit__ protocol for 'with' statements", "Exception handling inside __exit__"],
                "hint_for_fresher": "Explain the context manager protocol and why it ensures resources like files or database connections are always safely closed."
            }
        ],
        "HR": [
            {
                "question_text": "Describe a challenging technical bug or blocker you encountered in a project. How did you diagnose it, what steps did you take, and what was the outcome?",
                "category": "HR",
                "core_concept": "Problem Solving & Resilience (STAR Method)",
                "expected_points": ["Situation & Task context", "Structured diagnostic process", "Actions taken", "Positive quantifiable result and lessons learned"],
                "hint_for_fresher": "Use the STAR method: Situation, Task, Action, and Result. Highlight systematic debugging rather than random guesswork."
            },
            {
                "question_text": "How do you prioritize your work when facing competing deadlines or ambiguous technical requirements from senior stakeholders?",
                "category": "HR",
                "core_concept": "Prioritization & Communication",
                "expected_points": ["Clarifying expectations early", "Breaking tasks into milestones", "Communicating proactively", "Managing trade-offs transparently"],
                "hint_for_fresher": "Demonstrate that you are proactive in asking questions when requirements are unclear rather than making incorrect assumptions."
            }
        ]
    },
    "Data Scientist": {
        "Technical": [
            {
                "question_text": "Explain the Bias-Variance Tradeoff in Machine Learning. How do you detect high bias vs high variance, and what specific regularization techniques do you apply for each?",
                "category": "Technical",
                "core_concept": "Bias-Variance Tradeoff & Regularization",
                "expected_points": ["High bias = Underfitting, High variance = Overfitting", "L1 (Lasso) vs L2 (Ridge) regularization", "Cross-validation and learning curves", "Data augmentation and dropout"],
                "hint_for_fresher": "Contrast simple models that oversimplify the patterns vs overly complex models that memorize noise in training data."
            },
            {
                "question_text": "Suppose you are evaluating a fraud detection model where only 0.1% of transactions are fraudulent. Why is Accuracy a misleading metric, and which metrics should you track instead?",
                "category": "Scenario-Based",
                "core_concept": "Class Imbalance & Evaluation Metrics",
                "expected_points": ["Accuracy paradox in imbalanced datasets", "Precision, Recall, F1-Score, and PR-AUC", "Confusion Matrix trade-offs (False Positives vs False Negatives)", "Techniques like SMOTE or class weighting"],
                "hint_for_fresher": "Explain why a naive model predicting 'no fraud' achieves 99.9% accuracy but fails completely at the business goal."
            },
            {
                "question_text": "What is Feature Engineering, and how do you handle missing values, outliers, and categorical encoding without introducing data leakage?",
                "category": "Technical",
                "core_concept": "Feature Engineering & Data Preprocessing",
                "expected_points": ["Preventing data leakage by fitting transformers only on training set", "Mean/Median/KNN imputation", "One-Hot vs Target vs Ordinal encoding", "Outlier detection using IQR or Z-score"],
                "hint_for_fresher": "Emphasize that all scalers and encoders must be fitted on train data only, then applied to test data to prevent leakage."
            }
        ],
        "HR": [
            {
                "question_text": "How do you explain complex machine learning findings or predictive insights to non-technical business stakeholders?",
                "category": "HR",
                "core_concept": "Stakeholder Communication & Business Impact",
                "expected_points": ["Avoiding jargon", "Focusing on ROI and business metrics", "Using intuitive visual charts", "Translating probabilities into actionable decisions"],
                "hint_for_fresher": "Show empathy for the business audience and highlight how your model helps the company make better decisions."
            }
        ]
    }
}


class QuestionGenerator:
    """Orchestrates generation of non-repeating, high-quality interview questions."""

    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    def generate_interview_questions(
        self,
        job_role: str,
        interview_type: str,
        difficulty: str,
        total_questions: int,
        candidate_profile: Dict[str, Any]
    ) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        Generates a list of interview questions from Gemini.
        Falls back to rich curated industry questions if API encounters authorization/quota issues.
        """
        education = candidate_profile.get("education", "Computer Science")
        skills = candidate_profile.get("skills", "Python, SQL, Problem Solving")
        experience = candidate_profile.get("experience_level", "Fresher (0 - 1 years)")

        system_instruction = (
            "You are a Principal Technical Interviewer and Hiring Committee Lead at a top-tier tech company. "
            "You create rigorous, fair, practical, and highly relevant interview questions tailored to candidates."
        )

        prompt = f"""
Generate an interview question set with exactly {total_questions} distinct questions for a candidate with the following parameters:

Target Job Role: {job_role}
Interview Type: {interview_type}
Target Difficulty: {difficulty}
Candidate Experience Level: {experience}
Candidate Education: {education}
Candidate Skills: {skills}

RULES:
1. If Interview Type is 'Technical Interview': Generate 100% technical and practical problem-solving questions relevant to {job_role}.
2. If Interview Type is 'HR Interview': Generate 100% behavioral, cultural fit, conflict-resolution, and career-oriented questions (STAR method based).
3. If Interview Type is 'Mixed Interview': Provide approximately 60% technical questions and 40% behavioral/HR questions.
4. Difficulty calibrator:
   - Easy: Foundational concepts, basic code/architecture comprehension, standard behavioral questions suitable for freshers.
   - Medium: Real-world scenarios, debugging, optimization, trade-offs, situational edge cases.
   - Hard: System scalability, edge cases, deep algorithmic/architectural trade-offs, complex interpersonal/stakeholder dilemmas.
5. All questions must be completely distinct (no repeated topics).
6. Provide scenario-based context whenever appropriate.

Respond ONLY with a valid JSON array of objects adhering strictly to this schema:
[
  {{
    "question_number": 1,
    "question_text": "Detailed question text here...",
    "category": "Technical" or "HR" or "Scenario-Based",
    "difficulty": "{difficulty}",
    "core_concept": "Key technical concept or behavioral competency tested",
    "expected_points": [
      "Key point or nuance 1",
      "Key point or nuance 2",
      "Key point or nuance 3"
    ],
    "hint_for_fresher": "A short guiding tip on how to structure the answer effectively."
  }}
]
"""

        # Attempt AI generation
        if self.client.is_configured():
            success, data, error = self.client.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                expect_json=True
            )

            if success and data:
                questions = []
                if isinstance(data, list):
                    questions = data
                elif isinstance(data, dict):
                    for key in ["questions", "question_set", "data"]:
                        if key in data and isinstance(data[key], list):
                            questions = data[key]
                            break
                    if not questions and "question_text" in data:
                        questions = [data]

                if questions:
                    sanitized_questions = []
                    for i, q in enumerate(questions, start=1):
                        if not isinstance(q, dict):
                            continue
                        sanitized_questions.append({
                            "question_number": i,
                            "question_text": q.get("question_text", f"Question {i}"),
                            "category": q.get("category", "Technical" if "HR" not in interview_type else "HR"),
                            "difficulty": q.get("difficulty", difficulty),
                            "core_concept": q.get("core_concept", job_role),
                            "expected_points": q.get("expected_points", []),
                            "hint_for_fresher": q.get("hint_for_fresher", "Structure your thoughts clearly with examples.")
                        })

                    if len(sanitized_questions) > 0:
                        return True, sanitized_questions[:total_questions], ""

        # Fallback to Curated Question Bank
        fallback_questions = self._get_curated_fallback(job_role, interview_type, difficulty, total_questions)
        return True, fallback_questions, ""

    def _get_curated_fallback(self, job_role: str, interview_type: str, difficulty: str, count: int) -> List[Dict[str, Any]]:
        """Provides verified, high-quality interview questions when API key is unavailable or restricted."""
        role_bank = CURATED_QUESTIONS.get(job_role, CURATED_QUESTIONS["Python Developer"])
        
        pool = []
        if interview_type == "HR Interview":
            pool = role_bank.get("HR", []) + CURATED_QUESTIONS["Python Developer"].get("HR", [])
        elif interview_type == "Technical Interview":
            pool = role_bank.get("Technical", []) + CURATED_QUESTIONS["Python Developer"].get("Technical", [])
        else: # Mixed
            pool = role_bank.get("Technical", [])[:3] + role_bank.get("HR", [])[:2]

        # Duplicate or synthesize if pool is smaller than requested count
        results = []
        for i in range(count):
            base_q = pool[i % len(pool)]
            q_copy = dict(base_q)
            q_copy["question_number"] = i + 1
            q_copy["difficulty"] = difficulty
            results.append(q_copy)

        return results
