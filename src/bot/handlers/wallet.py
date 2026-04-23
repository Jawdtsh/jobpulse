import json
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()

PAYMENT_METHODS_PATH = (
    Path(__file__).parent.parent.parent.parent / "config" / "payment_methods.json"
)


def _load_payment_methods() -> list[dict]:
    try:
        with open(PAYMENT_METHODS_PATH, encoding="utf-8") as f:
            return json.load(f).get("methods", [])
    except FileNotFoundError:
        return []


@router.message(Command("wallet"))
async def cmd_wallet(message: Message):
    locale = get_locale(message.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            return

        wallet_svc = WalletService(session)
        wallet = await wallet_svc.get_or_create_wallet(user.id)
        await session.commit()

        from src.bot.keyboards import wallet_keyboard

        balance = wallet.balance_usd
        deposited = wallet.total_deposited_usd
        spent = wallet.total_spent_usd
        withdrawn = wallet.total_withdrawn_usd

        lines = [
            t("wallet_title", locale),
            "",
            f"💰 {t('wallet_balance', locale)}: ${balance:.2f}",
            f"📥 {t('wallet_deposited', locale)}: ${deposited:.2f}",
        ]
        if spent > 0:
            lines.append(f"📤 {t('wallet_spent', locale)}: ${spent:.2f}")
        if withdrawn > 0:
            lines.append(f"💸 {t('wallet_withdrawn', locale)}: ${withdrawn:.2f}")

        await message.answer(
            "\n".join(lines),
            reply_markup=wallet_keyboard(),
        )


@router.callback_query(F.data == "wallet:top_up")
async def callback_top_up(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    methods = _load_payment_methods()

    if not methods:
        await callback.answer(t("error_generic", locale), show_alert=True)
        return

    from config.settings import get_settings

    settings = get_settings()
    admin_contact = settings.wallet.admin_contact

    lines = [t("wallet_choose_payment", locale), ""]
    for method in methods:
        name = method.get(f"name_{locale}", method.get("name_en", method["id"]))
        lines.append(f"• {name}")

    lines.append("")
    lines.append(t("wallet_contact_admin", locale, admin_contact=admin_contact))

    from src.bot.keyboards import wallet_back_keyboard

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=wallet_back_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "wallet:withdraw")
async def callback_withdraw(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    methods = _load_payment_methods()

    lines = [t("wallet_withdraw_title", locale), ""]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        wallet_svc = WalletService(session)
        wallet = await wallet_svc.get_or_create_wallet(user.id)
        await session.commit()

        lines.append(f"{t('wallet_balance', locale)}: ${wallet.balance_usd:.2f}")
        lines.append("")
        lines.append(t("wallet_withdraw_instructions", locale))

        for method in methods:
            name = method.get(f"name_{locale}", method.get("name_en", method["id"]))
            lines.append(f"• {name}")

        lines.append("")
        lines.append(t("wallet_contact_admin_withdraw", locale))

    from src.bot.keyboards import wallet_back_keyboard

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=wallet_back_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "wallet:back")
async def callback_wallet_back(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

        wallet_svc = WalletService(session)
        wallet = await wallet_svc.get_or_create_wallet(user.id)
        await session.commit()

        from src.bot.keyboards import wallet_keyboard

        balance = wallet.balance_usd
        deposited = wallet.total_deposited_usd
        spent = wallet.total_spent_usd
        withdrawn = wallet.total_withdrawn_usd

        lines = [
            t("wallet_title", locale),
            "",
            f"💰 {t('wallet_balance', locale)}: ${balance:.2f}",
            f"📥 {t('wallet_deposited', locale)}: ${deposited:.2f}",
        ]
        if spent > 0:
            lines.append(f"📤 {t('wallet_spent', locale)}: ${spent:.2f}")
        if withdrawn > 0:
            lines.append(f"💸 {t('wallet_withdrawn', locale)}: ${withdrawn:.2f}")

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=wallet_keyboard(),
        )
    await callback.answer()
