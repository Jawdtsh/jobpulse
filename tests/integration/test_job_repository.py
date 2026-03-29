import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.job_repository import JobRepository
from src.repositories.channel_repository import ChannelRepository


@pytest_asyncio.fixture
async def channel_repo(async_session: AsyncSession):
    return ChannelRepository(async_session)


@pytest_asyncio.fixture
async def job_repo(async_session: AsyncSession):
    return JobRepository(async_session)


@pytest_asyncio.fixture
async def test_channel(channel_repo: ChannelRepository):
    return await channel_repo.create_channel(
        username="test_jobs",
        title="Test Jobs Channel",
    )


class TestJobRepository:
    @pytest.mark.asyncio
    async def test_create_job(self, job_repo: JobRepository):
        job = await job_repo.create_job(
            telegram_message_id=12345,
            title="Software Engineer",
            company="Tech Corp",
            description="Great opportunity",
        )
        assert job.title == "Software Engineer"
        assert job.company == "Tech Corp"
        assert job.content_hash is not None

    @pytest.mark.asyncio
    async def test_create_job_with_channel(
        self,
        job_repo: JobRepository,
        test_channel,
    ):
        job = await job_repo.create_job(
            telegram_message_id=54321,
            title="Backend Developer",
            company="Startup Inc",
            description="Join us",
            source_channel_id=test_channel.id,
        )
        assert job.source_channel_id == test_channel.id

    @pytest.mark.asyncio
    async def test_get_by_content_hash(self, job_repo: JobRepository):
        job = await job_repo.create_job(
            telegram_message_id=11111,
            title="Data Scientist",
            company="Data Co",
            description="Analyze data",
        )
        found = await job_repo.get_by_content_hash(job.content_hash)
        assert found is not None
        assert found.id == job.id

    @pytest.mark.asyncio
    async def test_deduplication_same_content(self, job_repo: JobRepository):
        job1 = await job_repo.create_job(
            telegram_message_id=22222,
            title="Same Job",
            company="Same Company",
            description="Same Description",
        )
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await job_repo.create_job(
                telegram_message_id=33333,
                title="Same Job",
                company="Same Company",
                description="Same Description",
            )
        assert job1.content_hash is not None

    @pytest.mark.asyncio
    async def test_get_active_jobs(self, job_repo: JobRepository):
        await job_repo.create_job(
            telegram_message_id=44444,
            title="Active Job",
            company="Active Co",
            description="Active",
        )
        archived = await job_repo.create_job(
            telegram_message_id=55555,
            title="Archived Job",
            company="Archived Co",
            description="Archived",
        )
        await job_repo.archive_job(archived.id)
        active_jobs = await job_repo.get_active_jobs()
        assert len(active_jobs) == 1
        assert active_jobs[0].telegram_message_id == 44444

    @pytest.mark.asyncio
    async def test_archive_job(self, job_repo: JobRepository):
        job = await job_repo.create_job(
            telegram_message_id=66666,
            title="To Archive",
            company="Archive Co",
            description="Will be archived",
        )
        archived = await job_repo.archive_job(job.id)
        assert archived is not None
        assert archived.is_archived == True

    @pytest.mark.asyncio
    async def test_update_embedding(self, job_repo: JobRepository):
        job = await job_repo.create_job(
            telegram_message_id=77777,
            title="Job with embedding",
            company="Embedding Co",
            description="Test",
        )
        embedding = [0.5] * 768
        updated = await job_repo.update_embedding(job.id, embedding)
        assert updated is not None
        assert updated.embedding_vector is not None
