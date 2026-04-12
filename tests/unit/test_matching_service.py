import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
    repo.get_active_cvs = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_job_repo():
    repo = AsyncMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def mock_settings():
    with patch("src.services.matching_service.get_settings") as mock:
        mock.return_value.matching.matching_threshold_default = 0.80
        yield mock


@pytest.fixture
def service(
    mock_session,
    mock_match_repo,
    mock_cv_repo,
    mock_job_repo,
    mock_user_repo,
    mock_settings,
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
    ):
        svc = MatchingService(mock_session)
        return svc


class TestMatchingService:
    @pytest.mark.asyncio
    async def test_match_new_job_not_found(self, service, mock_job_repo):
        mock_job_repo.get.return_value = None
        job_id = uuid.uuid4()

        with pytest.raises(Exception):
            await service.match_new_job(job_id)

    @pytest.mark.asyncio
    async def test_match_new_job_no_embedding(self, service, mock_job_repo):
        job = MagicMock()
        job.id = uuid.uuid4()
        job.embedding_vector = None
        mock_job_repo.get.return_value = job

        with pytest.raises(Exception):
            await service.match_new_job(job.id)

    @pytest.mark.asyncio
    async def test_match_new_job_no_active_cvs(
        self, service, mock_job_repo, mock_session
    ):
        job = MagicMock()
        job.id = uuid.uuid4()
        job.embedding_vector = [0.1] * 768
        mock_job_repo.get.return_value = job

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        results = await service.match_new_job(job.id)
        assert results == []


class TestCosineSimilarity:
    def test_identical_vectors(self):
        vec = [1.0, 0.0, 0.0]
        score = MatchingService._cosine_similarity(vec, vec)
        assert score == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        score = MatchingService._cosine_similarity(vec_a, vec_b)
        assert score == pytest.approx(0.0)

    def test_opposite_vectors(self):
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [-1.0, 0.0, 0.0]
        score = MatchingService._cosine_similarity(vec_a, vec_b)
        assert score == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self):
        vec_a = [0.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        score = MatchingService._cosine_similarity(vec_a, vec_b)
        assert score == 0.0

    def test_partial_overlap(self):
        vec_a = [1.0, 2.0, 3.0]
        vec_b = [2.0, 4.0, 6.0]
        score = MatchingService._cosine_similarity(vec_a, vec_b)
        assert score == pytest.approx(1.0)


class TestMatchHistorical:
    @pytest.mark.asyncio
    async def test_match_historical_non_pro_raises(
        self, service, mock_user_repo, mock_settings
    ):
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


class TestThreshold:
    @pytest.mark.asyncio
    async def test_get_threshold_default(self, service, mock_session, mock_settings):
        user_id = uuid.uuid4()
        threshold = await service._get_threshold(user_id)
        assert threshold == 0.80
