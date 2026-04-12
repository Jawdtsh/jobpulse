# Implementation Plan: Job-CV Matching Engine

**Branch**: `005-job-cv-matching` | **Date**: 2026-04-12 | **Spec**: spec.md
**Input**: Feature specification from `specs/005-job-cv-matching/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Job-CV Matching Engine: Real-time semantic matching of jobs against user CVs using pgvector cosine similarity, with tiered notification delivery via Telegram. Core feature for job matching pipeline (SPEC-005).

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, aiogram 3.x, Celery 5.4.0, Redis 5.2.1, SQLAlchemy 2.0 async, pgvector 0.4.2  
**Storage**: PostgreSQL 16 with pgvector extension  
**Testing**: pytest (from AGENTS.md: cd src; pytest)  
**Target Platform**: Linux server  
**Project Type**: backend service with Telegram bot integration  
**Performance Goals**: Matching completes within 5 seconds for 10,000 active CVs  
**Constraints**: Notification delay accuracy within ±30 seconds, Redis for queue, Celery Beat for periodic tasks  
**Scale/Scope**: 10,000+ active CVs, real-time matching on job ingestion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Clean Architecture | ✅ PASS | Matching service will call job_matches repository |
| SOLID | ✅ PASS | Dependency injection via constructor patterns |
| Clean Code | ✅ PASS | Max 20 lines per function enforced |
| Security First | ✅ PASS | No CV data stored in matching |
| Configuration | ✅ PASS | Settings via config/settings.py |
| Database Changes | ✅ PASS | Alembic migrations for schema |
| Testing | ✅ PASS | Unit and integration tests required |
| Error Handling | ✅ PASS | Custom exceptions + logging + Sentry |
| Async | ✅ PASS | async/await throughout

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── job_match.py          # JobMatch entity
│   ├── user_cv.py           # UserCV entity (from SPEC-004)
│   └── job.py               # Job entity (from SPEC-003)
├── services/
│   ├── matching_service.py # Core matching logic with pgvector
│   ├── notification_service.py # Tiered notification delivery
│   └── threshold_service.py # Similarity threshold management
├── repositories/
│   ├── job_match_repository.py
│   ├── user_cv_repository.py
│   └── job_repository.py
├── workers/
│   └── matching_tasks.py    # Celery tasks for matching pipeline
└── bot/
    └── handlers.py         # Telegram bot handlers for matching commands

tests/
├── unit/
│   ├── test_matching_service.py
│   └── test_notification_service.py
└── integration/
    └── test_matching_pipeline.py
```

**Structure Decision**: Using single project structure. Source code follows Clean Architecture with Services > Repositories > Database pattern as per Constitution. Matching worker tasks integrate with existing SPEC-003 job ingestion pipeline.

## Phase 0: Research

*Research completed during spec generation - no additional research needed.*

### Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| pgvector cosine similarity | Native PostgreSQL support, efficient for large CV datasets |
| Redis Sorted Set for notification queue | Native support for score-based delayed delivery |
| Celery Beat for periodic task | Integrates with existing SPEC-003 Celery setup |
| 3-minute batching window | Balances notification frequency with user experience |

## Phase 1: Design

*Data model and contracts generated from feature spec entities.*

### Entities

- **JobMatch**: job_id, user_id, cv_id, similarity_score, is_notified, notified_at, is_clicked, clicked_at
- **NotificationQueue**: (Redis) - score=notification_time, value=JSON(match_id, user_id, job_id, cv_id, tier, batch_key)
- **JobCategory**: id, name, similarity_threshold (default 0.80)
- **UserPreferences**: id, user_id, similarity_threshold (0.60-1.00)

## Complexity Tracking

| Principle | Compliance |
|-----------|------------|
| Clean Architecture | ✅ Services → Repositories → Database pattern maintained |
| Max 20 lines/function | ✅ Matching logic split into small functions: calculate_similarity(), filter_active_cvs(), apply_threshold() |
| Max 200 lines/file | ✅ Services split: MatchingService (matching), NotificationService (delivery), ThresholdService (config) |
| No violations | All new code follows constitution principles |

## Integration Points

### SPEC-003 (Job Ingestion Pipeline)
- **Hook**: After job storage in `JobRepository.create()`
- **Call**: `MatchingService.match_new_job(job_id)`
- **Location**: `src/workers/tasks/ingestion_tasks.py`

### SPEC-004 (CV Upload & Evaluation)
- **Hook**: After CV evaluation completes
- **Call**: `MatchingService.match_historical_jobs(cv_id, days=7)` (Pro users only)
- **Location**: `src/services/cv_service.py`

### SPEC-006 (Bot Handlers - Future)
- **Commands**: `/my_jobs`, `/set_threshold`, `/search_history`
- **Handlers**: `src/bot/handlers/matching_handlers.py`

### SPEC-007 (Cover Letters - Future)
- **Trigger**: "Generate Cover Letter" button in notification
- **Data**: `job_id`, `cv_id` from notification payload
