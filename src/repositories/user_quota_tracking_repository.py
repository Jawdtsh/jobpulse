import uuid
from datetime import date
from typing import Optional

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user_quota_tracking import UserQuotaTracking
from src.repositories.base import AbstractRepository


class UserQuotaTrackingRepository(AbstractRepository[UserQuotaTracking]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserQuotaTracking)

    async def get_today(
        self, user_id: uuid.UUID, damascus_date: date
    ) -> Optional[UserQuotaTracking]:
        stmt = select(UserQuotaTracking).where(
            and_(
                UserQuotaTracking.user_id == user_id,
                UserQuotaTracking.date == damascus_date,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_today(
        self,
        user_id: uuid.UUID,
        damascus_date: date,
        tier: str = "free",
    ) -> UserQuotaTracking:
        existing = await self.get_today(user_id, damascus_date)
        if existing:
            return existing
        return await self.create(
            user_id=user_id,
            date=damascus_date,
            daily_used=0,
            purchased_extra=0,
            tier_at_generation=tier,
        )

    async def increment_daily_used(
        self,
        user_id: uuid.UUID,
        damascus_date: date,
    ) -> int:
        stmt = (
            update(UserQuotaTracking)
            .where(
                UserQuotaTracking.user_id == user_id,
                UserQuotaTracking.date == damascus_date,
            )
            .values(daily_used=UserQuotaTracking.daily_used + 1)
            .returning(UserQuotaTracking.daily_used)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        row = result.scalar_one_or_none()
        return row if row else 0

    async def decrement_daily_used(
        self,
        user_id: uuid.UUID,
        damascus_date: date,
    ) -> int:
        stmt = (
            update(UserQuotaTracking)
            .where(
                UserQuotaTracking.user_id == user_id,
                UserQuotaTracking.date == damascus_date,
                UserQuotaTracking.daily_used > 0,
            )
            .values(daily_used=UserQuotaTracking.daily_used - 1)
            .returning(UserQuotaTracking.daily_used)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        row = result.scalar_one_or_none()
        return row if row is not None else 0

    async def add_purchased_extra(
        self,
        user_id: uuid.UUID,
        damascus_date: date,
        amount: int,
    ) -> int:
        record = await self.get_or_create_today(user_id, damascus_date)
        record.purchased_extra += amount
        await self._session.flush()
        await self._session.refresh(record)
        return record.purchased_extra

    async def get_all_for_date(self, target_date: date) -> list[UserQuotaTracking]:
        stmt = select(UserQuotaTracking).where(UserQuotaTracking.date == target_date)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def reset_daily_used(self, user_id: uuid.UUID, damascus_date: date) -> None:
        record = await self.get_today(user_id, damascus_date)
        if record:
            record.daily_used = 0
            await self._session.flush()
