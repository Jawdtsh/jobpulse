# Feature Specification: Migrate from Celery to TaskIQ

**Feature Branch**: `006-celery-to-taskiq-migration`  
**Created**: 2026-04-13  
**Status**: Draft  
**Input**: User description: "Migrate from Celery 5.4.0 to TaskIQ - strategic migration to align architecture with async-first codebase"

**Implementation Notes**:
- `cv_tasks.py` now uses MatchingService for business logic instead of direct repository calls
- `matching_service.py` has `match_cv_to_recent_jobs` method added
- `job_repository.py` has `find_similar_to_cv` method added
- `taskiq_app.py` uses lazy initialization to avoid test environment failures

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Migrate Task Queue Infrastructure (Priority: P1)

The development team needs to replace the Celery task queue with TaskIQ to achieve better async integration and performance.

**Why this priority**: This is the foundational change required before any other migration work can proceed. Without this, subsequent phases cannot be tested or deployed.

**Independent Test**: Can be fully tested by running the TaskIQ worker and scheduler as docker containers and verifying they connect to Redis and process tasks correctly.

**Acceptance Scenarios**:

1. **Given** a running Redis instance, **When** the TaskIQ worker starts, **Then** it connects successfully and logs "TaskIQ worker started successfully"
2. **Given** a running Redis instance, **When** the TaskIQ scheduler starts, **Then** it registers all scheduled tasks and logs their cron expressions
3. **Given** both worker and scheduler running, **When** a task is enqueued manually, **Then** the worker executes it and returns a result

---

### User Story 2 - Update Service Layer Task Calls (Priority: P2)

The service layer needs to use TaskIQ's kiq method instead of Celery's send_task to trigger background tasks.

**Why this priority**: All services that trigger background tasks must be updated for the migration to be complete. This affects CV evaluation and job ingestion triggering.

**Independent Test**: Can be tested by uploading a CV and verifying the ingestion pipeline is triggered via TaskIQ instead of Celery.

**Acceptance Scenarios**:

1. **Given** a CV upload triggers task call, **When** the service calls run_ingestion_pipeline.kiq(), **Then** the task is enqueued in Redis and executed by the TaskIQ worker
2. **Given** a new job is stored, **When** the service calls match_new_job.kiq(), **Then** the matching task is enqueued and executed

---

### User Story 3 - Update Docker Infrastructure (Priority: P3)

The docker-compose.yml needs to be updated to run TaskIQ workers instead of Celery workers.

**Why this priority**: Container orchestration must be updated to match the new task queue technology.

**Independent Test**: Can be tested by running docker-compose up and verifying the new container names and commands work correctly.

**Acceptance Scenarios**:

1. **Given** docker-compose is updated, **When** docker-compose up is run, **Then** taskiq-worker and taskiq-scheduler containers start successfully
2. **Given** containers are running, **When** logs are checked, **Then** worker and scheduler are properly connected to Redis

---

### Edge Cases

- What happens when TaskIQ cannot connect to Redis? Worker should fail fast with clear error message
- How does system handle task execution failures? Failures should be logged and retried according to TaskIQ configuration
- What happens if Celery is still referenced somewhere? Build should fail with import errors

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove Celery dependencies from requirements.txt and add TaskIQ dependencies (taskiq==0.11.7, taskiq-redis==1.0.0)
- **FR-002**: System MUST create workers/taskiq_app.py with Redis broker and result backend configuration
- **FR-003**: System MUST convert ingestion_tasks.py from Celery wrapper to TaskIQ native async task
- **FR-004**: System MUST convert matching_tasks.py from Celery wrapper to TaskIQ native async task
- **FR-005**: System MUST register scheduled tasks with cron expressions (every 3 minutes for ingestion, every 1 minute for matching)
- **FR-006**: Services MUST use TaskIQ kiq method instead of Celery send_task for async task triggering
- **FR-007**: Docker-compose MUST define taskiq-worker and taskiq-scheduler services with correct commands
- **FR-008**: Test files MUST be updated to mock TaskIQ task calls instead of Celery send_task

### Key Entities *(include if feature involves data)*

- **Task**: Background job execution unit defined with @broker.task decorator
- **Scheduler**: periodic task manager using cron expressions via TaskiqSchedule
- **Broker**: Redis-based message queue for task distribution
- **ResultBackend**: Redis-based storage for task execution results

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: TaskIQ worker starts and connects to Redis in under 10 seconds
- **SC-002**: Tasks execute 3-5x faster than Celery counterpart due to native async execution
- **SC-003**: System handles 10x more concurrent tasks compared to Celery configuration
- **SC-004**: All existing tests pass after migration with updated imports, achieving 100% test success rate

## Assumptions

- Existing Redis configuration will be reused (redis_url from settings)
- PostgreSQL remains unchanged - only task queue technology is being migrated
- No changes to service business logic - only infrastructure layer affected
- Job ingestion pipeline timing (every 3 minutes) remains unchanged
- Notification processing timing (every 1 minute) remains unchanged

## Clarifications

### Session 2026-04-13

- Q: What specific TaskIQ version should be used? → A: taskiq==0.11.7 and taskiq-redis==1.0.0
- Q: What reliability targets are expected for the TaskIQ infrastructure? → A: Worker restart on failure, scheduler persistence via Redis
- Q: Are there any observability requirements beyond logging? → A: Standard logging sufficient for infrastructure-level monitoring