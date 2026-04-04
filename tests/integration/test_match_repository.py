import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repository import UserRepository
from src.repositories.job_repository import JobRepository
from src.repositories.match_repository import MatchRepository


@pytest_asyncio.fixture
async def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def job_repo(async_session: AsyncSession):
    return JobRepository(async_session)


@pytest_asyncio.fixture
async def match_repo(async_session: AsyncSession):
    return MatchRepository(async_session)


@pytest_asyncio.fixture
async def sample_user(user_repo: UserRepository):
    return await user_repo.create_user(telegram_id=700, first_name="MatchUser")


@pytest_asyncio.fixture
async def sample_job(job_repo: JobRepository):
    return await job_repo.create_job(
        telegram_message_id=77777,
        title="Test Job",
        company="Test Co",
        description="Test description",
    )


class TestMatchRepository:
    @pytest.mark.asyncio
    async def test_create_match(
        self,
        match_repo: MatchRepository,
        sample_user,
        sample_job,
    ):
        match = await match_repo.create_match(
            job_id=sample_job.id,
            user_id=sample_user.id,
            similarity_score=0.95,
        )
        assert match is not None
        assert match.similarity_score == 0.95
        assert match.is_notified is False

    @pytest.mark.asyncio
    async def test_duplicate_match_returns_none(
        self,
        match_repo: MatchRepository,
        sample_user,
        sample_job,
    ):
        match1 = await match_repo.create_match(
            job_id=sample_job.id,
            user_id=sample_user.id,
            similarity_score=0.95,
        )
        match2 = await match_repo.create_match(
            job_id=sample_job.id,
            user_id=sample_user.id,
            similarity_score=0.88,
        )
        assert match1 is not None
        assert match2 is None

    @pytest.mark.asyncio
    async def test_session_survives_duplicate_match(
        self,
        user_repo: UserRepository,
        match_repo: MatchRepository,
        sample_job,
        async_session: AsyncSession,
    ):
        user = await user_repo.create_user(telegram_id=701, first_name="Survivor")
        match = await match_repo.create_match(
            job_id=sample_job.id,
            user_id=user.id,
            similarity_score=0.90,
        )
        assert match is not None
        duplicate = await match_repo.create_match(
            job_id=sample_job.id,
            user_id=user.id,
            similarity_score=0.80,
        )
        assert duplicate is None
        user2 = await user_repo.create_user(telegram_id=702, first_name="PostDupe")
        assert user2 is not None
        assert user2.first_name == "PostDupe"

    @pytest.mark.asyncio
    async def test_get_matches_by_user(
        self,
        match_repo: MatchRepository,
        user_repo: UserRepository,
        job_repo: JobRepository,
    ):
        user = await user_repo.create_user(telegram_id=710, first_name="Multi")
        job1 = await job_repo.create_job(
            telegram_message_id=71001, title="J1", company="C1", description="D1"
        )
        job2 = await job_repo.create_job(
            telegram_message_id=71002, title="J2", company="C2", description="D2"
        )
        await match_repo.create_match(
            job_id=job1.id, user_id=user.id, similarity_score=0.9
        )
        await match_repo.create_match(
            job_id=job2.id, user_id=user.id, similarity_score=0.8
        )
        matches = await match_repo.get_matches_by_user(user.id)
        assert len(matches) == 2

    @pytest.mark.asyncio
    async def test_mark_notified(
        self,
        match_repo: MatchRepository,
        sample_user,
        sample_job,
    ):
        match = await match_repo.create_match(
            job_id=sample_job.id,
            user_id=sample_user.id,
            similarity_score=0.85,
        )
        notified = await match_repo.mark_notified(match.id)
        assert notified is not None
        assert notified.is_notified is True
        assert notified.notified_at is not None
