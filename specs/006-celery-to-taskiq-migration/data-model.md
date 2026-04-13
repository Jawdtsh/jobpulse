# Data Model: Migrate from Celery to TaskIQ

**Feature**: Task queue migration  
**Date**: 2026-04-13

## Entities

### Task: IngestionPipeline

**Purpose**: Scheduled job that runs the job ingestion pipeline

| Field | Type | Description |
|-------|------|-------------|
| name | str | "ingestion.run_pipeline" |
| schedule | str | "*/3 * * * *" (every 3 minutes) |
| broker | TaskiqBroker | Redis broker reference |
| async | bool | True (native async) |

**State**: Always RUNNING when scheduler active  
**Relationships**: Calls JobIngestionService.run_pipeline()

---

### Task: ProcessNotifications

**Purpose**: Scheduled job that processes due notifications

| Field | Type | Description |
|-------|------|-------------|
| name | str | "matching.process_notifications" |
| schedule | str | "* * * * *" (every 1 minute) |
| broker | TaskiqBroker | Redis broker reference |
| async | bool | True (native async) |

**State**: Always RUNNING when scheduler active  
**Relationships**: Calls NotificationService.process_due_notifications()

---

### Entity: TaskiqBroker

**Purpose**: Redis-based message queue for task distribution

| Field | Type | Description |
|-------|------|-------------|
| url | str | Redis connection URL |
| queue_name | str | "taskiq" (default) |
| result_backend | ResultBackend | Optional result storage |

---

### Entity: TaskiqScheduler

**Purpose**: Manages periodic task scheduling

| Field | Type | Description |
|-------|------|-------------|
| broker | TaskiqBroker | Task queue reference |
| sources | list | Task schedule sources |
| timezone | str | "UTC" (default) |

---

## Validation Rules

1. All tasks MUST be decorated with @broker.task
2. All scheduled tasks MUST register with scheduler.register_schedule
3. Redis URL MUST come from settings.redis.redis_url
4. Cron expressions MUST be valid 5-field format

## State Transitions

| State | Valid Transitions |
|-------|-----------------|
| PENDING | → RUNNING |
| RUNNING | → SUCCESS, FAILED |
| SUCCESS | Terminal |
| FAILED | Terminal |

## Data Flow

```
Scheduler → Cron trigger → Broker.enqueue() → Worker picks task → Task execution → Result stored in Redis
```

## Notes

- Tasks store results in Redis via RedisAsyncResultBackend
- Task execution results available for 24 hours (default TTL)
- Failed tasks logged with full traceback for debugging