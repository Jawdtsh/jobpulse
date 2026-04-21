import logging
import uuid
from decimal import Decimal

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from src.bot.utils.i18n import t, get_locale
from src.services.wallet_admin_service import WalletAdminService

logger = logging.getLogger(__name__)

router = Router()


def _ensure_admin(telegram_id: int) -> bool:
    return WalletAdminService.is_admin(telegram_id)


@router.message(Command("admin_panel"))
async def cmd_admin_panel(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    from src.database import get_async_session

    async for session in get_async_session():
        admin_svc = WalletAdminService(session)
        stats = await admin_svc.get_stats()
        await session.commit()

        tier_counts = stats.get("tier_counts", {})
        free_count = tier_counts.get("free", 0)
        basic_count = tier_counts.get("basic", 0)
        pro_count = tier_counts.get("pro", 0)

        lines = [
            t("admin_panel_title", locale),
            "",
            f"👥 {t('admin_total_users', locale)}: {stats['total_users']}",
            "",
            f"{t('admin_active_subs', locale)}:",
            f"  • Free: {free_count}",
            f"  • Basic: {basic_count}",
            f"  • Pro: {pro_count}",
            "",
            f"💰 {t('admin_total_revenue', locale)}: ${stats['total_topups']:.2f}",
            f"📊 {t('admin_recent_tx', locale)}: {stats['recent_transactions']}",
        ]

        from src.bot.keyboards import admin_panel_keyboard

        await message.answer(
            "\n".join(lines),
            reply_markup=admin_panel_keyboard(),
        )


@router.message(Command("admin_add_balance"))
async def cmd_admin_add_balance(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer(t("admin_add_balance_usage", locale))
        return

    try:
        user_identifier = parts[1]
        amount = Decimal(parts[2])
        reason = parts[3].strip('"').strip("'")
    except Exception:
        await message.answer(t("admin_invalid_format", locale))
        return

    if amount <= 0:
        await message.answer(t("admin_invalid_amount", locale))
        return

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService

    async for session in get_async_session():
        user_repo = UserRepository(session)

        try:
            user_id = uuid.UUID(user_identifier)
            user = await user_repo.get(user_id)
        except ValueError:
            try:
                telegram_id = int(user_identifier)
                user = await user_repo.get_by_telegram_id(telegram_id)
            except ValueError:
                await message.answer(t("admin_user_not_found", locale))
                return

        if not user:
            await message.answer(t("admin_user_not_found", locale))
            return

        wallet_svc = WalletService(session)
        try:
            wallet, tx = await wallet_svc.admin_add_balance(
                user_id=user.id,
                amount=amount,
                admin_telegram_id=message.from_user.id,
                reason=reason,
            )
            await session.commit()

            await message.answer(
                f"✅ {t('admin_balance_added', locale)}\n"
                f"💰 ${amount:.2f} → {user.first_name} ({user.telegram_id})\n"
                f"💎 {t('wallet_balance', locale)}: ${wallet.balance_usd:.2f}"
            )

            from src.services.notification_sender import send_telegram_message

            try:
                await send_telegram_message(
                    chat_id=user.telegram_id,
                    text=(
                        f"💰 {t('wallet_topup_notification', locale)}\n"
                        f"${amount:.2f}\n"
                        f"{t('wallet_balance', locale)}: ${wallet.balance_usd:.2f}"
                    ),
                )
            except Exception:
                logger.warning("Failed to notify user %s", user.id)

        except Exception as e:
            await session.rollback()
            logger.exception("Admin add balance failed: %s", e)
            await message.answer(t("error_generic", locale))


@router.message(Command("admin_deduct_balance"))
async def cmd_admin_deduct_balance(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        await message.answer(t("admin_deduct_balance_usage", locale))
        return

    try:
        user_identifier = parts[1]
        amount = Decimal(parts[2])
        reason = parts[3].strip('"').strip("'")
    except Exception:
        await message.answer(t("admin_invalid_format", locale))
        return

    if amount <= 0:
        await message.answer(t("admin_invalid_amount", locale))
        return

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.wallet_service import WalletService
    from src.services.exceptions import InsufficientBalanceError

    async for session in get_async_session():
        user_repo = UserRepository(session)

        try:
            user_id = uuid.UUID(user_identifier)
            user = await user_repo.get(user_id)
        except ValueError:
            try:
                telegram_id = int(user_identifier)
                user = await user_repo.get_by_telegram_id(telegram_id)
            except ValueError:
                await message.answer(t("admin_user_not_found", locale))
                return

        if not user:
            await message.answer(t("admin_user_not_found", locale))
            return

        wallet_svc = WalletService(session)
        try:
            wallet, tx = await wallet_svc.admin_deduct_balance(
                user_id=user.id,
                amount=amount,
                admin_telegram_id=message.from_user.id,
                reason=reason,
            )
            await session.commit()

            await message.answer(
                f"✅ {t('admin_balance_deducted', locale)}\n"
                f"💰 ${amount:.2f} ← {user.first_name} ({user.telegram_id})\n"
                f"💎 {t('wallet_balance', locale)}: ${wallet.balance_usd:.2f}"
            )

        except InsufficientBalanceError:
            await message.answer(t("admin_insufficient_balance", locale))
        except Exception as e:
            await session.rollback()
            logger.exception("Admin deduct balance failed: %s", e)
            await message.answer(t("error_generic", locale))


@router.message(Command("admin_search"))
async def cmd_admin_search(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t("admin_search_usage", locale))
        return

    query = parts[1].strip()

    from src.database import get_async_session

    async for session in get_async_session():
        admin_svc = WalletAdminService(session)

        try:
            telegram_id = int(query)
            user_info = await admin_svc.get_user_info(telegram_id)
        except ValueError:
            user_info = None

        if not user_info:
            users = await admin_svc.search_users(query)
            if not users:
                await message.answer(t("admin_user_not_found", locale))
                return
            lines = [t("admin_search_results", locale), ""]
            for u in users[:5]:
                lines.append(
                    f"👤 {u['first_name']} (@{u['username'] or 'N/A'})\n"
                    f"   ID: {u['telegram_id']} | {u['tier']} | ${u['balance']:.2f}"
                )
            await message.answer("\n".join(lines))
            return

        await session.commit()

        sub = user_info.get("active_subscription")
        sub_info = ""
        if sub:
            sub_info = (
                f"\n📅 {t('admin_subscription', locale)}: {sub.tier} (→ {sub.end_date})"
            )

        lines = [
            f"👤 {user_info['first_name']} (@{user_info['username'] or 'N/A'})",
            f"🆔 Telegram ID: {user_info['telegram_id']}",
            f"💎 {t('wallet_balance', locale)}: ${user_info['balance_usd']:.2f}",
            f"📋 {t('admin_subscription', locale)}: {user_info['subscription_tier']}",
            sub_info,
            f"📥 {t('wallet_deposited', locale)}: ${user_info['total_deposited_usd']:.2f}",
            f"📤 {t('wallet_spent', locale)}: ${user_info['total_spent_usd']:.2f}",
            f"💸 {t('wallet_withdrawn', locale)}: ${user_info['total_withdrawn_usd']:.2f}",
        ]

        from src.bot.keyboards import admin_user_actions_keyboard

        await message.answer(
            "\n".join(lines),
            reply_markup=admin_user_actions_keyboard(str(user_info["user_id"])),
        )


@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    from src.database import get_async_session

    async for session in get_async_session():
        admin_svc = WalletAdminService(session)
        stats = await admin_svc.get_stats()
        await session.commit()

        tier_counts = stats.get("tier_counts", {})

        lines = [
            t("admin_stats_title", locale),
            "",
            f"💰 {t('admin_revenue', locale)}:",
            f"  {t('admin_total_topups', locale)}: ${stats['total_topups']:.2f}",
            f"  {t('admin_total_spent', locale)}: ${stats['total_spent']:.2f}",
            f"  {t('admin_total_withdrawn', locale)}: ${stats['total_withdrawn']:.2f}",
            "",
            f"📋 {t('admin_subscriptions', locale)}:",
            f"  {t('admin_active', locale)}: {stats['active_subscriptions']}",
            f"  Basic: {tier_counts.get('basic', 0)}",
            f"  Pro: {tier_counts.get('pro', 0)}",
            "",
            f"👥 {t('admin_users', locale)}:",
            f"  {t('admin_total', locale)}: {stats['total_users']}",
            f"  {t('admin_with_balance', locale)}: {stats['users_with_balance']}",
        ]

        await message.answer("\n".join(lines))


@router.message(Command("admin_users"))
async def cmd_admin_users(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    parts = message.text.split(maxsplit=1)
    limit = 10
    if len(parts) > 1:
        try:
            limit = min(int(parts[1]), 50)
        except ValueError:
            pass

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        users = await user_repo.get_all(limit=limit)
        await session.commit()

        if not users:
            await message.answer(t("admin_no_users", locale))
            return

        lines = [f"👥 {t('admin_users', locale)} ({len(users)}):", ""]
        for u in users:
            lines.append(
                f"• {u.first_name} (@{u.username or 'N/A'}) - {u.subscription_tier}"
            )

        await message.answer("\n".join(lines))


@router.message(Command("admin_transactions"))
async def cmd_admin_transactions(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    parts = message.text.split(maxsplit=1)
    limit = 10
    if len(parts) > 1:
        try:
            limit = min(int(parts[1]), 50)
        except ValueError:
            pass

    from src.database import get_async_session

    async for session in get_async_session():
        admin_svc = WalletAdminService(session)
        transactions = await admin_svc.get_recent_transactions(limit=limit)
        await session.commit()

        if not transactions:
            await message.answer(t("admin_no_transactions", locale))
            return

        lines = [f"📊 {t('admin_transactions', locale)}:", ""]
        for tx in transactions[:10]:
            lines.append(
                f"• [{tx['type']}] ${tx['amount_usd']:.2f} - {tx['status']}\n"
                f"  {tx['description'] or ''} ({tx['created_at'][:10] if tx['created_at'] else 'N/A'})"
            )

        await message.answer("\n".join(lines))


@router.message(Command("admin_force_expire"))
async def cmd_admin_force_expire(message: Message):
    locale = get_locale(message.from_user.language_code)

    if not _ensure_admin(message.from_user.id):
        await message.answer(t("admin_permission_denied", locale))
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(t("admin_force_expire_usage", locale))
        return

    user_identifier = parts[1].strip()

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.subscription_service import SubscriptionService

    async for session in get_async_session():
        user_repo = UserRepository(session)

        try:
            user_id = uuid.UUID(user_identifier)
            user = await user_repo.get(user_id)
        except ValueError:
            try:
                telegram_id = int(user_identifier)
                user = await user_repo.get_by_telegram_id(telegram_id)
            except ValueError:
                await message.answer(t("admin_user_not_found", locale))
                return

        if not user:
            await message.answer(t("admin_user_not_found", locale))
            return

        sub_svc = SubscriptionService(session)
        expired = await sub_svc.expire_subscription(user.id)
        await session.commit()

        if expired:
            await message.answer(
                f"✅ {t('admin_subscription_expired', locale)}\n"
                f"👤 {user.first_name} ({user.telegram_id})\n"
                f"📋 {expired.tier} → free"
            )
        else:
            await message.answer(t("admin_no_active_sub", locale))


@router.callback_query(F.data.startswith("admin_add_balance:"))
async def callback_admin_add_balance(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    await callback.answer(t("admin_add_balance_usage", locale), show_alert=True)


@router.callback_query(F.data.startswith("admin_deduct_balance:"))
async def callback_admin_deduct_balance(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    await callback.answer(t("admin_deduct_balance_usage", locale), show_alert=True)


@router.callback_query(F.data.startswith("admin_tx_history:"))
async def callback_admin_tx_history(callback: CallbackQuery):
    locale = get_locale(callback.from_user.language_code)
    user_id_str = callback.data.split(":")[1]

    from src.database import get_async_session

    async for session in get_async_session():
        admin_svc = WalletAdminService(session)
        transactions = await admin_svc.get_recent_transactions(
            user_id=uuid.UUID(user_id_str), limit=10
        )
        await session.commit()

        if not transactions:
            await callback.answer(t("admin_no_transactions", locale), show_alert=True)
            return

        lines = [f"📊 {t('admin_transactions', locale)}:", ""]
        for tx in transactions[:10]:
            lines.append(f"• [{tx['type']}] ${tx['amount_usd']:.2f} - {tx['status']}")

        await callback.message.answer("\n".join(lines))
    await callback.answer()
