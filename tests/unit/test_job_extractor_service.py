import json
from unittest.mock import AsyncMock, patch

import pytest

from src.services.exceptions import AIServiceUnavailableError
from src.services.job_extractor_service import JobExtractionResult, JobExtractorService


@pytest.fixture
def mock_ai():
    with patch("src.services.job_extractor_service.AIProviderService") as mock_cls:
        instance = AsyncMock()
        mock_cls.return_value = instance
        yield instance


class TestFullJsonExtraction:
    @pytest.mark.asyncio
    async def test_extracts_all_fields(self, mock_ai):
        mock_ai.call_model.return_value = json.dumps(
            {
                "title": "Software Engineer",
                "company": "Google",
                "location": "Remote",
                "salary_min": 5000,
                "salary_max": 10000,
                "salary_currency": "USD",
                "description": "Build software",
                "requirements": ["Python", "3 years exp"],
                "skills": ["Python", "FastAPI"],
            }
        )
        svc = JobExtractorService()
        result = await svc.extract_job_data("some job post text")
        assert result.title == "Software Engineer"
        assert result.company == "Google"
        assert result.location == "Remote"
        assert result.salary_min == 5000
        assert result.salary_max == 10000
        assert result.description == "Build software"
        assert len(result.requirements) == 2
        assert len(result.skills) == 2


class TestPartialExtraction:
    @pytest.mark.asyncio
    async def test_missing_fields_default_none(self, mock_ai):
        mock_ai.call_model.return_value = json.dumps(
            {
                "title": "Job Title",
                "company": "Corp",
            }
        )
        svc = JobExtractorService()
        result = await svc.extract_job_data("partial post")
        assert result.title == "Job Title"
        assert result.location is None
        assert result.salary_min is None
        assert result.salary_max is None


class TestInvalidJsonRetry:
    @pytest.mark.asyncio
    async def test_invalid_json_returns_defaults(self, mock_ai):
        mock_ai.call_model.return_value = "not valid json"
        svc = JobExtractorService()
        result = await svc.extract_job_data("text")
        assert result.title is None

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises(self, mock_ai):
        mock_ai.call_model.side_effect = AIServiceUnavailableError()
        svc = JobExtractorService()
        with pytest.raises(AIServiceUnavailableError):
            await svc.extract_job_data("text")


class TestNonEnglishHandling:
    @pytest.mark.asyncio
    async def test_arabic_text_extracted(self, mock_ai):
        mock_ai.call_model.return_value = json.dumps(
            {
                "title": "مهندس برمجيات",
                "company": "شركة التقنية",
            }
        )
        svc = JobExtractorService()
        result = await svc.extract_job_data("مطلوب مهندس برمجيات")
        assert result.title == "مهندس برمجيات"


class TestPydanticValidation:
    def test_result_model_defaults(self):
        r = JobExtractionResult()
        assert r.title is None
        assert r.salary_currency == "USD"
        assert r.requirements is None
        assert r.skills is None

    def test_result_model_with_data(self):
        r = JobExtractionResult(title="Dev", company="Co", skills=["Python"])
        assert r.title == "Dev"
        assert r.skills == ["Python"]
