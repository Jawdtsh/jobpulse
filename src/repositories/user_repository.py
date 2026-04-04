import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.repositories.base import AbstractRepository
import secrets
import string


def generate_referral_code(length: int = 8) -> str:
    characters = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))


class UserRepository(AbstractRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, referral_code: str) -> Optional[User]:
        stmt = select(User).where(User.referral_code == referral_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        referred_by: Optional[uuid.UUID] = None,
    ) -> User:
        referral_code = generate_referral_code()
        while await self.get_by_referral_code(referral_code) is not None:
            referral_code = generate_referral_code()

        return await self.create(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            referral_code=referral_code,
            referred_by=referred_by,
        )

    async def update_subscription_tier(
        self,
        user_id: uuid.UUID,
        tier: str,
    ) -> Optional[User]:
        return await self.update(user_id, subscription_tier=tier)
