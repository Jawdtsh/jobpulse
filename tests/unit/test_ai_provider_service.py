from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.ai_provider_service import AIProviderService
from src.services.exceptions import (
    AIServiceUnavailableError,
    DailyLimitReachedError,
    InvalidModelTypeError,
)


@pytest.fixture
def service():
    with patch("src.services.ai_provider_service.get_settings") as mock_settings:
        s = MagicMock()
        s.ai.gemini_api_key = "test-gemini-key"
        s.ai.groq_api_key = "test-groq-key"
        s.ai.openrouter_api_key = "test-openrouter-key"
        s.ai.zhipu_api_key = "test-zhipu-key"
        s.redis.redis_url = "redis://localhost:6379"
        mock_settings.return_value = s
        return AIProviderService()


class TestFallbackChain:
    @pytest.mark.asyncio
    async def test_iterates_fallback_on_failure(self, service):
        with (
            patch.object(
                service, "_call_provider", side_effect=Exception("fail")
            ) as mock_call,
            patch.object(service, "check_daily_limit", return_value=True),
            patch.object(service, "increment_usage"),
        ):
            with pytest.raises(AIServiceUnavailableError):
                await service.call_model("classifier", "test prompt")
            attempted_models = [call[0][0] for call in mock_call.call_args_list]
            assert mock_call.call_count == 9
            assert "regex_only" not in attempted_models

    @pytest.mark.asyncio
    async def test_returns_first_success(self, service):
        with (
            patch.object(service, "_call_provider", return_value="yes"),
            patch.object(service, "check_daily_limit", return_value=True),
            patch.object(service, "increment_usage"),
        ):
            result = await service.call_model("classifier", "test prompt")
            assert result == "yes"

    @pytest.mark.asyncio
    async def test_invalid_model_type_raises(self, service):
        with pytest.raises(InvalidModelTypeError):
            await service.call_model("invalid_type", "prompt")

    @pytest.mark.asyncio
    async def test_skips_regex_only_in_chain(self, service):
        attempted_models = []

        async def counting_call(
            model_name, provider_info, prompt, system_prompt, response_format, timeout
        ):
            attempted_models.append(model_name)
            return "ok"

        with (
            patch.object(
                service, "_call_provider", side_effect=counting_call
            ) as mock_call,
            patch.object(service, "check_daily_limit", return_value=True),
            patch.object(service, "increment_usage"),
        ):
            result = await service.call_model("classifier", "prompt")
            assert result == "ok"
            assert mock_call.call_count == 1
            assert "regex_only" not in attempted_models


class TestDailyLimit:
    @pytest.mark.asyncio
    async def test_raises_when_limit_reached(self, service):
        with patch.object(service, "check_daily_limit", return_value=False):
            with pytest.raises(DailyLimitReachedError):
                await service.call_model("classifier", "prompt")

    @pytest.mark.asyncio
    async def test_check_daily_limit_returns_true(self, service):
        with patch("src.services.ai_provider_service._get_redis") as mock_redis:
            r = AsyncMock()
            r.get.return_value = "5"
            mock_redis.return_value = r
            result = await service.check_daily_limit("gemini-2.5-flash-lite")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_daily_limit_returns_false(self, service):
        with patch("src.services.ai_provider_service._get_redis") as mock_redis:
            r = AsyncMock()
            r.get.return_value = "1000"
            mock_redis.return_value = r
            result = await service.check_daily_limit("gemini-2.5-flash-lite")
            assert result is False


class TestExponentialBackoff:
    @pytest.mark.asyncio
    async def test_retries_three_times_per_model(self, service):
        call_count = 0

        async def fail_then_succeed(
            model_name, provider_info, prompt, system_prompt, response_format, timeout
        ):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("transient error")
            return "success"

        with (
            patch.object(service, "_call_provider", side_effect=fail_then_succeed),
            patch.object(service, "check_daily_limit", return_value=True),
            patch.object(service, "increment_usage"),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            result = await service.call_model("classifier", "prompt")
            assert result == "success"
            assert call_count == 3


class TestTimeout:
    @pytest.mark.asyncio
    async def test_timeout_propagated_to_provider(self, service):
        with (
            patch.object(service, "_call_provider", return_value="ok") as mock_call,
            patch.object(service, "check_daily_limit", return_value=True),
            patch.object(service, "increment_usage"),
        ):
            await service.call_model("classifier", "prompt", timeout=60)
            args = mock_call.call_args[0]
            assert args[5] == 60


class TestProviderClientCreation:
    def test_get_openai_client_creates_client(self, service):
        client = service._get_openai_client("groq")
        assert client is not None
        assert "groq" in service._clients

    def test_get_openai_client_caches(self, service):
        c1 = service._get_openai_client("groq")
        c2 = service._get_openai_client("groq")
        assert c1 is c2
