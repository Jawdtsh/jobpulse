import asyncio
import logging
import uuid
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.user_wallet import UserWallet
from src.models.wallet_transaction import WalletTransaction
from src.models.subscription_history import SubscriptionHistory
from src.repositories.user_repository import UserRepository
from src.repositories.wallet_repository import WalletRepository
from src.repositories.admin_action_log_repository import AdminActionLogRepository
from src.repositories.transaction_repository import TransactionRepository
from config.settings import get_settings

logger = logging.getLogger(__name__)


class WalletAdminService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepository(session)
        self._wallet_repo = WalletRepository(session)
        self._admin_log_repo = AdminActionLogRepository(session)
        self._tx_repo = TransactionRepository(session)

    @staticmethod
    def is_admin(telegram_id: int) -> bool:
        settings = get_settings()
        return telegram_id in settings.wallet.admin_user_ids

    async def _count_users(self) -> int:
        stmt = select(func.count(User.id))
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def _count_users_with_balance(self) -> int:
        stmt = select(func.count(UserWallet.id)).where(UserWallet.balance_usd > 0)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def _count_tiers(self) -> dict:
        stmt = select(User.subscription_tier, func.count(User.id)).group_by(
            User.subscription_tier
        )
        result = await self._session.execute(stmt)
        return dict(result.all())

    async def _sum_transactions(self, tx_type: str) -> Decimal:
        stmt = select(func.sum(WalletTransaction.amount_usd)).where(
            WalletTransaction.type == tx_type,
            WalletTransaction.status == "completed",
        )
        result = await self._session.execute(stmt)
        return result.scalar() or Decimal("0")

    async def _sum_transactions_subscription(self) -> Decimal:
        stmt = select(func.sum(WalletTransaction.amount_usd)).where(
            WalletTransaction.type.in_(
                [
                    "subscription_purchase",
                    "generation_purchase",
                ]
            ),
            WalletTransaction.status == "completed",
        )
        result = await self._session.execute(stmt)
        return result.scalar() or Decimal("0")

    async def _count_active_subscriptions(self) -> int:
        stmt = select(func.count(SubscriptionHistory.id)).where(
            SubscriptionHistory.status == "active"
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def get_user_info(self, telegram_id: int) -> dict | None:
        user = await self._user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return None

        wallet = await self._wallet_repo.get_by_user_id(user.id)
        from src.repositories.subscription_history_repository import (
            SubscriptionHistoryRepository,
        )

        sub_repo = SubscriptionHistoryRepository(self._session)
        active_sub = await sub_repo.get_active_by_user(user.id)

        return {
            "user_id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "subscription_tier": user.subscription_tier,
            "balance_usd": wallet.balance_usd if wallet else Decimal("0"),
            "total_deposited_usd": wallet.total_deposited_usd
            if wallet
            else Decimal("0"),
            "total_spent_usd": wallet.total_spent_usd if wallet else Decimal("0"),
            "total_withdrawn_usd": wallet.total_withdrawn_usd
            if wallet
            else Decimal("0"),
            "active_subscription": active_sub,
        }

    async def get_user_by_uuid(self, user_id: uuid.UUID) -> dict | None:
        user = await self._user_repo.get(user_id)
        if not user:
            return None
        return await self.get_user_info(user.telegram_id)

    async def get_stats(self) -> dict:
        (
            total_users,
            users_with_balance,
            tier_counts,
            total_topups,
            total_spent,
            total_withdrawn,
            active_subs,
            recent_tx_count,
        ) = await asyncio.gather(
            self._count_users(),
            self._count_users_with_balance(),
            self._count_tiers(),
            self._sum_transactions("top_up"),
            self._sum_transactions_subscription(),
            self._sum_transactions("withdrawal"),
            self._count_active_subscriptions(),
            self._tx_repo.count_recent(hours=24),
        )

        return {
            "total_users": total_users,
            "users_with_balance": users_with_balance,
            "tier_counts": tier_counts,
            "total_topups": total_topups,
            "total_spent": total_spent,
            "total_withdrawn": total_withdrawn,
            "active_subscriptions": active_subs,
            "recent_transactions": recent_tx_count,
        }

    async def search_users(self, query: str, limit: int = 10) -> list[dict]:
        stmt = (
            select(User, UserWallet.balance_usd)
            .outerjoin(UserWallet, User.id == UserWallet.user_id)
            .where(
                (User.username.ilike(f"%{query}%"))
                | (User.first_name.ilike(f"%{query}%"))
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        user_infos = []
        for user, balance_usd in rows:
            user_infos.append(
                {
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "tier": user.subscription_tier,
                    "balance": balance_usd if balance_usd is not None else Decimal("0"),
                }
            )
        return user_infos

    async def get_recent_transactions(
        self, user_id: uuid.UUID | None = None, limit: int = 20
    ) -> list[dict]:
        from src.repositories.transaction_repository import TransactionRepository

        tx_repo = TransactionRepository(self._session)
        if user_id:
            transactions = await tx_repo.get_by_user(user_id, limit=limit)
        else:
            transactions = await tx_repo.get_all(limit=limit)

        return [
            {
                "id": str(tx.id),
                "user_id": str(tx.user_id),
                "type": tx.type,
                "amount_usd": tx.amount_usd,
                "status": tx.status,
                "description": tx.description,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ]
