import base64
from functools import lru_cache
from cryptography.fernet import Fernet, InvalidToken
from config.settings import get_settings


@lru_cache(maxsize=1)
def get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.fernet_key
    if not key:
        raise EnvironmentError(
            "FERNET_KEY is not configured. Set it in .env or environment variables."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_data(data: str) -> str:
    fernet = get_fernet()
    encrypted_bytes = fernet.encrypt(data.encode("utf-8"))
    return base64.b64encode(encrypted_bytes).decode("ascii")


def decrypt_data(encrypted_data: str) -> str:
    fernet = get_fernet()
    try:
        encrypted_bytes = base64.b64decode(encrypted_data.encode("ascii"))
    except Exception as exc:
        raise ValueError(f"Invalid encrypted data: not valid base64. {exc}") from exc
    try:
        return fernet.decrypt(encrypted_bytes).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Decryption failed: ciphertext is corrupted or was encrypted with a different key."
        ) from exc


def encrypt_bytes(data: bytes) -> bytes:
    fernet = get_fernet()
    return fernet.encrypt(data)


def decrypt_bytes(encrypted_data: bytes) -> bytes:
    fernet = get_fernet()
    return fernet.decrypt(encrypted_data)
