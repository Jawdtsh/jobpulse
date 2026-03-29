import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
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
            .where(MonitoredChannel.is_active == True)
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
        channel = await self.get(channel_id)
        if channel is None:
            return None
        updates = {}
        if jobs_found is not None:
            updates["jobs_found"] = channel.jobs_found + jobs_found
        if false_positives is not None:
            updates["false_positives"] = channel.false_positives + false_positives
        if updates:
            return await self.update(channel_id, **updates)
        return channel

    async def mark_scraped(self, channel_id: uuid.UUID) -> Optional[MonitoredChannel]:
        return await self.update(
            channel_id,
            last_scraped_at=datetime.utcnow(),
        )

    async def deactivate(self, channel_id: uuid.UUID) -> Optional[MonitoredChannel]:
        return await self.update(channel_id, is_active=False)

    async def activate(self, channel_id: uuid.UUID) -> Optional[MonitoredChannel]:
        return await self.update(channel_id, is_active=True)
