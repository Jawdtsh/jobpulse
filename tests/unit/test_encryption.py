import pytest
from unittest.mock import patch
from src.utils.encryption import encrypt_data, decrypt_data, get_fernet


class TestEncryption:
    def test_encrypt_decrypt_string(self):
        original = "This is a secret CV content"
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        assert decrypted == original
        assert encrypted != original

    def test_encrypt_produces_different_output(self):
        original = "Same content"
        encrypted1 = encrypt_data(original)
        encrypted2 = encrypt_data(original)
        assert encrypted1 != encrypted2

    def test_encrypt_returns_str(self):
        original = "Test content"
        encrypted = encrypt_data(original)
        assert isinstance(encrypted, str)

    def test_decrypt_returns_str(self):
        original = "Test content"
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        assert isinstance(decrypted, str)

    def test_decrypt_invalid_ciphertext_raises_value_error(self):
        with pytest.raises(ValueError, match="ciphertext is corrupted"):
            decrypt_data("aW52YWxpZF9lbmNyeXB0ZWRfZGF0YQ==")

    def test_decrypt_invalid_base64_raises_value_error(self):
        with pytest.raises(ValueError, match="ciphertext is corrupted"):
            decrypt_data("!!!not-base64!!!")

    def test_get_fernet_returns_singleton(self):
        get_fernet.cache_clear()
        fernet1 = get_fernet()
        fernet2 = get_fernet()
        assert fernet1 is fernet2

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

    @patch("config.settings.Settings")
    def test_missing_fernet_key_raises_environment_error(self, mock_settings_cls):
        mock_settings = mock_settings_cls.return_value
        mock_settings.fernet_key = ""
        get_fernet.cache_clear()
        with patch("src.utils.encryption.get_settings", return_value=mock_settings):
            with pytest.raises(EnvironmentError, match="FERNET_KEY is not configured"):
                get_fernet()
        get_fernet.cache_clear()
