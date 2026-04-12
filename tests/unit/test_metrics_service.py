import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.metrics_service import MetricsService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_match_repo():
    repo = AsyncMock()
    repo.get_matches_by_user = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def service(mock_session, mock_match_repo):
    with patch(
        "src.services.metrics_service.MatchRepository",
        return_value=mock_match_repo,
    ):
        svc = MetricsService(mock_session)
        svc._match_repo = mock_match_repo
        return svc


class TestMetricsService:
    @pytest.mark.asyncio
    async def test_calculate_metrics_returns_correct_structure(
        self, service, mock_match_repo
    ):
        match = MagicMock()
        match.id = uuid.uuid4()
        match.similarity_score = 0.85
        match.is_notified = True
        match.is_clicked = True
        mock_match_repo.get_matches_by_user = AsyncMock(return_value=[match])

        result = await service.calculate(user_id=uuid.uuid4())

        assert "score_buckets" in result
        assert isinstance(result["score_buckets"], dict)
        assert "ctr_data" in result
        assert isinstance(result["ctr_data"], dict)

    @pytest.mark.asyncio
    async def test_score_buckets_include_low_range(self, service, mock_match_repo):
        user_id = uuid.uuid4()
        matches = [
            MagicMock(
                id=uuid.uuid4(),
                similarity_score=0.50,
                is_notified=True,
                is_clicked=False,
            ),
            MagicMock(
                id=uuid.uuid4(),
                similarity_score=0.70,
                is_notified=True,
                is_clicked=True,
            ),
            MagicMock(
                id=uuid.uuid4(),
                similarity_score=0.90,
                is_notified=True,
                is_clicked=True,
            ),
        ]
        mock_match_repo.get_matches_by_user = AsyncMock(return_value=matches)

        result = await service.calculate(user_id=user_id)

        bucket_keys = list(result["score_buckets"].keys())
        low_bucket_found = any("0.00" in key or "0.60" in key for key in bucket_keys)
        assert low_bucket_found, f"Expected low bucket, got: {bucket_keys}"

    @pytest.mark.asyncio
    async def test_ctr_per_threshold_not_system_wide(self, service, mock_match_repo):
        user_id = uuid.uuid4()
        matches = [
            MagicMock(
                id=uuid.uuid4(),
                similarity_score=0.65,
                is_notified=True,
                is_clicked=False,
            ),
            MagicMock(
                id=uuid.uuid4(),
                similarity_score=0.65,
                is_notified=True,
                is_clicked=False,
            ),
            MagicMock(
                id=uuid.uuid4(),
                similarity_score=0.85,
                is_notified=True,
                is_clicked=True,
            ),
            MagicMock(
                id=uuid.uuid4(),
                similarity_score=0.85,
                is_notified=True,
                is_clicked=True,
            ),
        ]
        mock_match_repo.get_matches_by_user = AsyncMock(return_value=matches)

        result = await service.calculate(user_id=user_id)

        assert len(result["ctr_data"]) > 1 or any(
            "0.60" in key or "0.80" in key for key in result["ctr_data"].keys()
        ), "CTR should be per bucket, not system-wide"
