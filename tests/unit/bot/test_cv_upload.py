from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_message(text: str, user_id: int = 123, lang_code: str = "ar"):
    message = MagicMock()
    message.text = text
    message.from_user = MagicMock()
    message.from_user.id = user_id
    message.from_user.first_name = "Test"
    message.from_user.language_code = lang_code
    message.answer = AsyncMock()
    message.bot = MagicMock()
    return message


def _make_fsm_state(user_id: int = 123):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage

    return FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=user_id))


def _mock_session_gen():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def gen():
        yield mock_session

    return gen, mock_session


@pytest.mark.asyncio
async def test_upload_cv_prompt():
    user = MagicMock()
    user.subscription_tier = "free"

    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        message = _make_message("/upload_cv")
        state = _make_fsm_state()

        from src.bot.handlers.cv_upload import cmd_upload_cv

        await cmd_upload_cv(message, state)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "PDF" in text or "DOCX" in text


@pytest.mark.asyncio
async def test_upload_cv_not_registered():
    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=None)

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
    ):
        message = _make_message("/upload_cv")
        message.from_user.id = 999
        state = _make_fsm_state(user_id=999)

        from src.bot.handlers.cv_upload import cmd_upload_cv

        await cmd_upload_cv(message, state)

        message.answer.assert_called_once()
        text = message.answer.call_args[0][0]
        assert "/start" in text


@pytest.mark.asyncio
async def test_invalid_file_format():
    message = _make_message("test")
    message.document = MagicMock()
    message.document.file_name = "photo.jpg"
    message.document.file_size = 1000

    state = _make_fsm_state()
    from src.bot.states import CVUploadState

    await state.set_state(CVUploadState.waiting_for_file)

    from src.bot.handlers.cv_upload import handle_invalid_file

    await handle_invalid_file(message, state)

    message.answer.assert_called()
