import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.bot.keyboards import subscription_keyboard
from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    locale = get_locale(message.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            return

        tier = user.subscription_tier.lower()
        tier_name = tier.title()

        lines = [t("subscribe_title", locale, current_tier=tier_name)]
        lines.append("")
        lines.append(
            t("subscribe_free" if tier == "free" else "subscribe_free", locale)
        )
        if tier == "free":
            lines[3] = "📌 " + lines[3]
        lines.append("")
        lines.append(t("subscribe_basic", locale))
        if tier == "basic":
            lines[5] = "📌 " + lines[5]
        lines.append("")
        lines.append(t("subscribe_pro", locale))
        if tier == "pro":
            lines[7] = "📌 " + lines[7]

        await message.answer(
            "\n".join(lines),
            reply_markup=subscription_keyboard(tier),
        )


@router.callback_query(F.data.startswith("upgrade_plan:"))
async def callback_upgrade(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    await callback.answer(t("coming_soon", locale))
