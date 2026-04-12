# Quickstart: Job-CV Matching Engine

## Prerequisites

- PostgreSQL 16 with pgvector extension
- Redis 5.2.1+
- Python 3.12+
- Telegram bot configured (via SPEC-002)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start Celery worker
celery -A src.workers.matching_tasks worker --loglevel=info

# Start Celery Beat (for periodic notification delivery)
celery -A src.workers.matching_tasks beat --loglevel=info
```

## Usage

### Real-time Matching

Automatically triggered when a new job is ingested via SPEC-003 pipeline:

```python
# Matching runs automatically after job storage
await matching_service.match_job(job_id)
```

### Historical Matching

```python
# Pro user triggers historical search
await matching_service.match_historical(user_id, days=7, resend_existing=False)
```

### Notification Delivery

Notifications are sent via Celery Beat every minute:

```bash
# Process due notifications
celery -A src.workers.matching_tasks beat --schedule=60
```

## Bot Commands

| Command | Description |
|--------|-------------|
| /my_jobs | List your job matches |
| /set_threshold | Set your similarity threshold |
| /search_history | Search historical jobs (Pro only) |

## Configuration

Set in `config/settings.py`:

- `MATCHING_THRESHOLD_DEFAULT`: 0.80
- `NOTIFICATION_BATCH_WINDOW`: 180 (seconds, 3 minutes)
- `TIER_DELAYS`: {free: 3600, basic: 600, pro: 0}

## Testing

```bash
cd src
pytest
```

## Monitoring

- Check matching queue: `redis-cli ZRANGE notification_queue 0 -1`
- View match statistics: Logs in `src/logs/matching/`