import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from config.settings import get_settings

logger = logging.getLogger(__name__)

NOTIFICATION_QUEUE_KEY = "notification_queue"


class NotificationQueue:
    def __init__(self):
        settings = get_settings()
        self._redis = aioredis.from_url(
            settings.redis.redis_url,
            decode_responses=True,
        )

    async def enqueue(
        self,
        match_id: str,
        user_id: str,
        job_id: str,
        cv_id: str | None,
        tier: str,
        notification_time: datetime,
        batch_key: str | None = None,
        job_published_at: datetime | None = None,
    ) -> None:
        ts_source = job_published_at or notification_time
        floored = ts_source.replace(
            minute=(ts_source.minute // 3) * 3,
            second=0,
            microsecond=0,
        )
        batch_key = floored.isoformat()

        payload = {
            "match_id": match_id,
            "user_id": user_id,
            "job_id": job_id,
            "cv_id": cv_id,
            "tier": tier,
            "batch_key": batch_key,
            "job_published_at": job_published_at.timestamp()
            if job_published_at
            else notification_time.timestamp(),
        }
        data = json.dumps(payload)
        score = notification_time.timestamp()
        await self._redis.zadd(NOTIFICATION_QUEUE_KEY, {data: score})

    async def fetch_due(self, now: datetime | None = None) -> list[dict]:
        if now is None:
            now = datetime.now(timezone.utc)
        max_score = now.timestamp()
        results = await self._redis.zrangebyscore(NOTIFICATION_QUEUE_KEY, 0, max_score)
        return [json.loads(item) for item in results]

    async def remove(self, data: dict) -> int:
        return await self._redis.zrem(NOTIFICATION_QUEUE_KEY, json.dumps(data))

    async def remove_by_cv(self, cv_id: str) -> int:
        all_items = await self._redis.zrange(NOTIFICATION_QUEUE_KEY, 0, -1)
        removed = 0
        for item in all_items:
            data = json.loads(item)
            if data.get("cv_id") == cv_id:
                await self._redis.zrem(NOTIFICATION_QUEUE_KEY, item)
                removed += 1
        return removed

    async def update_score_by_user(self, user_id: str, new_tier: str) -> int:
        all_items = await self._redis.zrange(NOTIFICATION_QUEUE_KEY, 0, -1)
        updated = 0
        for item in all_items:
            data = json.loads(item)
            if data.get("user_id") != user_id:
                continue
            delay = self._get_tier_delay(new_tier)
            job_published_ts = data.get("job_published_at")
            if job_published_ts is not None:
                new_score = job_published_ts + delay
            else:
                current_score = await self._redis.zscore(NOTIFICATION_QUEUE_KEY, item)
                if current_score is not None:
                    old_delay = self._get_tier_delay(data.get("tier", "free"))
                    new_score = current_score - old_delay + delay
                else:
                    new_score = datetime.now(timezone.utc).timestamp() + delay
            await self._redis.zrem(NOTIFICATION_QUEUE_KEY, item)
            data["tier"] = new_tier
            await self._redis.zadd(
                NOTIFICATION_QUEUE_KEY, {json.dumps(data): new_score}
            )
            updated += 1
        return updated

    @staticmethod
    def _get_tier_delay(tier: str) -> int:
        settings = get_settings()
        delays = {
            "free": settings.matching.tier_delay_free,
            "basic": settings.matching.tier_delay_basic,
            "pro": settings.matching.tier_delay_pro,
        }
        return delays.get(tier, settings.matching.tier_delay_free)

    async def close(self) -> None:
        await self._redis.close()
