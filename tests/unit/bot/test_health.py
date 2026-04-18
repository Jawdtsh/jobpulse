import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_health_uses_proper_sqlalchemy_import():
    import src.bot.health as health_mod

    assert hasattr(health_mod, "text")
    from sqlalchemy import text as sa_text

    assert health_mod.text is sa_text


def test_health_no_dunder_import():
    import src.bot.health as health_mod

    source = inspect.getsource(health_mod)
    assert "__import__" not in source


@pytest.mark.asyncio
async def test_health_handler_database_ok():
    from src.bot.health import _health_handler

    mock_result = MagicMock()
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_gen():
        yield mock_session

    with (
        patch("src.bot.health.get_async_session", mock_gen),
        patch("src.bot.health.get_settings"),
        patch("src.bot.health.aioredis") as mock_aioredis,
    ):
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.aclose = AsyncMock()
        mock_aioredis.from_url.return_value = mock_redis

        request = MagicMock()
        response = await _health_handler(request)
        assert response.status == 200
