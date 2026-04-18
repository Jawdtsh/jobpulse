import inspect
from unittest.mock import AsyncMock, MagicMock

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


def test_process_upload_has_return_annotation():
    from src.bot.handlers.cv_upload import _process_upload

    sig = inspect.signature(_process_upload)
    assert sig.return_annotation is None


def test_handle_invalid_file_uses_underscore_state():
    from src.bot.handlers.cv_upload import handle_invalid_file

    sig = inspect.signature(handle_invalid_file)
    params = list(sig.parameters.keys())
    assert "_state" in params


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
