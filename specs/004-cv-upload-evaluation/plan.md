# Implementation Plan: CV Upload & Evaluation

**Branch**: `004-cv-upload-evaluation` | **Date**: 2026-04-08 | **Spec**: [link](004-cv-upload-evaluation/spec.md)

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Enable users to upload CVs via Telegram bot for job matching. System parses PDF/DOCX/TXT, evaluates quality using Gemini AI, calculates completeness score, generates 768-dim embeddings, and stores encrypted using Fernet. Enforces subscription tier limits (Free/Basic=1 CV, Pro=2 CVs).

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, aiogram 3.x, SQLAlchemy 2.0 async, PostgreSQL 16 + pgvector  
**Storage**: PostgreSQL with pgvector extension, Redis for caching  
**Testing**: pytest  
**Target Platform**: Linux server (Telegram bot + REST API)  
**Project Type**: web-service (FastAPI + Telegram bot)  
**Performance Goals**: CV upload under 30s, evaluation under 10s, 95% extraction success  
**Constraints**: 5MB max file size, PDF/DOCX/TXT only, 768-dim embeddings, Fernet encryption  
**Scale/Scope**: 10k users expected, up to 2 CVs per user

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

| Gate | Status |
|------|--------|
| Clean Architecture (Routes→Services→Repositories) | ✅ Service layer needed |
| SOLID Principles | ✅ DI for services |
| Clean Code (max 20 lines/function) | ✅ Enforced |
| Security First (Fernet encryption) | ✅ Already implemented in src/utils/encryption.py |
| Configuration Management (config/ai_models.py) | ✅ Use existing config |
| Language Policy (English only) | ✅ Enforced |
| Database Changes via Alembic | ⚠️ May need migration for new columns |
| Testing Requirements (80% coverage) | ✅ Required |
| Error Handling (Custom exceptions) | ✅ Required |
| Async Best Practices | ✅ Use async/await |

**Needs Alembic migration**: New columns for evaluation tracking (skills, experience, suggestions, completeness_score)

## Project Structure

### Documentation (this feature)

```text
specs/004-cv-upload-evaluation/
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
│   ├── user_cv.py       # Existing - needs new columns for evaluation
│   └── user.py          # Existing - add CV relationship if missing
├── repositories/
│   ├── cv_repository.py # Existing - add CV management methods
│   └── user_repository.py
├── services/
│   ├── cv_service.py    # NEW - main business logic
│   ├── cv_parser.py     # NEW - text extraction (PDF/DOCX/TXT)
│   ├── cv_evaluator.py # NEW - AI evaluation using Gemini
│   ├── cv_embedding.py # NEW - embedding generation
│   └── ai_provider_service.py # Existing - reused
├── utils/
│   ├── encryption.py    # Existing - Fernet encryption
│   └── vectors.py       # Existing - vector utilities
└── bot/
    ├── handlers/        # NEW - Telegram bot handlers for CV
    └── commands.py      # NEW - CV-related commands

tests/
├── unit/
│   ├── test_cv_parser.py
│   ├── test_cv_evaluator.py
│   └── test_cv_service.py
└── integration/
    └── test_cv_repository.py

config/
├── settings.py          # Existing
└── ai_models.py         # Existing - add CV evaluation model
```

**Structure Decision**: Single Python project with FastAPI backend and Telegram bot. CV parsing and evaluation handled in service layer. Existing encryption and embedding utilities reused.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification.

| Principle | Justification |
|-----------|---------------|
| No violations | All new services (cv_parser, cv_evaluator, cv_service) follow single responsibility. Existing encryption/embedding utilities reused. Constitution-compliant architecture maintained. |