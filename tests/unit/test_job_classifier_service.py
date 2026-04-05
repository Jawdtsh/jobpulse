from unittest.mock import AsyncMock, patch

import pytest

from src.services.exceptions import AIServiceUnavailableError, DailyLimitReachedError
from src.services.job_classifier_service import JobClassifierService


@pytest.fixture
def mock_ai():
    with patch("src.services.job_classifier_service.AIProviderService") as mock_cls:
        instance = AsyncMock()
        mock_cls.return_value = instance
        yield instance


class TestBinaryResponseParsing:
    @pytest.mark.asyncio
    async def test_yes_response_returns_true(self, mock_ai):
        mock_ai.call_model.return_value = "yes"
        svc = JobClassifierService()
        result = await svc.classify_post("مطلوب مهندس برمجيات")
        assert result is True

    @pytest.mark.asyncio
    async def test_no_response_returns_false(self, mock_ai):
        mock_ai.call_model.return_value = "no"
        svc = JobClassifierService()
        result = await svc.classify_post("هذا ليس إعلان وظيفة")
        assert result is False

    @pytest.mark.asyncio
    async def test_case_insensitive_yes(self, mock_ai):
        mock_ai.call_model.return_value = "Yes"
        svc = JobClassifierService()
        result = await svc.classify_post("some text")
        assert result is True

    @pytest.mark.asyncio
    async def test_case_insensitive_no(self, mock_ai):
        mock_ai.call_model.return_value = "No"
        svc = JobClassifierService()
        result = await svc.classify_post("some text")
        assert result is False


class TestFallbackChain:
    @pytest.mark.asyncio
    async def test_raises_on_all_failure(self, mock_ai):
        mock_ai.call_model.side_effect = AIServiceUnavailableError()
        svc = JobClassifierService()
        with pytest.raises(AIServiceUnavailableError):
            await svc.classify_post("text")


class TestDailyLimitPause:
    @pytest.mark.asyncio
    async def test_raises_daily_limit(self, mock_ai):
        mock_ai.call_model.side_effect = DailyLimitReachedError("model")
        svc = JobClassifierService()
        with pytest.raises(DailyLimitReachedError):
            await svc.classify_post("text")


class TestInvalidResponseRetry:
    @pytest.mark.asyncio
    async def test_unexpected_response_returns_false(self, mock_ai):
        mock_ai.call_model.return_value = "maybe"
        svc = JobClassifierService()
        result = await svc.classify_post("text")
        assert result is False


class TestTimeout:
    @pytest.mark.asyncio
    async def test_timeout_passed_to_provider(self, mock_ai):
        mock_ai.call_model.return_value = "yes"
        svc = JobClassifierService()
        await svc.classify_post("text")
        mock_ai.call_model.assert_called_once()
        kwargs = mock_ai.call_model.call_args[1]
        assert kwargs["timeout"] == 30
