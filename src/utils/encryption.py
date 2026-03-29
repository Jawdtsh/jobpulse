from cryptography.fernet import Fernet
from config.settings import get_settings

settings = get_settings()
_fernet_instance: Fernet | None = None


def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = Fernet(settings.fernet_key.encode())
    return _fernet_instance


def encrypt_data(data: str) -> bytes:
    fernet = get_fernet()
    return fernet.encrypt(data.encode("utf-8"))


def decrypt_data(encrypted_data: bytes) -> str:
    fernet = get_fernet()
    return fernet.decrypt(encrypted_data).decode("utf-8")


def encrypt_bytes(data: bytes) -> bytes:
    fernet = get_fernet()
    return fernet.encrypt(data)


def decrypt_bytes(encrypted_data: bytes) -> bytes:
    fernet = get_fernet()
    return fernet.decrypt(encrypted_data)
