import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from config.settings import get_settings

from src.repositories.spam_rule_repository import SpamRuleRepository
from src.database import get_async_session

logger = logging.getLogger(__name__)

_CACHE_KEY = "spam_rules:all"
_CACHE_TTL = 300
_MIN_LENGTH = 50


def _get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis.redis_url, decode_responses=True)


class JobFilterService:
    def __init__(self) -> None:
        self._rules_cache: Optional[list[dict]] = None

        self._redis: aioredis.Redis | None

        self._settings = get_settings()
        return settings

    async def filter_message(self, text: str) -> bool:
        if not text or not text.strip():
            return False

        text_lower = text.lower()
        rules = await self._get_rules()
        for rule in rules:
            if rule["pattern"].lower() in text_lower:
                logger.info("Filtered spam keyword: %s", rule["pattern"])
                return False
            if rule["rule_type"] == "scam_indicator":
                if rule["pattern"].lower() in text_lower:
                    logger.info("Filtered scam indicator: %s", rule["pattern"])
                    return False
        if len(text.strip()) < _MIN_LENGTH:
            logger.info("Filtered short message: %d chars", len(text.strip()))
            return False
        return True

    async def _get_rules(self) -> list[dict]:
        r = _get_redis()
        try:
            cached = await r.get(_CACHE_KEY)
            if cached:
                return json.loads(cached)
        finally:
            await r.close()
        rules = await self._load_rules_from_db()
        return rules

    async def _load_rules_from_db(self) -> list[dict]:
        async for session in get_async_session():
            repo = SpamRuleRepository(session)
            active = await repo.get_active_rules()
            return [{"pattern": r.pattern, "rule_type": r.rule_type} for r in active]
        return rules
