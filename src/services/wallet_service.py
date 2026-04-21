import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from src.repositories.wallet_repository import WalletRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.admin_action_log_repository import AdminActionLogRepository
from src.services.exceptions import InsufficientBalanceError, WalletError

logger = logging.getLogger(__name__)

TRANSACTION_TYPE_TOP_UP = "top_up"
TRANSACTION_TYPE_SUBSCRIPTION_PURCHASE = "subscription_purchase"
TRANSACTION_TYPE_GENERATION_PURCHASE = "generation_purchase"
TRANSACTION_TYPE_WITHDRAWAL = "withdrawal"
TRANSACTION_TYPE_ADMIN_ADJUSTMENT = "admin_adjustment"
TRANSACTION_TYPE_REFUND = "refund"

PURCHASE_RATE_LIMIT_SECONDS = 5
RATE_LIMIT_KEY_PREFIX = "wallet:purchase_rate_limit"


class WalletService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._wallet_repo = WalletRepository(session)
        self._tx_repo = TransactionRepository(session)
        self._admin_log_repo = AdminActionLogRepository(session)

    async def _check_rate_limit(self, user_id: uuid.UUID) -> bool:
        settings = get_settings()
        try:
            redis_client = aioredis.from_url(
                settings.redis.redis_url, decode_responses=True
            )
            key = f"{RATE_LIMIT_KEY_PREFIX}:{user_id}"
            existing = await redis_client.get(key)
            if existing:
                await redis_client.aclose()
                return False
            await redis_client.setex(key, PURCHASE_RATE_LIMIT_SECONDS, "1")
            await redis_client.aclose()
            return True
        except Exception:
            logger.warning("Rate limit check failed, allowing purchase")
            return True

    async def _release_rate_limit(self, user_id: uuid.UUID) -> None:
        settings = get_settings()
        try:
            redis_client = aioredis.from_url(
                settings.redis.redis_url, decode_responses=True
            )
            key = f"{RATE_LIMIT_KEY_PREFIX}:{user_id}"
            await redis_client.delete(key)
            await redis_client.aclose()
        except Exception:
            pass

    async def get_or_create_wallet(self, user_id: uuid.UUID):
        return await self._wallet_repo.get_or_create(user_id)

    async def get_balance(self, user_id: uuid.UUID) -> Decimal:
        wallet = await self.get_or_create_wallet(user_id)
        return wallet.balance_usd

    async def add_balance(
        self,
        user_id: uuid.UUID,
        amount: Decimal,
        description: str | None = None,
        admin_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> tuple:
        if amount <= 0:
            raise WalletError("Amount must be positive")

        wallet = await self.get_or_create_wallet(user_id)
        balance_before = wallet.balance_usd
        balance_after = balance_before + amount

        wallet.balance_usd = balance_after
        wallet.total_deposited_usd = wallet.total_deposited_usd + amount
        wallet.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

        tx = await self._tx_repo.create_transaction(
            user_id=user_id,
            type_=TRANSACTION_TYPE_TOP_UP,
            amount_usd=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            admin_id=admin_id,
            metadata=metadata,
        )

        if admin_id:
            await self._admin_log_repo.log_action(
                admin_user_id=admin_id.int >> 96 if hasattr(admin_id, "int") else 0,
                action_type="add_balance",
                target_user_id=user_id,
                amount_usd=amount,
                reason=description,
            )

        logger.info(
            "Added balance user=%s amount=%s before=%s after=%s",
            user_id,
            amount,
            balance_before,
            balance_after,
        )
        return wallet, tx

    async def deduct_balance(
        self,
        user_id: uuid.UUID,
        amount: Decimal,
        transaction_type: str,
        description: str | None = None,
        idempotency_key: str | None = None,
        metadata: dict | None = None,
        is_spending: bool = True,
    ) -> tuple:
        if amount <= 0:
            raise WalletError("Amount must be positive")

        if not await self._check_rate_limit(user_id):
            raise WalletError(
                f"Rate limit exceeded. Please wait {PURCHASE_RATE_LIMIT_SECONDS} seconds before another purchase."
            )

        if idempotency_key:
            existing = await self._tx_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                wallet = await self._wallet_repo.get_by_user_id(user_id)
                await self._release_rate_limit(user_id)
                return wallet, existing

        wallet = await self.get_or_create_wallet(user_id)
        if wallet.balance_usd < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance: {wallet.balance_usd} < {amount}"
            )

        balance_before = wallet.balance_usd
        balance_after = balance_before - amount

        wallet.balance_usd = balance_after
        if is_spending:
            wallet.total_spent_usd = wallet.total_spent_usd + amount
        wallet.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

        tx = await self._tx_repo.create_transaction(
            user_id=user_id,
            type_=transaction_type,
            amount_usd=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            metadata=metadata,
            idempotency_key=idempotency_key,
        )

        logger.info(
            "Deducted balance user=%s amount=%s type=%s before=%s after=%s",
            user_id,
            amount,
            transaction_type,
            balance_before,
            balance_after,
        )
        await self._release_rate_limit(user_id)
        return wallet, tx

    async def admin_add_balance(
        self,
        user_id: uuid.UUID,
        amount: Decimal,
        admin_telegram_id: int,
        reason: str,
    ) -> tuple:
        wallet = await self.get_or_create_wallet(user_id)
        balance_before = wallet.balance_usd
        balance_after = balance_before + amount

        wallet.balance_usd = balance_after
        wallet.total_deposited_usd = wallet.total_deposited_usd + amount
        wallet.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

        tx = await self._tx_repo.create_transaction(
            user_id=user_id,
            type_=TRANSACTION_TYPE_TOP_UP,
            amount_usd=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=reason,
            metadata={"admin_telegram_id": admin_telegram_id},
        )

        await self._admin_log_repo.log_action(
            admin_user_id=admin_telegram_id,
            action_type="add_balance",
            target_user_id=user_id,
            amount_usd=amount,
            reason=reason,
            details={"transaction_id": str(tx.id)},
        )

        logger.info(
            "Admin %s added %s to user %s (reason: %s)",
            admin_telegram_id,
            amount,
            user_id,
            reason,
        )
        return wallet, tx

    async def admin_deduct_balance(
        self,
        user_id: uuid.UUID,
        amount: Decimal,
        admin_telegram_id: int,
        reason: str,
    ) -> tuple:
        wallet = await self.get_or_create_wallet(user_id)
        if wallet.balance_usd < amount:
            raise InsufficientBalanceError(
                f"Insufficient balance: {wallet.balance_usd} < {amount}"
            )

        balance_before = wallet.balance_usd
        balance_after = balance_before - amount

        wallet.balance_usd = balance_after
        wallet.total_withdrawn_usd = wallet.total_withdrawn_usd + amount
        wallet.updated_at = datetime.now(timezone.utc)
        await self._session.flush()

        tx = await self._tx_repo.create_transaction(
            user_id=user_id,
            type_=TRANSACTION_TYPE_WITHDRAWAL,
            amount_usd=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=reason,
            metadata={"admin_telegram_id": admin_telegram_id},
        )

        await self._admin_log_repo.log_action(
            admin_user_id=admin_telegram_id,
            action_type="deduct_balance",
            target_user_id=user_id,
            amount_usd=amount,
            reason=reason,
            details={"transaction_id": str(tx.id)},
        )

        logger.info(
            "Admin %s deducted %s from user %s (reason: %s)",
            admin_telegram_id,
            amount,
            user_id,
            reason,
        )
        return wallet, tx
