import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis.asyncio as aioredis

from config.settings import get_settings

logger = logging.getLogger(__name__)

_QUOTA_KEY_TPL = "cv_eval_quota:{user_id}:{year}-{month}"

QUOTA_LIMITS = {
    "free": 1,
    "basic": 5,
    "pro": 10,
}

_redis: Optional[aioredis.Redis] = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(settings.redis.redis_url, decode_responses=True)
    return _redis


def _quota_key(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    return _QUOTA_KEY_TPL.format(
        user_id=str(user_id),
        year=now.year,
        month=f"{now.month:02d}",
    )


def _ttl_seconds() -> int:
    now = datetime.now(timezone.utc)
    next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
    return int((next_month - now).total_seconds())


class CVQuotaService:
    async def check_quota(self, user_id: uuid.UUID, tier: str) -> tuple[bool, int]:
        limit = QUOTA_LIMITS.get(tier, 1)
        redis = _get_redis()
        key = _quota_key(user_id)
        current = await redis.get(key)
        current_count = int(current) if current else 0
        remaining = max(0, limit - current_count)
        return current_count < limit, remaining

    async def increment_usage(self, user_id: uuid.UUID) -> int:
        redis = _get_redis()
        key = _quota_key(user_id)
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, _ttl_seconds())
        return count
