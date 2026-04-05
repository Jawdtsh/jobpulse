# Contract: Job Ingestion Pipeline Task

## Purpose

Defines the Celery task interface for the job ingestion pipeline. This is the entry point for the scheduled pipeline execution.

## Task: `run_ingestion_pipeline`

### Celery Task Configuration

```python
@app.task(
    name="ingestion.run_pipeline",
    bind=True,
    max_retries=0,
    acks_late=True,
    reject_on_worker_lost=True,
)
async def run_ingestion_pipeline(self) -> dict
```

**Schedule**: Every 3 minutes via Celery Beat
```python
app.conf.beat_schedule = {
    "run-ingestion-pipeline": {
        "task": "ingestion.run_pipeline",
        "schedule": crontab(minute="*/3"),
    },
}
```

### Parameters

None (scheduled task, no arguments).

### Returns

```python
{
    "status": "success" | "partial" | "failed",
    "channels_processed": int,
    "messages_scraped": int,
    "messages_filtered": int,
    "messages_classified": int,
    "jobs_extracted": int,
    "jobs_deduplicated": int,
    "jobs_stored": int,
    "errors": [
        {
            "stage": str,
            "channel_id": str | None,
            "message_id": int | None,
            "error": str,
        }
    ],
    "duration_seconds": float,
}
```

### Distributed Lock

The task acquires a Redis-based distributed lock (`pipeline:lock`) before execution to prevent concurrent runs. If the lock is already held (previous run still in progress), the task skips execution and logs a warning.

### Failure Behavior

- **All sessions banned**: Task returns `{"status": "failed"}`, sends admin alert, does not retry
- **All AI providers exhausted**: Task returns `{"status": "partial"}` with errors list, continues processing remaining messages
- **Unhandled exception**: Task logs error, sends admin alert, does not auto-retry (next scheduled run will attempt again)
