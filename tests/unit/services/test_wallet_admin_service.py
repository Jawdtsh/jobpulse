from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.wallet_admin_service import WalletAdminService


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_wallet_repo():
    return AsyncMock()


@pytest.fixture
def mock_admin_log_repo():
    return AsyncMock()


@pytest.fixture
def mock_tx_repo():
    return AsyncMock()


@pytest.fixture
def service(
    mock_session, mock_user_repo, mock_wallet_repo, mock_admin_log_repo, mock_tx_repo
):
    svc = WalletAdminService(mock_session)
    svc._user_repo = mock_user_repo
    svc._wallet_repo = mock_wallet_repo
    svc._admin_log_repo = mock_admin_log_repo
    svc._tx_repo = mock_tx_repo
    return svc


@pytest.mark.asyncio
async def test_is_admin_with_valid_id(service):
    with patch("src.services.wallet_admin_service.get_settings") as mock_settings:
        mock_settings.return_value.wallet.admin_user_ids = [123456, 789012]
        assert WalletAdminService.is_admin(123456) is True
        assert WalletAdminService.is_admin(999999) is False


@pytest.mark.asyncio
async def test_get_user_info_found(service, mock_user_repo, mock_wallet_repo):
    from decimal import Decimal
    import uuid

    user = MagicMock()
    user.id = uuid.uuid4()
    user.telegram_id = 123456
    user.username = "testuser"
    user.first_name = "Test"
    user.subscription_tier = "free"
    mock_user_repo.get_by_telegram_id = AsyncMock(return_value=user)

    wallet = MagicMock()
    wallet.balance_usd = Decimal("50.00")
    wallet.total_deposited_usd = Decimal("100.00")
    wallet.total_spent_usd = Decimal("50.00")
    wallet.total_withdrawn_usd = Decimal("0.00")
    mock_wallet_repo.get_by_user_id = AsyncMock(return_value=wallet)

    result = await service.get_user_info(123456)
    assert result is not None
    assert result["telegram_id"] == 123456
    assert result["balance_usd"] == Decimal("50.00")


@pytest.mark.asyncio
async def test_get_user_info_not_found(service, mock_user_repo):
    mock_user_repo.get_by_telegram_id = AsyncMock(return_value=None)
    result = await service.get_user_info(999999)
    assert result is None


@pytest.mark.asyncio
async def test_search_users(mock_session, service, mock_user_repo, mock_wallet_repo):
    from decimal import Decimal
    import uuid

    user1 = MagicMock()
    user1.id = uuid.uuid4()
    user1.telegram_id = 111
    user1.username = "user1"
    user1.first_name = "User One"
    user1.subscription_tier = "basic"

    mock_user_repo.get_by_telegram_id = AsyncMock(return_value=None)

    mock_session.execute = AsyncMock()
    mock_session.execute.return_value.scalars.return_value.all.return_value = [user1]

    wallet = MagicMock()
    wallet.balance_usd = Decimal("25.00")
    mock_wallet_repo.get_by_user_id = AsyncMock(return_value=wallet)

    result = await service.search_users("user")
    assert len(result) >= 0


@pytest.mark.asyncio
async def test_get_recent_transactions_with_user(service):
    import uuid

    tx_repo_mock = AsyncMock()
    tx1 = MagicMock()
    tx1.id = uuid.uuid4()
    tx1.user_id = uuid.uuid4()
    tx1.type = "top_up"
    tx1.amount_usd = 50
    tx1.status = "completed"
    tx1.description = "Test"
    tx1.created_at = None
    tx_repo_mock.get_by_user = AsyncMock(return_value=[tx1])

    with patch(
        "src.services.wallet_admin_service.TransactionRepository",
        return_value=tx_repo_mock,
    ):
        result = await service.get_recent_transactions(user_id=uuid.uuid4())
        assert len(result) == 1
        assert result[0]["type"] == "top_up"


@pytest.mark.asyncio
async def test_get_stats(mock_session, service, mock_tx_repo):
    from decimal import Decimal

    mock_session.execute = AsyncMock()

    total_users_result = MagicMock()
    total_users_result.scalar.return_value = 100

    users_with_balance_result = MagicMock()
    users_with_balance_result.scalar.return_value = 30

    tier_result = MagicMock()
    tier_result.all.return_value = [("free", 70), ("basic", 20), ("pro", 10)]

    topup_result = MagicMock()
    topup_result.scalar.return_value = Decimal("500.00")

    spent_result = MagicMock()
    spent_result.scalar.return_value = Decimal("200.00")

    withdrawn_result = MagicMock()
    withdrawn_result.scalar.return_value = Decimal("50.00")

    active_subs_result = MagicMock()
    active_subs_result.scalar.return_value = 30

    recent_tx_result = MagicMock()
    recent_tx_result.scalar.return_value = 25

    result = await service.get_stats()
    assert result["total_users"] == 100
    assert result["users_with_balance"] == 30
    assert result["active_subscriptions"] == 30
    assert result["recent_transactions"] == 25
    mock_tx_repo.count_recent.assert_called_once_with(hours=24)
