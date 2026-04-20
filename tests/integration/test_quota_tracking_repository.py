from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_quota_tracking_repository import UserQuotaTrackingRepository
from src.repositories.user_repository import UserRepository
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def quota_repo(async_session: AsyncSession):
    return UserQuotaTrackingRepository(async_session)


@pytest_asyncio.fixture
async def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def test_user(user_repo: UserRepository):
    return await user_repo.create_user(
        telegram_id=998877665,
        first_name="QuotaTest",
    )


class TestUserQuotaTrackingRepository:
    @pytest.mark.asyncio
    async def test_get_or_create_today(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
        async_session: AsyncSession,
    ):
        damascus_date = date(2026, 4, 19)
        record = await quota_repo.get_or_create_today(
            test_user.id, damascus_date, "free"
        )
        await async_session.flush()
        assert record.user_id == test_user.id
        assert record.daily_used == 0
        assert record.purchased_extra == 0

    @pytest.mark.asyncio
    async def test_increment_daily_used(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
        async_session: AsyncSession,
    ):
        damascus_date = date(2026, 4, 19)
        await quota_repo.get_or_create_today(test_user.id, damascus_date, "free")
        await async_session.flush()

        new_count = await quota_repo.increment_daily_used(test_user.id, damascus_date)
        assert new_count == 1

    @pytest.mark.asyncio
    async def test_add_purchased_extra(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
        async_session: AsyncSession,
    ):
        damascus_date = date(2026, 4, 19)
        await quota_repo.get_or_create_today(test_user.id, damascus_date, "free")
        await async_session.flush()

        new_extra = await quota_repo.add_purchased_extra(test_user.id, damascus_date, 5)
        assert new_extra == 5

    @pytest.mark.asyncio
    async def test_get_today_returns_none_for_missing(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
    ):
        result = await quota_repo.get_today(test_user.id, date(2025, 1, 1))
        assert result is None

    @pytest.mark.asyncio
    async def test_increment_daily_used_returns_zero_when_no_record(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
    ):
        result = await quota_repo.increment_daily_used(test_user.id, date(2026, 4, 20))
        assert result == 0

    @pytest.mark.asyncio
    async def test_increment_daily_used_atomic_multi_increment(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
        async_session: AsyncSession,
    ):
        damascus_date = date(2026, 4, 19)
        await quota_repo.get_or_create_today(test_user.id, damascus_date, "free")
        await async_session.flush()

        first = await quota_repo.increment_daily_used(test_user.id, damascus_date)
        assert first == 1

        second = await quota_repo.increment_daily_used(test_user.id, damascus_date)
        assert second == 2

        third = await quota_repo.increment_daily_used(test_user.id, damascus_date)
        assert third == 3

    @pytest.mark.asyncio
    async def test_decrement_daily_used(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
        async_session: AsyncSession,
    ):
        damascus_date = date(2026, 4, 19)
        await quota_repo.get_or_create_today(test_user.id, damascus_date, "free")
        await async_session.flush()

        await quota_repo.increment_daily_used(test_user.id, damascus_date)
        await quota_repo.increment_daily_used(test_user.id, damascus_date)
        result = await quota_repo.decrement_daily_used(test_user.id, damascus_date)
        assert result == 1

    @pytest.mark.asyncio
    async def test_decrement_daily_used_will_not_go_below_zero(
        self,
        quota_repo: UserQuotaTrackingRepository,
        test_user,
        async_session: AsyncSession,
    ):
        damascus_date = date(2026, 4, 19)
        await quota_repo.get_or_create_today(test_user.id, damascus_date, "free")
        await async_session.flush()

        result = await quota_repo.decrement_daily_used(test_user.id, damascus_date)
        assert result == 0
