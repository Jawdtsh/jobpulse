import logging
import uuid

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot.states import CoverLetterGeneration
from src.bot.keyboards import (
    cover_letter_customization_keyboard,
    cover_letter_action_keyboard,
    quota_exhausted_keyboard,
    purchase_packs_keyboard,
    cv_warning_keyboard,
)
from src.bot.utils.i18n import t, get_locale
from src.services.quota_service import QuotaService, get_midnight_countdown_seconds
from src.utils.encryption import decrypt_data

logger = logging.getLogger(__name__)

router = Router()

_DEFAULT_STATE = {
    "tone": "professional",
    "length": "medium",
    "focus": "all",
    "language": "english",
}


@router.callback_query(F.data.startswith("cover_letter:start:"))
async def callback_cover_letter_start(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer(t("error_generic", locale), show_alert=True)
        return

    job_id = parts[2]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.cv_repository import CVRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        quota_svc = QuotaService(session)
        has_quota = await quota_svc.has_quota(user.id, user.subscription_tier)
        if not has_quota:
            remaining = await quota_svc.get_remaining_quota(
                user.id, user.subscription_tier
            )
            countdown = get_midnight_countdown_seconds()
            hours = countdown // 3600
            minutes = (countdown % 3600) // 60
            await state.set_state(CoverLetterGeneration.quota_exhausted)
            await state.update_data(job_id=job_id)
            await callback.message.edit_text(
                t("cl_quota_exhausted", locale, remaining=remaining)
                + f"\n⏰ Reset in: {hours}h {minutes}m",
                reply_markup=quota_exhausted_keyboard(),
            )
            await callback.answer()
            return

        cv_repo = CVRepository(session)
        cv = await cv_repo.get_active_cv(user.id)
        if not cv:
            await callback.answer(t("cl_no_cv", locale), show_alert=True)
            return

        await state.set_state(CoverLetterGeneration.customizing)
        await state.update_data(job_id=job_id, cv_id=str(cv.id), **_DEFAULT_STATE)
        kb = cover_letter_customization_keyboard()
        await callback.message.edit_text(
            t("cl_customize", locale),
            reply_markup=kb,
        )
        await callback.answer()


@router.callback_query(F.data == "cl_tone:formal")
@router.callback_query(F.data == "cl_tone:casual")
@router.callback_query(F.data == "cl_tone:professional")
async def callback_set_tone(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    tone = callback.data.split(":")[1]
    data = await state.get_data()
    data["tone"] = tone
    await state.set_data(data)
    kb = cover_letter_customization_keyboard(
        tone=tone,
        length=data.get("length", "medium"),
        focus=data.get("focus", "all"),
        language=data.get("language", "english"),
    )
    try:
        await callback.message.edit_text(t("cl_customize", locale), reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "cl_length:short")
@router.callback_query(F.data == "cl_length:medium")
@router.callback_query(F.data == "cl_length:long")
async def callback_set_length(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    length = callback.data.split(":")[1]
    data = await state.get_data()
    data["length"] = length
    await state.set_data(data)
    kb = cover_letter_customization_keyboard(
        tone=data.get("tone", "professional"),
        length=length,
        focus=data.get("focus", "all"),
        language=data.get("language", "english"),
    )
    try:
        await callback.message.edit_text(t("cl_customize", locale), reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "cl_focus:skills")
@router.callback_query(F.data == "cl_focus:experience")
@router.callback_query(F.data == "cl_focus:education")
@router.callback_query(F.data == "cl_focus:all")
async def callback_set_focus(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    focus = callback.data.split(":")[1]
    data = await state.get_data()
    data["focus"] = focus
    await state.set_data(data)
    kb = cover_letter_customization_keyboard(
        tone=data.get("tone", "professional"),
        length=data.get("length", "medium"),
        focus=focus,
        language=data.get("language", "english"),
    )
    try:
        await callback.message.edit_text(t("cl_customize", locale), reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "cl_lang:arabic")
@router.callback_query(F.data == "cl_lang:english")
@router.callback_query(F.data == "cl_lang:bilingual")
async def callback_set_language(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    language = callback.data.split(":")[1]
    data = await state.get_data()
    data["language"] = language
    await state.set_data(data)
    kb = cover_letter_customization_keyboard(
        tone=data.get("tone", "professional"),
        length=data.get("length", "medium"),
        focus=data.get("focus", "all"),
        language=language,
    )
    try:
        await callback.message.edit_text(t("cl_customize", locale), reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "cl_generate")
async def callback_generate(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    await callback.answer(t("cl_generating", locale))

    data = await state.get_data()
    job_id = data.get("job_id", "")
    tone = data.get("tone", "professional")
    length = data.get("length", "medium")
    focus = data.get("focus", "all")
    language = data.get("language", "english")

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.cv_repository import CVRepository
    from src.repositories.job_repository import JobRepository
    from src.services.cover_letter_service import CoverLetterService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.message.edit_text(t("not_registered", locale))
            return

        quota_svc = QuotaService(session)
        has_quota = await quota_svc.has_quota(user.id, user.subscription_tier)
        if not has_quota:
            remaining = await quota_svc.get_remaining_quota(
                user.id, user.subscription_tier
            )
            countdown = get_midnight_countdown_seconds()
            hours = countdown // 3600
            minutes = (countdown % 3600) // 60
            await callback.message.edit_text(
                t("cl_quota_exhausted", locale, remaining=remaining)
                + f"\n⏰ Reset in: {hours}h {minutes}m",
                reply_markup=quota_exhausted_keyboard(),
            )
            return

        cv_repo = CVRepository(session)
        cv = await cv_repo.get_active_cv(user.id)
        if not cv:
            await callback.message.edit_text(t("cl_no_cv", locale))
            return

        is_complete, score = CoverLetterService.check_cv_completeness(cv)
        if not is_complete:
            await callback.message.edit_text(
                t("cl_cv_warning", locale, score=int(score)),
                reply_markup=cv_warning_keyboard(job_id),
            )
            return

        job_repo = JobRepository(session)
        job = await job_repo.get(uuid.UUID(job_id))
        if not job:
            await callback.message.edit_text(t("error_generic", locale))
            return

        await state.set_state(CoverLetterGeneration.generating)
        await callback.message.edit_text(t("cl_generating", locale))

        try:
            cv_text = _decrypt_cv(cv)
            cl_svc = CoverLetterService(session)
            content = await cl_svc.generate(
                user_id=user.id,
                job_id=uuid.UUID(job_id),
                cv_id=cv.id,
                job_title=job.title,
                company=job.company,
                location=job.location or "",
                job_description=job.description or "",
                cv_content=cv_text,
                user_name=user.first_name,
                tone=tone,
                length=length,
                focus=focus,
                language=language,
            )
            await quota_svc.increment_daily_used(user.id, user.subscription_tier)
            await session.commit()

            latest = await cl_svc.get_latest(user.id, uuid.UUID(job_id))
            cl_id = str(latest.id) if latest else ""

            await state.set_state(CoverLetterGeneration.displayed)
            await state.update_data(cover_letter_id=cl_id)
            await callback.message.edit_text(
                t("cl_result", locale) + "\n\n" + content,
                reply_markup=cover_letter_action_keyboard(cl_id),
            )
        except Exception as e:
            logger.exception("Cover letter generation failed: %s", e)
            await session.rollback()
            await callback.message.edit_text(
                t("cl_error", locale),
            )


@router.callback_query(F.data.startswith("cl_generate_anyway:"))
async def callback_generate_anyway(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    job_id = parts[2]
    data = await state.get_data()
    data["job_id"] = job_id
    await state.set_data(data)
    await state.set_state(CoverLetterGeneration.customizing)
    await callback_generate(callback, state)


@router.callback_query(F.data.startswith("cover_letter:regenerate:"))
async def callback_regenerate(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    cl_id = callback.data.split(":")[2]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.cover_letter_service import CoverLetterService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        quota_svc = QuotaService(session)
        has_quota = await quota_svc.has_quota(user.id, user.subscription_tier)
        if not has_quota:
            await callback.answer(
                t("cl_quota_exhausted", locale, remaining=0),
                show_alert=True,
            )
            return

        await callback.answer(t("cl_generating", locale))
        cl_svc = CoverLetterService(session)
        existing = await cl_svc.get_by_id(uuid.UUID(cl_id))
        if not existing or existing.user_id != user.id:
            await callback.message.edit_text(t("error_generic", locale))
            return

        data = await state.get_data()
        tone = data.get("tone", existing.tone)
        length = data.get("length", existing.length)
        focus = data.get("focus", existing.focus_area)
        language = data.get("language", existing.language)

        try:
            content = await cl_svc.regenerate(
                cover_letter_id=uuid.UUID(cl_id),
                user_id=user.id,
                tone=tone,
                length=length,
                focus=focus,
                language=language,
            )
            await quota_svc.increment_daily_used(user.id, user.subscription_tier)
            await session.commit()

            await callback.message.edit_text(
                t("cl_result", locale) + "\n\n" + content,
                reply_markup=cover_letter_action_keyboard(cl_id),
            )
        except Exception as e:
            logger.exception("Regeneration failed: %s", e)
            await session.rollback()
            await callback.message.edit_text(t("cl_error", locale))


@router.callback_query(F.data.startswith("cover_letter:copy:"))
async def callback_copy(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    cl_id = callback.data.split(":")[2]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.cover_letter_service import CoverLetterService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        cl_svc = CoverLetterService(session)
        record = await cl_svc.get_by_id(uuid.UUID(cl_id))
        if not record or record.user_id != user.id:
            await callback.answer(t("error_generic", locale), show_alert=True)
            return

        await callback.message.edit_text(
            f"```\n{record.content}\n```",
            parse_mode="Markdown",
            reply_markup=cover_letter_action_keyboard(cl_id),
        )
        await callback.answer(t("cl_copied", locale))


@router.callback_query(F.data == "cover_letter:wait")
async def callback_wait_for_reset(callback: CallbackQuery, state: FSMContext):
    countdown = get_midnight_countdown_seconds()
    hours = countdown // 3600
    minutes = (countdown % 3600) // 60
    await callback.answer(
        f"⏰ Reset in: {hours}h {minutes}m",
        show_alert=True,
    )


@router.callback_query(F.data.startswith("cover_letter:purchase:"))
async def callback_purchase(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    pack = callback.data.split(":")[2]

    if pack == "menu":
        await callback.message.edit_text(
            t("cl_purchase_title", locale),
            reply_markup=purchase_packs_keyboard(),
        )
        await callback.answer()
        return

    await callback.answer(t("cl_coming_soon", locale), show_alert=True)


@router.callback_query(F.data == "cl_cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    await state.clear()
    await callback.message.edit_text(t("cancel", locale))
    await callback.answer()


def _decrypt_cv(cv) -> str:
    if cv.content is None:
        return ""
    try:
        return decrypt_data(cv.content).decode("utf-8")
    except Exception:
        logger.warning("Failed to decrypt CV content for user")
        return ""
