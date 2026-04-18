import contextlib
import logging
import uuid

from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("save_job:"))
async def callback_save_job(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    job_id = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.saved_job_service import SavedJobService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        svc = SavedJobService(session)
        existing = await svc.is_saved(user.id, uuid.UUID(job_id))
        if existing:
            await callback.answer(t("job_already_saved", locale), show_alert=False)
            return

        await svc.save(user.id, uuid.UUID(job_id))
        await session.commit()
        await callback.answer(t("job_saved", locale), show_alert=False)


@router.callback_query(F.data.startswith("unsave_job:"))
async def callback_unsave_job(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    job_id = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.saved_job_service import SavedJobService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        svc = SavedJobService(session)
        await svc.unsave(user.id, uuid.UUID(job_id))
        await session.commit()

    await callback.answer(t("job_unsaved", locale), show_alert=False)
    with contextlib.suppress(Exception):
        await callback.message.delete()


@router.callback_query(F.data.startswith("job_details:"))
async def callback_job_details(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    job_id = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.job_repository import JobRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        job_repo = JobRepository(session)
        job = await job_repo.get(uuid.UUID(job_id))
        if not job:
            await callback.answer(t("error_generic", locale), show_alert=True)
            return

        salary = ""
        if job.salary_min and job.salary_max:
            salary = f"{job.salary_min}-{job.salary_max} {job.salary_currency}"

        description = job.description or ""
        text = t(
            "job_details",
            locale,
            company=job.company,
            location=job.location or "N/A",
            salary=salary or "N/A",
            match_percent="",
            description=description[:1000] + "..."
            if len(description) > 1000
            else description,
        )

        await callback.message.edit_text(text)

    await callback.answer()


@router.callback_query(F.data.startswith("dismiss_match:"))
async def callback_dismiss_match(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    match_id = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.match_repository import MatchRepository

    async for session in get_async_session():
        match_repo = MatchRepository(session)
        match = await match_repo.get(uuid.UUID(match_id))
        if match:
            await match_repo.update(match.id, is_dismissed=True)
            await session.commit()

    with contextlib.suppress(Exception):
        await callback.message.delete()

    await callback.answer(t("job_dismissed", locale))


@router.callback_query(F.data.startswith("cover_letter:"))
async def callback_cover_letter(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    await callback.answer(t("coming_soon", locale))
