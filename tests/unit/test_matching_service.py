import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.exceptions import (
    EmbeddingNotAvailableError,
    JobNotFoundError,
)
from src.services.matching_service import (
    MatchingService,
    ProTierRequiredError,
)


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_match_repo():
    repo = AsyncMock()
    repo.create_match = AsyncMock(return_value=MagicMock(id=uuid.uuid4()))
    repo.get_by_job_and_user = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_cv_repo():
    repo = AsyncMock()
    repo.find_similar_cvs = AsyncMock(return_value=[])
    repo.get_active_cvs = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_job_repo():
    repo = AsyncMock()
    repo.get = AsyncMock()
    repo.get_jobs_since = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_threshold_service():
    svc = AsyncMock()
    svc.get_effective_threshold = AsyncMock(return_value=0.80)
    return svc


@pytest.fixture
def service(
    mock_session,
    mock_match_repo,
    mock_cv_repo,
    mock_job_repo,
    mock_user_repo,
    mock_threshold_service,
):
    with (
        patch(
            "src.services.matching_service.MatchRepository",
            return_value=mock_match_repo,
        ),
        patch("src.services.matching_service.CVRepository", return_value=mock_cv_repo),
        patch(
            "src.services.matching_service.JobRepository", return_value=mock_job_repo
        ),
        patch(
            "src.services.matching_service.UserRepository", return_value=mock_user_repo
        ),
        patch(
            "src.services.matching_service.ThresholdService",
            return_value=mock_threshold_service,
        ),
    ):
        svc = MatchingService(mock_session)
        return svc


class TestMatchingService:
    @pytest.mark.asyncio
    async def test_match_new_job_not_found(self, service, mock_job_repo):
        mock_job_repo.get.return_value = None
        job_id = uuid.uuid4()

        with pytest.raises(JobNotFoundError):
            await service.match_new_job(job_id)

    @pytest.mark.asyncio
    async def test_match_new_job_no_embedding(self, service, mock_job_repo):
        job = MagicMock()
        job.id = uuid.uuid4()
        job.embedding_vector = None
        mock_job_repo.get.return_value = job

        with pytest.raises(EmbeddingNotAvailableError):
            await service.match_new_job(job.id)

    @pytest.mark.asyncio
    async def test_match_new_job_no_similar_cvs(
        self, service, mock_job_repo, mock_cv_repo
    ):
        job = MagicMock()
        job.id = uuid.uuid4()
        job.embedding_vector = [0.1] * 768
        mock_job_repo.get.return_value = job
        mock_cv_repo.find_similar_cvs.return_value = []

        results = await service.match_new_job(job.id)
        assert results == []

    @pytest.mark.asyncio
    async def test_match_new_job_pgvector_with_per_user_threshold(
        self,
        service,
        mock_job_repo,
        mock_cv_repo,
        mock_match_repo,
        mock_threshold_service,
    ):
        job = MagicMock()
        job.id = uuid.uuid4()
        job.embedding_vector = [0.1] * 768
        mock_job_repo.get.return_value = job

        cv1 = MagicMock()
        cv1.id = uuid.uuid4()
        cv1.user_id = uuid.uuid4()
        cv2 = MagicMock()
        cv2.id = uuid.uuid4()
        cv2.user_id = uuid.uuid4()
        cv3 = MagicMock()
        cv3.id = uuid.uuid4()
        cv3.user_id = uuid.uuid4()

        mock_cv_repo.find_similar_cvs.return_value = [
            (cv1, 0.92),
            (cv2, 0.85),
            (cv3, 0.70),
        ]
        mock_threshold_service.get_effective_threshold.side_effect = [0.85, 0.80, 0.80]

        await service.match_new_job(job.id)

        mock_cv_repo.find_similar_cvs.assert_called_once_with(
            job_embedding=job.embedding_vector,
            threshold=0.80,
            limit=10000,
        )
        assert mock_match_repo.create_match.call_count == 2


class TestMatchHistorical:
    @pytest.mark.asyncio
    async def test_match_historical_non_pro_raises(self, service, mock_user_repo):
        user_id = uuid.uuid4()
        mock_user = MagicMock()
        mock_user.subscription_tier = "free"
        mock_user_repo.get.return_value = mock_user

        with pytest.raises(ProTierRequiredError):
            await service.match_historical(user_id, days=3)

    @pytest.mark.asyncio
    async def test_match_historical_invalid_days_raises(self, service):
        user_id = uuid.uuid4()

        with pytest.raises(ValueError):
            await service.match_historical(user_id, days=10)

    @pytest.mark.asyncio
    async def test_match_historical_days_zero_raises(self, service):
        user_id = uuid.uuid4()

        with pytest.raises(ValueError):
            await service.match_historical(user_id, days=0)
