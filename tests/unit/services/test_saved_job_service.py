import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.saved_job_service import SavedJobService
from src.models.saved_job import SavedJob


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_repo):
    svc = SavedJobService(mock_session)
    svc._repo = mock_repo
    return svc


@pytest.mark.asyncio
async def test_save_new_job(service, mock_repo):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_repo.get_by_user_and_job = AsyncMock(return_value=None)

    saved = MagicMock(spec=SavedJob)
    saved.user_id = user_id
    saved.job_id = job_id
    mock_repo.save_job = AsyncMock(return_value=saved)

    result = await service.save(user_id, job_id)
    assert result == saved
    mock_repo.save_job.assert_called_once_with(user_id, job_id)


@pytest.mark.asyncio
async def test_save_already_saved_returns_existing(service, mock_repo):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    existing = MagicMock(spec=SavedJob)
    existing.user_id = user_id
    existing.job_id = job_id
    mock_repo.get_by_user_and_job = AsyncMock(return_value=existing)

    result = await service.save(user_id, job_id)
    assert result == existing
    mock_repo.save_job.assert_not_called()


@pytest.mark.asyncio
async def test_unsave_job(service, mock_repo):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_repo.unsave_job = AsyncMock(return_value=True)

    result = await service.unsave(user_id, job_id)
    assert result is True


@pytest.mark.asyncio
async def test_unsave_not_found(service, mock_repo):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_repo.unsave_job = AsyncMock(return_value=False)

    result = await service.unsave(user_id, job_id)
    assert result is False


@pytest.mark.asyncio
async def test_is_saved(service, mock_repo):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_repo.get_by_user_and_job = AsyncMock(return_value=MagicMock())
    assert await service.is_saved(user_id, job_id) is True

    mock_repo.get_by_user_and_job = AsyncMock(return_value=None)
    assert await service.is_saved(user_id, job_id) is False


@pytest.mark.asyncio
async def test_get_saved_jobs(service, mock_repo):
    user_id = uuid.uuid4()
    saved_jobs = [MagicMock(spec=SavedJob), MagicMock(spec=SavedJob)]
    mock_repo.get_saved_by_user = AsyncMock(return_value=saved_jobs)

    result = await service.get_saved_jobs(user_id, skip=0, limit=5)
    assert result == saved_jobs
    mock_repo.get_saved_by_user.assert_called_once_with(user_id, skip=0, limit=5)


@pytest.mark.asyncio
async def test_count_saved(service, mock_repo):
    user_id = uuid.uuid4()
    mock_repo.count_saved_by_user = AsyncMock(return_value=3)

    result = await service.count_saved(user_id)
    assert result == 3
