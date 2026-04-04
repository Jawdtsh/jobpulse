# jobpulse Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-04

## Active Technologies
- Python 3.12+ + Pydantic v2 (BaseSettings), python-dotenv, cryptography (Fernet validation) (002-settings-config-layer)
- N/A (configuration only, no persistent storage) (002-settings-config-layer)

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
- 002-settings-config-layer: Added Python 3.12+ + Pydantic v2 (BaseSettings), python-dotenv, cryptography (Fernet validation)

- 001-database-schema: Added Python 3.12+ + FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, pgvector, Fernet (cryptography)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
