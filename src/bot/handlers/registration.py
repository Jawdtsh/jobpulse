import logging

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import main_menu_keyboard
from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    args = message.text.split()[1:] if message.text else []
    referral_param = None
    if args and args[0].startswith("ref_"):
        referral_param = args[0][4:]

    locale = get_locale(message.from_user.language_code)

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)

        if user is None:
            referred_by = None
            if referral_param:
                referrer = await user_repo.get_by_referral_code(referral_param)
                if referrer:
                    referred_by = referrer.id

            user = await user_repo.create_user(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name or "User",
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                referred_by=referred_by,
            )
            await session.commit()

            if referred_by:
                try:
                    from src.repositories.referral_reward_repository import (
                        ReferralRewardRepository,
                    )
                    from datetime import datetime, timezone, timedelta

                    reward_repo = ReferralRewardRepository(session)
                    await reward_repo.create(
                        referrer_id=referred_by,
                        referred_user_id=user.id,
                        reward_type="signup_credit",
                        reward_value=1,
                        status="pending",
                        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                    )
                    await session.commit()
                except Exception:
                    logger.exception("Failed to track referral")

            welcome = t(
                "welcome",
                locale,
                first_name=user.first_name,
                tier=user.subscription_tier.title(),
            )
            await message.answer(welcome, reply_markup=main_menu_keyboard())
        else:
            welcome = t(
                "welcome_back",
                locale,
                first_name=user.first_name,
                tier=user.subscription_tier.title(),
            )
            await message.answer(welcome, reply_markup=main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    locale = get_locale(message.from_user.language_code)
    help_text = t("help", locale)
    await message.answer(help_text)


@router.callback_query(F.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    locale = get_locale(callback.from_user.language_code)
    await callback.message.edit_text(
        t(
            "welcome_back",
            locale,
            first_name=callback.from_user.first_name or "User",
            tier="Free",
        ),
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("menu:"))
async def callback_menu_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "upload_cv":
        from src.bot.handlers.cv_upload import cmd_upload_cv

        message_stub = callback.message
        message_stub.from_user = callback.from_user
        message_stub.text = "/upload_cv"
        await cmd_upload_cv(message_stub, state)
        await callback.answer()
    elif action == "my_jobs":
        from src.bot.handlers.saved_jobs import cmd_my_jobs

        message_stub = callback.message
        message_stub.from_user = callback.from_user
        message_stub.text = "/my_jobs"
        await cmd_my_jobs(message_stub, state)
        await callback.answer()
    elif action == "invite":
        from src.bot.handlers.referral import cmd_invite

        message_stub = callback.message
        message_stub.from_user = callback.from_user
        message_stub.text = "/invite"
        await cmd_invite(message_stub)
        await callback.answer()
    elif action == "settings":
        from src.bot.handlers.settings import cmd_settings

        message_stub = callback.message
        message_stub.from_user = callback.from_user
        message_stub.text = "/settings"
        await cmd_settings(message_stub)
        await callback.answer()
    else:
        await callback.answer(
            t("coming_soon", get_locale(callback.from_user.language_code))
        )
