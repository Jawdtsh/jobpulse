import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.models.referral_reward import ReferralReward
from src.repositories.base import AbstractRepository


class ReferralRewardRepository(AbstractRepository[ReferralReward]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReferralReward)

    async def get_rewards_by_referrer(
        self,
        referrer_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReferralReward]:
        stmt = (
            select(ReferralReward)
            .where(
                ReferralReward.referrer_id == referrer_id,
            )
            .order_by(ReferralReward.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_rewards(self, referrer_id: uuid.UUID) -> list[ReferralReward]:
        stmt = select(ReferralReward).where(
            ReferralReward.referrer_id == referrer_id,
            ReferralReward.status == "pending",
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_reward(
        self,
        referrer_id: uuid.UUID,
        referred_user_id: uuid.UUID,
        reward_type: str,
        reward_value: int,
        expires_at: datetime,
    ) -> Optional[ReferralReward]:
        try:
            async with self._session.begin_nested():
                return await self.create(
                    referrer_id=referrer_id,
                    referred_user_id=referred_user_id,
                    reward_type=reward_type,
                    reward_value=reward_value,
                    expires_at=expires_at,
                )
        except IntegrityError:
            return None

    async def apply_reward(self, reward_id: uuid.UUID) -> Optional[ReferralReward]:
        return await self.update(
            reward_id,
            status="applied",
            applied_at=datetime.now(timezone.utc),
        )

    async def expire_reward(self, reward_id: uuid.UUID) -> Optional[ReferralReward]:
        return await self.update(reward_id, status="expired")

    async def check_duplicate_reward(
        self,
        referrer_id: uuid.UUID,
        referred_user_id: uuid.UUID,
        reward_type: str,
    ) -> bool:
        stmt = select(ReferralReward).where(
            ReferralReward.referrer_id == referrer_id,
            ReferralReward.referred_user_id == referred_user_id,
            ReferralReward.reward_type == reward_type,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
