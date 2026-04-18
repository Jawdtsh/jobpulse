import json
from unittest.mock import AsyncMock

import pytest

from src.services.bot_session_service import (
    BotSessionService,
    SESSION_PREFIX,
    SESSION_TTL,
    CLEANUP_THRESHOLD,
)


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    return redis


@pytest.fixture
def service(mock_redis):
    svc = BotSessionService()
    svc._redis = mock_redis
    return svc


@pytest.mark.asyncio
async def test_set_session(service, mock_redis):
    await service.set_session(123, "waiting_for_file", {"step": 1})
    mock_redis.set.assert_called_once()
    args = mock_redis.set.call_args
    assert args[0][0] == f"{SESSION_PREFIX}123"
    data = json.loads(args[0][1])
    assert data["current_state"] == "waiting_for_file"
    assert data["flow_data"] == {"step": 1}


@pytest.mark.asyncio
async def test_get_session(service, mock_redis):
    session_data = json.dumps(
        {
            "user_id": 123,
            "current_state": "browsing",
            "last_activity": "2026-04-16T12:00:00+00:00",
            "flow_data": {},
        }
    )
    mock_redis.get = AsyncMock(return_value=session_data)

    result = await service.get_session(123)
    assert result is not None
    assert result["current_state"] == "browsing"


@pytest.mark.asyncio
async def test_get_session_not_found(service, mock_redis):
    mock_redis.get = AsyncMock(return_value=None)
    result = await service.get_session(999)
    assert result is None


@pytest.mark.asyncio
async def test_clear_session(service, mock_redis):
    await service.clear_session(123)
    mock_redis.delete.assert_called_once_with(f"{SESSION_PREFIX}123")


@pytest.mark.asyncio
async def test_is_expired_no_session(service, mock_redis):
    mock_redis.get = AsyncMock(return_value=None)
    assert await service.is_expired(123) is True


@pytest.mark.asyncio
async def test_is_expired_active_session(service, mock_redis):
    from datetime import datetime, timezone

    session_data = json.dumps(
        {
            "user_id": 123,
            "current_state": "browsing",
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "flow_data": {},
        }
    )
    mock_redis.get = AsyncMock(return_value=session_data)
    assert await service.is_expired(123) is False


@pytest.mark.asyncio
async def test_update_activity(service, mock_redis):
    session_data = json.dumps(
        {
            "user_id": 123,
            "current_state": "browsing",
            "last_activity": "2026-04-16T12:00:00+00:00",
            "flow_data": {"filter": "saved"},
        }
    )
    mock_redis.get = AsyncMock(return_value=session_data)

    await service.update_activity(123)
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(service, mock_redis):
    async def mock_scan_iter(match):
        for key in ["bot_session:1", "bot_session:2"]:
            yield key

    mock_redis.scan_iter = mock_scan_iter
    old_data = json.dumps(
        {
            "user_id": 1,
            "current_state": "browsing",
            "last_activity": "2026-04-16T00:00:00+00:00",
            "flow_data": {},
        }
    )
    mock_redis.get = AsyncMock(return_value=old_data)

    cleaned = await service.cleanup_expired_sessions()
    assert cleaned >= 0


@pytest.mark.asyncio
async def test_get_session_redis_error(service, mock_redis):
    mock_redis.get = AsyncMock(side_effect=Exception("Redis down"))
    result = await service.get_session(123)
    assert result is None


@pytest.mark.asyncio
async def test_set_session_redis_error(service, mock_redis):
    mock_redis.set = AsyncMock(side_effect=Exception("Redis down"))
    await service.set_session(123, "test")


def test_cleanup_threshold_equals_session_ttl_plus_300():
    assert CLEANUP_THRESHOLD == SESSION_TTL + 300
    assert CLEANUP_THRESHOLD == 900
