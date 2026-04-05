import pytest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet
from src.utils.encryption import encrypt_data, decrypt_data, get_fernet

_TEST_KEY = Fernet.generate_key().decode()
_TEST_FERNET = Fernet(_TEST_KEY.encode())


def _mock_get_fernet():
    return _TEST_FERNET


class TestEncryption:
    def test_encrypt_decrypt_string(self):
        with patch.object(get_fernet, "cache_clear"):
            with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
                original = "This is a secret CV content"
                encrypted = encrypt_data(original)
                decrypted = decrypt_data(encrypted)
                assert decrypted == original
                assert encrypted != original

    def test_encrypt_produces_different_output(self):
        with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
            original = "Same content"
            encrypted1 = encrypt_data(original)
            encrypted2 = encrypt_data(original)
            assert encrypted1 != encrypted2

    def test_encrypt_returns_str(self):
        with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
            encrypted = encrypt_data("Test content")
            assert isinstance(encrypted, str)

    def test_decrypt_returns_str(self):
        with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
            encrypted = encrypt_data("Test content")
            decrypted = decrypt_data(encrypted)
            assert isinstance(decrypted, str)

    def test_decrypt_invalid_ciphertext_raises_value_error(self):
        with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
            with pytest.raises(ValueError, match="ciphertext is corrupted"):
                decrypt_data("aW52YWxpZF9lbmNjeXB0ZWRfZGF0YQ==")

    def test_decrypt_invalid_base64_raises_value_error(self):
        with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
            with pytest.raises(ValueError, match="ciphertext is corrupted"):
                decrypt_data("!!!not-base64!!!")

    def test_get_fernet_returns_singleton(self):
        with patch("src.utils.encryption.get_settings") as mock_gs:
            mock_s = MagicMock()
            mock_s.security.encryption_key = _TEST_KEY
            mock_gs.return_value = mock_s
            get_fernet.cache_clear()
            fernet1 = get_fernet()
            fernet2 = get_fernet()
            assert fernet1 is fernet2
            get_fernet.cache_clear()

    def test_can_encrypt_empty_string(self):
        with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
            original = ""
            encrypted = encrypt_data(original)
            decrypted = decrypt_data(encrypted)
            assert decrypted == original

    def test_can_encrypt_long_content(self):
        with patch("src.utils.encryption.get_fernet", return_value=_TEST_FERNET):
            original = "A" * 10000
            encrypted = encrypt_data(original)
            decrypted = decrypt_data(encrypted)
            assert decrypted == original

    def test_missing_encryption_key_raises_os_error(self):
        mock_settings = MagicMock()
        mock_settings.security = MagicMock()
        mock_settings.security.encryption_key = ""
        get_fernet.cache_clear()
        with patch("src.utils.encryption.get_settings", return_value=mock_settings):
            with pytest.raises(OSError, match="ENCRYPTION_KEY is not configured"):
                get_fernet()
        get_fernet.cache_clear()
