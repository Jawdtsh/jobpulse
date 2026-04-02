import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repository import UserRepository
from src.repositories.job_repository import JobRepository
from src.repositories.report_repository import ReportRepository


@pytest_asyncio.fixture
async def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def job_repo(async_session: AsyncSession):
    return JobRepository(async_session)


@pytest_asyncio.fixture
async def report_repo(async_session: AsyncSession):
    return ReportRepository(async_session)


@pytest_asyncio.fixture
async def sample_job(job_repo: JobRepository):
    return await job_repo.create_job(
        telegram_message_id=99999,
        title="Suspect Job",
        company="Scam Corp",
        description="Too good to be true",
    )


class TestReportRepository:
    @pytest.mark.asyncio
    async def test_create_report(
        self,
        user_repo: UserRepository,
        report_repo: ReportRepository,
        sample_job,
    ):
        user = await user_repo.create_user(telegram_id=100, first_name="Reporter")
        report = await report_repo.create_report(
            job_id=sample_job.id,
            reporter_user_id=user.id,
            reason="spam",
        )
        assert report is not None
        assert report.reason == "spam"
        assert report.job_id == sample_job.id

    @pytest.mark.asyncio
    async def test_duplicate_report_rejected(
        self,
        user_repo: UserRepository,
        report_repo: ReportRepository,
        sample_job,
    ):
        user = await user_repo.create_user(telegram_id=101, first_name="Reporter2")
        report1 = await report_repo.create_report(
            job_id=sample_job.id,
            reporter_user_id=user.id,
            reason="spam",
        )
        report2 = await report_repo.create_report(
            job_id=sample_job.id,
            reporter_user_id=user.id,
            reason="scam",
        )
        assert report1 is not None
        assert report2 is None

    @pytest.mark.asyncio
    async def test_count_unique_reporters(
        self,
        user_repo: UserRepository,
        report_repo: ReportRepository,
        sample_job,
    ):
        u1 = await user_repo.create_user(telegram_id=200, first_name="U1")
        u2 = await user_repo.create_user(telegram_id=201, first_name="U2")
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u1.id, reason="spam"
        )
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u2.id, reason="scam"
        )
        count = await report_repo.count_unique_reporters_for_job(sample_job.id)
        assert count == 2

    @pytest.mark.asyncio
    async def test_should_auto_archive_false_below_threshold(
        self,
        user_repo: UserRepository,
        report_repo: ReportRepository,
        sample_job,
    ):
        u1 = await user_repo.create_user(telegram_id=300, first_name="U1")
        u2 = await user_repo.create_user(telegram_id=301, first_name="U2")
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u1.id, reason="spam"
        )
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u2.id, reason="scam"
        )
        assert await report_repo.should_auto_archive(sample_job.id) is False

    @pytest.mark.asyncio
    async def test_should_auto_archive_true_at_threshold(
        self,
        user_repo: UserRepository,
        report_repo: ReportRepository,
        sample_job,
    ):
        u1 = await user_repo.create_user(telegram_id=400, first_name="U1")
        u2 = await user_repo.create_user(telegram_id=401, first_name="U2")
        u3 = await user_repo.create_user(telegram_id=402, first_name="U3")
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u1.id, reason="spam"
        )
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u2.id, reason="scam"
        )
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u3.id, reason="fake"
        )
        assert await report_repo.should_auto_archive(sample_job.id) is True

    @pytest.mark.asyncio
    async def test_has_user_reported_job(
        self,
        user_repo: UserRepository,
        report_repo: ReportRepository,
        sample_job,
    ):
        user = await user_repo.create_user(telegram_id=500, first_name="U")
        assert await report_repo.has_user_reported_job(sample_job.id, user.id) is False
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=user.id, reason="spam"
        )
        assert await report_repo.has_user_reported_job(sample_job.id, user.id) is True

    @pytest.mark.asyncio
    async def test_get_reports_by_job(
        self,
        user_repo: UserRepository,
        report_repo: ReportRepository,
        sample_job,
    ):
        u1 = await user_repo.create_user(telegram_id=600, first_name="U1")
        u2 = await user_repo.create_user(telegram_id=601, first_name="U2")
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u1.id, reason="spam"
        )
        await report_repo.create_report(
            job_id=sample_job.id, reporter_user_id=u2.id, reason="scam"
        )
        reports = await report_repo.get_reports_by_job(sample_job.id)
        assert len(reports) == 2
