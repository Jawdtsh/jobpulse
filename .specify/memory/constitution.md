# JobPulse AI Constitution

## Core Principles

### I. Clean Architecture (Strict Layer Separation)
Routes layer MUST call Services layer; Services layer MUST call Repositories layer; Repositories layer MUST access Database only. No database calls from routes. No business logic in routes. Repository pattern MUST be used for all database access.

### II. SOLID Principles
Single Responsibility: each function performs ONE specific task. Open/Closed: extend via inheritance, not modification. Dependency Injection MUST be used for all services. Liskov Substitution, Interface Segregation, and Dependency Inversion principles MUST be followed.

### III. Clean Code Rules
Maximum 20 lines per function. Maximum 200 lines per file. Descriptive names required (no abbreviations except standard ones). Type hints MUST be present on all functions. No magic numbers - use named constants.

### IV. Security First
Fernet encryption REQUIRED for all CV data at rest. No secrets in code - environment variables only. Signature verification REQUIRED on all webhooks. Input validation REQUIRED on all endpoints. SQL injection prevention via parameterized queries.

### V. Configuration Management
ALL AI model names MUST come from config/ai_models.py only. ALL settings MUST come from config/settings.py only. No hardcoded values in business logic. Configuration changes require no code modifications.

### VI. Language Policy
Code, comments, and docstrings: English only. Database column names: English only. Variable and function names: English only. All user-facing text: English only.

### VII. Database Changes
All schema changes via Alembic migrations only. Never modify database manually. Migration files MUST have descriptive names. Migration downgrades MUST be maintained.

### VIII. Testing Requirements
All service functions MUST have unit tests. All repository functions MUST have integration tests. Test coverage minimum 80%. Tests MUST use descriptive names. Each test case MUST test one behavior.

### IX. Error Handling
Custom exceptions REQUIRED for business logic errors. Proper logging with context (user_id, job_id, etc.) REQUIRED. Sentry integration REQUIRED for production errors. HTTP status codes MUST match error types. Errors MUST be caught at appropriate layers.

### X. Async Best Practices
Use async/await consistently throughout codebase. No blocking operations in async functions. Proper connection pooling for database and Redis. Use asyncio.gather for concurrent operations. Connection timeouts MUST be configured.

## Technology Stack

**Language**: Python 3.12+
**Frameworks**: FastAPI, aiogram 3.x, Telethon
**Database**: PostgreSQL 16 with pgvector extension
**Cache**: Redis
**Task Queue**: Celery
**AI Models**: Gemini 2.5 models (configured via config/ai_models.py)

## Development Workflow

All features MUST follow the specification workflow:
1. Feature specification in .specify/specs/
2. Implementation plan required before coding
3. User stories MUST be independently testable
4. Tasks organized by user story priority
5. Constitution check REQUIRED in implementation plans

### Code Quality Gates
- Lint and typecheck MUST pass before merge
- All tests MUST pass before merge
- Coverage MUST meet 80% minimum
- No hardcoded secrets or configuration values

## Governance

This Constitution supersedes all other practices. Amendments require:
1. Documentation of changes
2. Approval from project maintainers
3. Migration plan if breaking changes
4. Version bump following semantic versioning

### Version Bumping Rules
- MAJOR: Backward incompatible governance changes or principle removals
- MINOR: New principle added or materially expanded guidance
- PATCH: Clarifications, wording changes, typo fixes

### Compliance
All PRs and reviews MUST verify constitution compliance. Complexity MUST be justified in implementation plans. Reference this constitution for development decisions.

**Version**: 1.0.0 | **Ratified**: 2026-03-28 | **Last Amended**: 2026-03-28
