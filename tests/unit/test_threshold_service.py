import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.threshold_service import (
    ThresholdService,
    ThresholdOutOfRangeError,
)


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def service(mock_session):
    return ThresholdService(mock_session)


class TestThresholdService:
    @pytest.mark.asyncio
    async def test_get_effective_threshold_default(self, service, mock_session):
        user_id = uuid.uuid4()
        with patch("src.services.threshold_service.get_settings") as mock:
            mock.return_value.matching.matching_threshold_default = 0.80

            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            threshold = await service.get_effective_threshold(user_id)
            assert threshold == 0.80

    @pytest.mark.asyncio
    async def test_set_user_threshold_valid(self, service, mock_session):
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.add = AsyncMock()
        mock_session.flush = AsyncMock()

        prefs = await service.set_user_threshold(user_id, 0.85)
        assert prefs.similarity_threshold == 0.85

    @pytest.mark.asyncio
    async def test_set_user_threshold_too_low_raises(self, service, mock_session):
        user_id = uuid.uuid4()
        with pytest.raises(ThresholdOutOfRangeError):
            await service.set_user_threshold(user_id, 0.50)

    @pytest.mark.asyncio
    async def test_set_user_threshold_too_high_raises(self, service, mock_session):
        user_id = uuid.uuid4()
        with pytest.raises(ThresholdOutOfRangeError):
            await service.set_user_threshold(user_id, 1.10)

    @pytest.mark.asyncio
    async def test_set_user_threshold_at_min_boundary(self, service, mock_session):
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.add = AsyncMock()
        mock_session.flush = AsyncMock()

        prefs = await service.set_user_threshold(user_id, 0.60)
        assert prefs.similarity_threshold == 0.60

    @pytest.mark.asyncio
    async def test_set_user_threshold_at_max_boundary(self, service, mock_session):
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        mock_session.add = AsyncMock()
        mock_session.flush = AsyncMock()

        prefs = await service.set_user_threshold(user_id, 1.00)
        assert prefs.similarity_threshold == 1.00
