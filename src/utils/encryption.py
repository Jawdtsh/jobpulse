from functools import lru_cache
from cryptography.fernet import Fernet, InvalidToken
from config.settings import get_settings


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    s = get_settings()
    key = s.security.encryption_key
    if not key:
        raise OSError(
            "ENCRYPTION_KEY is not configured. Set it in .env or environment variables."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_data(data: str) -> str:
    fernet = get_fernet()
    encrypted_bytes = fernet.encrypt(data.encode("utf-8"))
    return encrypted_bytes.decode("ascii")


def decrypt_data(encrypted_data: str) -> str:
    fernet = get_fernet()
    try:
        return fernet.decrypt(encrypted_data.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Decryption failed: ciphertext is corrupted or "
            "was encrypted with a different key."
        ) from exc


def encrypt_bytes(data: bytes) -> bytes:
    fernet = get_fernet()
    return fernet.encrypt(data)


def decrypt_bytes(encrypted_data: bytes) -> bytes:
    fernet = get_fernet()
    try:
        return fernet.decrypt(encrypted_data)
    except InvalidToken as exc:
        raise ValueError(
            "Decryption failed: ciphertext is corrupted or "
            "was encrypted with a different key."
        ) from exc
