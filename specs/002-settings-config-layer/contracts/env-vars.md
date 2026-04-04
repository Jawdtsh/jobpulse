# Environment Variable Contract

This document defines all environment variables required by the Settings & Config Layer.

## Required Variables

| Variable | Type | Format | Example |
|----------|------|--------|---------|
| `DATABASE_URL` | string | PostgreSQL URI | `postgresql+asyncpg://user:pass@localhost:5432/jobpulse` |
| `REDIS_URL` | string | Redis URI | `redis://localhost:6379/0` |
| `BOT_TOKEN` | string | NNNN:AAAA... | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `TELETHON_API_ID` | string | Numeric string | `12345678` |
| `TELETHON_API_HASH` | string | Hex string | `abcdef1234567890abcdef1234567890` |
| `GEMINI_API_KEY` | string | Non-empty | `AIzaSy...` |
| `GROQ_API_KEY` | string | Non-empty | `gsk_...` |
| `OPENROUTER_API_KEY` | string | Non-empty | `sk-or-...` |
| `ZHIPU_API_KEY` | string | Non-empty | `...` |
| `ENCRYPTION_KEY` | string | 44-char base64 | `your-fernet-key-here-44chars==` |
| `SECRET_KEY` | string | Non-empty | `your-secret-key-for-jwt` |
| `SHAMCASH_API_KEY` | string | Non-empty | `shamcash-key-...` |
| `CRYPTO_WALLET_ADDRESS` | string | T-prefixed, 34 chars | `TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` |

## Optional Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TELETHON_SESSION_NAME` | string | `bot_session` | Telethon session file name |
| `SENTRY_DSN` | string | (empty) | Sentry DSN for error tracking |
| `ENVIRONMENT` | string | `development` | One of: development, staging, production |
| `DEBUG` | bool | `false` | Enable debug mode |
| `DB_POOL_SIZE` | int | `5` | Database connection pool size |
| `DB_MAX_OVERFLOW` | int | `5` | Database max overflow connections |
| `DB_CONNECTION_TIMEOUT` | int | `30` | Database connection timeout (seconds) |
| `REDIS_CONNECTION_TIMEOUT` | int | `5` | Redis connection timeout (seconds) |
| `REDIS_MAX_CONNECTIONS` | int | `10` | Redis max connections in pool |

## Validation Rules

- All required variables MUST be present and non-empty
- `ENCRYPTION_KEY` MUST be a valid 44-character base64-encoded Fernet key
- `BOT_TOKEN` MUST match the pattern `^\d+:[a-zA-Z0-9_-]+$`
- `CRYPTO_WALLET_ADDRESS` MUST start with 'T' and be exactly 34 characters
- `ENVIRONMENT` MUST be one of: `development`, `staging`, `production`
- `DEBUG` MUST be a valid boolean string (`true`, `false`, `1`, `0`)

## Usage

```python
from config.settings import settings

# Access settings
db_url = settings.database.database_url
bot_token = settings.telegram.bot_token
gemini_key = settings.ai.gemini_api_key

# Settings are validated at import time
# If any required variable is missing or invalid, ImportError is raised
```
