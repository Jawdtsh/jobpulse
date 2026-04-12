import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.job_match import JobMatch
from src.repositories.match_repository import MatchRepository
from src.repositories.job_repository import JobRepository
from src.repositories.user_repository import UserRepository
from src.services.notification_queue import NotificationQueue
from config.settings import get_settings

logger = logging.getLogger(__name__)

TIER_FREE = "free"
TIER_BASIC = "basic"
TIER_PRO = "pro"


class NotificationService:
    def __init__(self, session: AsyncSession, queue: NotificationQueue | None = None):
        self._session = session
        self._match_repo = MatchRepository(session)
        self._job_repo = JobRepository(session)
        self._user_repo = UserRepository(session)
        self._queue = queue or NotificationQueue()

    async def queue_match_notification(self, match_id: uuid.UUID) -> None:
        match = await self._match_repo.get(match_id)
        if not match:
            return

        user = await self._user_repo.get(match.user_id)
        if not user:
            return

        job = await self._job_repo.get(match.job_id)
        if not job:
            return

        tier = getattr(user, "subscription_tier", TIER_FREE)
        delay = self._get_tier_delay(tier)
        notification_time = job.created_at + timedelta(seconds=delay)

        await self._queue.enqueue(
            match_id=str(match.id),
            user_id=str(user.id),
            job_id=str(job.id),
            cv_id=str(match.cv_id) if match.cv_id else None,
            tier=tier,
            notification_time=notification_time,
        )
        logger.info(
            "Queued notification match=%s tier=%s at=%s",
            match_id,
            tier,
            notification_time,
        )

    async def queue_match_immediate(self, match_id: uuid.UUID) -> None:
        match = await self._match_repo.get(match_id)
        if not match:
            return

        user = await self._user_repo.get(match.user_id)
        if not user:
            return

        tier = getattr(user, "subscription_tier", TIER_FREE)
        now = datetime.now(timezone.utc)

        await self._queue.enqueue(
            match_id=str(match.id),
            user_id=str(user.id),
            job_id=str(match.job_id),
            cv_id=str(match.cv_id) if match.cv_id else None,
            tier=tier,
            notification_time=now,
        )

    async def process_due_notifications(self) -> int:
        due_items = await self._queue.fetch_due()
        if not due_items:
            return 0

        sent = 0
        user_matches: dict[str, list[dict]] = {}
        for item in due_items:
            uid = item["user_id"]
            user_matches.setdefault(uid, []).append(item)

        for uid, items in user_matches.items():
            for item in items:
                try:
                    match = await self._match_repo.get(uuid.UUID(item["match_id"]))
                    if match:
                        await self._send_telegram_notification(match, item)
                        await self._queue.remove(item)
                        sent += 1
                except Exception as e:
                    logger.error("Failed to send notification: %s", e)
                    try:
                        await self._queue.remove(item)
                    except Exception:
                        pass

        return sent

    async def _send_telegram_notification(
        self, match: JobMatch, queue_data: dict
    ) -> None:
        job = await self._job_repo.get(match.job_id)
        if not job:
            logger.warning("Job %s not found for notification", match.job_id)
            return

        user = await self._user_repo.get(match.user_id)
        if not user:
            return

        all_user_cvs = await self._match_repo.get_unnotified_matches(match.user_id)
        cv_matches_for_job = [m for m in all_user_cvs if m.job_id == match.job_id]

        score_text = f"{match.similarity_score:.0%}"

        if len(cv_matches_for_job) > 1:
            parts = []
            for m in cv_matches_for_job:
                cv_name = "CV"
                if m.cv_id:
                    cv = await self._session.get(
                        __import__("src.models.user_cv", fromlist=["UserCV"]).UserCV,
                        m.cv_id,
                    )
                    if cv:
                        cv_name = cv.title
                parts.append(f"{cv_name}: {m.similarity_score:.0%}")
            score_text = ", ".join(parts)

        message = (
            f"🔔 New Job Match!\n\n"
            f"📊 Match: {score_text}\n"
            f"💼 {job.title}\n"
            f"🏢 {job.company}\n"
        )
        if job.salary_min and job.salary_max:
            message += f"💰 {job.salary_min}-{job.salary_max} {job.salary_currency}\n"
        if job.location:
            message += f"📍 {job.location}\n"

        from src.services.notification_sender import send_telegram_message

        await send_telegram_message(
            chat_id=user.telegram_id,
            text=message,
            job_id=str(job.id),
            cv_id=str(match.cv_id) if match.cv_id else None,
        )

        await self._match_repo.mark_notified(match.id)
        logger.info("Notification sent match=%s user=%s", match.id, match.user_id)

    async def cancel_notifications_for_cv(self, cv_id: uuid.UUID) -> int:
        pending = await self._match_repo.get_pending_by_cv(cv_id)
        removed = await self._queue.remove_by_cv(str(cv_id))
        for match in pending:
            await self._session.delete(match)
        await self._session.flush()
        return removed

    async def handle_tier_upgrade(self, user_id: uuid.UUID, new_tier: str) -> int:
        return await self._queue.update_score_by_user(str(user_id), new_tier)

    @staticmethod
    def _get_tier_delay(tier: str) -> int:
        settings = get_settings()
        delays = {
            "free": settings.matching.tier_delay_free,
            "basic": settings.matching.tier_delay_basic,
            "pro": settings.matching.tier_delay_pro,
        }
        return delays.get(tier, settings.matching.tier_delay_free)
