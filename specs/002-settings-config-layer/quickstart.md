# Quickstart: Settings & Config Layer

## Prerequisites

- Python 3.12+
- Access to all required API keys and credentials (see `contracts/env-vars.md`)

## Setup

1. **Create .env file** in project root:

```bash
cp .env.example .env  # If template exists
```

2. **Add required environment variables** to `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/jobpulse

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELETHON_API_ID=12345678
TELETHON_API_HASH=abcdef1234567890abcdef1234567890

# AI Models
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=your-groq-key
OPENROUTER_API_KEY=your-openrouter-key
ZHIPU_API_KEY=your-zhipu-key

# Security
ENCRYPTION_KEY=your-44-char-base64-fernet-key==
SECRET_KEY=your-secret-key-for-jwt

# Payment
SHAMCASH_API_KEY=your-shamcash-key
CRYPTO_WALLET_ADDRESS=TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Monitoring (optional)
# SENTRY_DSN=
ENVIRONMENT=development
DEBUG=true
```

3. **Generate Fernet key**:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

4. **Import and use**:

```python
from config.settings import settings

# Access settings
print(settings.database.database_url)
print(settings.telegram.bot_token)
print(settings.ai.gemini_api_key)
```

## Testing

```bash
# Run settings tests
pytest tests/config/test_settings.py -v
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ValidationError: DATABASE_URL` | Missing or invalid database URL | Check DATABASE_URL in .env |
| `ValidationError: ENCRYPTION_KEY` | Invalid Fernet key format | Generate new key with `Fernet.generate_key()` |
| `ValidationError: BOT_TOKEN` | Invalid bot token format | Verify format: NNNN:AAAA... |
| `ValidationError: CRYPTO_WALLET_ADDRESS` | Invalid TRC20 address | Must start with 'T', 34 chars |
