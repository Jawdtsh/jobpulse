import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("search_history"))
async def cmd_search_history(message: Message):
    args = message.text.split()[1:] if message.text else []

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    user = None
    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        break

    if not user:
        await message.answer("You are not registered. Please /start first.")
        return

    if user.subscription_tier.lower() != "pro":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Upgrade to Pro", callback_data="upgrade:pro"
                    )
                ]
            ]
        )
        await message.answer(
            "This feature is Pro-only. Upgrade to access historical search.",
            reply_markup=kb,
        )
        return

    if not args:
        await message.answer("Usage: /search_history <days 1-7>")
        return

    try:
        days = int(args[0])
    except ValueError:
        await message.answer("Please provide a number (1-7).")
        return

    if not 1 <= days <= 7:
        await message.answer("Days must be between 1 and 7.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Yes", callback_data=f"hist:{days}:yes"),
                InlineKeyboardButton(text="No", callback_data=f"hist:{days}:no"),
            ]
        ]
    )
    await message.answer("Re-send jobs you already received?", reply_markup=kb)


@router.callback_query(F.data.startswith("hist:"))
async def handle_history_callback(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid callback")
        return

    days = int(parts[1])
    resend = parts[2] == "yes"

    await callback.answer("Searching historical jobs...")
    await callback.message.edit_text(f"Searching last {days} days...")

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.matching_service import MatchingService

    results = []
    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.message.edit_text(
                "You are not registered. Please /start first."
            )
            return

        svc = MatchingService(session)
        try:
            results = await svc.match_historical(user.id, days, resend)
            await session.commit()
        except Exception as e:
            await session.rollback()
            await callback.message.edit_text(f"Error: {e}")
            return

    await callback.message.edit_text(
        f"Historical search complete. Found {len(results)} matches."
    )


@router.message(Command("my_jobs"))
async def cmd_my_jobs(message: Message):
    from src.database import get_async_session
    from src.repositories.match_repository import MatchRepository
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("You are not registered. Please /start first.")
            return

        match_repo = MatchRepository(session)
        matches = await match_repo.get_notified_matches_by_user(user.id, limit=10)

        if not matches:
            await message.answer("No job matches yet.")
            return

        lines = ["📋 Your recent job matches:\n"]
        for m in matches:
            score = f"{m.similarity_score:.0%}"
            status = "✓ Clicked" if m.is_clicked else "○ New"
            date = m.notified_at.strftime("%Y-%m-%d") if m.notified_at else "N/A"

            job_title = "Unknown"
            if m.job:
                job_title = m.job.title
            lines.append(f"{status} {job_title} ({score}) - {date}")

        await message.answer("\n".join(lines))


@router.message(Command("set_threshold"))
async def cmd_set_threshold(message: Message):
    args = message.text.split()[1:] if message.text else []
    if not args:
        await message.answer("Usage: /set_threshold <0.60-1.00>")
        return

    try:
        threshold = float(args[0])
    except ValueError:
        await message.answer("Please provide a number between 0.60 and 1.00.")
        return

    if not 0.60 <= threshold <= 1.00:
        await message.answer("Threshold must be between 0.60 and 1.00.")
        return

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.services.threshold_service import ThresholdService

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("You are not registered. Please /start first.")
            return

        svc = ThresholdService(session)
        await svc.set_user_threshold(user.id, threshold)
        await session.commit()
        await message.answer(f"Similarity threshold set to {threshold:.2f}")


@router.callback_query(F.data.startswith("view:"))
async def handle_view_details(callback: CallbackQuery):
    job_id = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.match_repository import MatchRepository
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Not registered")
            return

        match_repo = MatchRepository(session)
        matches = await match_repo.get_matches_by_user(user.id)
        for m in matches:
            if str(m.job_id) == job_id and not m.is_clicked:
                await match_repo.mark_clicked(m.id)
                await session.commit()
                break

    await callback.answer("Viewing details...")


@router.callback_query(F.data.startswith("cover:"))
async def handle_cover_letter(callback: CallbackQuery):
    await callback.answer("Cover letter generation coming soon!")
