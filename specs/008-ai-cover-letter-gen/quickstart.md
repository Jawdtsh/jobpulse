# Quickstart: AI Cover Letter Generation

**Feature**: 008-ai-cover-letter-gen  
**Date**: 2026-04-19

## Prerequisites

- Python 3.12+
- PostgreSQL 16 with pgvector extension
- Redis server
- Telegram Bot API token
- Gemini API key

## Quick Start

### 1. Database Setup

Run the migration to create/modify tables:

```bash
cd src
alembic upgrade head
```

### 2. Configuration

Add to `config/settings.py`:
```python
# Cover Letter Settings
COVER_LETTER_PROMPT_PATH: str = "config/prompts/cover_letter_prompt.txt"
QUOTA_RESET_CRON: str = "0 0 * * *"  # Daily at midnight
```

Create prompt template at `config/prompts/cover_letter_prompt.txt`:
```
Write a {length} cover letter in {language} language with {tone} tone.
Focus on: {focus}

Job Details:
- Position: {job_title}
- Company: {company}
- Location: {location}
- Description: {job_description}

My Background:
{cv_content}

Name: {user_name}
```

### 3. Start Services

```bash
# Start Redis
redis-server

# Start TaskIQ worker
python -m src.services.worker

# Start Telegram bot
python -m src.bot.main
```

## Usage Flow

1. User receives job notification with [Cover Letter] button
2. User clicks button → system checks quota and CV
3. If quota available + CV exists → show customization form
4. User selects options and clicks Generate
5. System calls Gemini API, saves cover letter, increments quota
6. Display cover letter with [Regenerate] and [Copy Text] buttons

## Testing

```bash
# Run unit tests
pytest tests/unit/services/test_cover_letter_service.py -v

# Run integration tests
pytest tests/integration/test_cover_letter_flow.py -v
```

## Key Files

| File | Purpose |
|------|---------|
| `src/services/cover_letter_service.py` | Main generation logic |
| `src/services/quota_service.py` | Quota tracking and reset |
| `src/bot/handlers/cover_letter.py` | Telegram handler |
| `src/repositories/cover_letter_repository.py` | Data access |
| `config/prompts/cover_letter_prompt.txt` | AI prompt template |

## Architecture

```
User (Telegram)
    ↓
Bot Handler (cover_letter.py)
    ↓
Cover Letter Service
    ├→ Quota Service (check/increment)
    ├→ CV Service (get CV data)
    ├→ AI Provider (Gemini API)
    └→ Cover Letter Repository (save)
    ↓
Database (PostgreSQL)
```