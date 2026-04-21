import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.bot.keyboards import subscription_keyboard, subscription_confirm_keyboard
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

        from src.services.wallet_service import WalletService

        wallet_svc = WalletService(session)
        wallet = await wallet_svc.get_or_create_wallet(user.id)
        await session.commit()

        tiers_info = [
            ("free", "subscribe_free"),
            ("basic", "subscribe_basic"),
            ("pro", "subscribe_pro"),
        ]
        lines = [
            t("subscribe_title", locale, current_tier=tier_name),
            "",
            f"💰 {t('wallet_balance', locale)}: ${wallet.balance_usd:.2f}",
            "",
        ]
        for tier_key, msg_key in tiers_info:
            text = t(msg_key, locale)
            if tier == tier_key:
                text = "📌 " + text
            lines.extend([text, ""])
        lines.pop()

        await message.answer(
            "\n".join(lines),
            reply_markup=subscription_keyboard(tier),
        )


@router.callback_query(F.data.startswith("subscribe:"))
async def callback_subscribe_tier(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    tier_id = callback.data.split(":")[1]

    if tier_id in ("back", "current"):
        await callback.answer()
        return

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService
    from src.services.subscription_service import SubscriptionService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        sub_svc = SubscriptionService(session)
        tier_config = sub_svc.get_tier_config(tier_id)
        if not tier_config:
            await callback.answer(t("error_generic", locale), show_alert=True)
            return

        wallet_svc = WalletService(session)
        wallet = await wallet_svc.get_or_create_wallet(user.id)
        await session.commit()

        price = tier_config["price_usd"]
        new_balance = float(wallet.balance_usd) - price

        tier_name = tier_config.get(
            f"name_{locale}", tier_config.get("name_en", tier_id)
        )
        lines = [
            t("subscribe_confirm_title", locale),
            "",
            f"📋 {tier_name}",
            f"💰 ${price:.2f}/{t('subscribe_month', locale)}",
            f"💎 {t('wallet_balance', locale)}: ${wallet.balance_usd:.2f}",
            f"{'✅' if new_balance >= 0 else '❌'} {t('subscribe_new_balance', locale)}: ${new_balance:.2f}",
        ]

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=subscription_confirm_keyboard(tier_id),
        )
    await callback.answer()


@router.callback_query(F.data == "confirm:yes")
async def callback_confirm_purchase(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService
    from src.services.subscription_service import SubscriptionService
    from src.services.exceptions import InsufficientBalanceError, WalletError

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        wallet_svc = WalletService(session)
        sub_svc = SubscriptionService(session)

        active_sub = await sub_svc.get_active_subscription(user.id)
        if active_sub:
            tier_id = active_sub.tier
        else:
            tier_id = "basic"

        tier_config = sub_svc.get_tier_config(tier_id)

        try:
            subscription = await sub_svc.purchase_tier(
                user_id=user.id,
                tier_id=tier_id,
                wallet_service=wallet_svc,
            )
            await session.commit()

            tier_name = (
                tier_config.get(f"name_{locale}", tier_config.get("name_en", tier_id))
                if tier_config
                else tier_id
            )

            await callback.message.edit_text(
                f"✅ {t('subscribe_success', locale)}\n\n"
                f"🎉 {t('subscribe_activated', locale, tier=tier_name)}\n"
                f"📅 {t('subscribe_expires', locale)}: {subscription.end_date}",
                reply_markup=subscription_back_keyboard(),
            )
        except InsufficientBalanceError:
            wallet = await wallet_svc.get_or_create_wallet(user.id)
            await session.commit()

            from src.bot.keyboards import wallet_top_up_keyboard

            needed = (
                tier_config["price_usd"] - float(wallet.balance_usd)
                if tier_config
                else 0
            )
            await callback.message.edit_text(
                f"❌ {t('subscribe_insufficient', locale)}\n\n"
                f"{t('subscribe_need_more', locale, amount=f'{needed:.2f}')}\n"
                f"{t('wallet_balance', locale)}: ${wallet.balance_usd:.2f}",
                reply_markup=wallet_top_up_keyboard(),
            )
        except WalletError as e:
            await callback.message.edit_text(f"❌ {e.message}")
        except Exception as e:
            logger.exception("Purchase failed: %s", e)
            await callback.message.edit_text(t("error_generic", locale))


@router.callback_query(F.data == "confirm:no")
async def callback_cancel_purchase(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    await callback.message.edit_text(t("cancel", locale))
    await callback.answer()


def subscription_back_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 القائمة (Menu)", callback_data="back_to_menu")
    return builder.as_markup()


@router.callback_query(F.data.startswith("upgrade_plan:"))
async def callback_upgrade(callback: CallbackQuery):
    tier_id = callback.data.split(":")[1]
    if tier_id == "current":
        await callback.answer()
        return
    await callback_subscribe_tier(callback)
