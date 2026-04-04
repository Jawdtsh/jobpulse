import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.monitored_channel import MonitoredChannel
from src.repositories.base import AbstractRepository


class ChannelRepository(AbstractRepository[MonitoredChannel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MonitoredChannel)

    async def get_by_username(self, username: str) -> Optional[MonitoredChannel]:
        stmt = select(MonitoredChannel).where(MonitoredChannel.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_channels(self) -> list[MonitoredChannel]:
        stmt = (
            select(MonitoredChannel)
            .where(MonitoredChannel.is_active)
            .order_by(MonitoredChannel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_channel(
        self,
        username: str,
        title: str,
        member_count: Optional[int] = None,
    ) -> MonitoredChannel:
        return await self.create(
            username=username,
            title=title,
            member_count=member_count,
        )

    async def update_stats(
        self,
        channel_id: uuid.UUID,
        jobs_found: Optional[int] = None,
        false_positives: Optional[int] = None,
    ) -> Optional[MonitoredChannel]:
        # Use atomic DB-side increments to prevent race conditions
        updates = {}
        if jobs_found is not None:
            updates["jobs_found"] = MonitoredChannel.jobs_found + jobs_found
        if false_positives is not None:
            updates["false_positives"] = (
                MonitoredChannel.false_positives + false_positives
            )

        if not updates:
            return await self.get(channel_id)

        # Perform atomic update
        stmt = (
            update(MonitoredChannel)
            .where(MonitoredChannel.id == channel_id)
            .values(**updates)
            .returning(MonitoredChannel)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()

    async def mark_scraped(self, channel_id: uuid.UUID) -> Optional[MonitoredChannel]:
        return await self.update(
            channel_id,
            last_scraped_at=datetime.now(timezone.utc),
        )

    async def deactivate(self, channel_id: uuid.UUID) -> Optional[MonitoredChannel]:
        return await self.update(channel_id, is_active=False)

    async def activate(self, channel_id: uuid.UUID) -> Optional[MonitoredChannel]:
        return await self.update(channel_id, is_active=True)
