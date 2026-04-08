# Implementation Plan: Job Ingestion Pipeline

**Branch**: `003-job-ingestion-pipeline` | **Date**: 2026-04-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-job-ingestion-pipeline/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a 7-stage background pipeline (scrape → filter → classify → extract → deduplicate → embed → store) that runs every 3 minutes via Celery Beat. The pipeline uses Telethon to fetch messages from monitored Telegram channels, applies database-driven spam/length filtering, classifies posts as job/not-job via Gemini Flash-Lite with fallback chain, extracts structured job data via Gemini Flash, deduplicates globally using SHA-256 content hashes, generates 768-dim embeddings via Text Embedding 004, and stores unique jobs via the existing JobRepository. Critical failures trigger alerts to a designated admin Telegram channel.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Telethon 1.42.0 (Telegram scraping), Celery 5.4.0 (task queue), google-generativeai 0.8.3 (Gemini AI), openai 1.68.2 (fallback providers), Redis 5.2.1 (Celery broker/cache), SQLAlchemy 2.0.38 async (database access), pgvector 0.4.2 (vector storage)
**Storage**: PostgreSQL 16 with pgvector (jobs table with HNSW index), Redis (Celery broker, spam rule caching)
**Testing**: pytest 8.3.4, pytest-asyncio 0.25.2, pytest-cov 6.0.0 (80% minimum coverage)
**Target Platform**: Linux server (Docker Compose deployment)
**Project Type**: Backend service (Celery worker + FastAPI application)
**Performance Goals**: 500 unique jobs/day throughput, 100-message batch processed within 10 minutes, max 5 concurrent AI API calls per batch
**Constraints**: 30s timeout per AI call, exponential backoff 1s/2s/4s max 3 retries, daily API limits (Flash-Lite 1000 RPD, Flash 250 RPD), 768-dim embedding validation, session rotation on ban
**Scale/Scope**: Monitored Telegram channels (variable count), 3-minute polling interval, global deduplication across all channels

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| **I. Clean Architecture** | PASS | Routes → Services → Repositories → Database. New services (JobIngestionService, JobFilterService, JobClassifierService, JobExtractorService, JobEmbeddingService) will follow this pattern. No direct DB calls from services. |
| **II. SOLID Principles** | PASS | Each service has single responsibility. Dependency injection via constructor. Interfaces defined for AI provider abstraction. |
| **III. Clean Code Rules** | PASS | Max 20 lines per function, max 200 lines per file, type hints on all functions, named constants for magic numbers. |
| **IV. Security First** | PASS | No secrets in code (all from settings.ai). Input validation on all extracted fields. Parameterized queries via SQLAlchemy. |
| **V. Configuration Management** | PASS | AI model names from config/ai_models.py only. All settings from config/settings.py only. No hardcoded values. |
| **VI. Language Policy** | PASS | All code, comments, docstrings in English. Database columns in English. |
| **VII. Database Changes** | PASS | New spam_rules table requires Alembic migration with descriptive name and downgrade support. |
| **VIII. Testing Requirements** | PASS | Unit tests for all service functions. Integration tests for all repository functions. 80% coverage minimum. |
| **IX. Error Handling** | PASS | Custom exceptions for pipeline stages. Proper logging with context (channel_id, message_id, job_id). Sentry integration for production errors. |
| **X. Async Best Practices** | PASS | async/await throughout. No blocking operations in async functions. asyncio.gather for concurrent AI calls. Connection timeouts configured. |

### Post-Design Re-evaluation

All gates remain PASS after Phase 1 design. No violations introduced. Research decisions (AI provider pattern, Celery Beat scheduling, spam rule caching, session rotation, extraction schema, content hash normalization, admin alerts) all align with constitution principles.

## Project Structure

### Documentation (this feature)

```text
specs/003-job-ingestion-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── job.py                  # Existing - Job model (SPEC-001)
│   ├── monitored_channel.py    # Existing - Channel model (SPEC-001)
│   ├── telegram_session.py     # Existing - Session model (SPEC-001)
│   └── spam_rule.py            # NEW - Spam rule model for database-driven filtering
├── repositories/
│   ├── job_repository.py       # Existing - Job CRUD operations
│   ├── channel_repository.py   # Existing - Channel operations
│   ├── telegram_session_repository.py  # Existing - Session management
│   └── spam_rule_repository.py # NEW - Spam rule CRUD operations
├── services/
│   ├── __init__.py
│   ├── job_ingestion_service.py    # NEW - Orchestrates full 7-stage pipeline
│   ├── job_filter_service.py       # NEW - Spam/length filtering
│   ├── job_classifier_service.py   # NEW - AI binary classification
│   ├── job_extractor_service.py    # NEW - Structured data extraction
│   ├── job_embedding_service.py    # NEW - Vector embedding generation
│   └── ai_provider_service.py      # NEW - Fallback chain + provider abstraction
├── utils/
│   ├── __init__.py
│   ├── text_normalizer.py      # NEW - Text normalization for hashing
│   └── content_hasher.py       # NEW - SHA-256 content hash computation

workers/
├── __init__.py
├── celery_app.py               # NEW - Celery app configuration
└── tasks/
    └── ingestion_tasks.py      # NEW - Celery Beat scheduled task

docker-compose.yml              # UPDATED - Add Celery worker + beat services

tests/
├── unit/
│   ├── test_job_filter_service.py
│   ├── test_job_classifier_service.py
│   ├── test_job_extractor_service.py
│   ├── test_job_embedding_service.py
│   ├── test_ai_provider_service.py
│   ├── test_content_hasher.py
│   └── test_text_normalizer.py
└── integration/
    ├── test_job_ingestion_pipeline.py
    └── test_spam_rule_repository.py
```

**Structure Decision**: Single-project backend structure. New services go in `src/services/`, new model in `src/models/`, new repository in `src/repositories/`. Celery workers in `workers/` directory (existing stub). No frontend changes needed.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 5 new service classes | Each pipeline stage has distinct responsibility, error handling, and retry logic | Single monolithic service would exceed 200-line file limit and violate SRP |
| ai_provider_service abstraction layer | Fallback chain requires provider-agnostic interface with unified retry/backoff | Hardcoding provider calls in each service would duplicate retry logic and violate DRY |
| spam_rule_repository + spam_rule model | Database-driven spam rules (per clarification) require persistence layer | Hardcoded rules would require code deployment for every spam rule update |
