from unittest.mock import AsyncMock, MagicMock

import pytest
import uuid

from src.bot.handlers.cover_letter import router
from src.bot.handlers.job_notifications import router as job_notifications_router


class TestCoverLetterHandlerCallbacks:
    def test_router_has_start_handler(self):
        handlers = router.callback_query.handlers
        assert len(handlers) > 0

    def test_job_notifications_router_has_no_cover_letter_handler(self):
        for handler in job_notifications_router.callback_query.handlers:
            for filter_ in handler.filters:
                if hasattr(filter_, "regexp"):
                    import re

                    pattern = (
                        filter_.regexp.pattern
                        if hasattr(filter_.regexp, "pattern")
                        else str(filter_.regexp)
                    )
                    assert not re.search(r"cover_letter:start", pattern)

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

    @pytest.mark.asyncio
    async def test_callback_generate_anyway_parses_job_id_correctly(self):
        from src.bot.handlers.cover_letter import callback_generate_anyway

        callback = AsyncMock()
        callback.data = f"cl_generate_anyway:job:{'a' * 36}"
        state = AsyncMock()
        state.get_data = AsyncMock(return_value={})

        try:
            await callback_generate_anyway(callback, state)
        except Exception:
            pass

        state.set_data.assert_called_once()
        call_kwargs = state.set_data.call_args[0][0]
        assert call_kwargs["job_id"] == "a" * 36

    @pytest.mark.asyncio
    async def test_callback_generate_anyway_sets_skip_cv_warning(self):
        from src.bot.handlers.cover_letter import callback_generate_anyway

        callback = AsyncMock()
        callback.data = f"cl_generate_anyway:job:{'b' * 36}"
        state = AsyncMock()
        state.get_data = AsyncMock(return_value={})

        try:
            await callback_generate_anyway(callback, state)
        except Exception:
            pass

        state.set_data.assert_called_once()
        call_kwargs = state.set_data.call_args[0][0]
        assert call_kwargs["skip_cv_warning"] is True

    def test_decrypt_cv_raises_on_failure(self):
        from src.bot.handlers.cover_letter import _decrypt_cv

        cv = MagicMock()
        cv.content = b"invalid_encrypted_data"

        with pytest.raises(ValueError, match="Failed to decrypt CV content"):
            _decrypt_cv(cv)

    def test_decrypt_cv_returns_empty_for_none_content(self):
        from src.bot.handlers.cover_letter import _decrypt_cv

        cv = MagicMock()
        cv.content = None

        result = _decrypt_cv(cv)
        assert result == ""

    def test_i18n_has_cl_error_job_deleted_key(self):
        import json
        from pathlib import Path

        messages_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "bot"
            / "locales"
            / "messages.json"
        )
        with open(messages_path, encoding="utf-8") as f:
            messages = json.load(f)
        assert "cl_error_job_deleted" in messages
        assert "ar" in messages["cl_error_job_deleted"]
        assert "en" in messages["cl_error_job_deleted"]

    def test_i18n_has_cl_error_decrypt_failed_key(self):
        import json
        from pathlib import Path

        messages_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "bot"
            / "locales"
            / "messages.json"
        )
        with open(messages_path, encoding="utf-8") as f:
            messages = json.load(f)
        assert "cl_error_decrypt_failed" in messages
        assert "ar" in messages["cl_error_decrypt_failed"]
        assert "en" in messages["cl_error_decrypt_failed"]

    def test_helpers_are_private_functions(self):
        from src.bot.handlers import cover_letter as cl

        assert callable(cl._check_user)
        assert callable(cl._validate_quota)
        assert callable(cl._validate_cv)
        assert callable(cl._execute_generation)
        assert callable(cl._display_result)
        assert callable(cl._build_quota_exhausted_text)

    @pytest.mark.asyncio
    async def test_validate_cv_reads_job_id_from_state(self):
        from unittest.mock import patch

        from src.bot.handlers.cover_letter import _validate_cv

        callback = AsyncMock()
        state = AsyncMock()
        state.get_data = AsyncMock(return_value={"job_id": "abc-123"})
        user = MagicMock()
        user.id = uuid.uuid4()
        session = AsyncMock()

        cv = MagicMock()
        cv.id = uuid.uuid4()
        incomplete_cv_result = (False, 30.0)

        with (
            patch("src.bot.handlers.cover_letter.CVRepository") as MockCVRepo,
            patch("src.bot.handlers.cover_letter.CoverLetterService") as MockCLSvc,
        ):
            MockCVRepo.return_value.get_active_cv = AsyncMock(return_value=cv)
            MockCLSvc.check_cv_completeness = MagicMock(
                return_value=incomplete_cv_result
            )

            result = await _validate_cv(callback, state, user, session, "en")

        assert result is None
        callback.message.edit_text.assert_called_once()
        call_args = callback.message.edit_text.call_args
        reply_markup = call_args.kwargs.get("reply_markup") or call_args[1].get(
            "reply_markup"
        )
        assert reply_markup is not None

    @pytest.mark.asyncio
    async def test_validate_cv_accepts_state_parameter(self):
        import inspect
        from src.bot.handlers.cover_letter import _validate_cv

        sig = inspect.signature(_validate_cv)
        param_names = list(sig.parameters.keys())
        assert "state" in param_names
