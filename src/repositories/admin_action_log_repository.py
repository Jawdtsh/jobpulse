from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.admin_action_log import AdminActionLog
from src.repositories.base import AbstractRepository


class AdminActionLogRepository(AbstractRepository[AdminActionLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AdminActionLog)

    async def log_action(
        self,
        admin_user_id: int,
        action_type: str,
        target_user_id=None,
        amount_usd=None,
        reason: str | None = None,
        details: dict | None = None,
    ) -> AdminActionLog:
        now = datetime.now(timezone.utc)
        return await self.create(
            admin_user_id=admin_user_id,
            action_type=action_type,
            target_user_id=target_user_id,
            amount_usd=amount_usd,
            reason=reason,
            details=details,
            created_at=now,
        )

    async def get_by_admin(
        self, admin_user_id: int, limit: int = 50
    ) -> list[AdminActionLog]:
        stmt = (
            select(AdminActionLog)
            .where(AdminActionLog.admin_user_id == admin_user_id)
            .order_by(AdminActionLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_recent(self, hours: int = 24) -> int:
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(func.count()).where(AdminActionLog.created_at >= cutoff)
        result = await self._session.execute(stmt)
        return result.scalar() or 0
