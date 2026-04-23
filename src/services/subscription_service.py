import json
import logging
import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription_history import SubscriptionHistory
from src.models.user import User
from src.models.wallet_transaction import WalletTransaction
from src.repositories.subscription_history_repository import (
    SubscriptionHistoryRepository,
)
from src.repositories.user_repository import UserRepository
from src.services.exceptions import WalletError

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "subscription_tiers.json"


def _load_tiers_config() -> dict:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("subscription_tiers.json not found at %s", CONFIG_PATH)
        return {"tiers": [], "generation_packs": []}


class SubscriptionService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._sub_history_repo = SubscriptionHistoryRepository(session)
        self._user_repo = UserRepository(session)

    def get_tier_config(self, tier_id: str) -> dict | None:
        config = _load_tiers_config()
        for tier in config.get("tiers", []):
            if tier["id"] == tier_id:
                return tier
        return None

    def get_all_tiers(self) -> list[dict]:
        return _load_tiers_config().get("tiers", [])

    def get_generation_packs(self) -> list[dict]:
        return _load_tiers_config().get("generation_packs", [])

    def get_pack_config(self, pack_id: str) -> dict | None:
        for pack in self.get_generation_packs():
            if pack["id"] == pack_id:
                return pack
        return None

    async def purchase_tier(
        self,
        user_id: uuid.UUID,
        tier_id: str,
        wallet_service,
    ) -> SubscriptionHistory:
        tier_config = self.get_tier_config(tier_id)
        if not tier_config:
            raise WalletError(f"Unknown tier: {tier_id}")

        price = Decimal(str(tier_config["price_usd"]))
        if price <= 0:
            raise WalletError("Cannot purchase free tier")

        idempotency_key = f"sub:{user_id}:{tier_id}:{date.today().isoformat()}"

        wallet, tx = await wallet_service.deduct_balance(
            user_id=user_id,
            amount=price,
            transaction_type="subscription_purchase",
            description=f"Subscription purchase: {tier_config.get('name_en', tier_id)}",
            idempotency_key=idempotency_key,
            extra_data={"tier": tier_id, "duration_days": tier_config["duration_days"]},
        )

        existing_sub = await self._sub_history_repo.get_by_transaction_id(tx.id)
        if existing_sub:
            return existing_sub

        now = datetime.now(timezone.utc)
        start = now.date()
        end = start + timedelta(days=tier_config["duration_days"])

        sub_history = await self._sub_history_repo.create(
            user_id=user_id,
            tier=tier_id,
            start_date=start,
            end_date=end,
            status="active",
            purchase_transaction_id=tx.id,
            created_at=now,
        )

        user = await self._user_repo.get(user_id)
        if user:
            user.subscription_tier = tier_id
            await self._session.flush()

        logger.info(
            "Subscription purchased user=%s tier=%s end=%s tx=%s",
            user_id,
            tier_id,
            end,
            tx.id,
        )
        return sub_history

    async def purchase_generation_pack(
        self,
        user_id: uuid.UUID,
        pack_id: str,
        wallet_service,
        quota_service=None,
    ) -> WalletTransaction | None:
        pack_config = self.get_pack_config(pack_id)
        if not pack_config:
            raise WalletError(f"Unknown generation pack: {pack_id}")

        price = Decimal(str(pack_config["price_usd"]))
        generations = pack_config["generations"]

        idempotency_key = f"gen_pack:{user_id}:{pack_id}:{date.today().isoformat()}"

        before_call = datetime.now(timezone.utc)
        wallet, tx = await wallet_service.deduct_balance(
            user_id=user_id,
            amount=price,
            transaction_type="generation_purchase",
            description=f"Generation pack: {pack_config.get('name_en', pack_id)} ({generations} gens)",
            idempotency_key=idempotency_key,
            extra_data={
                "pack_id": pack_id,
                "generations": generations,
            },
        )

        if quota_service and tx.created_at >= before_call:
            from src.services.quota_service import get_damascus_date

            damascus_date = get_damascus_date()
            await quota_service.add_purchased_extra(user_id, generations, damascus_date)

        logger.info(
            "Generation pack purchased user=%s pack=%s gens=%d",
            user_id,
            pack_id,
            generations,
        )
        return tx

    async def expire_subscription(
        self, user_id: uuid.UUID
    ) -> SubscriptionHistory | None:
        active = await self._sub_history_repo.get_active_by_user(user_id)
        if not active:
            return None

        await self._sub_history_repo.expire_subscription(active.id)

        user = await self._user_repo.get(user_id)
        if user:
            user.subscription_tier = "free"
            await self._session.flush()

        logger.info("Subscription expired user=%s tier=%s", user_id, active.tier)
        return active

    async def get_active_subscription(
        self, user_id: uuid.UUID
    ) -> SubscriptionHistory | None:
        return await self._sub_history_repo.get_active_by_user(user_id)

    async def get_expiring_subscriptions(
        self, days: int = 3
    ) -> list[SubscriptionHistory]:
        from datetime import timedelta

        target_date = date.today() + timedelta(days=days)
        stmt = select(SubscriptionHistory).where(
            SubscriptionHistory.status == "active",
            SubscriptionHistory.end_date <= target_date,
            SubscriptionHistory.end_date >= date.today(),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_subscription_stats(self) -> dict:
        user_count_stmt = select(
            User.subscription_tier,
            func.count(User.id),
        ).group_by(User.subscription_tier)
        result = await self._session.execute(user_count_stmt)
        tier_counts = dict(result.all())

        revenue_stmt = select(
            func.sum(WalletTransaction.amount_usd),
        ).where(
            WalletTransaction.type == "subscription_purchase",
            WalletTransaction.status == "completed",
        )
        rev_result = await self._session.execute(revenue_stmt)
        total_revenue = rev_result.scalar() or Decimal("0")

        return {
            "tier_counts": tier_counts,
            "total_revenue": total_revenue,
        }
