# Quickstart: Job Ingestion Pipeline

## Prerequisites

- PostgreSQL 16 with pgvector extension running (via docker-compose)
- Redis 7.4 running (via docker-compose)
- Python 3.12+ with dependencies installed (`pip install -r requirements.txt`)
- Environment variables configured (`.env` file with Telegram, AI, database credentials)
- SPEC-001 (Database Schema) migrations applied
- SPEC-002 (Settings & Config) validated
- At least one active Telegram session in `telegram_sessions` table
- At least one active monitored channel in `monitored_channels` table

## Setup Steps

### 1. Run Database Migration

```bash
cd migrations
alembic upgrade head
```

This creates the `spam_rules` table (migration 005) and seeds initial spam rules.

### 2. Seed Spam Rules (if not done by migration)

```python
# From Python shell or script
from src.repositories.spam_rule_repository import SpamRuleRepository
from src.database import get_session

async def seed_spam_rules():
    async with get_session() as session:
        repo = SpamRuleRepository(session)
        # Add spam keywords
        await repo.create(pattern="ربح سريع", rule_type="spam_keyword")
        await repo.create(pattern="عمل من المنزل", rule_type="spam_keyword")
        # Add scam indicators
        await repo.create(pattern="رسوم تسجيل", rule_type="scam_indicator")
        await repo.create(pattern="تحويل أموال", rule_type="scam_indicator")
```

### 3. Start Celery Worker

```bash
celery -A workers.celery_app worker --loglevel=info --pool=asyncio
```

### 4. Start Celery Beat (Scheduler)

```bash
celery -A workers.celery_app beat --loglevel=info
```

The pipeline will automatically run every 3 minutes.

### 5. Monitor Pipeline Execution

Check Celery logs for pipeline run output:

```
[INFO] Task ingestion.run_pipeline succeeded
  channels_processed: 5
  messages_scraped: 230
  messages_filtered: 180
  messages_classified: 35
  jobs_extracted: 20
  jobs_deduplicated: 5
  jobs_stored: 15
```

## Manual Trigger

Run the pipeline immediately without waiting for the next scheduled interval:

```bash
celery -A workers.celery_app call ingestion.run_pipeline
```

Or from Python:

```python
from workers.tasks.ingestion_tasks import run_ingestion_pipeline
result = run_ingestion_pipeline.delay()
print(result.get())
```

## Verification

### Check Stored Jobs

```sql
SELECT id, title, company, source_channel_id, created_at
FROM jobs
ORDER BY created_at DESC
LIMIT 10;
```

### Check Channel Stats

```sql
SELECT username, jobs_found, false_positives, last_scraped_at, is_active
FROM monitored_channels;
```

### Check AI Usage

```bash
redis-cli KEYS "ai_daily_usage:*"
redis-cli GET "ai_daily_usage:gemini-2.5-flash-lite:2026-04-05"
```

## Troubleshooting

### Pipeline Not Running

1. Verify Celery Beat is running: `celery -A workers.celery_app status`
2. Check Redis connection: `redis-cli ping`
3. Verify schedule: `celery -A workers.celery_app inspect scheduled`

### All Sessions Banned

1. Check session status: `SELECT phone_number, is_active, is_banned FROM telegram_sessions;`
2. Add new sessions or reactivate existing ones
3. Pipeline will resume on next scheduled run

### AI Provider Errors

1. Check API key configuration in `.env`
2. Verify daily limits: `redis-cli GET "ai_daily_usage:{model}:{date}"`
3. Check fallback chain in `config/ai_models.py`

### Spam Rules Not Updating

1. Clear Redis cache: `redis-cli DEL spam_rules:all`
2. Cache refreshes automatically within 5 minutes
