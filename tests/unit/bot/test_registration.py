import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_message(text: str, user_id: int = 123, lang_code: str = "ar"):
    message = MagicMock()
    message.text = text
    message.from_user = MagicMock()
    message.from_user.id = user_id
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.username = "testuser"
    message.from_user.language_code = lang_code
    message.answer = AsyncMock()
    message.bot = MagicMock()
    return message


def _make_fsm_state(user_id: int = 123):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage

    return FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=user_id))


async def _run_with_db_session(handler, *args, session_data=None):
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def _mock_gen():
        yield mock_session

    with patch("src.database.get_async_session", _mock_gen()):
        if session_data:
            for key, value in session_data.items():
                with patch(key, return_value=value):
                    return await handler(*args), mock_session
        return await handler(*args), mock_session


@pytest.mark.asyncio
async def test_start_new_user():
    new_user = MagicMock()
    new_user.first_name = "Test"
    new_user.subscription_tier = "free"
    new_user.id = uuid.uuid4()

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def _mock_gen():
        yield mock_session

    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=None)
    repo_instance.create_user = AsyncMock(return_value=new_user)

    with (
        patch("src.database.get_async_session", _mock_gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        message = _make_message("/start")
        state = _make_fsm_state()

        from src.bot.handlers.registration import cmd_start

        await cmd_start(message, state)

        message.answer.assert_called_once()
        assert "JobPulse" in message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_start_existing_user():
    existing_user = MagicMock()
    existing_user.first_name = "Existing"
    existing_user.subscription_tier = "pro"

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def _mock_gen():
        yield mock_session

    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=existing_user)

    with (
        patch("src.database.get_async_session", _mock_gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        message = _make_message("/start")
        state = _make_fsm_state()

        from src.bot.handlers.registration import cmd_start

        await cmd_start(message, state)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "JobPulse" in text or "عودتك" in text


@pytest.mark.asyncio
async def test_help_command():
    message = _make_message("/help")
    from src.bot.handlers.registration import cmd_help

    await cmd_help(message)

    message.answer.assert_called_once()
    help_text = message.answer.call_args[0][0]
    for cmd in ["/start", "/upload_cv", "/settings", "/cancel"]:
        assert cmd in help_text


@pytest.mark.asyncio
async def test_start_with_referral():
    referrer_id = uuid.uuid4()
    referrer = MagicMock()
    referrer.id = referrer_id

    new_user = MagicMock()
    new_user.first_name = "Referred"
    new_user.subscription_tier = "free"

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def _mock_gen():
        yield mock_session

    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=None)
    repo_instance.get_by_referral_code = AsyncMock(return_value=referrer)
    repo_instance.create_user = AsyncMock(return_value=new_user)

    with (
        patch("src.database.get_async_session", _mock_gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        message = _make_message("/start ref_ABC12345")
        state = _make_fsm_state()

        from src.bot.handlers.registration import cmd_start

        await cmd_start(message, state)

        repo_instance.create_user.assert_called_once()
        call_kwargs = repo_instance.create_user.call_args[1]
        assert call_kwargs.get("referred_by") == referrer_id
