import pytest
from decimal import Decimal

from src.repositories.user_repository import UserRepository
from src.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_wallet_auto_creation(db_session):
    from src.repositories.wallet_repository import WalletRepository

    user_repo = UserRepository(db_session)
    wallet_repo = WalletRepository(db_session)

    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]

    existing = await wallet_repo.get_by_user_id(test_user.id)
    if existing:
        wallet = existing
    else:
        wallet_svc = WalletService(db_session)
        wallet = await wallet_svc.get_or_create_wallet(test_user.id)
        await db_session.commit()

    assert wallet is not None
    assert wallet.balance_usd >= Decimal("0.00")


@pytest.mark.asyncio
async def test_wallet_balance_display(db_session):
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]
    wallet_svc = WalletService(db_session)

    balance = await wallet_svc.get_balance(test_user.id)
    assert balance >= Decimal("0.00")


@pytest.mark.asyncio
async def test_admin_add_balance_flow(db_session):
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService

    user_repo = UserRepository(db_session)
    users = await user_repo.get_all(limit=1)
    if not users:
        pytest.skip("No test users available")

    test_user = users[0]
    wallet_svc = WalletService(db_session)

    initial_balance = await wallet_svc.get_balance(test_user.id)

    try:
        wallet, tx = await wallet_svc.admin_add_balance(
            user_id=test_user.id,
            amount=Decimal("10.00"),
            admin_telegram_id=123456,
            reason="Test top-up",
        )
        await db_session.commit()

        new_balance = await wallet_svc.get_balance(test_user.id)
        assert new_balance == initial_balance + Decimal("10.00")
    except Exception:
        await db_session.rollback()
        raise


@pytest.mark.asyncio
async def test_subscription_tier_prices(db_session):
    from src.services.subscription_service import SubscriptionService

    sub_svc = SubscriptionService(db_session)

    free_tier = sub_svc.get_tier_config("free")
    assert free_tier is not None
    assert free_tier["price_usd"] == 0

    basic_tier = sub_svc.get_tier_config("basic")
    assert basic_tier is not None
    assert basic_tier["price_usd"] == 10

    pro_tier = sub_svc.get_tier_config("pro")
    assert pro_tier is not None
    assert pro_tier["price_usd"] == 25


@pytest.mark.asyncio
async def test_generation_packs(db_session):
    from src.services.subscription_service import SubscriptionService

    sub_svc = SubscriptionService(db_session)

    small_pack = sub_svc.get_pack_config("small")
    assert small_pack is not None
    assert small_pack["generations"] == 5

    medium_pack = sub_svc.get_pack_config("medium")
    assert medium_pack is not None
    assert medium_pack["generations"] == 12

    large_pack = sub_svc.get_pack_config("large")
    assert large_pack is not None
    assert large_pack["generations"] == 40
