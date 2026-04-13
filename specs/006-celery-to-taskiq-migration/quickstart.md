# Quickstart: Migrate from Celery to TaskIQ

## Prerequisites

- Python 3.12+
- Redis running
- Access to settings.redis.redis_url

## Installation

```bash
# Install new dependencies
pip install taskiq==0.11.7 taskiq-redis==1.0.0
```

## Development

### Start TaskIQ Worker

```bash
taskiq worker workers.taskiq_app:broker --fs-discover
```

Expected output:
```
[INFO] TaskIQ worker started successfully
[INFO] Discovered tasks: ingestion.run_pipeline, matching.process_notifications
[INFO] Listening for tasks...
```

### Start TaskIQ Scheduler

```bash
taskiq scheduler workers.taskiq_app:scheduler --fs-discover
```

Expected output:
```
[INFO] Scheduler started
[INFO] Registered schedules:
  ingestion.run_pipeline (cron: */3 * * * *)
  matching.process_notifications (cron: * * * * *)
```

### Test Manual Task Execution

```python
import asyncio
from workers.tasks.ingestion_tasks import run_ingestion_pipeline

asyncio.run(run_ingestion_pipeline.kiq())
```

## Docker

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Start worker
docker-compose up taskiq-worker

# Start scheduler
docker-compose up taskiq-scheduler
```

## Verification

1. Worker starts and connects to Redis in < 10 seconds
2. Tasks execute successfully
3. All tests pass

## Common Issues

| Issue | Solution |
|-------|----------|
| Redis connection failed | Check settings.redis.redis_url |
| Tasks not discovered | Ensure --fs-discover flag used |
| ImportError for celery | Old Celery references still exist |