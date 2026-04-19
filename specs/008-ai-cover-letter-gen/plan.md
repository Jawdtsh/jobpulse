# Implementation Plan: AI Cover Letter Generation

**Branch**: `008-ai-cover-letter-gen` | **Date**: 2026-04-19 | **Spec**: spec.md
**Input**: Feature specification from `spec.md`

**Note**: This plan was created by the `/speckit.plan` command.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

AI-powered cover letter generation for job applications with daily quota management (Free: 3, Basic: 15, Pro: 50 per day), Damascus timezone tracking, and Gemini AI integration. Users generate cover letters from job notifications or saved jobs with customization options (tone, length, focus, language).

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, aiogram 3.x, Google Generative AI (gemini-1.5-flash/pro), SQLAlchemy 2.0 async, PostgreSQL 16 with pgvector  
**Storage**: PostgreSQL 16 with pgvector extension  
**Testing**: pytest  
**Target Platform**: Linux server (Telegram Bot)  
**Project Type**: web-service (Telegram Bot API backend)  
**Performance Goals**: 10 seconds p95 latency for cover letter generation  
**Constraints**: <200ms p95 for quota checks, Damascus timezone (Asia/Damascus) for daily reset  
**Scale/Scope**: Telegram bot users, 3-tier subscription model  

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| Clean Architecture (Layer Separation) | PASS | Routes → Services → Repositories pattern exists |
| SOLID Principles | PASS | Existing services follow DI patterns |
| Max 20 lines/function | PASS | Will enforce in implementation |
| Max 200 lines/file | PASS | Will enforce in implementation |
| Type hints required | PASS | Existing codebase uses type hints |
| Fernet encryption for CV data | PASS | CV data encrypted at rest |
| No hardcoded config values | PASS | Settings via config/settings.py |
| Bilingual UI (Arabic + English) | PASS | i18n pattern established |
| Alembic for DB migrations | PASS | Existing migration pattern |
| Tests required | PASS | 80% coverage target |

## Project Structure

### Documentation (this feature)

```text
specs/008-ai-cover-letter-gen/
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
├── bot/
│   ├── handlers/        # Telegram bot handlers (SPEC-007)
│   ├── keyboards.py     # Inline keyboards
│   ├── states.py        # FSM states
│   └── router.py        # Bot router
├── services/            # Business logic layer
│   ├── cover_letter_service.py  # NEW - Cover letter generation
│   ├── quota_service.py         # NEW - Daily quota management
│   └── ...
├── repositories/        # Data access layer
│   ├── cover_letter_repository.py  # EXISTS - needs enhancement
│   └── ...
├── models/              # SQLAlchemy models
│   ├── cover_letter_log.py  # EXISTS - needs fields update
│   └── ...
└── database.py          # DB session management

config/
├── settings.py          # Settings (Constitution: all config from here)
└── ai_models.py         # AI model names

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: Single project with clean layer separation. New services go in `src/services/`, new handlers in `src/bot/handlers/`, new repositories extend existing `src/repositories/`.

## Complexity Tracking

No Constitution violations require justification.

## Phase Status

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0: Research | COMPLETE | Damascus timezone, Gemini API, prompt storage, quota reset |
| Phase 1: Design | COMPLETE | Data model, contracts, quickstart, agent context |
| Phase 2: Tasks | COMPLETE | With additions for integration points |

## Integration Points

| Dependency | Spec | Integration | Usage |
|------------|------|-------------|-------|
| SPEC-004 (CV Upload) | CVService.get_cv_by_id | src/services/cv_service.py | Get parsed_text for prompt |
| SPEC-005 (Job Matching) | JobRepository.get_by_id | src/repositories/job_repository.py | Get job description for prompt |
| SPEC-007 (Bot Handlers) | Bot handlers extension | src/bot/keyboards.py, src/bot/utils/i18n.py | Keyboards and bilingual messages |
| SPEC-009 (Payment) | Payment hooks | user_quota_tracking.purchased_extra | Add purchased generations to quota |
