import pytest
from cryptography.fernet import Fernet
from pydantic import ValidationError
import config.settings as mod


_NESTED_MODELS = [
    mod.DatabaseSettings,
    mod.RedisSettings,
    mod.TelegramSettings,
    mod.AISettings,
    mod.SecuritySettings,
    mod.PaymentSettings,
    mod.MonitoringSettings,
    mod.Settings,
]


def _fernet_key():
    return Fernet.generate_key().decode()


def _base_env(**overrides):
    env = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/testdb",
        "DATABASE_POOL_SIZE": "5",
        "DATABASE_MAX_OVERFLOW": "5",
        "DATABASE_CONNECTION_TIMEOUT": "30",
        "REDIS_URL": "redis://localhost:6379/0",
        "REDIS_CONNECTION_TIMEOUT": "5",
        "REDIS_MAX_CONNECTIONS": "10",
        "BOT_TOKEN": "123456789:" + "A" * 35,
        "TELETHON_API_ID": "12345678",
        "TELETHON_API_HASH": "a" * 32,
        "GEMINI_API_KEY": "test-gemini-key",
        "GROQ_API_KEY": "test-groq-key",
        "OPENROUTER_API_KEY": "test-openrouter-key",
        "ZHIPU_API_KEY": "test-zhipu-key",
        "ENCRYPTION_KEY": _fernet_key(),
        "SECRET_KEY": "a" * 32,
        "SHAMCASH_API_KEY": "test-shamcash-key",
        "CRYPTO_WALLET_ADDRESS": "T" + "A" * 33,
        "ENVIRONMENT": "development",
        "DEBUG": "false",
    }
    env.update(overrides)
    return env


def _patch_env(monkeypatch, env):
    for cls in _NESTED_MODELS:
        monkeypatch.setitem(cls.model_config, "env_file", "")
    for k, v in env.items():
        monkeypatch.setenv(k, v)


def _make_settings(monkeypatch, **overrides):
    env = _base_env(**overrides)
    _patch_env(monkeypatch, env)
    return mod.Settings(_env_file="")


class TestSuccessfulLoad:
    def test_all_settings_accessible(self, monkeypatch):
        s = _make_settings(monkeypatch)
        assert s.database.database_url == (
            "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        )
        assert s.redis.redis_url == "redis://localhost:6379/0"
        assert s.telegram.bot_token == "123456789:" + "A" * 35
        assert s.ai.gemini_api_key == "test-gemini-key"
        assert s.security.encryption_key is not None
        assert s.security.secret_key == "a" * 32
        assert s.payment.shamcash_api_key == "test-shamcash-key"
        assert s.payment.crypto_wallet_address == "T" + "A" * 33
        assert s.monitoring.environment == "development"
        assert s.monitoring.debug is False

    def test_defaults_applied(self, monkeypatch):
        env = _base_env()
        for k in (
            "DATABASE_POOL_SIZE",
            "DATABASE_MAX_OVERFLOW",
            "DATABASE_CONNECTION_TIMEOUT",
            "REDIS_CONNECTION_TIMEOUT",
            "REDIS_MAX_CONNECTIONS",
            "TELETHON_SESSION_NAME",
            "ENVIRONMENT",
            "DEBUG",
        ):
            env.pop(k, None)
            monkeypatch.delenv(k, raising=False)
        _patch_env(monkeypatch, env)
        s = mod.Settings(_env_file="")
        assert s.database.pool_size == 5
        assert s.database.max_overflow == 5
        assert s.database.connection_timeout == 30
        assert s.redis.connection_timeout == 5
        assert s.redis.max_connections == 10
        assert s.telegram.telethon_session_name == "bot_session"
        assert s.monitoring.environment == "development"
        assert s.monitoring.debug is False

    def test_sentry_dsn_optional(self, monkeypatch):
        s = _make_settings(monkeypatch, SENTRY_DSN="")
        assert s.monitoring.sentry_dsn is None

    def test_sentry_dsn_set(self, monkeypatch):
        s = _make_settings(monkeypatch, SENTRY_DSN="https://abc@sentry.io/123")
        assert s.monitoring.sentry_dsn == "https://abc@sentry.io/123"


class TestMissingRequired:
    @pytest.mark.parametrize(
        "var",
        [
            "DATABASE_URL",
            "REDIS_URL",
            "BOT_TOKEN",
            "TELETHON_API_ID",
            "TELETHON_API_HASH",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "OPENROUTER_API_KEY",
            "ZHIPU_API_KEY",
            "ENCRYPTION_KEY",
            "SECRET_KEY",
            "SHAMCASH_API_KEY",
            "CRYPTO_WALLET_ADDRESS",
        ],
    )
    def test_missing_required_var_raises(self, monkeypatch, var):
        env = _base_env()
        env.pop(var, None)
        monkeypatch.delenv(var, raising=False)
        _patch_env(monkeypatch, env)
        with pytest.raises(ValidationError):
            mod.Settings(_env_file="")


class TestInvalidFormat:
    def test_wrong_type_pool_size(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_POOL_SIZE="not_a_number")


class TestDatabaseUrlValidation:
    def test_valid_asyncpg_prefix(self, monkeypatch):
        s = _make_settings(monkeypatch)
        assert s.database.database_url.startswith("postgresql+asyncpg://")

    def test_valid_plain_postgresql_prefix(self, monkeypatch):
        import warnings

        with warnings.catch_warnings():
            s = _make_settings(
                monkeypatch,
                DATABASE_URL="postgresql://user:pass@localhost:5432/testdb",
            )
        assert s.database.database_url.startswith("postgresql://")


class TestDatabaseOverrides:
    def test_custom_pool_size(self, monkeypatch):
        s = _make_settings(monkeypatch, DATABASE_POOL_SIZE="10")
        assert s.database.pool_size == 10

    def test_custom_max_overflow(self, monkeypatch):
        s = _make_settings(monkeypatch, DATABASE_MAX_OVERFLOW="15")
        assert s.database.max_overflow == 15

    def test_custom_connection_timeout(self, monkeypatch):
        s = _make_settings(monkeypatch, DATABASE_CONNECTION_TIMEOUT="60")
        assert s.database.connection_timeout == 60


class TestDatabaseUrlInvalid:
    def test_mysql_prefix_rejected(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(
                monkeypatch, DATABASE_URL="mysql://user:pass@localhost:3306/db"
            )

    def test_sqlite_prefix_rejected(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_URL="sqlite:///test.db")


class TestDatabaseFieldValidators:
    def test_pool_size_too_low(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_POOL_SIZE="0")

    def test_pool_size_too_high(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_POOL_SIZE="21")

    def test_max_overflow_negative(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_MAX_OVERFLOW="-1")

class TestCryptoWallet:
    def test_valid_address(self, monkeypatch):
        addr = "T" + "B" * 33
        s = _make_settings(monkeypatch, CRYPTO_WALLET_ADDRESS=addr)
        assert s.payment.crypto_wallet_address == addr

    def test_missing_t_prefix(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, CRYPTO_WALLET_ADDRESS="A" + "B" * 33)

    def test_wrong_length(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, CRYPTO_WALLET_ADDRESS="T" + "B" * 32)

    def test_too_long(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, CRYPTO_WALLET_ADDRESS="T" + "B" * 34)


class TestSentryDsn:
    def test_empty_sentry_dsn(self, monkeypatch):
        s = _make_settings(monkeypatch, SENTRY_DSN="")
        assert s.monitoring.sentry_dsn is None

    def test_none_sentry_dsn(self, monkeypatch):
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        env = _base_env()
        env.pop("SENTRY_DSN", None)
        _patch_env(monkeypatch, env)
        s = mod.Settings(_env_file="")
        assert s.monitoring.sentry_dsn is None


class TestEnvironmentAndDebug:
    def test_environment_development(self, monkeypatch):
        s = _make_settings(monkeypatch, ENVIRONMENT="development")
        assert s.monitoring.environment == "development"

    def test_environment_staging(self, monkeypatch):
        s = _make_settings(monkeypatch, ENVIRONMENT="staging")
        assert s.monitoring.environment == "staging"

    def test_environment_production(self, monkeypatch):
        s = _make_settings(monkeypatch, ENVIRONMENT="production")
        assert s.monitoring.environment == "production"

    def test_environment_invalid(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, ENVIRONMENT="invalid")

    def test_debug_true(self, monkeypatch):
        s = _make_settings(monkeypatch, DEBUG="true")
        assert s.monitoring.debug is True

    def test_debug_false(self, monkeypatch):
        s = _make_settings(monkeypatch, DEBUG="false")
        assert s.monitoring.debug is False

    def test_debug_1(self, monkeypatch):
        s = _make_settings(monkeypatch, DEBUG="1")
        assert s.monitoring.debug is True

    def test_debug_0(self, monkeypatch):
        s = _make_settings(monkeypatch, DEBUG="0")
        assert s.monitoring.debug is False


class TestEnvFileIntegration:
    def test_loads_from_env_file(self, monkeypatch, tmp_path):
        key = _fernet_key()
        env_file = tmp_path / ".env"
        env_file.write_text(
            "DATABASE_URL=postgresql+asyncpg://u:p@h:5432/fromfile\n"
            "REDIS_URL=redis://localhost:6379/0\n"
            "BOT_TOKEN=123456789:" + "A" * 35 + "\n"
            "TELETHON_API_ID=12345678\n"
            "TELETHON_API_HASH=" + "a" * 32 + "\n"
            "GEMINI_API_KEY=file-key\n"
            "GROQ_API_KEY=file-key\n"
            "OPENROUTER_API_KEY=file-key\n"
            "ZHIPU_API_KEY=file-key\n"
            f"ENCRYPTION_KEY={key}\n"
            "SECRET_KEY=" + "s" * 32 + "\n"
            "SHAMCASH_API_KEY=file-key\n"
            "CRYPTO_WALLET_ADDRESS=T" + "X" * 33 + "\n"
        )
        for var_name in [
            "DATABASE_URL",
            "REDIS_URL",
            "BOT_TOKEN",
            "TELETHON_API_ID",
            "TELETHON_API_HASH",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "OPENROUTER_API_KEY",
            "ZHIPU_API_KEY",
            "ENCRYPTION_KEY",
            "SECRET_KEY",
            "SHAMCASH_API_KEY",
            "CRYPTO_WALLET_ADDRESS",
        ]:
            monkeypatch.delenv(var_name, raising=False)

        class FileSettings(mod.Settings):
            model_config = {
                "env_file": str(env_file),
                "env_file_encoding": "utf-8",
                "extra": "ignore",
            }

        for cls in _NESTED_MODELS[:-1]:
            monkeypatch.setitem(cls.model_config, "env_file", str(env_file))
        s = FileSettings()
        assert "fromfile" in s.database.database_url


class TestSecretMasking:
    def test_repr_masks_secrets(self, monkeypatch):
        s = _make_settings(monkeypatch)
        r = repr(s)
        assert "test-gemini-key" not in r
        assert "test-shamcash-key" not in r
        assert "a" * 32 not in r

    def test_str_masks_secrets(self, monkeypatch):
        s = _make_settings(monkeypatch)
        text = str(s)
        assert "test-gemini-key" not in text

    def test_masked_shows_prefix(self, monkeypatch):
        s = _make_settings(monkeypatch)
        r = repr(s)
        assert "test-gem" in r


    def test_max_overflow_too_high(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_MAX_OVERFLOW="21")

    def test_connection_timeout_zero(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_CONNECTION_TIMEOUT="0")

    def test_connection_timeout_negative(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, DATABASE_CONNECTION_TIMEOUT="-5")


class TestEncryptionKeyValid:
    def test_valid_fernet_key(self, monkeypatch):
        key = Fernet.generate_key().decode()
        s = _make_settings(monkeypatch, ENCRYPTION_KEY=key)
        assert s.security.encryption_key == key


class TestEncryptionKeyInvalid:
    def test_invalid_base64(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, ENCRYPTION_KEY="not-valid-base64!!!")

    def test_wrong_length(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, ENCRYPTION_KEY="dG9vLXNob3J0LWtleQ==")


class TestSecretKey:
    def test_valid_32_chars(self, monkeypatch):
        s = _make_settings(monkeypatch, SECRET_KEY="a" * 32)
        assert s.security.secret_key == "a" * 32

    def test_valid_longer(self, monkeypatch):
        s = _make_settings(monkeypatch, SECRET_KEY="b" * 64)
        assert len(s.security.secret_key) == 64

    def test_too_short(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, SECRET_KEY="short_key")


class TestBotToken:
    def test_valid_token(self, monkeypatch):
        token = "987654321:" + "x" * 36
        s = _make_settings(monkeypatch, BOT_TOKEN=token)
        assert s.telegram.bot_token == token

    def test_invalid_no_colon(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, BOT_TOKEN="invalidtoken")

    def test_invalid_short_after_colon(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, BOT_TOKEN="123:short")


class TestTelethon:
    def test_valid_api_id(self, monkeypatch):
        s = _make_settings(monkeypatch, TELETHON_API_ID="99999999")
        assert s.telegram.telethon_api_id == 99999999

    def test_invalid_api_id_negative(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, TELETHON_API_ID="-1")

    def test_valid_api_hash(self, monkeypatch):
        h = "abcdef0123456789" * 2
        s = _make_settings(monkeypatch, TELETHON_API_HASH=h)
        assert s.telegram.telethon_api_hash == h

    def test_invalid_api_hash_short(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, TELETHON_API_HASH="abc123")

    def test_invalid_api_hash_non_hex(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, TELETHON_API_HASH="g" * 32)


class TestAiApiKeys:
    def test_all_keys_loaded(self, monkeypatch):
        s = _make_settings(monkeypatch)
        assert s.ai.gemini_api_key == "test-gemini-key"
        assert s.ai.groq_api_key == "test-groq-key"
        assert s.ai.openrouter_api_key == "test-openrouter-key"
        assert s.ai.zhipu_api_key == "test-zhipu-key"

    def test_empty_gemini_rejected(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, GEMINI_API_KEY="")

    def test_whitespace_only_rejected(self, monkeypatch):
        with pytest.raises(ValidationError):
            _make_settings(monkeypatch, GROQ_API_KEY="   ")


class TestSettingsImmutability:
    def test_settings_frozen_after_creation(self, monkeypatch):
        s = _make_settings(monkeypatch)
        original_url = s.database.database_url
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://new:new@h:5432/changed",
        )
        assert s.database.database_url == original_url


class TestAiModelsIntegration:
    def test_ai_models_property(self, monkeypatch):
        s = _make_settings(monkeypatch)
        models = s.ai.ai_models
        assert "active" in models
        assert "fallback" in models
        assert "classifier" in models["active"]
