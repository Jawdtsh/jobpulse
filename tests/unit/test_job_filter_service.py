import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.job_filter_service import JobFilterService


@pytest.fixture
def mock_spam_rule_repo():
    repo = AsyncMock()
    repo.get_active_rules.return_value = []
    return repo


@pytest.fixture
def service(mock_spam_rule_repo):
    with patch("src.services.job_filter_service.get_settings") as mock_settings:
        s = MagicMock()
        s.redis.redis_url = "redis://localhost:6379"
        mock_settings.return_value = s
        return JobFilterService(mock_spam_rule_repo)


@pytest.fixture
def mock_redis(service):
    r = AsyncMock()
    service._redis = r
    return r


class TestSpamKeywordMatching:
    @pytest.mark.asyncio
    async def test_blocks_spam_keyword(self, service, mock_redis):
        mock_redis.get.return_value = json.dumps(
            [{"pattern": "إعلان", "rule_type": "spam_keyword"}]
        )
        result = await service.filter_message("هذا إعلان مدفوع")
        assert result is False

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, service, mock_redis):
        mock_redis.get.return_value = json.dumps(
            [{"pattern": "SPAM", "rule_type": "spam_keyword"}]
        )
        result = await service.filter_message("this is spam here")
        assert result is False


class TestScamIndicatorMatching:
    @pytest.mark.asyncio
    async def test_blocks_scam_indicator(self, service, mock_redis):
        mock_redis.get.return_value = json.dumps(
            [{"pattern": "رسوم تسجيل", "rule_type": "scam_indicator"}]
        )
        result = await service.filter_message("يرجى دفع رسوم تسجيل")
        assert result is False


class TestMinimumLength:
    @pytest.mark.asyncio
    async def test_blocks_short_messages(
        self, service, mock_redis, mock_spam_rule_repo
    ):
        mock_redis.get.return_value = None
        mock_spam_rule_repo.get_active_rules.return_value = []
        result = await service.filter_message("hi")
        assert result is False

    @pytest.mark.asyncio
    async def test_allows_long_enough(self, service, mock_redis, mock_spam_rule_repo):
        mock_redis.get.return_value = None
        mock_spam_rule_repo.get_active_rules.return_value = []
        text = "a" * 50
        result = await service.filter_message(text)
        assert result is True


class TestTextOnlyExtraction:
    @pytest.mark.asyncio
    async def test_blocks_empty_text(self, service, mock_redis, mock_spam_rule_repo):
        mock_redis.get.return_value = None
        mock_spam_rule_repo.get_active_rules.return_value = []
        result = await service.filter_message("")
        assert result is False


class TestCacheHitMiss:
    @pytest.mark.asyncio
    async def test_cache_hit_path(self, service, mock_redis):
        mock_redis.get.return_value = json.dumps(
            [{"pattern": "blocked", "rule_type": "spam_keyword"}]
        )
        result = await service.filter_message(
            "this is a blocked message that is long enough"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_miss_loads_from_db(
        self, service, mock_redis, mock_spam_rule_repo
    ):
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()
        mock_spam_rule_repo.get_active_rules.return_value = []
        result = await service.filter_message("a" * 60)
        mock_spam_rule_repo.get_active_rules.assert_called_once()
        mock_redis.setex.assert_awaited_once()
        assert result is True
