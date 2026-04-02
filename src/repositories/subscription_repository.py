import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.subscription import Subscription
from src.repositories.base import AbstractRepository


class SubscriptionRepository(AbstractRepository[Subscription]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Subscription)

    async def get_active_subscription(
        self, user_id: uuid.UUID
    ) -> Optional[Subscription]:
        now = datetime.now(timezone.utc)
        stmt = select(Subscription).where(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.valid_from <= now,
                Subscription.valid_until >= now,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_subscriptions_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Subscription]:
        stmt = (
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
            )
            .order_by(Subscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_subscription(
        self,
        user_id: uuid.UUID,
        plan_type: str,
        amount: int,
        payment_method: str,
        valid_from: datetime,
        valid_until: datetime,
        currency: str = "USD",
        payment_id: Optional[str] = None,
    ) -> Subscription:
        return await self.create(
            user_id=user_id,
            plan_type=plan_type,
            amount=amount,
            payment_method=payment_method,
            valid_from=valid_from,
            valid_until=valid_until,
            currency=currency,
            payment_id=payment_id,
        )

    async def cancel_subscription(
        self, subscription_id: uuid.UUID
    ) -> Optional[Subscription]:
        return await self.update(subscription_id, status="cancelled")

    async def expire_subscription(
        self, subscription_id: uuid.UUID
    ) -> Optional[Subscription]:
        return await self.update(subscription_id, status="expired")

    async def check_user_has_active_subscription(self, user_id: uuid.UUID) -> bool:
        sub = await self.get_active_subscription(user_id)
        return sub is not None
