import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.job_filter_service import JobFilterService


@pytest.fixture
def mock_redis():
    with patch("src.services.job_filter_service._get_redis") as m:
        r = AsyncMock()
        m.return_value = r
        yield r


@pytest.fixture
def service():
    return JobFilterService()


def _make_rules(patterns, rule_type):
    return [MagicMock(pattern=p, rule_type=rule_type, is_active=True) for p in patterns]


class TestSpamKeywordMatching:
    @pytest.mark.asyncio
    async def test_blocks_spam_keyword(self, service, mock_redis):
        rules = _make_rules(["إعلان"], "spam_keyword")
        mock_redis.get.return_value = json.dumps(
            [{"pattern": r.pattern, "rule_type": r.rule_type} for r in rules]
        )
        mock_redis.close = AsyncMock()
        result = await service.filter_message("هذا إعلان مدفوع")
        assert result is False

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, service, mock_redis):
        mock_redis.get.return_value = json.dumps(
            [{"pattern": "SPAM", "rule_type": "spam_keyword"}]
        )
        mock_redis.close = AsyncMock()
        result = await service.filter_message("this is spam here")
        assert result is False


class TestScamIndicatorMatching:
    @pytest.mark.asyncio
    async def test_blocks_scam_indicator(self, service, mock_redis):
        mock_redis.get.return_value = json.dumps(
            [{"pattern": "رسوم تسجيل", "rule_type": "scam_indicator"}]
        )
        mock_redis.close = AsyncMock()
        result = await service.filter_message("يرجى دفع رسوم تسجيل")
        assert result is False


class TestMinimumLength:
    @pytest.mark.asyncio
    async def test_blocks_short_messages(self, service, mock_redis):
        mock_redis.get.return_value = None
        with patch.object(service, "_load_rules_from_db", return_value=[]):
            mock_redis.close = AsyncMock()
            result = await service.filter_message("hi")
            assert result is False

    @pytest.mark.asyncio
    async def test_allows_long_enough(self, service, mock_redis):
        mock_redis.get.return_value = None
        with patch.object(service, "_load_rules_from_db", return_value=[]):
            mock_redis.close = AsyncMock()
            text = "a" * 50
            result = await service.filter_message(text)
            assert result is True


class TestTextOnlyExtraction:
    @pytest.mark.asyncio
    async def test_blocks_empty_text(self, service, mock_redis):
        mock_redis.get.return_value = None
        with patch.object(service, "_load_rules_from_db", return_value=[]):
            mock_redis.close = AsyncMock()
            result = await service.filter_message("")
            assert result is False


class TestCacheHitMiss:
    @pytest.mark.asyncio
    async def test_cache_hit_path(self, service, mock_redis):
        mock_redis.get.return_value = json.dumps(
            [{"pattern": "blocked", "rule_type": "spam_keyword"}]
        )
        mock_redis.close = AsyncMock()
        result = await service.filter_message(
            "this is a perfectly fine message that is long enough"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_miss_loads_from_db(self, service, mock_redis):
        mock_redis.get.return_value = None
        mock_redis.setex = AsyncMock()
        mock_redis.close = AsyncMock()
        with patch.object(service, "_load_rules_from_db", return_value=[]) as mock_db:
            result = await service.filter_message("a" * 60)
            mock_db.assert_called_once()
            assert result is True
