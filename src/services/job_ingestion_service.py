import logging
import time
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.channel_repository import ChannelRepository
from src.repositories.telegram_session_repository import TelegramSessionRepository
from src.services.exceptions import ChannelInaccessibleError, SessionExhaustedError
from src.services.job_filter_service import JobFilterService
from src.services.telegram_scraper_service import TelegramScraperService

logger = logging.getLogger(__name__)


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
        self._filter = filter_service or JobFilterService()
        self._scraper = scraper_service or TelegramScraperService()
        self._classifier = classifier_service
        self._extractor = extractor_service
        self._embedder = embedding_service
        self._channel_repo = ChannelRepository(session)
        self._session_repo = TelegramSessionRepository(session)
        self._errors: list[dict] = []

    async def run_pipeline(self) -> dict:
        start = time.time()
        metrics = {
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
        self._errors = []
        self._alert_service = None

        try:
            from src.services.admin_alert_service import AdminAlertService

            self._alert_service = AdminAlertService()
        except Exception:
            pass

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

        metrics["errors"] = self._errors
        metrics["duration_seconds"] = round(time.time() - start, 2)

        if self._errors:
            metrics["status"] = "partial" if metrics["jobs_stored"] > 0 else "failed"
        else:
            metrics["status"] = "success"

        logger.info("Pipeline completed: %s", metrics)
        return metrics

    async def _process_channel(self, channel, metrics: dict) -> None:
        log_ctx = {"channel_id": str(channel.id), "channel_username": channel.username}
        logger.info("Processing channel %s", channel.username, extra=log_ctx)

        try:
            session = await self._get_active_session()
        except SessionExhaustedError:
            raise

        try:
            messages = await self._scraper.fetch_messages(
                channel_username=channel.username,
                batch_size=100,
                after_message_id=None,
            )
            await self._session_repo.mark_used(session.id)
            await self._session.flush()
        except ChannelInaccessibleError:
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
            return
        except Exception as e:
            logger.error("Scrape error for %s: %s", channel.username, e)
            self._errors.append(
                {
                    "stage": "scrape",
                    "channel_id": str(channel.id),
                    "error": str(e),
                }
            )
            return

        metrics["messages_scraped"] += len(messages)

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
                    extra={**log_ctx, "message_id": msg["id"], "filter_reason": "spam"},
                )

        metrics["messages_filtered"] += len(filtered)

        classified = await self._classify_messages(filtered, metrics, log_ctx)
        extracted = await self._extract_jobs(classified, metrics, log_ctx)
        await self._store_jobs(extracted, channel, metrics, log_ctx)

        await self._channel_repo.mark_scraped(channel.id)
        await self._session.flush()

    async def _get_active_session(self):
        from config.settings import get_settings

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
        from src.repositories.job_repository import JobRepository
        from src.utils.content_hasher import compute_content_hash

        job_repo = JobRepository(self._session)

        for msg in messages:
            try:
                content_hash = compute_content_hash(msg["text"])
                existing = await job_repo.get_by_content_hash(content_hash)
                if existing:
                    metrics["jobs_deduplicated"] += 1
                    await self._channel_repo.increment_false_positives(channel.id)
                    continue

                extracted = msg.get("extracted")
                title = extracted.title if extracted else msg["text"][:100]
                company = extracted.company if extracted else "Unknown"
                description = extracted.description if extracted else msg["text"]

                job = await job_repo.create_job(
                    telegram_message_id=msg["id"],
                    title=title,
                    company=company,
                    description=description,
                    source_channel_id=channel.id,
                    location=extracted.location if extracted else None,
                    salary_min=extracted.salary_min if extracted else None,
                    salary_max=extracted.salary_max if extracted else None,
                    salary_currency=extracted.salary_currency if extracted else "USD",
                    requirements=extracted.requirements if extracted else None,
                    skills=extracted.skills if extracted else None,
                )
                await self._session.flush()

                if self._embedder and job:
                    try:
                        embedding = await self._embedder.generate_embedding(msg["text"])
                        if embedding:
                            await job_repo.update_embedding(job.id, embedding)
                            await self._session.flush()
                    except Exception as e:
                        logger.warning("Embedding failed for job %s: %s", job.id, e)

                await self._channel_repo.increment_jobs_found(channel.id)
                await self._session.flush()
                metrics["jobs_stored"] += 1

            except Exception as e:
                logger.error(
                    "Store error: %s",
                    e,
                    extra={**log_ctx, "message_id": msg.get("id")},
                )
                self._errors.append(
                    {"stage": "store", "error": str(e), "message_id": msg.get("id")}
                )

    async def _send_alert(self, error_type: str, details: dict) -> None:
        try:
            if self._alert_service:
                await self._alert_service.send_alert(error_type, details)
        except Exception as e:
            logger.error("Failed to send admin alert: %s", e)
