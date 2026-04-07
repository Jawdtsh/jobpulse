from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.channel_repository import ChannelRepository
from src.repositories.spam_rule_repository import SpamRuleRepository


@pytest_asyncio.fixture
async def channel_repo(db_session: AsyncSession):
    return ChannelRepository(db_session)


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

            with patch("src.services.job_filter_service.get_settings") as mock_st:
                s = MagicMock()
                s.redis.redis_url = "redis://localhost:6379"
                mock_st.return_value = s

                from src.services.job_filter_service import JobFilterService
                from src.services.job_ingestion_service import JobIngestionService

                spam_rule_repo = SpamRuleRepository(db_session)
                filter_svc = JobFilterService(spam_rule_repo)
                filter_svc._redis = AsyncMock()
                filter_svc._redis.get.return_value = None
                filter_svc._redis.setex = AsyncMock()
                with patch.object(
                    filter_svc._spam_rule_repo,
                    "get_active_rules",
                    new_callable=AsyncMock,
                    return_value=[],
                ):
                    svc = JobIngestionService(
                        session=db_session,
                        filter_service=filter_svc,
                    )
                    metrics = await svc.run_pipeline()
                    assert metrics["channels_processed"] == 1
                    assert metrics["messages_scraped"] >= 1
