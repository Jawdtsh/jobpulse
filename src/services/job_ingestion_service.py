import logging
import time
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    FloodWaitError,
)

from config.settings import get_settings
from src.repositories.channel_repository import ChannelRepository
from src.repositories.job_repository import JobRepository
from src.repositories.spam_rule_repository import SpamRuleRepository
from src.repositories.telegram_session_repository import TelegramSessionRepository
from src.services.admin_alert_service import AdminAlertService
from src.services.exceptions import (
    ChannelInaccessibleError,
    DailyLimitReachedError,
    SessionExhaustedError,
)
from src.services.job_filter_service import JobFilterService
from src.services.telegram_scraper_service import TelegramScraperService
from src.utils.content_hasher import compute_content_hash

logger = logging.getLogger(__name__)

_PIPELINE_LOCK_KEY = "pipeline:lock"
_PIPELINE_LOCK_TTL = 180


class JobIngestionService:
    def __init__(
        self,
        session: AsyncSession,
        filter_service: Optional[JobFilterService] = None,
        scraper_service: Optional[TelegramScraperService] = None,
        classifier_service=None,
        extractor_service=None,
        embedding_service=None,
    ) -> None:
        self._session = session
        self._spam_rule_repo = SpamRuleRepository(session)
        self._filter = filter_service or JobFilterService(self._spam_rule_repo)
        self._scraper = scraper_service or TelegramScraperService()
        self._classifier = classifier_service
        self._extractor = extractor_service
        self._embedder = embedding_service
        self._channel_repo = ChannelRepository(session)
        self._session_repo = TelegramSessionRepository(session)
        self._job_repo = JobRepository(session)
        self._errors: list[dict] = []
        self._alert_service: Optional[AdminAlertService] = None
        self._redis: Optional[aioredis.Redis] = None

    def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            settings = get_settings()
            self._redis = aioredis.from_url(
                settings.redis.redis_url, decode_responses=True
            )
        return self._redis

    async def run_pipeline(self) -> dict:
        start = time.time()
        metrics = self._init_metrics()
        redis = self._get_redis()
        acquired = await redis.set(
            _PIPELINE_LOCK_KEY, "1", nx=True, ex=_PIPELINE_LOCK_TTL
        )
        if not acquired:
            logger.warning("Pipeline already running, skipping this cycle")
            metrics["status"] = "skipped"
            return metrics
        try:
            self._errors = []
            self._alert_service = AdminAlertService()
            await self._scrape_channels(metrics)
            metrics["errors"] = self._errors
            metrics["duration_seconds"] = round(time.time() - start, 2)
            metrics["status"] = self._compute_status(metrics)
            logger.info("Pipeline completed: %s", metrics)
            return metrics
        finally:
            await redis.delete(_PIPELINE_LOCK_KEY)

    def _init_metrics(self) -> dict:
        return {
            "channels_processed": 0,
            "messages_scraped": 0,
            "messages_filtered": 0,
            "messages_classified": 0,
            "jobs_extracted": 0,
            "jobs_deduplicated": 0,
            "jobs_stored": 0,
            "errors": [],
            "duration_seconds": 0.0,
        }

    def _compute_status(self, metrics: dict) -> str:
        if self._errors:
            return "partial" if metrics["jobs_stored"] > 0 else "failed"
        return "success"

    async def _scrape_channels(self, metrics: dict) -> None:
        try:
            channels = await self._channel_repo.get_active_channels()
            for channel in channels:
                await self._process_channel(channel, metrics)
                metrics["channels_processed"] += 1
        except SessionExhaustedError as e:
            logger.error("All sessions exhausted: %s", e)
            self._errors.append({"stage": "scrape", "error": str(e)})
            await self._send_alert("session_exhausted", {"error": str(e)})
        except Exception as e:
            logger.exception("Pipeline crash: %s", e)
            self._errors.append({"stage": "pipeline", "error": str(e)})
            await self._send_alert("pipeline_crash", {"error": str(e)})
        finally:
            await self._scraper.disconnect()

    async def _process_channel(self, channel, metrics: dict) -> None:
        log_ctx = {"channel_id": str(channel.id), "channel_username": channel.username}
        logger.info("Processing channel %s", channel.username, extra=log_ctx)
        try:
            session = await self._get_active_session()
        except SessionExhaustedError:
            raise
        try:
            messages = await self._scrape_channel(channel, session, log_ctx)
        except Exception:
            return
        metrics["messages_scraped"] += len(messages)
        await self._update_channel_cursor(channel, messages)
        filtered = await self._filter_messages(messages, channel, log_ctx)
        metrics["messages_filtered"] += len(filtered)
        classified = await self._classify_messages(filtered, metrics, log_ctx)
        extracted = await self._extract_jobs(classified, metrics, log_ctx)
        await self._store_jobs(extracted, channel, metrics, log_ctx)
        await self._channel_repo.mark_scraped(channel.id)
        await self._session.flush()

    async def _scrape_channel(self, channel, session, log_ctx: dict) -> list:
        after_id = getattr(channel, "last_message_id", None)
        try:
            messages = await self._scraper.fetch_messages(
                channel_username=channel.username,
                batch_size=100,
                after_message_id=after_id,
            )
            await self._session_repo.mark_used(session.id)
            await self._session.flush()
            return messages
        except Exception as e:
            await self._handle_scrape_exception(channel, session, e, log_ctx)
            raise

    async def _handle_scrape_exception(
        self, channel, session, error: Exception, log_ctx: dict
    ) -> None:
        if isinstance(error, FloodWaitError):
            await self._handle_flood_wait(session, error, log_ctx)
        elif isinstance(error, (ChannelPrivateError, ChannelInvalidError)):
            await self._handle_session_ban(session, error, log_ctx)
        elif isinstance(error, ChannelInaccessibleError):
            await self._handle_channel_inaccessible(channel, log_ctx)
        else:
            logger.error("Scrape error for %s: %s", channel.username, error)
            self._errors.append(
                {"stage": "scrape", "channel_id": str(channel.id), "error": str(error)}
            )

    async def _handle_flood_wait(self, session, error, log_ctx: dict) -> None:
        wait_seconds = getattr(error, "seconds", 60)
        logger.warning(
            "FloodWait %ds for session %s", wait_seconds, session.id, extra=log_ctx
        )
        self._errors.append(
            {"stage": "scrape", "error": "flood_wait", "wait_seconds": wait_seconds}
        )

    async def _handle_session_ban(self, session, error, log_ctx: dict) -> None:
        logger.warning("Session banned/error: %s", error, extra=log_ctx)
        await self._session_repo.mark_banned(session.id, reason=str(error))
        await self._session.flush()
        self._errors.append(
            {"stage": "scrape", "error": "session_banned", "reason": str(error)}
        )

    async def _handle_channel_inaccessible(self, channel, log_ctx: dict) -> None:
        logger.warning("Deactivating inaccessible channel: %s", channel.username)
        await self._channel_repo.deactivate(channel.id)
        await self._session.flush()
        self._errors.append(
            {
                "stage": "scrape",
                "channel_id": str(channel.id),
                "error": "channel_inaccessible",
            }
        )

    async def _update_channel_cursor(self, channel, messages: list) -> None:
        if messages:
            max_id = max(msg["id"] for msg in messages)
            await self._channel_repo.update_last_message_id(channel.id, max_id)
            await self._session.flush()

    async def _filter_messages(
        self,
        messages: list,
        channel,
        log_ctx: dict,
    ) -> list:
        filtered = []
        for msg in messages:
            passed = await self._filter.filter_message(msg["text"])
            if passed:
                filtered.append(msg)
            else:
                logger.debug(
                    "Filtered message %d from %s",
                    msg["id"],
                    channel.username,
                    extra={**log_ctx, "message_id": msg["id"]},
                )
        return filtered

    async def _get_active_session(self):
        session = await self._session_repo.get_next_active_session()
        if session is None:
            raise SessionExhaustedError()

        settings = get_settings()
        decrypted = self._session_repo.decrypt_session(session)
        await self._scraper.connect_session(
            session_string=decrypted,
            api_id=settings.telegram.telethon_api_id,
            api_hash=settings.telegram.telethon_api_hash,
        )
        return session

    async def _classify_messages(self, messages, metrics, log_ctx):
        if not self._classifier:
            return messages

        classified = []
        for msg in messages:
            try:
                is_job = await self._classifier.classify_post(msg["text"])
                if is_job:
                    classified.append(msg)
                metrics["messages_classified"] += 1
            except DailyLimitReachedError:
                raise
            except Exception as e:
                logger.error(
                    "Classification error: %s",
                    e,
                    extra={**log_ctx, "message_id": msg["id"]},
                )
                self._errors.append(
                    {"stage": "classify", "error": str(e), "message_id": msg["id"]}
                )
        return classified

    async def _extract_jobs(self, messages, metrics, log_ctx):
        if not self._extractor:
            return messages

        extracted = []
        for msg in messages:
            try:
                result = await self._extractor.extract_job_data(msg["text"])
                msg["extracted"] = result
                extracted.append(msg)
                metrics["jobs_extracted"] += 1
            except DailyLimitReachedError:
                raise
            except Exception as e:
                logger.error(
                    "Extraction error: %s",
                    e,
                    extra={**log_ctx, "message_id": msg["id"]},
                )
                self._errors.append(
                    {"stage": "extract", "error": str(e), "message_id": msg["id"]}
                )
        return extracted

    async def _store_jobs(self, messages, channel, metrics, log_ctx):
        for msg in messages:
            try:
                await self._persist_job(msg, channel, metrics)
            except Exception as e:
                logger.error(
                    "Store error: %s",
                    e,
                    extra={**log_ctx, "message_id": msg.get("id")},
                )
                self._errors.append(
                    {"stage": "store", "error": str(e), "message_id": msg.get("id")}
                )

    async def _persist_job(self, msg: dict, channel, metrics: dict) -> None:
        content_hash = compute_content_hash(msg["text"])
        existing = await self._job_repo.get_by_content_hash(content_hash)
        if existing:
            metrics["jobs_deduplicated"] += 1
            await self._channel_repo.increment_false_positives(channel.id)
            return

        job_dict = self._build_job_dict(msg)
        job = await self._job_repo.create_job(
            telegram_message_id=msg["id"],
            source_channel_id=channel.id,
            content_hash=content_hash,
            **job_dict,
        )
        await self._session.flush()

        await self._persist_embedding(job, msg["text"])
        await self._channel_repo.increment_jobs_found(channel.id)
        await self._session.flush()
        metrics["jobs_stored"] += 1

    def _build_job_dict(self, msg: dict) -> dict:
        extracted = msg.get("extracted")
        return {
            "title": self._safe_field(extracted, "title") or msg["text"][:100],
            "company": self._safe_field(extracted, "company") or "Unknown",
            "description": self._safe_field(extracted, "description") or msg["text"],
            "location": self._safe_field(extracted, "location"),
            "salary_min": self._safe_field(extracted, "salary_min"),
            "salary_max": self._safe_field(extracted, "salary_max"),
            "salary_currency": self._safe_field(extracted, "salary_currency") or "USD",
            "requirements": self._safe_field(extracted, "requirements") or [],
            "skills": self._safe_field(extracted, "skills") or [],
        }

    def _safe_field(self, extracted, field: str):
        if extracted is None:
            return None
        return getattr(extracted, field, None)

    async def _persist_embedding(self, job, text: str) -> None:
        if not self._embedder or not job:
            return
        try:
            embedding = await self._embedder.generate_embedding(text)
            if embedding:
                await self._job_repo.update_embedding(job.id, embedding)
                await self._session.flush()
        except Exception as e:
            logger.warning("Embedding failed for job %s: %s", job.id, e)

    async def _send_alert(self, error_type: str, details: dict) -> None:
        try:
            if self._alert_service:
                await self._alert_service.send_alert(error_type, details)
        except Exception as e:
            logger.error("Failed to send admin alert: %s", e)
