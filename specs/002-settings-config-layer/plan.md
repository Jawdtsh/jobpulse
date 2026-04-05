# Implementation Plan: Settings & Config Layer

**Branch**: `002-settings-config-layer` | **Date**: 2026-04-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-settings-config-layer/spec.md`

## Summary

Build a centralized, type-safe configuration management module (`config/settings.py`) using Pydantic v2 BaseSettings. All application settings (database, Redis, Telegram, AI models, security, payment, monitoring) will be loaded from environment variables with validation at import time. This is foundational infrastructure required before any business logic specs can be implemented.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: 
- pydantic>=2.0 (core validation)
- pydantic-settings>=2.0 (BaseSettings - separate package in Pydantic v2)
- python-dotenv>=1.0 (for .env file loading)
- cryptography>=41.0 (for Fernet key validation)
**Storage**: N/A (configuration only, no persistent storage)
**Testing**: pytest with monkeypatch for environment variable testing
**Target Platform**: Linux server (Docker containers)
**Project Type**: Web-service (FastAPI backend)
**Performance Goals**: Settings load in <200ms at application startup (measured from first import to singleton creation)
**Constraints**: No hardcoded secrets; all secrets from environment; fail-fast on missing required settings
**Testing Strategy**: 
- Unit tests with pytest monkeypatch for environment variable mocking
- Integration tests with temporary .env files
- Validation error tests for each required field format
- Secret masking verification in error messages
**Scale/Scope**: Single settings singleton shared across all application components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Clean Architecture | PASS | Settings module is infrastructure layer; no layer violations |
| II. SOLID Principles | PASS | Single responsibility (config loading); type hints on all functions |
| III. Clean Code Rules | PASS | Descriptive names; type hints; no magic values |
| IV. Security First | PASS | No secrets in code; env vars only; Fernet key validation |
| V. Configuration Management | PASS | All settings from config/settings.py; AI model names from config/ai_models.py; no hardcoded values |
| VI. Language Policy | PASS | All identifiers in English |
| VII. Database Changes | N/A | No schema changes in this feature |
| VIII. Testing Requirements | PASS | Unit tests for settings validation; integration tests for env loading |
| IX. Error Handling | PASS | Clear error messages for missing/invalid settings; secrets masked in logs |
| X. Async Best Practices | N/A | Settings loading is synchronous at startup |

## Project Structure

### Documentation (this feature)

```text
specs/002-settings-config-layer/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (environment variable contract)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
config/
├── __init__.py
├── settings.py          # Main settings module (Pydantic BaseSettings)
└── ai_models.py         # Existing AI model definitions (integrated)

tests/
└── config/
    ├── __init__.py
    └── test_settings.py # Unit tests for settings validation
```

**Structure Decision**: Single project structure. The `config/` directory already exists with `ai_models.py`. The new `settings.py` will be added alongside it. Tests will be placed in `tests/config/` following the project's existing test structure.

## Complexity Tracking

> No constitution violations. This feature directly supports Principle V (Configuration Management) and Principle IV (Security First).
