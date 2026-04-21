import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.wallet_service import WalletService
from src.services.exceptions import InsufficientBalanceError, WalletError


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_wallet_repo():
    return AsyncMock()


@pytest.fixture
def mock_tx_repo():
    return AsyncMock()


@pytest.fixture
def mock_admin_log_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_session, mock_wallet_repo, mock_tx_repo, mock_admin_log_repo):
    svc = WalletService(mock_session)
    svc._wallet_repo = mock_wallet_repo
    svc._tx_repo = mock_tx_repo
    svc._admin_log_repo = mock_admin_log_repo
    return svc


@pytest.mark.asyncio
async def test_get_or_create_wallet_existing(service, mock_wallet_repo):
    user_id = uuid.uuid4()
    existing = MagicMock()
    mock_wallet_repo.get_by_user_id = AsyncMock(return_value=existing)

    result = await service.get_or_create_wallet(user_id)
    assert result is existing
    mock_wallet_repo.get_by_user_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_or_create_wallet_creates(service, mock_wallet_repo):
    user_id = uuid.uuid4()
    mock_wallet_repo.get_by_user_id = AsyncMock(return_value=None)
    new_wallet = MagicMock()
    mock_wallet_repo.create = AsyncMock(return_value=new_wallet)

    result = await service.get_or_create_wallet(user_id)
    assert result is new_wallet
    mock_wallet_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_balance(service, mock_wallet_repo):
    user_id = uuid.uuid4()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("50.00")
    mock_wallet_repo.get_or_create = AsyncMock(return_value=wallet)

    result = await service.get_balance(user_id)
    assert result == Decimal("50.00")


@pytest.mark.asyncio
async def test_add_balance_success(service, mock_wallet_repo, mock_tx_repo):
    user_id = uuid.uuid4()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("0.00")
    wallet.total_deposited_usd = Decimal("0.00")
    mock_wallet_repo.get_or_create = AsyncMock(return_value=wallet)
    mock_tx_repo.create_transaction = AsyncMock(return_value=MagicMock())

    result_wallet, result_tx = await service.add_balance(
        user_id, Decimal("50.00"), description="Test top-up"
    )
    assert wallet.balance_usd == Decimal("50.00")
    assert wallet.total_deposited_usd == Decimal("50.00")
    mock_tx_repo.create_transaction.assert_called_once()


@pytest.mark.asyncio
async def test_add_balance_negative_amount(service):
    user_id = uuid.uuid4()
    with pytest.raises(WalletError, match="positive"):
        await service.add_balance(user_id, Decimal("-10.00"))


@pytest.mark.asyncio
async def test_deduct_balance_success(service, mock_wallet_repo, mock_tx_repo):
    user_id = uuid.uuid4()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("50.00")
    wallet.total_spent_usd = Decimal("0.00")
    mock_wallet_repo.get_or_create = AsyncMock(return_value=wallet)
    mock_tx_repo.create_transaction = AsyncMock(return_value=MagicMock())

    result_wallet, result_tx = await service.deduct_balance(
        user_id, Decimal("10.00"), "subscription_purchase"
    )
    assert wallet.balance_usd == Decimal("40.00")
    assert wallet.total_spent_usd == Decimal("10.00")


@pytest.mark.asyncio
async def test_deduct_balance_insufficient(service, mock_wallet_repo):
    user_id = uuid.uuid4()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("5.00")
    mock_wallet_repo.get_or_create = AsyncMock(return_value=wallet)

    with pytest.raises(InsufficientBalanceError):
        await service.deduct_balance(user_id, Decimal("10.00"), "subscription_purchase")


@pytest.mark.asyncio
async def test_deduct_balance_idempotency(service, mock_wallet_repo, mock_tx_repo):
    user_id = uuid.uuid4()
    existing_tx = MagicMock()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("50.00")
    mock_tx_repo.get_by_idempotency_key = AsyncMock(return_value=existing_tx)
    mock_wallet_repo.get_by_user_id = AsyncMock(return_value=wallet)

    result_wallet, result_tx = await service.deduct_balance(
        user_id,
        Decimal("10.00"),
        "subscription_purchase",
        idempotency_key="test-key",
    )
    assert result_tx is existing_tx


@pytest.mark.asyncio
async def test_deduct_balance_negative_amount(service):
    user_id = uuid.uuid4()
    with pytest.raises(WalletError, match="positive"):
        await service.deduct_balance(user_id, Decimal("-5.00"), "withdrawal")


@pytest.mark.asyncio
async def test_admin_add_balance(
    service, mock_wallet_repo, mock_tx_repo, mock_admin_log_repo
):
    user_id = uuid.uuid4()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("0.00")
    wallet.total_deposited_usd = Decimal("0.00")
    mock_wallet_repo.get_or_create = AsyncMock(return_value=wallet)
    mock_tx_repo.create_transaction = AsyncMock(return_value=MagicMock())
    mock_admin_log_repo.log_action = AsyncMock(return_value=MagicMock())

    result_wallet, result_tx = await service.admin_add_balance(
        user_id, Decimal("100.00"), 123456, "MTN Cash top-up"
    )
    assert wallet.balance_usd == Decimal("100.00")
    mock_admin_log_repo.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_admin_deduct_balance_success(
    service, mock_wallet_repo, mock_tx_repo, mock_admin_log_repo
):
    user_id = uuid.uuid4()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("100.00")
    wallet.total_withdrawn_usd = Decimal("0.00")
    mock_wallet_repo.get_or_create = AsyncMock(return_value=wallet)
    mock_tx_repo.create_transaction = AsyncMock(return_value=MagicMock())
    mock_admin_log_repo.log_action = AsyncMock(return_value=MagicMock())

    result_wallet, result_tx = await service.admin_deduct_balance(
        user_id, Decimal("30.00"), 123456, "Withdrawal to USDT"
    )
    assert wallet.balance_usd == Decimal("70.00")
    assert wallet.total_withdrawn_usd == Decimal("30.00")


@pytest.mark.asyncio
async def test_admin_deduct_balance_insufficient(service, mock_wallet_repo):
    user_id = uuid.uuid4()
    wallet = MagicMock()
    wallet.balance_usd = Decimal("10.00")
    mock_wallet_repo.get_or_create = AsyncMock(return_value=wallet)

    with pytest.raises(InsufficientBalanceError):
        await service.admin_deduct_balance(
            user_id, Decimal("50.00"), 123456, "Over-deduction"
        )
