import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription_history import SubscriptionHistory
from src.repositories.base import AbstractRepository


class SubscriptionHistoryRepository(AbstractRepository[SubscriptionHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SubscriptionHistory)

    async def get_active_by_user(
        self, user_id: uuid.UUID
    ) -> SubscriptionHistory | None:
        stmt = select(SubscriptionHistory).where(
            SubscriptionHistory.user_id == user_id,
            SubscriptionHistory.status == "active",
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> list[SubscriptionHistory]:
        stmt = (
            select(SubscriptionHistory)
            .where(SubscriptionHistory.user_id == user_id)
            .order_by(SubscriptionHistory.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def expire_subscription(self, subscription_id: uuid.UUID) -> bool:
        sub = await self.get(subscription_id)
        if sub is None:
            return False
        sub.status = "expired"
        await self._session.flush()
        return True
