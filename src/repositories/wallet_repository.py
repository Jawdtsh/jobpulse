import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_wallet import UserWallet
from src.repositories.base import AbstractRepository


class WalletRepository(AbstractRepository[UserWallet]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserWallet)

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserWallet | None:
        stmt = select(UserWallet).where(UserWallet.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID) -> UserWallet:
        wallet = await self.get_by_user_id(user_id)
        if wallet is not None:
            return wallet
        now = datetime.now(timezone.utc)
        wallet = await self.create(
            user_id=user_id,
            balance_usd=Decimal("0.00"),
            total_deposited_usd=Decimal("0.00"),
            total_spent_usd=Decimal("0.00"),
            total_withdrawn_usd=Decimal("0.00"),
            updated_at=now,
            created_at=now,
        )
        return wallet
