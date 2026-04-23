import pytest
from decimal import Decimal

from src.services.wallet_service import WalletService
from src.services.exceptions import InsufficientBalanceError


@pytest.mark.asyncio
async def test_negative_balance_prevention(db_session):
    from src.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]

    wallet_svc = WalletService(db_session)

    wallet = await wallet_svc.get_or_create_wallet(test_user.id)
    await db_session.commit()

    wallet.balance_usd = Decimal("5.00")
    await db_session.commit()

    with pytest.raises(InsufficientBalanceError):
        await wallet_svc.deduct_balance(
            user_id=test_user.id,
            amount=Decimal("10.00"),
            transaction_type="test",
        )


@pytest.mark.asyncio
async def test_duplicate_purchase_prevention(db_session):
    from src.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]

    wallet_svc = WalletService(db_session)
    wallet, _ = await wallet_svc.admin_add_balance(
        user_id=test_user.id,
        amount=Decimal("15.00"),
        admin_telegram_id=999999,
        reason="Test balance",
    )
    await db_session.commit()

    idempotency_key = "unique:test:purchase:456"

    wallet1, tx1 = await wallet_svc.deduct_balance(
        user_id=test_user.id,
        amount=Decimal("5.00"),
        transaction_type="test_purchase",
        idempotency_key=idempotency_key,
    )
    await db_session.commit()

    wallet2, tx2 = await wallet_svc.deduct_balance(
        user_id=test_user.id,
        amount=Decimal("5.00"),
        transaction_type="test_purchase",
        idempotency_key=idempotency_key,
    )
    await db_session.commit()

    assert tx1.id == tx2.id

    final_balance = await wallet_svc.get_balance(test_user.id)
    assert final_balance == Decimal("10.00")


@pytest.mark.asyncio
async def test_admin_deduct_more_than_balance(db_session):
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
        reason="Test balance",
    )
    await db_session.commit()

    with pytest.raises(InsufficientBalanceError):
        await wallet_svc.admin_deduct_balance(
            user_id=test_user.id,
            amount=Decimal("50.00"),
            admin_telegram_id=999999,
            reason="Invalid deduction",
        )


@pytest.mark.asyncio
async def test_subscription_purchase_exact_balance(db_session):
    from src.repositories.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]

    wallet_svc = WalletService(db_session)
    wallet, _ = await wallet_svc.admin_add_balance(
        user_id=test_user.id,
        amount=Decimal("10.00"),
        admin_telegram_id=999999,
        reason="Exact balance for test",
    )
    await db_session.commit()

    from src.services.subscription_service import SubscriptionService

    sub_svc = SubscriptionService(db_session)

    subscription = await sub_svc.purchase_tier(
        user_id=test_user.id,
        tier_id="basic",
        wallet_service=wallet_svc,
    )
    await db_session.commit()

    final_balance = await wallet_svc.get_balance(test_user.id)
    assert final_balance == Decimal("0.00")
    assert subscription is not None
    assert subscription.tier == "basic"
