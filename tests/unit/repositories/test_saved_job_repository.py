import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.saved_job_repository import SavedJobRepository


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def repo(mock_session):
    return SavedJobRepository(mock_session)


@pytest.mark.asyncio
async def test_get_saved_by_user_no_days_filter(repo, mock_session):
    user_id = uuid.uuid4()
    mock_result = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await repo.get_saved_by_user(user_id, skip=0, limit=5)

    assert result == []
    call_args = mock_session.execute.call_args[0][0]
    compiled = str(call_args)
    assert "saved_at" not in compiled or ">=" not in compiled


@pytest.mark.asyncio
async def test_get_saved_by_user_with_days_filter(repo, mock_session):
    user_id = uuid.uuid4()
    mock_result = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await repo.get_saved_by_user(user_id, skip=0, limit=5, days=7)

    assert result == []
    call_args = mock_session.execute.call_args[0][0]
    compiled = str(call_args)
    assert "saved_at" in compiled


@pytest.mark.asyncio
async def test_unsave_job_single_delete_found(repo, mock_session):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()

    result = await repo.unsave_job(user_id, job_id)

    assert result is True
    mock_session.execute.assert_called_once()
    mock_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_unsave_job_single_delete_not_found(repo, mock_session):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.flush = AsyncMock()

    result = await repo.unsave_job(user_id, job_id)

    assert result is False


@pytest.mark.asyncio
async def test_get_saved_by_user_no_min_similarity_param(repo, mock_session):
    import inspect

    sig = inspect.signature(repo.get_saved_by_user)
    assert "min_similarity" not in sig.parameters
    assert "days" in sig.parameters
