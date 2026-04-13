# Research: Migrate from Celery to TaskIQ

**Feature**: Migrate from Celery 5.4.0 to TaskIQ 0.11.7  
**Date**: 2026-04-13

## Technical Decisions

### Decision 1: TaskIQ Library Version

**Choice**: taskiq==0.11.7, taskiq-redis==1.0.0

**Rationale**: Latest stable version with Redis broker and async-native support. taskiq-redis provides ListQueueBroker and RedisAsyncResultBackend required for this migration.

**Alternatives considered**:
- celery-redis: Would require keeping Celery (rejected - purpose is to migrate away from Celery)
- Custom Redis implementation: Too much maintenance overhead (rejected)

---

### Decision 2: Broker Configuration

**Choice**: ListQueueBroker for task queue, RedisAsyncResultBackend for results

**Rationale**: TaskIQ's native Redis broker implementations. ListQueueBroker provides FIFO queue semantics matching Celery. RedisAsyncResultBackend stores task results for later retrieval.

**Alternatives considered**:
- In-memory broker: Not suitable for distributed worker setup (rejected)
- RabbitMQ broker: Would require additional infrastructure (rejected)

---

### Decision 3: Task Calling Pattern

**Choice**: Direct kiq() method calls (e.g., `run_ingestion_pipeline.kiq()`)

**Rationale**: TaskIQ provides .kiq() method on decorated tasks for async queuing. No asyncio.to_thread wrapper needed - native async throughout.

**Alternatives considered**:
- send_task-style: Not available in TaskIQ (N/A)
- Celery-like send_task wrapper: Would re-introduce sync/async mixing (rejected)

---

### Decision 4: Scheduler Configuration

**Choice**: TaskiqSchedule with cron expressions for periodic tasks

**Rationale**: TaskIQ's scheduler source supports cron expressions directly. Maintains existing timing (every 3 minutes for ingestion, every 1 minute for matching).

**Alternatives considered**:
- Interval-based: Less precise than cron for exact timing (rejected)
- External cron: Would require additional orchestration (rejected)

---

### Decision 5: Docker Services

**Choice**: taskiq-worker and taskiq-scheduler containers

**Rationale**: Matches TaskIQ CLI commands. Worker processes tasks, scheduler runs periodic jobs.

**Alternatives considered**:
- Single combined container: Would blur separation of concerns (rejected)
- celery-flower container: Monitoring tool not needed for v1 (deferred)

---

## Implementation Notes

1. **Import changes**: `from workers.taskiq_app import broker` instead of `from workers.celery_app import celery_app`

2. **Task decoration**: `@broker.task(task_name="...")` instead of `@celery_app.task(name="...", bind=True)`

3. **Service calls**: `await task.kiq()` instead of `await asyncio.to_thread(celery_app.send_task, '...')`

4. **Cron format**: TaskIQ uses standard cron format (e.g., `"*/3 * * * *"` for every 3 minutes)

5. **Result handling**: TaskIQ returns TaskiqResult objects; use `.await_result()` for synchronous access if needed

## References

- TaskIQ Documentation: https://taskiq.readthedocs.io
- TaskIQ Redis Broker: https://taskiq-redis.readthedocs.io