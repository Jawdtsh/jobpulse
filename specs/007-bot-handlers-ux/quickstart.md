# Quickstart: Bot Handlers & UX Flow

**Feature Branch**: `007-bot-handlers-ux`  
**Date**: 2026-04-16

## Prerequisites

- Python 3.12+
- PostgreSQL 16 with pgvector extension
- Redis 5.2.1+
- Telegram Bot Token (from config/settings.py)

## Setup

1. **Install dependencies**:
   ```bash
   pip install aiogram==3.4.1 redis==5.2.1
   ```

2. **Run migrations**:
   ```bash
   alembic upgrade head
   ```
   (Creates `saved_jobs` table and adds `is_dismissed` column)

3. **Configure bot**:
   Ensure `telegram.bot_token` in `config/settings.py`

## Project Structure

```
src/bot/
├── __init__.py
├── router.py           # Main router
├── middlewares.py      # Auth, rate-limit, session
├── keyboards.py        # Inline/Reply keyboards
├── filters.py          # Custom filters
├── states.py           # FSM states
├── formatters.py       # Message formatters
└── handlers/
    ├── __init__.py
    ├── start.py        # /start, /help
    ├── cv_upload.py    # /upload_cv
    ├── cv_management.py # /my_cvs
    ├── job_notifications.py # Notification callbacks
    ├── my_jobs.py      # /my_jobs
    ├── settings.py     # /settings
    ├── referral.py     # /invite
    ├── subscription.py # /subscribe
    └── errors.py       # /cancel, errors
```

## Key Services (NEW)

- `BotSessionService`: Manages user session state in Redis
- `SavedJobService`: CRUD for saved jobs
- `RateLimiter`: Per-user rate limiting middleware
- `i18n`: Bilingual message resolver

## Running the Bot

### Webhook Mode (Production)
```bash
python -m src.bot.webhook
```

### Polling Mode (Development)
```bash
python -m src.bot.polling
```

## Testing

```bash
cd src
pytest tests/unit/bot/ -v
```

## Bot Commands Quick Reference

| Command | Description |
|---------|-------------|
| `/start` | Register/welcome user |
| `/help` | Show commands |
| `/upload_cv` | Upload CV flow |
| `/my_cvs` | List CVs |
| `/my_jobs` | Browse saved jobs |
| `/settings` | Edit preferences |
| `/invite` | Referral link |
| `/subscribe` | View tiers |
| `/cancel` | Cancel flow |

## Environment Variables

- `TELEGRAM_BOT_TOKEN` - Bot API token
- `REDIS_URL` - Redis connection (default: redis://localhost:6379)
- `DATABASE_URL` - PostgreSQL connection

## Next Steps

1. Implement handlers in `src/bot/handlers/`
2. Create BotSessionService with Redis
3. Create SavedJobService and repository
4. Add rate limiting middleware
5. Implement i18n message resolver
6. Write unit tests