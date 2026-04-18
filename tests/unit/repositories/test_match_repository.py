import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.match_repository import MatchRepository


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def repo(mock_session):
    return MatchRepository(mock_session)


@pytest.mark.asyncio
async def test_get_notified_exclude_dismissed_true(repo, mock_session):
    user_id = uuid.uuid4()
    mock_result = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    await repo.get_notified_matches_by_user(
        user_id, skip=0, limit=5, exclude_dismissed=True
    )

    call_args = mock_session.execute.call_args[0][0]
    compiled = str(call_args)
    assert "is_dismissed" in compiled


@pytest.mark.asyncio
async def test_get_notified_exclude_dismissed_false(repo, mock_session):
    user_id = uuid.uuid4()
    mock_result = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    await repo.get_notified_matches_by_user(
        user_id, skip=0, limit=5, exclude_dismissed=False
    )

    call_args = mock_session.execute.call_args[0][0]
    compiled = str(call_args)
    assert "is_dismissed" not in compiled


@pytest.mark.asyncio
async def test_get_notified_default_excludes_dismissed(repo, mock_session):
    user_id = uuid.uuid4()
    mock_result = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    await repo.get_notified_matches_by_user(user_id, skip=0, limit=5)

    call_args = mock_session.execute.call_args[0][0]
    compiled = str(call_args)
    assert "is_dismissed" in compiled
