# Implementation Plan: Migrate from Celery to TaskIQ

**Branch**: `006-celery-to-taskiq-migration` | **Date**: 2026-04-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-celery-to-taskiq-migration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Migrate task queue infrastructure from Celery 5.4.0 to TaskIQ 0.11.7 to achieve native async integration with the async-first codebase, improving performance and reducing sync/async mixing in the codebase.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: taskiq==0.11.7, taskiq-redis==1.0.0  
**Storage**: Redis (existing, via settings.redis.redis_url)  
**Testing**: pytest (existing)  
**Target Platform**: Linux server (Docker containers)  
**Project Type**: Backend service with background task processing  
**Performance Goals**: 3-5x faster task execution, 10x more concurrent tasks  
**Constraints**: Worker startup under 10 seconds, backward compatible API for task triggering  
**Scale/Scope**: 7 files to modify, ~3 hours estimated effort

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| X. Async Best Practices | IMPROVED | TaskIQ provides native async (vs Celery's sync wrapper) |
| V. Configuration Management | COMPLIANT | All Redis config via settings.py |
| I. Clean Architecture | COMPLIANT | Only infrastructure layer affected |
| VIII. Testing Requirements | ADDRESSED | Tests updated with new mocks |
| Technology Stack | UPDATE NEEDED | Constitution line 44: "Task Queue: Celery" → "Task Queue: TaskIQ" |

## Project Structure

### Documentation (this feature)

```text
specs/006-celery-to-taskiq-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md            # /speckit.tasks output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
workers/
├── taskiq_app.py          # NEW: TaskIQ application config
├── celery_app.py        # DELETED
└── tasks/
    ├── ingestion_tasks.py # MODIFIED: Celery → TaskIQ
    └── matching_tasks.py # MODIFIED: Celery → TaskIQ

src/services/
├── cv_service.py             # MODIFIED: send_task → kiq()
├── job_ingestion_service.py # MODIFIED: send_task → kiq()

tests/
├── [test files]           # MODIFIED: updated imports/mocks

docker-compose.yml         # MODIFIED: services
requirements.txt         # MODIFIED: dependencies
```

**Structure Decision**: Single existing backend project. Modifications to existing files only. No new source code directories required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | This is a migration, not new feature | N/A |
