import json
import logging
from dataclasses import dataclass, field
from decimal import Decimal

from src.services.ai_provider_service import AIProviderService

logger = logging.getLogger(__name__)

_COMPLETENESS_WEIGHTS = {
    "contact": 0.20,
    "skills": 0.25,
    "experience": 0.30,
    "education": 0.15,
    "summary": 0.10,
}

_REFERRAL_THRESHOLD = Decimal("40")

_EVALUATION_SYSTEM_PROMPT = """You are a professional CV/resume evaluator.
Analyze the given CV text and return a JSON object with exactly these fields:
- "skills": a list of strings, each a skill found in the CV
- "experience_summary": a string summarizing the candidate's work experience (2-3 sentences)
- "improvement_suggestions": a list of strings with specific suggestions to improve the CV
- "sections_found": an object with keys "contact", "skills", "experience", "education", "summary", each boolean

Return ONLY valid JSON, no other text."""


@dataclass
class CVEvaluationResult:
    skills: list[str] = field(default_factory=list)
    experience_summary: str = ""
    completeness_score: Decimal = Decimal("0")
    improvement_suggestions: list[str] = field(default_factory=list)
    is_referral_eligible: bool = False


class CVEvaluator:
    def __init__(self, ai_service: AIProviderService | None = None) -> None:
        self._ai = ai_service or AIProviderService()

    async def evaluate(self, text: str) -> CVEvaluationResult:
        raw = await self._ai.call_model(
            model_type="evaluator",
            prompt=text,
            system_prompt=_EVALUATION_SYSTEM_PROMPT,
            response_format={"type": "json_object"},
            timeout=60,
        )
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> CVEvaluationResult:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.exception("AI returned invalid JSON: %s", raw[:200])
            return CVEvaluationResult()

        skills = data.get("skills", [])
        if isinstance(skills, list):
            skills = [str(s) for s in skills]
        else:
            skills = []

        experience_summary = str(data.get("experience_summary", ""))

        suggestions = data.get("improvement_suggestions", [])
        if isinstance(suggestions, list):
            suggestions = [str(s) for s in suggestions]
        else:
            suggestions = []

        sections_found = data.get("sections_found", {})
        completeness = self._calculate_completeness(sections_found)
        is_eligible = completeness >= _REFERRAL_THRESHOLD

        return CVEvaluationResult(
            skills=skills,
            experience_summary=experience_summary,
            completeness_score=completeness,
            improvement_suggestions=suggestions,
            is_referral_eligible=is_eligible,
        )

    def _calculate_completeness(self, sections_found: dict) -> Decimal:
        score = Decimal("0")
        for section, weight in _COMPLETENESS_WEIGHTS.items():
            if sections_found.get(section, False):
                score += Decimal(str(weight)) * 100
        return score
