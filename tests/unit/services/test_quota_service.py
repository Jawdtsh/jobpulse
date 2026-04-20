import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.quota_service import QuotaService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_repo):
    svc = QuotaService(mock_session)
    svc._repo = mock_repo
    return svc


@pytest.mark.asyncio
async def test_has_quota_sufficient(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_today = AsyncMock(return_value=None)

    result = await service.has_quota(user_id, "free")
    assert result is True


@pytest.mark.asyncio
async def test_has_quota_insufficient(service, mock_repo):
    user_id = uuid.uuid4()
    record = MagicMock()
    record.daily_used = 3
    record.purchased_extra = 0
    mock_repo.get_today = AsyncMock(return_value=record)

    result = await service.has_quota(user_id, "free")
    assert result is False


@pytest.mark.asyncio
async def test_get_remaining_quota_no_record(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_today = AsyncMock(return_value=None)
    created = MagicMock()
    created.daily_used = 0
    created.purchased_extra = 0
    mock_repo.get_or_create_today = AsyncMock(return_value=created)

    result = await service.get_remaining_quota(user_id, "free")
    assert result == 3


@pytest.mark.asyncio
async def test_get_remaining_quota_with_usage(service, mock_repo):
    user_id = uuid.uuid4()
    record = MagicMock()
    record.daily_used = 1
    record.purchased_extra = 0
    mock_repo.get_today = AsyncMock(return_value=record)

    result = await service.get_remaining_quota(user_id, "free")
    assert result == 2


@pytest.mark.asyncio
async def test_increment_daily_used(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_or_create_today = AsyncMock(return_value=MagicMock())
    mock_repo.increment_daily_used = AsyncMock(return_value=1)

    result = await service.increment_daily_used(user_id, "free")
    assert result == 1
    mock_repo.get_or_create_today.assert_called_once()
    mock_repo.increment_daily_used.assert_called_once()


@pytest.mark.asyncio
async def test_increment_daily_used_ensures_row_exists(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_or_create_today = AsyncMock(return_value=MagicMock())
    mock_repo.increment_daily_used = AsyncMock(return_value=1)

    await service.increment_daily_used(user_id, "free")

    call_order = []
    mock_repo.get_or_create_today.side_effect = lambda *a, **kw: (
        call_order.append("create") or MagicMock()
    )
    mock_repo.increment_daily_used.side_effect = lambda *a, **kw: (
        call_order.append("increment") or 1
    )
    call_order.clear()

    await service.increment_daily_used(user_id, "free")
    assert call_order == ["create", "increment"]


@pytest.mark.asyncio
async def test_add_purchased_extra(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.add_purchased_extra = AsyncMock(return_value=5)

    result = await service.add_purchased_extra(user_id, 5)
    assert result == 5
    mock_repo.add_purchased_extra.assert_called_once()


@pytest.mark.asyncio
async def test_get_daily_limit_free(service):
    result = await service.get_daily_limit("free")
    assert result == 3


@pytest.mark.asyncio
async def test_get_daily_limit_basic(service):
    result = await service.get_daily_limit("basic")
    assert result == 15


@pytest.mark.asyncio
async def test_get_daily_limit_pro(service):
    result = await service.get_daily_limit("pro")
    assert result == 50


@pytest.mark.asyncio
async def test_has_quota_with_purchased_extra(service, mock_repo):
    user_id = uuid.uuid4()
    record = MagicMock()
    record.daily_used = 4
    record.purchased_extra = 5
    mock_repo.get_today = AsyncMock(return_value=record)

    result = await service.has_quota(user_id, "free")
    assert result is True


@pytest.mark.asyncio
async def test_midnight_countdown():
    from src.services.quota_service import get_midnight_countdown_seconds

    countdown = get_midnight_countdown_seconds()
    assert 0 < countdown <= 86400


@pytest.mark.asyncio
async def test_decrement_daily_used(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.decrement_daily_used = AsyncMock(return_value=2)

    result = await service.decrement_daily_used(user_id, "free")
    assert result == 2
    mock_repo.decrement_daily_used.assert_called_once()


@pytest.mark.asyncio
async def test_get_remaining_quota_no_record_creates_it(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_today = AsyncMock(return_value=None)
    created = MagicMock()
    created.daily_used = 0
    created.purchased_extra = 5
    mock_repo.get_or_create_today = AsyncMock(return_value=created)

    result = await service.get_remaining_quota(user_id, "free")
    mock_repo.get_or_create_today.assert_called_once()
    assert result == 8


@pytest.mark.asyncio
async def test_has_quota_no_record_creates_and_checks(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_today = AsyncMock(return_value=None)
    created = MagicMock()
    created.daily_used = 0
    created.purchased_extra = 0
    mock_repo.get_or_create_today = AsyncMock(return_value=created)

    result = await service.has_quota(user_id, "free")
    assert result is True
