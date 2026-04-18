import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.bot.keyboards import referral_keyboard
from src.bot.utils.i18n import t, get_locale
from config.settings import get_settings

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("invite"))
async def cmd_invite(message: Message):
    locale = get_locale(message.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from sqlalchemy import func, select
    from src.models.referral_reward import ReferralReward

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            return

        bot_username = get_settings().telegram.bot_username or message.bot.username
        link = f"https://t.me/{bot_username}?start=ref_{user.referral_code}"

        stmt_total = (
            select(func.count())
            .select_from(ReferralReward)
            .where(ReferralReward.referrer_id == user.id)
        )
        result = await session.execute(stmt_total)
        total_invited = result.scalar_one()

        stmt_registered = (
            select(func.count())
            .select_from(ReferralReward)
            .where(
                ReferralReward.referrer_id == user.id,
                ReferralReward.status == "completed",
            )
        )
        result = await session.execute(stmt_registered)
        registered = result.scalar_one()

        text = t("referral_title", locale, link=link)
        text += "\n\n" + t(
            "referral_stats",
            locale,
            total=total_invited,
            registered=registered,
        )

        await message.answer(
            text,
            reply_markup=referral_keyboard(user.referral_code, bot_username),
        )
