import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repository import UserRepository
from src.repositories.referral_reward_repository import ReferralRewardRepository


@pytest_asyncio.fixture
async def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def referral_repo(async_session: AsyncSession):
    return ReferralRewardRepository(async_session)


@pytest_asyncio.fixture
async def referrer(user_repo: UserRepository):
    return await user_repo.create_user(
        telegram_id=111111111,
        first_name="Referrer",
    )


@pytest_asyncio.fixture
async def referred_user(user_repo: UserRepository):
    return await user_repo.create_user(
        telegram_id=222222222,
        first_name="Referred",
    )


class TestReferralRewardRepository:
    @pytest.mark.asyncio
    async def test_create_reward(
        self,
        referral_repo: ReferralRewardRepository,
        referrer,
        referred_user,
    ):
        reward = await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        assert reward is not None
        assert reward.reward_type == "credits"
        assert reward.reward_value == 100
        assert reward.status == "pending"

    @pytest.mark.asyncio
    async def test_unique_constraint_prevents_duplicate(
        self,
        referral_repo: ReferralRewardRepository,
        referrer,
        referred_user,
    ):
        expires = datetime.utcnow() + timedelta(days=30)
        await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=expires,
        )
        duplicate = await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=200,
            expires_at=expires,
        )
        assert duplicate is None

    @pytest.mark.asyncio
    async def test_different_reward_types_allowed(
        self,
        referral_repo: ReferralRewardRepository,
        referrer,
        referred_user,
    ):
        expires = datetime.utcnow() + timedelta(days=30)
        reward1 = await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=expires,
        )
        reward2 = await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="subscription_month",
            reward_value=1,
            expires_at=expires,
        )
        assert reward1 is not None
        assert reward2 is not None
        assert reward1.id != reward2.id

    @pytest.mark.asyncio
    async def test_apply_reward(
        self,
        referral_repo: ReferralRewardRepository,
        referrer,
        referred_user,
    ):
        reward = await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        applied = await referral_repo.apply_reward(reward.id)
        assert applied is not None
        assert applied.status == "applied"
        assert applied.applied_at is not None

    @pytest.mark.asyncio
    async def test_expire_reward(
        self,
        referral_repo: ReferralRewardRepository,
        referrer,
        referred_user,
    ):
        reward = await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        expired = await referral_repo.expire_reward(reward.id)
        assert expired is not None
        assert expired.status == "expired"

    @pytest.mark.asyncio
    async def test_get_pending_rewards(
        self,
        referral_repo: ReferralRewardRepository,
        referrer,
        referred_user,
    ):
        await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        pending = await referral_repo.get_pending_rewards(referrer.id)
        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_session_survives_duplicate_reward(
        self,
        referral_repo: ReferralRewardRepository,
        user_repo: UserRepository,
        referrer,
        referred_user,
        async_session: AsyncSession,
    ):
        expires = datetime.utcnow() + timedelta(days=30)
        await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=expires,
        )
        duplicate = await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=200,
            expires_at=expires,
        )
        assert duplicate is None
        post_dupe_user = await user_repo.create_user(
            telegram_id=999999999,
            first_name="PostDuplicate",
        )
        assert post_dupe_user is not None
        assert post_dupe_user.first_name == "PostDuplicate"

    @pytest.mark.asyncio
    async def test_check_duplicate_reward(
        self,
        referral_repo: ReferralRewardRepository,
        referrer,
        referred_user,
    ):
        await referral_repo.create_reward(
            referrer_id=referrer.id,
            referred_user_id=referred_user.id,
            reward_type="credits",
            reward_value=100,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        is_duplicate = await referral_repo.check_duplicate_reward(
            referrer.id,
            referred_user.id,
            "credits",
        )
        assert is_duplicate is True

        is_duplicate_other = await referral_repo.check_duplicate_reward(
            referrer.id,
            referred_user.id,
            "subscription_month",
        )
        assert is_duplicate_other is False
