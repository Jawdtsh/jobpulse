# Implementation Plan: Database Schema & Migrations

**Branch**: `001-database-schema` | **Date**: 2026-03-28 | **Spec**: specs/001-database-schema/spec.md
**Input**: Feature specification from `/specs/001-database-schema/spec.md`

## Summary

This is the foundation spec for JobPulse AI database layer. Primary requirement: Create 12 database tables with vector embeddings, Fernet encryption, and Alembic migrations. Technical approach: Use SQLAlchemy 2.0 async with pgvector for vector storage, implement repository pattern per Constitution I, and ensure all config from settings.py per Constitution V.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, pgvector, Fernet (cryptography)  
**Storage**: PostgreSQL 16 with pgvector extension  
**Testing**: pytest with async support, pytest-cov  
**Target Platform**: Linux server (Docker)  
**Project Type**: Web service with background workers  
**Performance Goals**: Vector similarity queries <500ms for 100k records, connection pool with 5-10 connections  
**Constraints**: Fernet encryption required for CV data, HNSW indexes (m=16, ef_construction=64), all timestamps UTC  
**Scale/Scope**: 12 tables, ~100k user CVs, ~1M job postings expected  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Clean Architecture (I) | PASS | Repository pattern required - implemented via AbstractRepository base class |
| SOLID Principles (II) | PASS | Single Responsibility - separate repositories per entity; Dependency Injection via constructor |
| Clean Code Rules (III) | PASS | Max 20 lines per function, type hints required, descriptive names |
| Security First (IV) | PASS | Fernet encryption for CV and session data; parameterized queries via SQLAlchemy |
| Configuration Management (V) | PASS | Database config from settings.py; Fernet key from environment |
| Language Policy (VI) | PASS | English only for code, comments, database columns |
| Database Changes (VII) | PASS | Alembic migrations with descriptive names; downgrades maintained |
| Testing Requirements (VIII) | PASS | Integration tests for repositories required; unit tests for models |
| Error Handling (IX) | PASS | Custom exceptions defined; logging with context required |
| Async Best Practices (X) | PASS | Async/await throughout; connection pooling configured |

## Project Structure

### Documentation (this feature)

```text
specs/001-database-schema/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - internal DB only)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Database layer following Clean Architecture
src/
├── database.py          # Async engine, session factory, connection pool
├── models/
│   ├── __init__.py
│   ├── base.py          # SQLAlchemy declarative base
│   ├── user.py          # User entity model
│   ├── user_cv.py       # UserCV entity model
│   ├── job.py           # Job entity model
│   ├── job_match.py     # JobMatch entity model
│   ├── subscription.py  # Subscription entity model
│   ├── referral_reward.py
│   ├── cover_letter_log.py
│   ├── user_interaction.py
│   ├── job_report.py
│   ├── archived_job.py
│   ├── telegram_session.py
│   └── monitored_channel.py
├── repositories/
│   ├── __init__.py
│   ├── base.py          # AbstractRepository with async CRUD
│   ├── user_repository.py
│   ├── cv_repository.py
│   ├── job_repository.py
│   ├── match_repository.py
│   ├── subscription_repository.py
│   ├── referral_reward_repository.py
│   ├── cover_letter_repository.py
│   ├── interaction_repository.py
│   ├── report_repository.py
│   ├── archived_job_repository.py
│   ├── telegram_session_repository.py
│   └── channel_repository.py
├── schemas/             # Pydantic schemas for validation (if needed)
└── utils/
    ├── encryption.py    # Fernet encryption helpers
    └── vectors.py       # Vector embedding helpers

migrations/
├── env.py               # Alembic async environment
├── script.py.mako
└── versions/
    ├── 001_initial_schema.py      # 12 tables
    ├── 002_hnsw_indexes.py        # Vector indexes
    └── 003_performance_indexes.py # B-tree indexes

tests/
├── integration/
│   ├── conftest.py
│   ├── test_user_repository.py
│   ├── test_cv_repository.py
│   ├── test_job_repository.py
│   ├── test_subscription_repository.py
│   └── test_referral_reward_repository.py
└── unit/
    ├── test_models.py
    ├── test_encryption.py
    └── test_vectors.py
```

**Structure Decision**: Single project with src/ root. Database models in src/models/, repositories in src/repositories/, migrations at root level following Alembic conventions. Tests follow standard pytest layout with integration/ and unit/ directories.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|---------------------------------------|
| None | N/A | N/A |

All Constitution gates pass without violations. The architecture follows clean architecture principles as required.
