from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.middlewares import RateLimiterMiddleware


def test_callback_validation_middleware_removed():
    import src.bot.middlewares as mod

    assert not hasattr(mod, "CallbackValidationMiddleware")


def test_rate_limiter_no_queue_attr():
    rl = RateLimiterMiddleware()
    assert not hasattr(rl, "_queue")


def test_rate_limiter_uses_ttl_cache():
    from cachetools import TTLCache

    rl = RateLimiterMiddleware()
    assert isinstance(rl._user_timestamps, TTLCache)
    assert rl._user_timestamps.maxsize == 10000
    assert rl._user_timestamps.ttl == 60


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit():
    rl = RateLimiterMiddleware(rate_limit=2)

    event = MagicMock()
    event.from_user = MagicMock()
    event.from_user.id = 1

    handler = AsyncMock(return_value="ok")

    result1 = await rl(handler, event, {})
    result2 = await rl(handler, event, {})
    assert result1 == "ok"
    assert result2 == "ok"


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit():
    rl = RateLimiterMiddleware(rate_limit=2)

    event = MagicMock()
    event.from_user = MagicMock()
    event.from_user.id = 2

    handler = AsyncMock(return_value="ok")

    await rl(handler, event, {})
    await rl(handler, event, {})
    result = await rl(handler, event, {})
    assert result is None


@pytest.mark.asyncio
async def test_rate_limiter_no_user_passes_through():
    rl = RateLimiterMiddleware()

    event = MagicMock()
    event.from_user = None

    handler = AsyncMock(return_value="ok")
    result = await rl(handler, event, {})
    assert result == "ok"
