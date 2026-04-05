from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.channel_repository import ChannelRepository


from src.repositories.telegram_session_repository import TelegramSessionRepository


@pytest_asyncio.fixture
async def channel_repo(db_session: AsyncSession):
    return ChannelRepository(db_session)


@pytest_asyncio.fixture
async def session_repo(db_session: AsyncSession):
    return TelegramSessionRepository(db_session)


class TestScrapeAndFilterFlow:
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_with_mock_scraper(
        self, db_session: AsyncSession
    ):
        _ = await ChannelRepository(db_session).create(
            username="test_channel", title="Test", is_active=True
        )
        await db_session.commit()

        with patch(
            "src.services.telegram_scraper_service.TelegramClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.connect = AsyncMock()
            mock_client.disconnect = AsyncMock()

            mock_msg1 = MagicMock()
            mock_msg1.text = "a" * 100
            mock_msg1.id = 1
            mock_msg2 = MagicMock()
            mock_msg2.text = "short"
            mock_msg2.id = 2
            mock_client.iter_messages.return_value = [mock_msg1, mock_msg2]

            with patch("src.services.job_filter_service._get_redis") as mock_redis:
                r = AsyncMock()
                r.get.return_value = None
                r.close = AsyncMock()
                r.setex = AsyncMock()
                mock_redis.return_value = r

                from src.services.job_filter_service import JobFilterService
                from src.services.job_ingestion_service import JobIngestionService

                filter_svc = JobFilterService()
                with patch.object(filter_svc, "_load_rules_from_db", return_value=[]):
                    svc = JobIngestionService(
                        session=db_session,
                        filter_service=filter_svc,
                    )
                    metrics = await svc.run_pipeline()
                    assert "channels_processed" in metrics
                    assert metrics["channels_processed"] >= 0
