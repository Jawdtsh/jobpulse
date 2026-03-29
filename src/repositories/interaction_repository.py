import uuid
from datetime import datetime, timedelta
from typing import Optional, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user_interaction import UserInteraction
from src.repositories.base import AbstractRepository


class InteractionRepository(AbstractRepository[UserInteraction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserInteraction)

    async def get_interactions_by_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserInteraction]:
        stmt = (
            select(UserInteraction)
            .where(
                UserInteraction.user_id == user_id,
            )
            .order_by(UserInteraction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_interactions(
        self,
        user_id: uuid.UUID,
        hours: int = 24,
    ) -> list[UserInteraction]:
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.created_at >= since,
                )
            )
            .order_by(UserInteraction.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_interaction(
        self,
        user_id: uuid.UUID,
        action_type: str,
        action_data: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserInteraction:
        return await self.create(
            user_id=user_id,
            action_type=action_type,
            action_data=action_data or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def count_interactions_by_type(
        self,
        user_id: uuid.UUID,
        action_type: str,
        hours: int = 24,
    ) -> int:
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(func.count())
            .select_from(UserInteraction)
            .where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.action_type == action_type,
                    UserInteraction.created_at >= since,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_interactions_by_ip(
        self,
        ip_address: str,
        hours: int = 24,
    ) -> list[UserInteraction]:
        since = datetime.utcnow() - timedelta(hours=hours)
        stmt = (
            select(UserInteraction)
            .where(
                and_(
                    UserInteraction.ip_address == ip_address,
                    UserInteraction.created_at >= since,
                )
            )
            .order_by(UserInteraction.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
