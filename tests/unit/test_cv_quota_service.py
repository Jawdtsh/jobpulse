import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.services.cv_quota_service import CVQuotaService, QUOTA_LIMITS


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def service(mock_redis):
    with patch("src.services.cv_quota_service._get_redis", return_value=mock_redis):
        svc = CVQuotaService()
        yield svc


class TestCheckAndIncrementQuota:
    @pytest.mark.asyncio
    async def test_first_use_returns_1(self, service, mock_redis):
        mock_redis.eval.return_value = 1
        user_id = uuid.uuid4()

        result = await service.check_and_increment_quota(user_id, "free")

        assert result == 1
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_under_limit_returns_count(self, service, mock_redis):
        mock_redis.eval.return_value = 3
        user_id = uuid.uuid4()

        result = await service.check_and_increment_quota(user_id, "basic")

        assert result == 3

    @pytest.mark.asyncio
    async def test_at_limit_returns_minus_1(self, service, mock_redis):
        mock_redis.eval.return_value = -1
        user_id = uuid.uuid4()

        result = await service.check_and_increment_quota(user_id, "free")

        assert result == -1

    @pytest.mark.asyncio
    async def test_lua_script_called_with_correct_args(self, service, mock_redis):
        mock_redis.eval.return_value = 1
        user_id = uuid.uuid4()

        await service.check_and_increment_quota(user_id, "pro")

        call_args = mock_redis.eval.call_args
        assert call_args[0][3] == str(QUOTA_LIMITS["pro"])

    @pytest.mark.asyncio
    async def test_unknown_tier_defaults_to_1(self, service, mock_redis):
        mock_redis.eval.return_value = 1
        user_id = uuid.uuid4()

        await service.check_and_increment_quota(user_id, "unknown_tier")

        call_args = mock_redis.eval.call_args
        assert call_args[0][3] == "1"

    @pytest.mark.asyncio
    async def test_pro_limit_is_10(self, service, mock_redis):
        mock_redis.eval.return_value = 5
        user_id = uuid.uuid4()

        await service.check_and_increment_quota(user_id, "pro")

        call_args = mock_redis.eval.call_args
        assert call_args[0][3] == "10"

    @pytest.mark.asyncio
    async def test_basic_limit_is_5(self, service, mock_redis):
        mock_redis.eval.return_value = 2
        user_id = uuid.uuid4()

        await service.check_and_increment_quota(user_id, "basic")

        call_args = mock_redis.eval.call_args
        assert call_args[0][3] == "5"


class TestCheckQuotaLegacy:
    @pytest.mark.asyncio
    async def test_check_quota_under_limit(self, service, mock_redis):
        mock_redis.eval.return_value = 1
        user_id = uuid.uuid4()

        result = await service.check_and_increment_quota(user_id, "free")

        assert result == 1

    @pytest.mark.asyncio
    async def test_check_quota_at_limit(self, service, mock_redis):
        mock_redis.eval.return_value = -1
        user_id = uuid.uuid4()

        result = await service.check_and_increment_quota(user_id, "free")

        assert result == -1

    @pytest.mark.asyncio
    async def test_check_quota_no_key(self, service, mock_redis):
        mock_redis.eval.return_value = 1
        user_id = uuid.uuid4()

        result = await service.check_and_increment_quota(user_id, "basic")

        assert result == 1
