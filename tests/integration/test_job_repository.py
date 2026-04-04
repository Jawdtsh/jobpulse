import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.job import Job
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
        assert archived.is_archived

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

    @pytest.mark.asyncio
    async def test_find_similar_returns_jobs_with_scores(self, job_repo: JobRepository):
        job1 = await job_repo.create_job(
            telegram_message_id=80001,
            title="Python Developer",
            company="PyCo",
            description="Python job",
        )
        job2 = await job_repo.create_job(
            telegram_message_id=80002,
            title="Java Developer",
            company="JavaCo",
            description="Java job",
        )
        embedding = [0.1] * 768
        await job_repo.update_embedding(job1.id, embedding)
        embedding2 = [0.9] * 768
        await job_repo.update_embedding(job2.id, embedding2)

        query_embedding = [0.1] * 768
        results = await job_repo.find_similar(
            embedding_vector=query_embedding, threshold=0.5, limit=10
        )
        assert len(results) >= 1
        for job, score in results:
            assert isinstance(job, Job)
            assert isinstance(score, float)
            assert score >= 0.5
        job_ids = [job.id for job, _ in results]
        assert job1.id in job_ids

    @pytest.mark.asyncio
    async def test_find_similar_excludes_archived(self, job_repo: JobRepository):
        job = await job_repo.create_job(
            telegram_message_id=80010,
            title="Archived Similar",
            company="ArchCo",
            description="Will be archived",
        )
        embedding = [0.5] * 768
        await job_repo.update_embedding(job.id, embedding)
        await job_repo.archive_job(job.id)

        results = await job_repo.find_similar(
            embedding_vector=embedding, threshold=0.0, limit=10
        )
        result_ids = [j.id for j, _ in results]
        assert job.id not in result_ids

    @pytest.mark.asyncio
    async def test_find_similar_respects_limit(self, job_repo: JobRepository):
        for i in range(5):
            job = await job_repo.create_job(
                telegram_message_id=80020 + i,
                title=f"Limit Job {i}",
                company="LimitCo",
                description=f"Job {i}",
            )
            await job_repo.update_embedding(job.id, [0.5] * 768)

        results = await job_repo.find_similar(
            embedding_vector=[0.5] * 768, threshold=0.0, limit=2
        )
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_find_similar_returns_empty_for_no_matches(
        self, job_repo: JobRepository
    ):
        results = await job_repo.find_similar(
            embedding_vector=[0.5] * 768, threshold=0.99, limit=10
        )
        assert results == []
