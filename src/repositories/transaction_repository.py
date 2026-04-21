import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.wallet_transaction import WalletTransaction
from src.repositories.base import AbstractRepository


class TransactionRepository(AbstractRepository[WalletTransaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WalletTransaction)

    async def get_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[WalletTransaction]:
        stmt = (
            select(WalletTransaction)
            .where(WalletTransaction.user_id == user_id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_idempotency_key(self, key: str) -> WalletTransaction | None:
        stmt = select(WalletTransaction).where(WalletTransaction.idempotency_key == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(WalletTransaction.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def create_transaction(
        self,
        user_id: uuid.UUID,
        type_: str,
        amount_usd: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        status: str = "completed",
        description: str | None = None,
        admin_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        idempotency_key: str | None = None,
    ) -> WalletTransaction:
        now = datetime.now(timezone.utc)
        return await self.create(
            user_id=user_id,
            type=type_,
            amount_usd=amount_usd,
            balance_before=balance_before,
            balance_after=balance_after,
            status=status,
            description=description,
            admin_id=admin_id,
            metadata=metadata,
            created_at=now,
            idempotency_key=idempotency_key,
        )
