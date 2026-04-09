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

_CHECK_AND_INCREMENT_LUA = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local limit = tonumber(ARGV[1])
if current >= limit then
    return -1
end
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
end
return count
"""

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
    async def check_and_increment_quota(self, user_id: uuid.UUID, tier: str) -> int:
        limit = QUOTA_LIMITS.get(tier, 1)
        redis = _get_redis()
        key = _quota_key(user_id)
        result = await redis.eval(
            _CHECK_AND_INCREMENT_LUA, 1, key, str(limit), str(_ttl_seconds())
        )
        return int(result)
