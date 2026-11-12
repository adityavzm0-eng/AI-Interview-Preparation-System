"""
Answer Evaluator module.
Evaluates candidate responses using Google Gemini API across 5 key dimensions:
1. Technical correctness
2. Conceptual understanding
3. Relevance
4. Clarity
5. Completeness
Enriches evaluation with NLP readability and structural metrics.
Includes intelligent NLP semantic fallback if API key encounters authentication/quota errors.
"""

import re
from typing import Dict, Any, Tuple
from utils.gemini_client import GeminiClient
from utils.helpers import compute_nlp_metrics


class AnswerEvaluator:
    """Evaluates candidate answers against role expectations and provides structured feedback."""

    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    def evaluate_answer(
        self,
        question_data: Dict[str, Any],
        candidate_answer: str,
        job_role: str,
        experience_level: str
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Submits candidate answer to Gemini/OpenAI for multidimensional scoring.
        If API authorization/quota error occurs, gracefully transitions to NLP semantic scoring.
        """
        nlp_stats = compute_nlp_metrics(candidate_answer)

        system_instruction = (
            "You are an encouraging, experienced Technical Interview Evaluator and Career Mentor. "
            "Your objective is to provide rigorous yet constructive evaluation of candidate answers. "
            "Always tailor your evaluation tone to be supportive for freshers while maintaining industry standards."
        )

        prompt = f"""
Evaluate the candidate's answer to the following interview question.

Role: {job_role}
Candidate Experience Level: {experience_level}
Question: {question_data.get('question_text')}
Category: {question_data.get('category', 'Technical')}
Core Concept: {question_data.get('core_concept', '')}
Expected Nuances: {', '.join(question_data.get('expected_points', []))}

Candidate's Submitted Answer:
\"\"\"{candidate_answer.strip()}\"\"\"

EVALUATION INSTRUCTIONS:
1. Score each dimension on a scale of 0.0 to 10.0:
   - technical_correctness: Accuracy of facts, syntax, algorithmic logic, or HR situational principles.
   - conceptual_understanding: Depth of foundational comprehension (does the candidate understand 'why', not just 'what').
   - relevance: How directly the answer addresses the specific question asked.
   - clarity: Articulation, flow, readability, and communication quality.
   - completeness: Thoroughness in addressing edge cases, examples, trade-offs, or the STAR framework.
2. overall_score: Weighted composite average out of 10.0 (round to 1 decimal place).
3. strengths: 2-3 specific bullet points highlighting what the candidate explained well.
4. weaknesses: 1-3 specific areas where the answer fell short or was vague.
5. missing_points: Key technical concepts, keywords, or situational aspects the candidate missed.
6. improved_answer: A model, production-level, well-structured answer (approx 120-200 words) that would receive a 10/10 in an actual interview.
7. personalized_suggestions: 2-3 actionable tips for freshers/candidates to improve their interview performance for this specific topic.

Respond strictly in the following JSON schema:
{{
  "overall_score": 7.5,
  "scores": {{
    "technical_correctness": 8.0,
    "conceptual_understanding": 7.5,
    "relevance": 8.5,
    "clarity": 7.0,
    "completeness": 6.5
  }},
  "strengths": [
    "Identified the core concept accurately...",
    "Used clean terminology..."
  ],
  "weaknesses": [
    "Did not mention time complexity...",
    "Lacked practical application example..."
  ],
  "missing_points": [
    "Mention of index fragmentation...",
    "Edge case handling for null inputs..."
  ],
  "improved_answer": "In Python, ...",
  "personalized_suggestions": [
    "Practice using the STAR format (Situation, Task, Action, Result)...",
    "Always state time/space complexity trade-offs upfront."
  ]
}}
"""

        # Try API evaluation if configured
        if self.client.is_configured():
            success, data, error = self.client.generate_content(
                prompt=prompt,
                system_instruction=system_instruction,
                expect_json=True
            )

            if success and isinstance(data, dict):
                scores = data.get("scores", {})
                tech_score = float(scores.get("technical_correctness", 7.0))
                concept_score = float(scores.get("conceptual_understanding", 7.0))
                rel_score = float(scores.get("relevance", 7.0))
                clarity_score = float(scores.get("clarity", 7.0))
                comp_score = float(scores.get("completeness", 7.0))

                overall = float(data.get("overall_score", (tech_score + concept_score + rel_score + clarity_score + comp_score) / 5.0))
                overall = round(min(10.0, max(0.0, overall)), 1)

                return True, {
                    "overall_score": overall,
                    "scores": {
                        "technical_correctness": round(min(10.0, max(0.0, tech_score)), 1),
                        "conceptual_understanding": round(min(10.0, max(0.0, concept_score)), 1),
                        "relevance": round(min(10.0, max(0.0, rel_score)), 1),
                        "clarity": round(min(10.0, max(0.0, clarity_score)), 1),
                        "completeness": round(min(10.0, max(0.0, comp_score)), 1),
                    },
                    "strengths": data.get("strengths", ["Addressed the core subject directly."]),
                    "weaknesses": data.get("weaknesses", ["Could elaborate with additional technical examples."]),
                    "missing_points": data.get("missing_points", []),
                    "improved_answer": data.get("improved_answer", "N/A"),
                    "personalized_suggestions": data.get("personalized_suggestions", ["Structure responses clearly with real-world scenarios."]),
                    "nlp_metrics": nlp_stats,
                    "engine": "AI LLM Engine"
                }, ""

        # Fallback to Local NLP Semantic Evaluation Engine
        nlp_evaluation = self._evaluate_with_nlp_fallback(question_data, candidate_answer, nlp_stats, job_role)
        return True, nlp_evaluation, ""

    def _evaluate_with_nlp_fallback(
        self,
        question_data: Dict[str, Any],
        candidate_answer: str,
        nlp_stats: Dict[str, Any],
        job_role: str
    ) -> Dict[str, Any]:
        """Local heuristic & NLP semantic evaluation engine when API is unavailable."""
        expected_points = question_data.get("expected_points", [])
        ans_lower = candidate_answer.lower()

        # Check matched expected points
        matched = []
        unmatched = []
        for pt in expected_points:
            words = [w for w in re.findall(r"\w+", pt.lower()) if len(w) > 3]
            overlap = sum(1 for w in words if w in ans_lower)
            if overlap >= max(1, len(words) // 3):
                matched.append(pt)
            else:
                unmatched.append(pt)

        # Dimension scoring heuristics
        wc = nlp_stats.get("word_count", 0)
        vr = nlp_stats.get("vocab_richness", 50.0)

        # Relevance
        rel = min(10.0, 5.0 + (len(matched) * 1.5))
        # Clarity
        clarity = 8.5 if 20 <= wc <= 180 else (6.0 if wc < 15 else 7.5)
        # Completeness
        completeness = min(10.0, max(4.0, (wc / 15.0) + (len(matched) * 1.2)))
        # Technical correctness
        tech = min(10.0, max(5.0, 6.0 + (len(matched) * 1.2)))
        # Conceptual understanding
        concept = min(10.0, max(5.0, (tech + completeness) / 2.0))

        overall = round((tech + concept + rel + clarity + completeness) / 5.0, 1)

        strengths = [
            f"Communicated key principles with good clarity ({wc} words).",
            f"Demonstrated good vocabulary richness ({vr}% type-token ratio)."
        ]
        if matched:
            strengths.append(f"Successfully addressed: '{matched[0]}'.")

        weaknesses = []
        if wc < 25:
            weaknesses.append("Answer was too concise; elaborate with more architecture or code details.")
        if unmatched:
            weaknesses.append(f"Did not fully cover: '{unmatched[0]}'.")
        if not weaknesses:
            weaknesses.append("Consider discussing edge cases and performance trade-offs.")

        # Model answer synthesis
        concept_name = question_data.get("core_concept", job_role)
        model_answer = (
            f"In {job_role}, {concept_name} plays an essential role. A comprehensive answer should define the fundamental "
            f"principles, illustrate with a concrete practical scenario, analyze edge cases, and highlight trade-offs "
            f"(such as computational complexity, memory overhead, or team maintainability). Key nuances include: "
            + "; ".join(expected_points) + "."
        )

        suggestions = [
            "Structure your thoughts using the PREP method (Point, Reason, Example, Point).",
            "Always quantify performance implications (e.g. O(1) vs O(N), memory overhead).",
            "Connect API key in sidebar (Google Gemini) for full generative feedback."
        ]

        return {
            "overall_score": overall,
            "scores": {
                "technical_correctness": round(tech, 1),
                "conceptual_understanding": round(concept, 1),
                "relevance": round(rel, 1),
                "clarity": round(clarity, 1),
                "completeness": round(completeness, 1)
            },
            "strengths": strengths,
            "weaknesses": weaknesses,
            "missing_points": unmatched if unmatched else ["Deeper discussion on edge cases and scalability."],
            "improved_answer": model_answer,
            "personalized_suggestions": suggestions,
            "nlp_metrics": nlp_stats,
            "engine": "NLP Semantic Engine (Active Practice Mode)"
        }
