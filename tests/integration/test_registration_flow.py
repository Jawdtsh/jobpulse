import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_session_gen():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def gen():
        yield mock_session

    return gen, mock_session


@pytest.mark.asyncio
async def test_full_registration_flow_new_user():
    new_user = MagicMock()
    new_user.first_name = "Ahmad"
    new_user.subscription_tier = "free"
    new_user.referral_code = "ABC12345"

    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=None)
    repo_instance.create_user = AsyncMock(return_value=new_user)

    message = MagicMock()
    message.text = "/start"
    message.from_user = MagicMock()
    message.from_user.id = 111222333
    message.from_user.first_name = "Ahmad"
    message.from_user.last_name = "Test"
    message.from_user.username = "ahmad_test"
    message.from_user.language_code = "ar"
    message.answer = AsyncMock()

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.memory import MemoryStorage

        state = FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=111222333))

        from src.bot.handlers.registration import cmd_start

        await cmd_start(message, state)

        repo_instance.create_user.assert_called_once_with(
            telegram_id=111222333,
            first_name="Ahmad",
            last_name="Test",
            username="ahmad_test",
            referred_by=None,
        )
        message.answer.assert_called_once()
        assert message.answer.call_args[1].get("reply_markup") is not None


@pytest.mark.asyncio
async def test_registration_with_referral_tracking():
    referrer_id = uuid.uuid4()
    referrer = MagicMock()
    referrer.id = referrer_id

    new_user = MagicMock()
    new_user.first_name = "Referred"
    new_user.subscription_tier = "free"
    new_user.referral_code = "XYZ98765"

    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=None)
    repo_instance.get_by_referral_code = AsyncMock(return_value=referrer)
    repo_instance.create_user = AsyncMock(return_value=new_user)

    message = MagicMock()
    message.text = "/start ref_ABC12345"
    message.from_user = MagicMock()
    message.from_user.id = 444555666
    message.from_user.first_name = "Referred"
    message.from_user.last_name = None
    message.from_user.username = None
    message.from_user.language_code = "ar"
    message.answer = AsyncMock()

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.memory import MemoryStorage

        state = FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=444555666))

        from src.bot.handlers.registration import cmd_start

        await cmd_start(message, state)

        create_kwargs = repo_instance.create_user.call_args[1]
        assert create_kwargs["referred_by"] == referrer_id


@pytest.mark.asyncio
async def test_help_displays_all_commands():
    message = MagicMock()
    message.text = "/help"
    message.from_user = MagicMock()
    message.from_user.language_code = "ar"
    message.answer = AsyncMock()

    from src.bot.handlers.registration import cmd_help

    await cmd_help(message)

    help_text = message.answer.call_args[0][0]
    for cmd in [
        "/start",
        "/upload_cv",
        "/my_cvs",
        "/my_jobs",
        "/settings",
        "/invite",
        "/subscribe",
        "/cancel",
    ]:
        assert cmd in help_text
