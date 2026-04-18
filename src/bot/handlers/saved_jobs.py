import logging
import uuid
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import (
    saved_jobs_view_keyboard,
)
from src.bot.states import MyJobsState
from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()

JOBS_PER_PAGE = 5


@router.message(Command("my_jobs"))
async def cmd_my_jobs(message: Message, state: FSMContext):
    locale = get_locale(message.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            return

    await state.set_state(MyJobsState.browsing)
    await state.update_data(view="saved", page=1, sim_filter="all", date_filter="all")

    await _render_jobs_list(
        message, user.id, "saved", 1, "all", "all", locale, state, edit=False
    )


@router.callback_query(F.data.startswith("view:"))
async def callback_switch_view(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    view = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

    await state.update_data(view=view, page=1)
    data = await state.get_data()
    await _render_jobs_list(
        callback.message,
        user.id,
        view,
        1,
        data.get("sim_filter", "all"),
        data.get("date_filter", "all"),
        locale,
        state,
        edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("jobs_page:"))
async def callback_jobs_page(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    parts = callback.data.split(":")
    view = parts[1]
    page = int(parts[2])

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

    await state.update_data(view=view, page=page)
    data = await state.get_data()
    await _render_jobs_list(
        callback.message,
        user.id,
        view,
        page,
        data.get("sim_filter", "all"),
        data.get("date_filter", "all"),
        locale,
        state,
        edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_sim:"))
async def callback_filter_similarity(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    value = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

    await state.update_data(sim_filter=value, page=1)
    data = await state.get_data()
    await _render_jobs_list(
        callback.message,
        user.id,
        data.get("view", "saved"),
        1,
        value,
        data.get("date_filter", "all"),
        locale,
        state,
        edit=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("filter_date:"))
async def callback_filter_date(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    value = callback.data.split(":")[1]

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            return

    await state.update_data(date_filter=value, page=1)
    data = await state.get_data()
    await _render_jobs_list(
        callback.message,
        user.id,
        data.get("view", "saved"),
        1,
        data.get("sim_filter", "all"),
        value,
        locale,
        state,
        edit=True,
    )
    await callback.answer()


async def _render_jobs_list(
    message,
    user_id: uuid.UUID,
    view: str,
    page: int,
    sim_filter: str,
    date_filter: str,
    locale: str,
    state: FSMContext,
    edit: bool = False,
):
    from src.database import get_async_session
    from src.repositories.match_repository import MatchRepository
    from src.services.saved_job_service import SavedJobService

    skip = (page - 1) * JOBS_PER_PAGE
    lines = []
    job_items = []

    async for session in get_async_session():
        if view == "saved":
            svc = SavedJobService(session)
            saved_jobs = await svc.get_saved_jobs(
                user_id, skip=skip, limit=JOBS_PER_PAGE
            )
            for sj in saved_jobs:
                job = sj.job
                if not job:
                    continue
                rel_time = _relative_time(sj.saved_at)
                lines.append(f"💼 {job.title} @ {job.company}\n   📊 N/A | {rel_time}")
                job_items.append((str(job.id), False))
        elif view == "notified":
            match_repo = MatchRepository(session)
            all_matches = await match_repo.get_notified_matches_by_user(
                user_id, skip=skip, limit=JOBS_PER_PAGE, exclude_dismissed=True
            )
            for m in all_matches:
                job = m.job
                if not job:
                    continue
                score = f"{m.similarity_score:.0%}"
                rel_time = _relative_time(m.notified_at) if m.notified_at else ""
                lines.append(
                    f"💼 {job.title} @ {job.company}\n   📊 {score} | {rel_time}"
                )
                job_items.append((str(job.id), False))
        elif view == "dismissed":
            match_repo = MatchRepository(session)
            from sqlalchemy import select, func
            from src.models.job_match import JobMatch

            stmt = (
                select(func.count())
                .select_from(JobMatch)
                .where(
                    JobMatch.user_id == user_id,
                    JobMatch.is_dismissed.is_(True),
                )
            )
            await session.execute(stmt)

            stmt = (
                select(JobMatch)
                .where(
                    JobMatch.user_id == user_id,
                    JobMatch.is_dismissed.is_(True),
                )
                .order_by(JobMatch.notified_at.desc())
                .offset(skip)
                .limit(JOBS_PER_PAGE)
            )
            result = await session.execute(stmt)
            dismissed = list(result.scalars().all())
            for m in dismissed:
                job = m.job
                if not job:
                    continue
                score = f"{m.similarity_score:.0%}"
                lines.append(f"💼 {job.title} @ {job.company} | 📊 {score}")
                job_items.append((str(job.id), False))

    if not lines:
        text = t("no_jobs", locale) + f"\n({view})"
        kb = saved_jobs_view_keyboard()
    else:
        view_names = {
            "saved": "💾 المحفوظة",
            "notified": "📋 الإشعارات",
            "dismissed": "🗑️ المتجاهلة",
        }
        text = f"{view_names.get(view, view)} - {locale}\n\n" + "\n\n".join(lines)
        kb = saved_jobs_view_keyboard()

    send_fn = message.edit_text if edit else message.answer
    try:
        await send_fn(text, reply_markup=kb)
    except Exception as e:
        logger.debug("Failed to edit message, falling back to answer: %s", e)
        await message.answer(text, reply_markup=kb)


def _relative_time(dt: datetime) -> str:
    if not dt:
        return ""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "الآن (now)"
    minutes = seconds // 60
    if minutes < 60:
        return f"منذ {minutes}د ({minutes}m ago)"
    hours = minutes // 60
    if hours < 24:
        return f"منذ {hours}س ({hours}h ago)"
    days = hours // 24
    return f"منذ {days}ي ({days}d ago)"
