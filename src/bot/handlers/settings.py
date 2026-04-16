import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.bot.keyboards import settings_keyboard
from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    locale = get_locale(message.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.threshold_service import ThresholdService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            return

        threshold_svc = ThresholdService(session)
        threshold = await threshold_svc.get_effective_threshold(user.id)
        threshold_pct = int(threshold * 100)

        from sqlalchemy import select
        from src.models.user_preferences import UserPreferences

        stmt = select(UserPreferences).where(UserPreferences.user_id == user.id)
        result = await session.execute(stmt)
        prefs = result.scalar_one_or_none()
        notifications_on = prefs.notification_enabled if prefs else True

        notif_text = "✅ مفعل (Enabled)" if notifications_on else "❌ معطل (Disabled)"

        text = t(
            "settings_display",
            locale,
            threshold=threshold_pct,
            notifications=notif_text,
            language="العربية" if locale == "ar" else "English",
            tier=user.subscription_tier.title(),
            referral_code=user.referral_code,
        )

        await message.answer(
            text,
            reply_markup=settings_keyboard(threshold_pct, notifications_on),
        )


@router.callback_query(F.data.startswith("threshold:"))
async def callback_set_threshold(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    value = int(callback.data.split(":")[1])
    threshold = value / 100.0

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.threshold_service import ThresholdService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        svc = ThresholdService(session)
        await svc.set_user_threshold(user.id, threshold)
        await session.commit()

        await callback.message.edit_text(
            t("threshold_set", locale, value=value),
        )
        await callback.answer("✅")

    message = callback.message
    message.from_user = callback.from_user
    await cmd_settings(message)


@router.callback_query(F.data == "toggle_notifications")
async def callback_toggle_notifications(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from sqlalchemy import select
    from src.models.user_preferences import UserPreferences

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        stmt = select(UserPreferences).where(UserPreferences.user_id == user.id)
        result = await session.execute(stmt)
        prefs = result.scalar_one_or_none()

        if prefs:
            prefs.notification_enabled = not prefs.notification_enabled
            new_state = prefs.notification_enabled
        else:
            new_state = True
            prefs = UserPreferences(
                user_id=user.id,
                notification_enabled=True,
            )
            session.add(prefs)

        await session.commit()

    msg_text = t("notifications_on" if new_state else "notifications_off", locale)
    await callback.answer(msg_text, show_alert=False)

    message = callback.message
    message.from_user = callback.from_user
    await cmd_settings(message)


@router.callback_query(F.data == "copy_referral")
async def callback_copy_referral(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        await callback.answer(
            t("referral_code", locale, code=user.referral_code),
            show_alert=True,
        )


@router.callback_query(F.data == "share_referral")
async def callback_share_referral(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        link = f"https://t.me/jobpulse_bot?start=ref_{user.referral_code}"
        await callback.answer(
            t("referral_title", locale, link=link),
            show_alert=True,
        )


@router.callback_query(F.data.startswith("upgrade_plan:"))
async def callback_upgrade_plan(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    tier = callback.data.split(":")[1]

    if tier == "current":
        await callback.answer(t("coming_soon", locale))
        return

    await callback.answer(t("coming_soon", locale))


@router.callback_query(F.data == "back_to_settings")
async def callback_back_to_settings(callback: CallbackQuery):
    message = callback.message
    message.from_user = callback.from_user
    await cmd_settings(message)
    await callback.answer()
