import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_session_gen():
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()

    async def gen():
        yield mock_session

    return gen, mock_session


def _make_callback(data: str, user_id: int = 123):
    callback = MagicMock()
    callback.data = data
    callback.from_user = MagicMock()
    callback.from_user.id = user_id
    callback.from_user.language_code = "ar"
    callback.answer = AsyncMock()
    callback.message = MagicMock()
    callback.message.delete = AsyncMock()
    callback.message.edit_text = AsyncMock()
    return callback


@pytest.mark.asyncio
async def test_unsave_uses_localized_text():
    job_id = uuid.uuid4()
    callback = _make_callback(f"unsave_job:{job_id}")

    user = MagicMock()
    user.id = uuid.uuid4()

    gen, mock_session = _mock_session_gen()
    repo_instance = AsyncMock()
    repo_instance.get_by_telegram_id = AsyncMock(return_value=user)

    svc_instance = AsyncMock()
    svc_instance.unsave = AsyncMock(return_value=True)

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=repo_instance,
        ),
        patch(
            "src.services.saved_job_service.SavedJobService",
            return_value=svc_instance,
        ),
    ):
        from src.bot.handlers.job_notifications import callback_unsave_job

        await callback_unsave_job(callback)

        answer_text = callback.answer.call_args[0][0]
        assert (
            "حفظ" in answer_text or "Unsaved" in answer_text or "إلغاء" in answer_text
        )


@pytest.mark.asyncio
async def test_job_details_null_description():
    job_id = uuid.uuid4()
    callback = _make_callback(f"job_details:{job_id}")

    user = MagicMock()
    user.id = uuid.uuid4()

    job = MagicMock()
    job.description = None
    job.company = "TestCo"
    job.location = "Remote"
    job.salary_min = None
    job.salary_max = None
    job.salary_currency = "USD"

    gen, mock_session = _mock_session_gen()
    user_repo = AsyncMock()
    user_repo.get_by_telegram_id = AsyncMock(return_value=user)

    job_repo = AsyncMock()
    job_repo.get = AsyncMock(return_value=job)

    with (
        patch("src.database.get_async_session", gen),
        patch(
            "src.repositories.user_repository.UserRepository",
            return_value=user_repo,
        ),
        patch(
            "src.repositories.job_repository.JobRepository",
            return_value=job_repo,
        ),
    ):
        from src.bot.handlers.job_notifications import callback_job_details

        await callback_job_details(callback)

        callback.message.edit_text.assert_called_once()
        text = callback.message.edit_text.call_args[0][0]
        assert "TestCo" in text


@pytest.mark.asyncio
async def test_dismiss_uses_contextlib_suppress():
    import inspect
    from src.bot.handlers.job_notifications import callback_dismiss_match

    source = inspect.getsource(callback_dismiss_match)
    assert "contextlib.suppress" in source
    assert "try" not in source or "try:" not in source.split("contextlib")[0]


def test_no_cover_letter_start_handler_in_job_notifications_router():
    import inspect
    from src.bot.handlers import job_notifications

    source = inspect.getsource(job_notifications)
    assert "cover_letter:start" not in source
    assert "callback_cover_letter_start" not in source
