import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.metrics_service import MetricsService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def service(mock_session):
    return MetricsService(mock_session)


class TestMetricsService:
    @pytest.mark.asyncio
    async def test_calculate_ctr_zero_matches(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = MagicMock(total_notified=0, total_clicked=0)
        mock_session.execute.return_value = mock_result

        ctr = await service.calculate_ctr()
        assert ctr["total_notified"] == 0
        assert ctr["total_clicked"] == 0
        assert ctr["ctr"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_ctr_with_clicks(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = MagicMock(total_notified=100, total_clicked=25)
        mock_session.execute.return_value = mock_result

        ctr = await service.calculate_ctr()
        assert ctr["total_notified"] == 100
        assert ctr["total_clicked"] == 25
        assert ctr["ctr"] == 0.25

    @pytest.mark.asyncio
    async def test_get_score_distribution_empty(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        dist = await service.get_score_distribution()
        assert dist["count"] == 0

    @pytest.mark.asyncio
    async def test_get_score_distribution_with_scores(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.all.return_value = [(0.65,), (0.75,), (0.85,), (0.95,)]
        mock_session.execute.return_value = mock_result

        dist = await service.get_score_distribution()
        assert dist["count"] == 4
        assert dist["distribution"]["0.60-0.70"] == 1
        assert dist["distribution"]["0.70-0.80"] == 1
        assert dist["distribution"]["0.80-0.90"] == 1
        assert dist["distribution"]["0.90-1.00"] == 1

    @pytest.mark.asyncio
    async def test_check_low_performing_below_threshold(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = MagicMock(total_notified=100, total_clicked=2)
        mock_session.execute.return_value = mock_result

        warnings = await service.check_low_performing()
        assert len(warnings) > 0

    @pytest.mark.asyncio
    async def test_check_low_performing_above_threshold(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = MagicMock(total_notified=100, total_clicked=50)
        mock_session.execute.return_value = mock_result

        warnings = await service.check_low_performing()
        assert len(warnings) == 0

    @pytest.mark.asyncio
    async def test_generate_report(self, service, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = MagicMock(total_notified=50, total_clicked=10)
        mock_result.all.return_value = [(0.85,)]
        mock_session.execute.return_value = mock_result

        report = await service.generate_report()
        assert "ctr" in report
        assert "score_distribution" in report
        assert "warnings" in report
        assert "generated_at" in report
