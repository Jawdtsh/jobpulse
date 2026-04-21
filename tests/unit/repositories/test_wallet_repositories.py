import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.wallet_repository import WalletRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.subscription_history_repository import (
    SubscriptionHistoryRepository,
)
from src.repositories.admin_action_log_repository import AdminActionLogRepository


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_wallet_repository_get_by_user_id(mock_session):
    repo = WalletRepository(mock_session)
    user_id = uuid.uuid4()

    from src.models.user_wallet import UserWallet
    from sqlalchemy import select

    mock_session.execute = AsyncMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = None

    result = await repo.get_by_user_id(user_id)
    assert result is None


@pytest.mark.asyncio
async def test_wallet_repository_get_or_create_existing(mock_session):
    repo = WalletRepository(mock_session)
    user_id = uuid.uuid4()

    existing_wallet = MagicMock()
    repo.get_by_user_id = AsyncMock(return_value=existing_wallet)

    result = await repo.get_or_create(user_id)
    assert result is existing_wallet


@pytest.mark.asyncio
async def test_wallet_repository_get_or_create_new(mock_session):
    repo = WalletRepository(mock_session)
    user_id = uuid.uuid4()

    repo.get_by_user_id = AsyncMock(return_value=None)
    new_wallet = MagicMock()
    repo.create = AsyncMock(return_value=new_wallet)

    result = await repo.get_or_create(user_id)
    assert result is new_wallet
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_transaction_repository_get_by_user(mock_session):
    repo = TransactionRepository(mock_session)
    user_id = uuid.uuid4()

    mock_session.execute = AsyncMock()
    mock_session.execute.return_value.scalars.return_value.all.return_value = []

    result = await repo.get_by_user(user_id)
    assert result == []


@pytest.mark.asyncio
async def test_transaction_repository_get_by_idempotency_key(mock_session):
    repo = TransactionRepository(mock_session)

    mock_session.execute = AsyncMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = None

    result = await repo.get_by_idempotency_key("test-key")
    assert result is None


@pytest.mark.asyncio
async def test_transaction_repository_create_transaction(mock_session):
    repo = TransactionRepository(mock_session)
    user_id = uuid.uuid4()
    from decimal import Decimal

    tx = MagicMock()
    repo.create = AsyncMock(return_value=tx)

    result = await repo.create_transaction(
        user_id=user_id,
        type_="top_up",
        amount_usd=Decimal("50.00"),
        balance_before=Decimal("0.00"),
        balance_after=Decimal("50.00"),
        description="Test",
    )
    assert result is tx
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_subscription_history_repository_get_active(mock_session):
    repo = SubscriptionHistoryRepository(mock_session)
    user_id = uuid.uuid4()

    mock_session.execute = AsyncMock()
    mock_session.execute.return_value.scalar_one_or_none.return_value = None

    result = await repo.get_active_by_user(user_id)
    assert result is None


@pytest.mark.asyncio
async def test_subscription_history_repository_expire(mock_session):
    repo = SubscriptionHistoryRepository(mock_session)
    sub_id = uuid.uuid4()

    sub = MagicMock()
    repo.get = AsyncMock(return_value=sub)

    result = await repo.expire_subscription(sub_id)
    assert result is True
    assert sub.status == "expired"


@pytest.mark.asyncio
async def test_subscription_history_repository_expire_not_found(mock_session):
    repo = SubscriptionHistoryRepository(mock_session)
    sub_id = uuid.uuid4()

    repo.get = AsyncMock(return_value=None)

    result = await repo.expire_subscription(sub_id)
    assert result is False


@pytest.mark.asyncio
async def test_admin_action_log_repository_log_action(mock_session):
    repo = AdminActionLogRepository(mock_session)

    log = MagicMock()
    repo.create = AsyncMock(return_value=log)

    result = await repo.log_action(
        admin_user_id=123456,
        action_type="add_balance",
        reason="Test top-up",
    )
    assert result is log
    repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_admin_action_log_repository_count_recent(mock_session):
    repo = AdminActionLogRepository(mock_session)

    mock_session.execute = AsyncMock()
    mock_session.execute.return_value.scalar.return_value = 5

    result = await repo.count_recent(hours=24)
    assert result == 5
