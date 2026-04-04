# Data Model: Settings Configuration

## Settings (Root Container)

Singleton instance exported as `settings` from `config/settings.py`.

### Nested Configuration Models

#### DatabaseSettings
- `database_url`: str (required) - PostgreSQL connection string
- `pool_size`: int (default: 5) - Base connection pool size
- `max_overflow`: int (default: 5) - Overflow connections beyond pool_size
- `connection_timeout`: int (default: 30) - Seconds before connection attempt times out

#### RedisSettings
- `redis_url`: str (required) - Redis connection string
- `connection_timeout`: int (default: 5) - Seconds before Redis connection times out
- `max_connections`: int (default: 10) - Maximum Redis connections in pool

#### TelegramSettings
- `bot_token`: str (required) - Format: NNNN:AAAA...
- `telethon_api_id`: int (required) - Telethon API identifier (integer value)
- `telethon_api_hash`: str (required) - Telethon API secret
- `telethon_session_name`: str (default: "bot_session") - Session file name

#### AISettings
- `gemini_api_key`: str (required) - Google Gemini API key
- `groq_api_key`: str (required) - Groq API key
- `openrouter_api_key`: str (required) - OpenRouter API key
- `zhipu_api_key`: str (required) - Zhipu AI API key
- `ai_models`: imported from config/ai_models.py (read-only reference)

#### SecuritySettings
- `encryption_key`: str (required) - Fernet key, 44-char base64 encoded
- `secret_key`: str (required) - JWT/session signing key, non-empty

#### PaymentSettings
- `shamcash_api_key`: str (required) - ShamCash payment gateway key
- `crypto_wallet_address`: str (required) - USDT TRC20 address (T-prefixed, 34 chars)

#### MonitoringSettings
- `sentry_dsn`: str | None (optional) - Sentry error tracking DSN
- `environment`: str (default: "development") - One of: development, staging, production
- `debug`: bool (default: False) - Debug mode flag

## Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| database_url | Must start with postgresql:// or postgresql+asyncpg:// | "DATABASE_URL must be valid PostgreSQL connection string" |
| redis_url | Must start with redis:// | "REDIS_URL must be valid Redis connection string" |
| bot_token | Must match pattern ^\d+:[A-Za-z0-9_-]{35,}$ | "BOT_TOKEN must be in format NNNN:AAAA..." |
| telethon_api_id | Must be positive integer | "TELETHON_API_ID must be a valid positive integer" |
| telethon_api_hash | Must be 32 hexadecimal characters | "TELETHON_API_HASH must be 32-character hexadecimal string" |
| encryption_key | Must be 44-char base64 string (validate with cryptography.fernet.Fernet) | "ENCRYPTION_KEY must be valid 44-character base64 Fernet key" |
| secret_key | Must be at least 32 characters | "SECRET_KEY must be at least 32 characters long" |
| crypto_wallet_address | Must be exactly 34 alphanumeric chars starting with 'T' | "CRYPTO_WALLET_ADDRESS must be valid USDT TRC20 address (T + 33 chars)" |
| environment | Must be one of: development, staging, production | "ENVIRONMENT must be one of: development, staging, production" |
| debug | Must be parseable as boolean | "DEBUG must be a boolean value (true/false)" |
| All API keys | Must be non-empty string | "{KEY_NAME} is required and cannot be empty" |

## Environment Variable Mapping

| Python Attribute | Environment Variable | Required | Default |
|------------------|---------------------|----------|---------|
| database_url | DATABASE_URL | Yes | - |
| pool_size | DATABASE_POOL_SIZE | No | 5 |
| max_overflow | DATABASE_MAX_OVERFLOW | No | 5 |
| connection_timeout | DATABASE_CONNECTION_TIMEOUT | No | 30 |
| redis_url | REDIS_URL | Yes | - |
| connection_timeout (Redis) | REDIS_CONNECTION_TIMEOUT | No | 5 |
| max_connections | REDIS_MAX_CONNECTIONS | No | 10 |
| bot_token | BOT_TOKEN | Yes | - |
| telethon_api_id | TELETHON_API_ID | Yes | - |
| telethon_api_hash | TELETHON_API_HASH | Yes | - |
| telethon_session_name | TELETHON_SESSION_NAME | No | "bot_session" |
| gemini_api_key | GEMINI_API_KEY | Yes | - |
| groq_api_key | GROQ_API_KEY | Yes | - |
| openrouter_api_key | OPENROUTER_API_KEY | Yes | - |
| zhipu_api_key | ZHIPU_API_KEY | Yes | - |
| encryption_key | ENCRYPTION_KEY | Yes | - |
| secret_key | SECRET_KEY | Yes | - |
| shamcash_api_key | SHAMCASH_API_KEY | Yes | - |
| crypto_wallet_address | CRYPTO_WALLET_ADDRESS | Yes | - |
| sentry_dsn | SENTRY_DSN | No | None |
| environment | ENVIRONMENT | No | "development" |
| debug | DEBUG | No | False |

## State Transitions

N/A - Settings are immutable after initialization (loaded once at startup).

## Relationships

- Settings → DatabaseSettings (1:1)
- Settings → RedisSettings (1:1)
- Settings → TelegramSettings (1:1)
- Settings → AISettings (1:1)
- Settings → SecuritySettings (1:1)
- Settings → PaymentSettings (1:1)
- Settings → MonitoringSettings (1:1)
- AISettings → config/ai_models.py (imports, read-only)
