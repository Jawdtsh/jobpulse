import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repository import UserRepository, generate_referral_code


@pytest_asyncio.fixture
async def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_create_user(self, user_repo: UserRepository):
        user = await user_repo.create_user(
            telegram_id=123456789,
            first_name="John",
            last_name="Doe",
            username="johndoe",
        )
        assert user.telegram_id == 123456789
        assert user.first_name == "John"
        assert user.subscription_tier == "free"
        assert user.referral_code is not None

    @pytest.mark.asyncio
    async def test_get_by_telegram_id(self, user_repo: UserRepository):
        created = await user_repo.create_user(
            telegram_id=987654321,
            first_name="Jane",
        )
        found = await user_repo.get_by_telegram_id(987654321)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_referral_code(self, user_repo: UserRepository):
        created = await user_repo.create_user(
            telegram_id=111222333,
            first_name="Bob",
        )
        found = await user_repo.get_by_referral_code(created.referral_code)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_update_subscription_tier(self, user_repo: UserRepository):
        user = await user_repo.create_user(
            telegram_id=444555666,
            first_name="Alice",
        )
        updated = await user_repo.update_subscription_tier(user.id, "pro")
        assert updated is not None
        assert updated.subscription_tier == "pro"

    @pytest.mark.asyncio
    async def test_referral_code_unique(self, user_repo: UserRepository):
        user1 = await user_repo.create_user(
            telegram_id=111111111,
            first_name="User1",
        )
        user2 = await user_repo.create_user(
            telegram_id=222222222,
            first_name="User2",
        )
        assert user1.referral_code != user2.referral_code


class TestGenerateReferralCode:
    def test_generate_referral_code_length(self):
        code = generate_referral_code(8)
        assert len(code) == 8

    def test_generate_referral_code_alphanumeric(self):
        code = generate_referral_code(10)
        assert code.isalnum()

    def test_generate_referral_code_different(self):
        code1 = generate_referral_code()
        code2 = generate_referral_code()
        assert code1 != code2
