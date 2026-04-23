import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.subscription_service import SubscriptionService

_test_config = {
    "tiers": [
        {
            "id": "free",
            "price_usd": 0,
            "duration_days": 0,
            "daily_generations": 3,
            "name_ar": "مجاني",
            "name_en": "Free",
        },
        {
            "id": "basic",
            "price_usd": 10,
            "duration_days": 30,
            "daily_generations": 15,
            "name_ar": "أساسي",
            "name_en": "Basic",
        },
        {
            "id": "pro",
            "price_usd": 25,
            "duration_days": 30,
            "daily_generations": 50,
            "name_ar": "احترافي",
            "name_en": "Pro",
        },
    ],
    "generation_packs": [
        {
            "id": "small",
            "price_usd": 0.50,
            "generations": 5,
            "name_ar": "صغيرة",
            "name_en": "Small",
        },
        {
            "id": "medium",
            "price_usd": 1.00,
            "generations": 12,
            "name_ar": "متوسطة",
            "name_en": "Medium",
        },
        {
            "id": "large",
            "price_usd": 3.00,
            "generations": 40,
            "name_ar": "كبيرة",
            "name_en": "Large",
        },
    ],
}


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_sub_history_repo():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_config():
    with patch(
        "src.services.subscription_service._load_tiers_config",
        return_value=_test_config,
    ):
        yield _test_config


@pytest.fixture
def service(mock_session, mock_sub_history_repo, mock_user_repo, mock_config):
    svc = SubscriptionService(mock_session)
    svc._sub_history_repo = mock_sub_history_repo
    svc._user_repo = mock_user_repo
    return svc


@pytest.mark.asyncio
async def test_get_tier_config_basic(service):
    config = service.get_tier_config("basic")
    assert config is not None
    assert config["id"] == "basic"
    assert config["price_usd"] == 10


@pytest.mark.asyncio
async def test_get_tier_config_pro(service):
    config = service.get_tier_config("pro")
    assert config is not None
    assert config["price_usd"] == 25


@pytest.mark.asyncio
async def test_get_tier_config_free(service):
    config = service.get_tier_config("free")
    assert config is not None
    assert config["price_usd"] == 0


@pytest.mark.asyncio
async def test_get_tier_config_unknown(service):
    config = service.get_tier_config("enterprise")
    assert config is None


@pytest.mark.asyncio
async def test_get_all_tiers(service):
    tiers = service.get_all_tiers()
    assert len(tiers) == 3
    assert tiers[0]["id"] == "free"
    assert tiers[1]["id"] == "basic"
    assert tiers[2]["id"] == "pro"


@pytest.mark.asyncio
async def test_get_generation_packs(service):
    packs = service.get_generation_packs()
    assert len(packs) == 3
    assert packs[0]["id"] == "small"
    assert packs[1]["id"] == "medium"
    assert packs[2]["id"] == "large"


@pytest.mark.asyncio
async def test_get_pack_config(service):
    config = service.get_pack_config("medium")
    assert config is not None
    assert config["price_usd"] == 1.00
    assert config["generations"] == 12


@pytest.mark.asyncio
async def test_purchase_tier_idempotency(
    service, mock_sub_history_repo, mock_user_repo
):
    user_id = uuid.uuid4()
    mock_sub_history_repo.get_active_by_user = AsyncMock(return_value=None)

    wallet_mock = MagicMock()
    wallet_mock.balance_usd = Decimal("50.00")
    wallet_mock.total_spent_usd = Decimal("0.00")

    tx_mock = MagicMock()
    tx_mock.id = uuid.uuid4()

    wallet_svc = AsyncMock()
    wallet_svc.deduct_balance = AsyncMock(return_value=(wallet_mock, tx_mock))

    sub_mock = MagicMock()
    mock_sub_history_repo.create = AsyncMock(return_value=sub_mock)

    user_mock = MagicMock()
    user_mock.subscription_tier = "free"
    mock_user_repo.get = AsyncMock(return_value=user_mock)

    result = await service.purchase_tier(user_id, "basic", wallet_svc)
    assert result is sub_mock
    wallet_svc.deduct_balance.assert_called_once()


@pytest.mark.asyncio
async def test_purchase_tier_already_active(service, mock_sub_history_repo):
    user_id = uuid.uuid4()
    active_sub = MagicMock()
    mock_sub_history_repo.get_by_transaction_id = AsyncMock(return_value=active_sub)

    wallet_mock = MagicMock()
    wallet_mock.balance_usd = Decimal("50.00")
    tx_mock = MagicMock()
    tx_mock.id = uuid.uuid4()

    wallet_svc = AsyncMock()
    wallet_svc.deduct_balance = AsyncMock(return_value=(wallet_mock, tx_mock))

    result = await service.purchase_tier(user_id, "basic", wallet_svc)
    assert result is active_sub


@pytest.mark.asyncio
async def test_purchase_tier_unknown(service, mock_sub_history_repo):
    user_id = uuid.uuid4()
    mock_sub_history_repo.get_active_by_user = AsyncMock(return_value=None)

    from src.services.exceptions import WalletError

    with pytest.raises(WalletError, match="Unknown tier"):
        await service.purchase_tier(user_id, "enterprise", AsyncMock())


@pytest.mark.asyncio
async def test_expire_subscription(service, mock_sub_history_repo, mock_user_repo):
    user_id = uuid.uuid4()
    active_sub = MagicMock()
    active_sub.id = uuid.uuid4()
    active_sub.tier = "basic"
    mock_sub_history_repo.get_active_by_user = AsyncMock(return_value=active_sub)
    mock_sub_history_repo.expire_subscription = AsyncMock(return_value=True)

    user = MagicMock()
    user.subscription_tier = "basic"
    mock_user_repo.get = AsyncMock(return_value=user)

    result = await service.expire_subscription(user_id)
    assert result is active_sub
    assert user.subscription_tier == "free"
    mock_sub_history_repo.expire_subscription.assert_called_once_with(active_sub.id)


@pytest.mark.asyncio
async def test_expire_subscription_no_active(service, mock_sub_history_repo):
    user_id = uuid.uuid4()
    mock_sub_history_repo.get_active_by_user = AsyncMock(return_value=None)

    result = await service.expire_subscription(user_id)
    assert result is None
