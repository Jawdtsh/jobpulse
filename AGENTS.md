# jobpulse Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-05

## Active Technologies
- Python 3.12+ + Pydantic v2 (BaseSettings), python-dotenv, cryptography (Fernet validation) (002-settings-config-layer)
- N/A (configuration only, no persistent storage) (002-settings-config-layer)
- Python 3.12+ + Telethon 1.42.0 (Telegram scraping), Celery 5.4.0 (task queue), google-generativeai 0.8.3 (Gemini AI), openai 1.68.2 (fallback providers), Redis 5.2.1 (Celery broker/cache), SQLAlchemy 2.0.38 async (database access), pgvector 0.4.2 (vector storage) (003-job-ingestion-pipeline)
- PostgreSQL 16 with pgvector (jobs table with HNSW index), Redis (Celery broker, spam rule caching) (003-job-ingestion-pipeline)

- Python 3.12+ + FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, pgvector, Fernet (cryptography) (001-database-schema)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.12+: Follow standard conventions

## Recent Changes
- 003-job-ingestion-pipeline: Added Python 3.12+ + Telethon 1.42.0 (Telegram scraping), Celery 5.4.0 (task queue), google-generativeai 0.8.3 (Gemini AI), openai 1.68.2 (fallback providers), Redis 5.2.1 (Celery broker/cache), SQLAlchemy 2.0.38 async (database access), pgvector 0.4.2 (vector storage)
- 002-settings-config-layer: Added Python 3.12+ + Pydantic v2 (BaseSettings), python-dotenv, cryptography (Fernet validation)

- 001-database-schema: Added Python 3.12+ + FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, pgvector, Fernet (cryptography)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
