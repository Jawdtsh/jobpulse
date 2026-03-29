import pytest
from cryptography.fernet import Fernet
from src.utils.encryption import encrypt_data, decrypt_data, get_fernet


class TestEncryption:
    def test_encrypt_decrypt_string(self):
        original = "This is a secret CV content"
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        assert decrypted == original
        assert encrypted != original.encode()

    def test_encrypt_produces_different_output(self):
        original = "Same content"
        encrypted1 = encrypt_data(original)
        encrypted2 = encrypt_data(original)
        assert encrypted1 != encrypted2

    def test_decrypt_invalid_data_raises_error(self):
        with pytest.raises(Exception):
            decrypt_data(b"invalid_encrypted_data")

    def test_get_fernet_returns_singleton(self):
        fernet1 = get_fernet()
        fernet2 = get_fernet()
        assert fernet1 is fernet2

    def test_encrypted_data_is_bytes(self):
        original = "Test content"
        encrypted = encrypt_data(original)
        assert isinstance(encrypted, bytes)

    def test_can_encrypt_empty_string(self):
        original = ""
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        assert decrypted == original

    def test_can_encrypt_long_content(self):
        original = "A" * 10000
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        assert decrypted == original
