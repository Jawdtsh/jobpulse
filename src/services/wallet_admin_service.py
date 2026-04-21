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
from config.settings import get_settings

logger = logging.getLogger(__name__)


class WalletAdminService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._user_repo = UserRepository(session)
        self._wallet_repo = WalletRepository(session)
        self._admin_log_repo = AdminActionLogRepository(session)

    @staticmethod
    def is_admin(telegram_id: int) -> bool:
        settings = get_settings()
        return telegram_id in settings.wallet.admin_user_ids

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
        total_users = await self._session.execute(select(func.count(User.id)))
        users_with_balance = await self._session.execute(
            select(func.count(UserWallet.id)).where(UserWallet.balance_usd > 0)
        )
        tier_counts_result = await self._session.execute(
            select(User.subscription_tier, func.count(User.id)).group_by(
                User.subscription_tier
            )
        )
        tier_counts = dict(tier_counts_result.all())

        total_topups = await self._session.execute(
            select(func.sum(WalletTransaction.amount_usd)).where(
                WalletTransaction.type == "top_up",
                WalletTransaction.status == "completed",
            )
        )
        total_spent = await self._session.execute(
            select(func.sum(WalletTransaction.amount_usd)).where(
                WalletTransaction.type.in_(
                    [
                        "subscription_purchase",
                        "generation_purchase",
                    ]
                ),
                WalletTransaction.status == "completed",
            )
        )
        total_withdrawn = await self._session.execute(
            select(func.sum(WalletTransaction.amount_usd)).where(
                WalletTransaction.type == "withdrawal",
                WalletTransaction.status == "completed",
            )
        )

        active_subs = await self._session.execute(
            select(func.count(SubscriptionHistory.id)).where(
                SubscriptionHistory.status == "active"
            )
        )

        recent_tx_count = await self._admin_log_repo.count_recent(hours=24)

        return {
            "total_users": total_users.scalar() or 0,
            "users_with_balance": users_with_balance.scalar() or 0,
            "tier_counts": tier_counts,
            "total_topups": total_topups.scalar() or Decimal("0"),
            "total_spent": total_spent.scalar() or Decimal("0"),
            "total_withdrawn": total_withdrawn.scalar() or Decimal("0"),
            "active_subscriptions": active_subs.scalar() or 0,
            "recent_transactions": recent_tx_count,
        }

    async def search_users(self, query: str, limit: int = 10) -> list[dict]:
        stmt = (
            select(User)
            .where(
                (User.username.ilike(f"%{query}%"))
                | (User.first_name.ilike(f"%{query}%"))
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        users = result.scalars().all()

        user_infos = []
        for user in users:
            wallet = await self._wallet_repo.get_by_user_id(user.id)
            user_infos.append(
                {
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "tier": user.subscription_tier,
                    "balance": wallet.balance_usd if wallet else Decimal("0"),
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
