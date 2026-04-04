import pytest
import pytest_asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repository import UserRepository
from src.repositories.job_repository import JobRepository
from src.repositories.cover_letter_repository import CoverLetterRepository


@pytest_asyncio.fixture
async def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def job_repo(async_session: AsyncSession):
    return JobRepository(async_session)


@pytest_asyncio.fixture
async def cover_letter_repo(async_session: AsyncSession):
    return CoverLetterRepository(async_session)


@pytest_asyncio.fixture
async def test_user(user_repo: UserRepository):
    return await user_repo.create_user(
        telegram_id=123456789,
        first_name="Test",
    )


@pytest_asyncio.fixture
async def test_job(job_repo: JobRepository):
    return await job_repo.create_job(
        telegram_message_id=99999,
        title="Test Job",
        company="Test Company",
        description="Test Description",
    )


class TestCoverLetterRepository:
    @pytest.mark.asyncio
    async def test_create_log(
        self,
        cover_letter_repo: CoverLetterRepository,
        test_user,
        test_job,
    ):
        log = await cover_letter_repo.create_log(
            user_id=test_user.id,
            job_id=test_job.id,
        )
        assert log.user_id == test_user.id
        assert log.job_id == test_job.id

    @pytest.mark.asyncio
    async def test_monthly_count(
        self,
        cover_letter_repo: CoverLetterRepository,
        test_user,
        test_job,
    ):
        await cover_letter_repo.create_log(test_user.id, test_job.id)
        await cover_letter_repo.create_log(test_user.id, test_job.id)
        await cover_letter_repo.create_log(test_user.id, test_job.id)
        count = await cover_letter_repo.get_monthly_count(test_user.id)
        assert count == 3

    @pytest.mark.asyncio
    async def test_check_quota_available(
        self,
        cover_letter_repo: CoverLetterRepository,
        test_user,
        test_job,
    ):
        for _ in range(5):
            await cover_letter_repo.create_log(test_user.id, test_job.id)
        available = await cover_letter_repo.check_quota_available(
            test_user.id,
            monthly_limit=10,
        )
        assert available

    @pytest.mark.asyncio
    async def test_check_quota_exceeded(
        self,
        cover_letter_repo: CoverLetterRepository,
        test_user,
        test_job,
    ):
        for _ in range(10):
            await cover_letter_repo.create_log(test_user.id, test_job.id)
        available = await cover_letter_repo.check_quota_available(
            test_user.id,
            monthly_limit=10,
        )
        assert not available

    @pytest.mark.asyncio
    async def test_get_logs_by_user(
        self,
        cover_letter_repo: CoverLetterRepository,
        test_user,
        test_job,
    ):
        await cover_letter_repo.create_log(test_user.id, test_job.id)
        logs = await cover_letter_repo.get_logs_by_user(test_user.id)
        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_separate_users_separate_quotas(
        self,
        cover_letter_repo: CoverLetterRepository,
        user_repo: UserRepository,
        test_job,
    ):
        user1 = await user_repo.create_user(telegram_id=111111111, first_name="User1")
        user2 = await user_repo.create_user(telegram_id=222222222, first_name="User2")

        for _ in range(5):
            await cover_letter_repo.create_log(user1.id, test_job.id)

        for _ in range(3):
            await cover_letter_repo.create_log(user2.id, test_job.id)

        count1 = await cover_letter_repo.get_monthly_count(user1.id)
        count2 = await cover_letter_repo.get_monthly_count(user2.id)

        assert count1 == 5
        assert count2 == 3
