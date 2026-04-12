import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.notification_service import NotificationService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_match_repo():
    repo = AsyncMock()
    repo.get = AsyncMock(
        return_value=MagicMock(
            id=uuid.uuid4(),
            job_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            cv_id=uuid.uuid4(),
            similarity_score=0.85,
        )
    )
    repo.mark_notified = AsyncMock()
    repo.get_pending_by_cv = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_job_repo():
    repo = AsyncMock()
    job = MagicMock()
    job.id = uuid.uuid4()
    job.title = "Software Engineer"
    job.company = "Tech Corp"
    job.salary_min = 5000
    job.salary_max = 10000
    job.salary_currency = "USD"
    job.location = "Remote"
    job.created_at = datetime.now(timezone.utc)
    repo.get = AsyncMock(return_value=job)
    return repo


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.telegram_id = 123456789
    user.subscription_tier = "pro"
    repo.get = AsyncMock(return_value=user)
    return repo


@pytest.fixture
def mock_queue():
    queue = AsyncMock()
    queue.enqueue = AsyncMock()
    queue.fetch_due = AsyncMock(return_value=[])
    queue.remove_by_cv = AsyncMock()
    return queue


@pytest.fixture
def service(mock_session, mock_match_repo, mock_job_repo, mock_user_repo, mock_queue):
    with (
        patch(
            "src.services.notification_service.MatchRepository",
            return_value=mock_match_repo,
        ),
        patch(
            "src.services.notification_service.JobRepository",
            return_value=mock_job_repo,
        ),
        patch(
            "src.services.notification_service.UserRepository",
            return_value=mock_user_repo,
        ),
        patch(
            "src.services.notification_service.NotificationQueue",
            return_value=mock_queue,
        ),
    ):
        svc = NotificationService(mock_session, mock_queue)
        return svc


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_queue_match_notification(self, service, mock_queue):
        match_id = uuid.uuid4()
        await service.queue_match_notification(match_id)
        mock_queue.enqueue.assert_called_once()

    @pytest.mark.asyncio
    async def test_queue_match_immediate(self, service, mock_queue):
        match_id = uuid.uuid4()
        await service.queue_match_immediate(match_id)
        mock_queue.enqueue.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_due_notifications_empty(self, service, mock_queue):
        mock_queue.fetch_due.return_value = []
        count = await service.process_due_notifications()
        assert count == 0

    @pytest.mark.asyncio
    async def test_cancel_notifications_for_cv(self, service, mock_queue):
        cv_id = uuid.uuid4()
        await service.cancel_notifications_for_cv(cv_id)
        mock_queue.remove_by_cv.assert_called_once()


class TestTierDelays:
    def test_free_tier_delay(self):
        with patch("src.services.notification_service.get_settings") as mock:
            mock.return_value.matching.tier_delay_free = 3600
            mock.return_value.matching.tier_delay_basic = 600
            mock.return_value.matching.tier_delay_pro = 0
            delay = NotificationService._get_tier_delay("free")
            assert delay == 3600

    def test_basic_tier_delay(self):
        with patch("src.services.notification_service.get_settings") as mock:
            mock.return_value.matching.tier_delay_free = 3600
            mock.return_value.matching.tier_delay_basic = 600
            mock.return_value.matching.tier_delay_pro = 0
            delay = NotificationService._get_tier_delay("basic")
            assert delay == 600

    def test_pro_tier_delay(self):
        with patch("src.services.notification_service.get_settings") as mock:
            mock.return_value.matching.tier_delay_free = 3600
            mock.return_value.matching.tier_delay_basic = 600
            mock.return_value.matching.tier_delay_pro = 0
            delay = NotificationService._get_tier_delay("pro")
            assert delay == 0
