from unittest.mock import AsyncMock

import pytest

from src.bot.handlers.cover_letter import router


class TestCoverLetterHandlerCallbacks:
    def test_router_has_start_handler(self):
        handlers = router.callbacks
        assert len(handlers) > 0

    @pytest.mark.asyncio
    async def test_callback_cancel_clears_state(self):
        from src.bot.handlers.cover_letter import callback_cancel

        callback = AsyncMock()
        callback.data = "cl_cancel"
        state = AsyncMock()

        await callback_cancel(callback, state)

        state.clear.assert_called_once()
        callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_wait_for_reset_shows_countdown(self):
        from src.bot.handlers.cover_letter import callback_wait_for_reset

        callback = AsyncMock()
        state = AsyncMock()

        await callback_wait_for_reset(callback, state)

        callback.answer.assert_called_once()
        answer_text = callback.answer.call_args[0][0]
        assert "Reset in" in answer_text
