import logging
import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.bot.keyboards import (
    cv_list_keyboard,
    cv_details_keyboard,
    confirm_delete_keyboard,
    main_menu_keyboard,
)
from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("my_cvs"))
async def cmd_my_cvs(message: Message):
    locale = get_locale(message.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.cv_repository import CVRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            return

        cv_repo = CVRepository(session)
        cvs = await cv_repo.get_by_user_id(user.id)

        if not cvs:
            await message.answer(
                t("no_jobs", locale),
                reply_markup=main_menu_keyboard(),
            )
            return

        lines = [t("help", locale).split("\n")[0]]
        cv_data = []
        for i, cv in enumerate(cvs, 1):
            status = "✅ نشط" if cv.is_active else "⏸️ غير نشط"
            score = f"{cv.completeness_score}%" if cv.completeness_score else "N/A"
            date = cv.created_at.strftime("%Y-%m-%d") if cv.created_at else "N/A"
            lines.append(f"{i}. {cv.title} - {status} - {score} - {date}")
            cv_data.append(
                {
                    "id": str(cv.id),
                    "title": cv.title,
                    "is_active": cv.is_active,
                    "score": score,
                    "date": date,
                }
            )

        await message.answer(
            "\n".join(lines),
            reply_markup=cv_list_keyboard(cv_data),
        )


@router.callback_query(F.data.startswith("cv_details:"))
async def callback_cv_details(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    cv_id = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.cv_repository import CVRepository

    async for session in get_async_session():
        cv_repo = CVRepository(session)
        cv = await cv_repo.get(uuid.UUID(cv_id))

        if not cv or cv.deleted_at:
            await callback.answer(t("error_generic", locale), show_alert=True)
            return

        lines = [
            f"📄 {cv.title}",
            f"Status: {'✅ Active' if cv.is_active else '⏸️ Inactive'}",
        ]
        if cv.completeness_score:
            lines.append(f"Score: {cv.completeness_score}%")
        if cv.skills:
            lines.append(f"Skills: {', '.join(cv.skills[:10])}")
        if cv.experience_summary:
            lines.append(f"Experience: {cv.experience_summary}")
        if cv.improvement_suggestions:
            lines.append(f"Suggestions: {'; '.join(cv.improvement_suggestions[:5])}")

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=cv_details_keyboard(cv_id, cv.is_active),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("activate_cv:"))
async def callback_activate_cv(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    cv_id = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.cv_repository import CVRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        cv_repo = CVRepository(session)
        cv = await cv_repo.set_active_cv(uuid.UUID(cv_id), user.id)
        await session.commit()

        if cv:
            await callback.message.edit_text(
                t("cv_activated", locale),
                reply_markup=cv_details_keyboard(cv_id, True),
            )
        else:
            await callback.answer(t("error_generic", locale), show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("delete_cv:"))
async def callback_delete_cv(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    cv_id = callback.data.split(":")[1]

    await callback.message.edit_text(
        t("cv_delete_confirm", locale),
        reply_markup=confirm_delete_keyboard(cv_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def callback_confirm_delete(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    parts = callback.data.split(":")
    cv_id = parts[1]
    answer = parts[2] if len(parts) > 2 else "no"

    if answer != "yes":
        await callback.message.edit_text(t("cancel", locale))
        await callback.answer()
        return

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.cv_repository import CVRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        cv_repo = CVRepository(session)
        cv = await cv_repo.get(uuid.UUID(cv_id))
        was_active = cv.is_active if cv else False

        await cv_repo.soft_delete_cv(uuid.UUID(cv_id), user.id)
        await session.commit()

        remaining_cvs = await cv_repo.get_by_user_id(user.id)

        messages = [t("cv_deleted", locale)]
        if was_active and not remaining_cvs:
            messages.append(t("cv_no_active_prompt", locale))
        elif was_active and remaining_cvs:
            inactive = [
                c for c in remaining_cvs if not c.is_active and not c.deleted_at
            ]
            if inactive:
                messages.append(t("cv_activate_replacement", locale))

        await callback.message.edit_text(
            "\n".join(messages),
            reply_markup=main_menu_keyboard(),
        )

    await callback.answer()


@router.callback_query(F.data == "back_to_cvs")
async def callback_back_to_cvs(callback: CallbackQuery):
    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.cv_repository import CVRepository

    locale = get_locale(callback.from_user.language_code)

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        cv_repo = CVRepository(session)
        cvs = await cv_repo.get_by_user_id(user.id)

        cv_data = [
            {"id": str(cv.id), "title": cv.title, "is_active": cv.is_active}
            for cv in cvs
        ]
        await callback.message.edit_text(
            "📁 " + t("help", locale).split("\n")[0],
            reply_markup=cv_list_keyboard(cv_data),
        )

    await callback.answer()
