from __future__ import annotations

import logging
from datetime import date
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from src.repositories.user_quota_tracking_repository import (
    UserQuotaTrackingRepository,
)

logger = logging.getLogger(__name__)

DAMASCUS_TZ = ZoneInfo("Asia/Damascus")


def get_damascus_date() -> date:
    from datetime import datetime

    return datetime.now(DAMASCUS_TZ).date()


def get_midnight_countdown_seconds() -> int:
    from datetime import datetime, timedelta

    now = datetime.now(DAMASCUS_TZ)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int((tomorrow - now).total_seconds())


class QuotaService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserQuotaTrackingRepository(session)

    async def get_daily_limit(self, tier: str) -> int:
        settings = get_settings()
        limits = settings.cover_letter.daily_limits
        return limits.get(tier.lower(), limits.get("free", 3))

    async def get_remaining_quota(
        self,
        user_id,
        tier: str,
        damascus_date: date | None = None,
    ) -> int:
        if damascus_date is None:
            damascus_date = get_damascus_date()
        record = await self._repo.get_today(user_id, damascus_date)
        if record is None:
            record = await self._repo.get_or_create_today(user_id, damascus_date, tier)
        daily_limit = await self.get_daily_limit(tier)
        used = record.daily_used
        extra = record.purchased_extra
        return max(0, daily_limit + extra - used)

    async def has_quota(
        self,
        user_id,
        tier: str,
        damascus_date: date | None = None,
    ) -> bool:
        return await self.get_remaining_quota(user_id, tier, damascus_date) > 0

    async def increment_daily_used(
        self,
        user_id,
        tier: str,
        damascus_date: date | None = None,
    ) -> int:
        if damascus_date is None:
            damascus_date = get_damascus_date()
        await self._repo.get_or_create_today(user_id, damascus_date, tier)
        return await self._repo.increment_daily_used(user_id, damascus_date)

    async def decrement_daily_used(
        self,
        user_id,
        tier: str,
        damascus_date: date | None = None,
    ) -> int:
        if damascus_date is None:
            damascus_date = get_damascus_date()
        return await self._repo.decrement_daily_used(user_id, damascus_date)

    async def add_purchased_extra(
        self,
        user_id,
        amount: int,
        damascus_date: date | None = None,
    ) -> int:
        if damascus_date is None:
            damascus_date = get_damascus_date()
        return await self._repo.add_purchased_extra(user_id, damascus_date, amount)

    async def reset_all_for_date(self, target_date: date) -> int:
        records = await self._repo.get_all_for_date(target_date)
        count = 0
        for record in records:
            record.daily_used = 0
            count += 1
        if count > 0:
            await self._session.flush()
        return count
