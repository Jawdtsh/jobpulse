import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.monitored_channel import MonitoredChannel
from src.repositories.channel_repository import ChannelRepository
from src.repositories.job_repository import JobRepository


@pytest_asyncio.fixture
async def channel(db_session: AsyncSession):
    repo = ChannelRepository(db_session)
    ch = await repo.create(username="dedup_test", title="Dedup Test", is_active=True)
    await db_session.commit()
    return ch


class TestDeduplicateAndStore:
    @pytest.mark.asyncio
    async def test_duplicate_detection_via_content_hash(
        self, db_session: AsyncSession, channel: MonitoredChannel
    ):
        repo = JobRepository(db_session)
        text = "Software Engineer at Google Remote Position " * 3

        job1 = await repo.create_job(
            telegram_message_id=1,
            title="Software Engineer",
            company="Google",
            description=text,
            source_channel_id=channel.id,
        )
        await db_session.commit()

        existing = await repo.get_by_content_hash(job1.content_hash)
        assert existing is not None

    @pytest.mark.asyncio
    async def test_unique_job_insertion(
        self, db_session: AsyncSession, channel: MonitoredChannel
    ):
        repo = JobRepository(db_session)
        job = await repo.create_job(
            telegram_message_id=42,
            title="DevOps Engineer",
            company="Amazon",
            description="Manage infrastructure and CI/CD pipelines",
            source_channel_id=channel.id,
            location="Remote",
            salary_min=5000,
            salary_max=8000,
            requirements=["Docker", "Kubernetes"],
            skills=["AWS", "Terraform"],
        )
        await db_session.commit()

        fetched = await repo.get(job.id)
        assert fetched is not None
        assert fetched.title == "DevOps Engineer"
        assert fetched.location == "Remote"
        assert fetched.salary_min == 5000

    @pytest.mark.asyncio
    async def test_embedding_storage(
        self, db_session: AsyncSession, channel: MonitoredChannel
    ):
        repo = JobRepository(db_session)
        job = await repo.create_job(
            telegram_message_id=99,
            title="Test",
            company="TestCo",
            description="Test description for embedding",
            source_channel_id=channel.id,
        )
        await db_session.commit()

        embedding = [0.1] * 768
        _ = await repo.update_embedding(job.id, embedding)
        await db_session.commit()

        fetched = await repo.get(job.id)
        assert fetched.embedding_vector is not None
        assert len(fetched.embedding_vector) == 768

    @pytest.mark.asyncio
    async def test_channel_counter_increments(
        self, db_session: AsyncSession, channel: MonitoredChannel
    ):
        repo = ChannelRepository(db_session)
        updated = await repo.increment_jobs_found(channel.id, 1)
        await db_session.commit()

        fetched = await repo.get(channel.id)
        assert fetched.jobs_found == 1

        _ = await repo.increment_false_positives(channel.id, 1)
        await db_session.commit()

        fetched = await repo.get(channel.id)
        assert fetched.false_positives == 1
