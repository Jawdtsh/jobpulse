import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.cv_repository import CVRepository
from src.utils.encryption import encrypt_data

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100
_LOCK_KEY = "cv:reencryption:lock"
_LOCK_TTL = 3600


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CVRepository(session)

    async def reencrypt_cvs(self, old_fernet_key: str) -> dict:
        import redis.asyncio as aioredis
        from config.settings import get_settings
        from cryptography.fernet import Fernet

        settings = get_settings()
        redis = aioredis.from_url(settings.redis.redis_url, decode_responses=True)

        lock = redis.lock(_LOCK_KEY, timeout=_LOCK_TTL)
        acquired = await lock.acquire()
        if not acquired:
            return {"status": "failed", "error": "Re-encryption already in progress"}

        try:
            from src.utils.encryption import get_fernet

            old_fernet = Fernet(
                old_fernet_key.encode()
                if isinstance(old_fernet_key, str)
                else old_fernet_key
            )

            total_reencrypted = 0
            while True:
                cvs = await self._repo.get_all_for_reencryption(batch_size=_BATCH_SIZE)
                if not cvs:
                    break

                for cv in cvs:
                    try:
                        old_encrypted = cv.content.decode("utf-8")
                        plaintext = old_fernet.decrypt(
                            old_encrypted.encode("ascii")
                        ).decode("utf-8")
                        new_encrypted = encrypt_data(plaintext)
                        cv.content = new_encrypted.encode("utf-8")
                        total_reencrypted += 1
                    except Exception:
                        logger.warning(
                            "Failed to re-encrypt cv_id=%s, skipping",
                            cv.id,
                            exc_info=True,
                        )

                await self._session.flush()
                logger.info("Re-encryption batch processed total=%d", total_reencrypted)

            await self._session.commit()
            get_fernet.cache_clear()
            return {"status": "success", "total_reencrypted": total_reencrypted}
        except Exception as e:
            logger.exception("Re-encryption failed: %s", e)
            return {"status": "failed", "error": str(e)}
        finally:
            try:
                await lock.release()
            except Exception:
                pass
