import json
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from src.services.cv_evaluator import CVEvaluator, CVEvaluationResult


@pytest.fixture
def mock_ai_service():
    return AsyncMock()


@pytest.fixture
def evaluator(mock_ai_service):
    return CVEvaluator(ai_service=mock_ai_service)


class TestCVEvaluator:
    @pytest.mark.asyncio
    async def test_evaluate_returns_result(self, evaluator, mock_ai_service):
        ai_response = json.dumps(
            {
                "skills": ["Python", "FastAPI", "SQL"],
                "experience_summary": "5 years of backend development.",
                "improvement_suggestions": ["Add more quantifiable achievements"],
                "sections_found": {
                    "contact": True,
                    "skills": True,
                    "experience": True,
                    "education": True,
                    "summary": False,
                },
            }
        )
        mock_ai_service.call_model.return_value = ai_response

        result = await evaluator.evaluate("Sample CV text")

        assert isinstance(result, CVEvaluationResult)
        assert result.skills == ["Python", "FastAPI", "SQL"]
        assert result.experience_summary == "5 years of backend development."
        assert result.completeness_score == Decimal("90")
        assert result.improvement_suggestions == ["Add more quantifiable achievements"]
        assert result.is_referral_eligible is True

    @pytest.mark.asyncio
    async def test_evaluate_referral_ineligible_below_40(
        self, evaluator, mock_ai_service
    ):
        ai_response = json.dumps(
            {
                "skills": [],
                "experience_summary": "",
                "improvement_suggestions": ["Add contact info"],
                "sections_found": {
                    "contact": False,
                    "skills": False,
                    "experience": True,
                    "education": False,
                    "summary": False,
                },
            }
        )
        mock_ai_service.call_model.return_value = ai_response

        result = await evaluator.evaluate("Minimal CV text")

        assert result.completeness_score == Decimal("30")
        assert result.is_referral_eligible is False

    @pytest.mark.asyncio
    async def test_evaluate_handles_invalid_json(self, evaluator, mock_ai_service):
        mock_ai_service.call_model.return_value = "not valid json {{{"

        result = await evaluator.evaluate("Some CV")

        assert result.skills == []
        assert result.experience_summary == ""
        assert result.completeness_score == Decimal("0")

    @pytest.mark.asyncio
    async def test_evaluate_completeness_all_sections(self, evaluator, mock_ai_service):
        ai_response = json.dumps(
            {
                "skills": ["Python"],
                "experience_summary": "Experienced dev",
                "improvement_suggestions": [],
                "sections_found": {
                    "contact": True,
                    "skills": True,
                    "experience": True,
                    "education": True,
                    "summary": True,
                },
            }
        )
        mock_ai_service.call_model.return_value = ai_response

        result = await evaluator.evaluate("Full CV")

        assert result.completeness_score == Decimal("100")
        assert result.is_referral_eligible is True

    @pytest.mark.asyncio
    async def test_evaluate_completeness_no_sections(self, evaluator, mock_ai_service):
        ai_response = json.dumps(
            {
                "skills": [],
                "experience_summary": "",
                "improvement_suggestions": [],
                "sections_found": {
                    "contact": False,
                    "skills": False,
                    "experience": False,
                    "education": False,
                    "summary": False,
                },
            }
        )
        mock_ai_service.call_model.return_value = ai_response

        result = await evaluator.evaluate("Empty CV")

        assert result.completeness_score == Decimal("0")
        assert result.is_referral_eligible is False

    @pytest.mark.asyncio
    async def test_evaluate_non_list_skills_handled(self, evaluator, mock_ai_service):
        ai_response = json.dumps(
            {
                "skills": "Python, Java",
                "experience_summary": "Some experience",
                "improvement_suggestions": "Add projects",
                "sections_found": {"contact": True},
            }
        )
        mock_ai_service.call_model.return_value = ai_response

        result = await evaluator.evaluate("CV")

        assert result.skills == []
        assert result.improvement_suggestions == []

    def test_calculate_completeness_weights(self, evaluator):
        sections = {
            "contact": True,
            "skills": True,
            "experience": False,
            "education": False,
            "summary": False,
        }
        score = evaluator._calculate_completeness(sections)
        assert score == Decimal("45")
