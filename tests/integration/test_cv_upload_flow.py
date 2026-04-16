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
async def test_cv_upload_flow_valid_file():
    user = MagicMock()
    user.id = uuid.uuid4()
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
        from aiogram.fsm.context import FSMContext
        from aiogram.fsm.storage.memory import MemoryStorage

        state = FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=123))

        from src.bot.handlers.cv_upload import cmd_upload_cv

        message = MagicMock()
        message.text = "/upload_cv"
        message.from_user = MagicMock()
        message.from_user.id = 123
        message.from_user.language_code = "ar"
        message.answer = AsyncMock()

        await cmd_upload_cv(message, state)
        assert message.answer.call_count == 1


@pytest.mark.asyncio
async def test_cv_upload_rejects_invalid_format():
    message = MagicMock()
    message.document = MagicMock()
    message.document.file_name = "photo.jpg"
    message.document.file_size = 1000
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.language_code = "ar"
    message.answer = AsyncMock()

    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from src.bot.states import CVUploadState

    state = FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=123))
    await state.set_state(CVUploadState.waiting_for_file)

    from src.bot.handlers.cv_upload import handle_cv_file

    await handle_cv_file(message, state)

    message.answer.assert_called()


@pytest.mark.asyncio
async def test_cv_upload_rejects_oversized_file():
    message = MagicMock()
    message.document = MagicMock()
    message.document.file_name = "big_cv.pdf"
    message.document.file_size = 10 * 1024 * 1024
    message.from_user = MagicMock()
    message.from_user.id = 123
    message.from_user.language_code = "ar"
    message.answer = AsyncMock()

    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.memory import MemoryStorage
    from src.bot.states import CVUploadState

    state = FSMContext(storage=MemoryStorage(), key=MagicMock(user_id=123))
    await state.set_state(CVUploadState.waiting_for_file)

    from src.bot.handlers.cv_upload import handle_cv_file

    await handle_cv_file(message, state)

    assert message.answer.call_count >= 1
    text = message.answer.call_args[0][0]
    assert "5MB" in text or "كبير" in text
