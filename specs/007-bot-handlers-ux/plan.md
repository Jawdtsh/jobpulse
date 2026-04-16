# Implementation Plan: Bot Handlers & UX Flow

**Branch**: `007-bot-handlers-ux` | **Date**: 2026-04-16 | **Spec**: specs/007-bot-handlers-ux/spec.md
**Input**: Feature specification from `/specs/007-bot-handlers-ux/spec.md`

## Summary

Build a complete Telegram bot user interface using aiogram 3.x that enables users to register, upload CVs, receive job match notifications, manage saved jobs, configure preferences, view subscription plans, and handle errors gracefully. Uses Redis-backed FSM for multi-step flows and follows clean architecture with repository pattern.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: aiogram 3.x, FastAPI, SQLAlchemy 2.0 async, Redis, TaskIQ  
**Storage**: PostgreSQL 16 with pgvector, Redis (session state)  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Linux server (Telegram Bot in webhook mode)  
**Project Type**: Telegram Bot / Web Service  
**Performance Goals**: <2s registration, <30s CV evaluation, <1s job list load, <500ms button response, <5s session expiry  
**Constraints**: <200ms p95, 30 msg/s rate limit handling  
**Scale/Scope**: ~10k users expected

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| I. Clean Architecture | PASS | Routes → Services → Repositories → DB |
| II. SOLID Principles | PASS | DI used, single responsibility functions |
| III. Clean Code Rules | PASS | Max 20 lines/function, type hints present |
| IV. Security First | PASS | Fernet encryption on CVs, input validation |
| V. Configuration Management | PASS | All config via settings.py |
| VI. Language Policy | PASS | Bilingual (Arabic + English) for user messages |
| VII. Database Changes | PASS | Alembic migrations required |
| VIII. Testing Requirements | PASS | Unit tests required for services |
| IX. Error Handling | PASS | Custom exceptions, Sentry, logging |
| X. Async Best Practices | PASS | async/await, connection pooling |

## Project Structure

### Documentation (this feature)

```text
specs/007-bot-handlers-ux/
├── plan.md              # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output
└── tasks.md              # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── bot/
│   ├── __init__.py
│   ├── handlers.py           # Existing handlers (refactor needed)
│   ├── handlers/              # NEW: modular handlers
│   │   ├── __init__.py
│   │   ├── registration.py    # /start, /help
│   │   ├── cv_upload.py       # CV upload flow with FSM
│   │   ├── cv_management.py   # /my_cvs, delete
│   │   ├── job_notifications.py # match notifications
│   │   ├── saved_jobs.py      # /my_jobs, save/unsave
│   │   ├── settings.py        # /settings, preferences
│   │   ├── referral.py        # /invite, share
│   │   ├── subscription.py    # /subscribe
│   │   └── errors.py          # /cancel, error handling
│   ├── keyboards.py           # NEW: inline keyboard builders
│   ├── middlewares.py         # NEW: Rate Limiter and Callback Validation Middlewares (foundational infrastructure)
│   └── utils/
│       └── i18n.py            # NEW: bilingual message resolver
├── services/
│   ├── bot_session_service.py # NEW: Redis-backed session FSM
│   ├── saved_job_service.py   # NEW: saved jobs CRUD
│   ├── notification_service.py # existing, extend for rich notifications
│   └── cv_service.py          # existing, extend with quota checks
├── repositories/
│   ├── saved_job_repository.py # NEW: saved_jobs table
│   ├── user_repository.py     # existing
│   └── match_repository.py    # existing, extend
├── models/
│   ├── user.py                # existing
│   ├── user_cv.py             # existing
│   ├── language.py            # NEW: languages table
│   ├── saved_job.py           # NEW: saved_jobs table
│   └── job_match.py           # existing, add is_dismissed
config/
├── settings.py                 # existing
└── ai_models.py               # existing

tests/
├── unit/
│   ├── services/
│   │   ├── test_bot_session_service.py
│   │   └── test_saved_job_service.py
│   └── bot/
│       ├── test_registration.py
│       └── test_cv_upload.py
└── integration/
    └── test_bot_flows.py
```

**Structure Decision**: Modular handler structure under `src/bot/handlers/` with service layer for business logic and repository pattern for data access. Redis used for BotSession state management.

## Complexity Tracking

| Constitution Principle | Compliance Strategy | Implementation Approach |
|------------------------|---------------------|--------------------------|
| I. Clean Architecture | Routes → Services → Repositories → DB | Handlers call services, services call repositories |
| II. SOLID Principles | Single responsibility, DI | Each handler file handles one user story |
| III. Clean Code Rules | Max 20 lines/function, max 200 lines/file | Modular handler structure split by feature |
| IV. Security First | Input validation, Fernet encryption | Validate all inputs, existing CV encryption |
| V. Configuration Management | All config via settings.py | Bot token, Redis URL from settings |
| VI. Language Policy | Bilingual Arabic + English | i18n utility loads messages from JSON |
| VII. Database Changes | Alembic migrations only | Migrations 008, 009 for new tables/columns |
| VIII. Testing Requirements | Unit tests for services | T077-T080 in Phase 12 |
| IX. Error Handling | Custom exceptions, Sentry | Graceful degradation in Redis unavailability |
| X. Async Best Practices | async/await, connection pooling | Async handlers, proper session management |

## Integration Points

This SPEC integrates with other specifications as follows:

| Source SPEC | Integration | Implementation |
|-------------|-------------|----------------|
| SPEC-004 (CV Upload) | Call `CVService.upload_cv()`, display evaluation results | Task T024: Integrate with existing CV evaluation service |
| SPEC-005 (Job Matching) | Receive notifications, send user preferences (similarity threshold) | Tasks T034-T041: Notification handler uses user preferences |
| SPEC-006 (Task Queue) | Queue background tasks for CV processing | Task T028: FSM state transitions for async CV evaluation |
| SPEC-008 (Cover Letter) | UI button present but functionality deferred | Task T036: Cover Letter button shows "coming soon" message |
| SPEC-009 (Payment) | UI button present but functionality deferred | Task T067: Choose Plan buttons are non-functional placeholders |

## Phase 0: Research Complete

Research completed in `research.md`. Key findings:
- Aiogram 3.x FSM with Redis context for session state
- 10-minute session expiry
- Rate limiting via middleware (~30 msg/s)
- Bilingual messages (Arabic + English)
- File validation: PDF, DOCX, TXT, max 5MB
- Tier-based CV limits: Free/Basic=1, Pro=2
- Pagination: 5 jobs per page

## Phase 1: Design Artifacts

### Data Model

See `data-model.md` for entity definitions:
- SavedJob table (new)
- BotSession (Redis-based)
- JobMatch.is_dismissed column

### Contracts

See `/contracts/` for interface definitions:
- Telegram Bot command schema
- Inline keyboard callback format
- Notification message template

### Quick Start

See `quickstart.md` for implementation guide.
