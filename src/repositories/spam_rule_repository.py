from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.spam_rule import SpamRule
from src.repositories.base import AbstractRepository


class SpamRuleRepository(AbstractRepository[SpamRule]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SpamRule)

    async def get_active_rules(self) -> list[SpamRule]:
        stmt = (
            select(SpamRule)
            .where(SpamRule.is_active)
            .order_by(SpamRule.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
