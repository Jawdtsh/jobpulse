import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import google.generativeai as genai
import redis.asyncio as aioredis
from openai import AsyncOpenAI

from config.ai_models import (
    ACTIVE_MODELS,
    API_PROVIDERS,
    DAILY_LIMITS,
    FALLBACK_CHAIN,
    PROVIDER_BASE_URLS,
)
from config.settings import get_settings
from src.services.exceptions import (
    AIServiceUnavailableError,
    DailyLimitReachedError,
    InvalidEmbeddingDimensionsError,
    InvalidModelTypeError,
)

logger = logging.getLogger(__name__)

_REDIS_KEY_TPL = "ai_daily_usage:{model}:{date}"
_DAILY_TTL = 86400

_redis: aioredis.Redis | None = None


def _ensure_redis() -> None:
    global _redis
    if _redis is not None:
        return
    settings = get_settings()
    _redis = aioredis.from_url(settings.redis.redis_url, decode_responses=True)


def _get_redis() -> aioredis.Redis:
    _ensure_redis()
    return _redis  # type: ignore[return-value]


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class AIProviderService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._clients: dict[str, AsyncOpenAI] = {}

    def _get_openai_client(self, provider: str) -> AsyncOpenAI:
        if provider in self._clients:
            return self._clients[provider]
        base_url = PROVIDER_BASE_URLS.get(provider)
        key_env = {
            "groq": self._settings.ai.groq_api_key,
            "openrouter": self._settings.ai.openrouter_api_key,
            "zhipu": self._settings.ai.zhipu_api_key,
        }
        api_key = key_env.get(provider, "")
        client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._clients[provider] = client
        return client

    async def call_model(
        self,
        model_type: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict] = None,
        timeout: int = 30,
    ) -> str:
        self._validate_model_type(model_type)
        chain = FALLBACK_CHAIN.get(model_type, [])
        if not chain:
            raise AIServiceUnavailableError(
                f"No fallback chain for model_type: {model_type}"
            )
        return await self._try_fallback_chain(
            chain, prompt, system_prompt, response_format, timeout, model_type
        )

    def _validate_model_type(self, model_type: str) -> None:
        if model_type not in ACTIVE_MODELS:
            raise InvalidModelTypeError(model_type)

    async def _try_fallback_chain(
        self,
        chain: list[str],
        prompt: str,
        system_prompt: Optional[str],
        response_format: Optional[dict],
        timeout: int,
        model_type: str,
    ) -> str:
        for model_name in chain:
            if model_name == "regex_only":
                continue
            provider_info = API_PROVIDERS.get(model_name)
            if not provider_info:
                continue
            if not await self.check_daily_limit(model_name):
                raise DailyLimitReachedError(model_name)
            result = await self._call_with_retries(
                model_name,
                provider_info,
                prompt,
                system_prompt,
                response_format,
                timeout,
            )
            if result is not None:
                return result
        raise AIServiceUnavailableError(
            f"All providers failed for model_type: {model_type}"
        )

    async def _call_with_retries(
        self,
        model_name: str,
        provider_info: dict,
        prompt: str,
        system_prompt: Optional[str],
        response_format: Optional[dict],
        timeout: int,
    ) -> Optional[str]:
        for attempt in range(3):
            try:
                result = await self._call_provider(
                    model_name,
                    provider_info,
                    prompt,
                    system_prompt,
                    response_format,
                    timeout,
                )
                await self.increment_usage(model_name)
                return result
            except Exception as exc:
                self._log_provider_error(model_name, attempt + 1, exc)
                if attempt < 2:
                    await asyncio.sleep(2**attempt)
        return None

    def _log_provider_error(
        self, model_name: str, attempt: int, error: Exception
    ) -> None:
        logger.warning(
            "AI call failed model=%s attempt=%d: %s",
            model_name,
            attempt,
            error,
        )

    async def _call_provider(
        self,
        model_name: str,
        provider_info: dict,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict] = None,
        timeout: int = 30,
    ) -> str:
        provider = provider_info["provider"]
        if provider == "google":
            return await self._call_google(
                model_name, prompt, system_prompt, response_format, timeout
            )
        client = self._get_openai_client(provider)
        kwargs = self._build_openai_kwargs(
            model_name, prompt, system_prompt, response_format, timeout
        )
        resp = await client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    def _build_openai_kwargs(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str],
        response_format: Optional[dict],
        timeout: int,
    ) -> dict:
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        kwargs: dict = {
            "model": model_name,
            "messages": messages,
            "timeout": timeout,
        }
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    async def _call_google(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict] = None,
        timeout: int = 30,
    ) -> str:
        genai.configure(api_key=self._settings.ai.gemini_api_key)
        generation_config: dict = {}
        if response_format:
            generation_config["response_mime_type"] = "application/json"
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt,
            generation_config=generation_config,
        )
        result = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=timeout,
        )
        return result.text or ""

    async def generate_embedding(
        self,
        text: str,
        expected_dimensions: int = 768,
    ) -> Optional[list[float]]:
        chain = FALLBACK_CHAIN.get("embedder", [])
        for model_name in chain:
            if not await self.check_daily_limit(model_name):
                return None
            embedding = await self._try_embedding_model(
                model_name, text, expected_dimensions
            )
            if embedding is not None:
                return embedding
        return None

    async def _try_embedding_model(
        self,
        model_name: str,
        text: str,
        expected_dimensions: int,
    ) -> Optional[list[float]]:
        for attempt in range(3):
            try:
                embedding = await self._fetch_embedding(model_name, text)
                if len(embedding) != expected_dimensions:
                    raise InvalidEmbeddingDimensionsError(
                        expected_dimensions, len(embedding)
                    )
                await self.increment_usage(model_name)
                return embedding
            except InvalidEmbeddingDimensionsError:
                logger.warning(
                    "Embedding dim mismatch model=%s attempt=%d",
                    model_name,
                    attempt + 1,
                )
            except Exception as exc:
                self._log_provider_error(model_name, attempt + 1, exc)
            if attempt < 2:
                await asyncio.sleep(2**attempt)
        return None

    async def _fetch_embedding(
        self,
        model_name: str,
        text: str,
    ) -> list[float]:
        provider_info = API_PROVIDERS.get(model_name)
        if not provider_info:
            raise ValueError(f"Unknown model: {model_name}")
        if provider_info["provider"] == "google":
            return await self._google_embedding(model_name, text)
        return await self._openai_embedding(model_name, provider_info, text)

    async def _google_embedding(
        self,
        model_name: str,
        text: str,
    ) -> list[float]:
        genai.configure(api_key=self._settings.ai.gemini_api_key)
        result = await asyncio.to_thread(
            genai.embed_content, [text], model=f"models/{model_name}"
        )
        return result["embedding"][0]

    async def _openai_embedding(
        self,
        model_name: str,
        provider_info: dict,
        text: str,
    ) -> list[float]:
        client = self._get_openai_client(provider_info["provider"])
        resp = await client.embeddings.create(model=model_name, input=text)
        return resp.data[0].embedding

    async def check_daily_limit(self, model_name: str) -> bool:
        limits = DAILY_LIMITS.get(model_name)
        if not limits or limits.get("rpd") is None:
            return True
        rpd = limits["rpd"]
        redis = _get_redis()
        key = _REDIS_KEY_TPL.format(model=model_name, date=_today())
        current = await redis.get(key)
        if current is not None and int(current) >= rpd:
            return False
        return True

    async def increment_usage(self, model_name: str) -> int:
        redis = _get_redis()
        key = _REDIS_KEY_TPL.format(model=model_name, date=_today())
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, _DAILY_TTL)
        return count
