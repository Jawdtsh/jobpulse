import pytest
from decimal import Decimal

from src.services.wallet_service import WalletService
from src.services.subscription_service import SubscriptionService
from src.services.quota_service import QuotaService


@pytest.mark.asyncio
async def test_user_purchases_basic_subscription(db_session):
    from src.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]

    wallet_svc = WalletService(db_session)
    wallet, _ = await wallet_svc.admin_add_balance(
        user_id=test_user.id,
        amount=Decimal("20.00"),
        admin_telegram_id=999999,
        reason="Initial balance for test",
    )
    await db_session.commit()

    initial_balance = wallet.balance_usd

    sub_svc = SubscriptionService(db_session)
    quota_svc = QuotaService(db_session)

    try:
        subscription = await sub_svc.purchase_tier(
            user_id=test_user.id,
            tier_id="basic",
            wallet_service=wallet_svc,
        )
        await db_session.commit()

        new_balance = await wallet_svc.get_balance(test_user.id)
        assert new_balance == initial_balance - Decimal("10.00")

        assert subscription is not None
        assert subscription.tier == "basic"

        remaining_quota = await quota_svc.get_remaining_quota(test_user.id, "basic")
        assert remaining_quota >= 15

    except Exception:
        await db_session.rollback()
        raise


@pytest.mark.asyncio
async def test_concurrent_purchases_idempotency(db_session):
    from src.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]

    wallet_svc = WalletService(db_session)
    wallet, _ = await wallet_svc.admin_add_balance(
        user_id=test_user.id,
        amount=Decimal("30.00"),
        admin_telegram_id=999999,
        reason="Initial balance for test",
    )
    await db_session.commit()

    idempotency_key = "test:idempotent:purchase:123"

    wallet_svc2 = WalletService(db_session)

    wallet1, tx1 = await wallet_svc2.deduct_balance(
        user_id=test_user.id,
        amount=Decimal("5.00"),
        transaction_type="test_purchase",
        idempotency_key=idempotency_key,
    )
    await db_session.commit()

    wallet_svc3 = WalletService(db_session)
    wallet2, tx2 = await wallet_svc3.deduct_balance(
        user_id=test_user.id,
        amount=Decimal("5.00"),
        transaction_type="test_purchase",
        idempotency_key=idempotency_key,
    )
    await db_session.commit()

    assert tx1.id == tx2.id


@pytest.mark.asyncio
async def test_subscription_expiry_auto_downgrade(db_session):
    from datetime import date, timedelta
    from src.repositories.user_repository import UserRepository
    from src.models.subscription_history import SubscriptionHistory

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]

    sub_history = SubscriptionHistory(
        id=test_user.id,
        user_id=test_user.id,
        tier="basic",
        start_date=date.today() - timedelta(days=35),
        end_date=date.today() - timedelta(days=5),
        status="active",
    )
    db_session.add(sub_history)
    await db_session.commit()

    sub_svc = SubscriptionService(db_session)
    expired = await sub_svc.expire_subscription(test_user.id)
    await db_session.commit()

    assert expired is not None
    assert expired.tier == "basic"

    updated_user = await user_repo.get(test_user.id)
    assert updated_user.subscription_tier == "free"
