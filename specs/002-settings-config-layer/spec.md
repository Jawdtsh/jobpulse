# Feature Specification: Settings & Config Layer

**Feature Branch**: `002-settings-config-layer`  
**Created**: 2026-04-04  
**Status**: Implemented  
**Input**: Centralized, type-safe configuration management for all application components

## Clarifications

### Session 2026-04-05

- Fix: `src/utils/encryption.py` error message corrected from duplicated/misleading `"FERNET_KEY is not configured...ENCRYPTION_KEY is not configured..."` to single accurate `OSError("ENCRYPTION_KEY is not configured. Set it in .env or environment variables.")` — Constitution Principle IX.
- Fix: `tests/unit/test_encryption.py` updated: mock path corrected from `mock_settings.fernet_key` (flat) to `mock_settings.security.encryption_key` (nested); exception type corrected from `EnvironmentError` to `OSError`; all happy-path tests now mock `get_fernet` to avoid `.env` bleeding.
- Fix: `tests/config/test_settings.py` four test gaps resolved:
  1. TestSecretMasking now contains proper masking tests: `test_repr_masks_encryption_key` + `test_repr_masks_api_keys` (FR-004, SC-003).
  2. Moved misplaced DB tests from TestSecretMasking to TestDatabaseFieldValidators.
  3. `test_valid_plain_postgresql_prefix` now asserts exactly 1 warning containing "asyncpg" (FR-018 edge case).
  4. Added `TestEdgeCases.test_whitespace_stripped_from_env_values` — required adding `_strip_environment` field_validator to MonitoringSettings (T019).
- Fix: `contracts/env-vars.md` BOT_TOKEN pattern updated from `^\d+:[a-zA-Z0-9_-]+$` to `^\d+:[A-Za-z0-9_-]{35,}$` to match data-model.md (Constitution Principle V — spec consistency).
- Fix: `contracts/env-vars.md` DB env var names updated from `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`/`DB_CONNECTION_TIMEOUT` to `DATABASE_POOL_SIZE`/`DATABASE_MAX_OVERFLOW`/`DATABASE_CONNECTION_TIMEOUT` to match implementation and data-model.md.
- Fix: `src/__init__.py` `__getattr__` return type annotated `-> object`; `src/database.py` `_ensure_engine` return type annotated `-> None`, `__getattr__` return type annotated `-> object` (Constitution Principle III).
- Fix: `tests/config/test_settings.py` mutable `model_config = {...}` dict replaced with `SettingsConfigDict(...)` (Ruff RUF012).
- Optimization: `_fernet_key()` function replaced with module-level `_TEST_FERNET_KEY` constant in test_settings.py.
- 81 tests pass (71 settings + 10 encryption); ruff lint clean on all changed files.

### Session 2026-04-04

- Q: What should be the default connection pool size? → A: Default pool size of 5 with MAX_OVERFLOW of 5 (total 10 connections peak)
- Q: What should be the default Redis connection settings? → A: Max connections: 10, timeout: 5 seconds
- Q: What should be the default database connection timeout? → A: 30 seconds

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Centralized Settings Module (Priority: P1)

As a developer, I need a single config/settings.py module that loads all application settings from environment variables with type safety and validation, so that I don't have to hunt for scattered configuration values or worry about type mismatches.

**Why this priority**: This is the foundation for all other features. Without it, no other spec can be implemented safely.

**Independent Test**: Can be fully tested by importing the settings module and verifying all environment variables are loaded, validated, and accessible with correct types.

**Acceptance Scenarios**:

1. **Given** a properly configured .env file with all required variables, **When** the settings module is imported, **Then** all settings are loaded without errors and accessible as typed attributes
2. **Given** a missing required environment variable, **When** the settings module is imported, **Then** the application fails fast with a clear error message identifying the missing variable
3. **Given** an invalid value (wrong type or format), **When** the settings module is imported, **Then** validation fails with a descriptive error message

---

### User Story 2 - Database Configuration (Priority: P2)

As a system, I need database connection settings (URL, pool size, timeout) so that the database layer can establish connections with proper pooling and timeout behavior.

**Why this priority**: Database connectivity is required for all data persistence operations.

**Independent Test**: Can be tested by verifying database settings are loaded and match the configuration used in the database connection layer.

**Acceptance Scenarios**:

1. **Given** DATABASE_URL is set in environment, **When** settings are loaded, **Then** the database URL is accessible and pool size/timeout have sensible defaults
2. **Given** custom pool size and timeout values are set, **When** settings are loaded, **Then** the custom values override defaults

---

### User Story 3 - Security Keys Configuration (Priority: P3)

As a system, I need security keys (encryption key, secret key) loaded and validated so that encryption and authentication operations work correctly.

**Why this priority**: Security is critical but can be implemented after basic connectivity is established.

**Independent Test**: Can be tested by verifying encryption key format (44-char base64) and secret key are loaded and non-empty.

**Acceptance Scenarios**:

1. **Given** valid ENCRYPTION_KEY and SECRET_KEY are set, **When** settings are loaded, **Then** both keys are accessible and validated
2. **Given** an invalid ENCRYPTION_KEY format, **When** settings are loaded, **Then** validation fails with a clear format error

---

### User Story 4 - External Service Credentials (Priority: P4)

As a system, I need Telegram, AI model, payment, and monitoring credentials loaded so that external service integrations can authenticate when they are implemented.

**Why this priority**: These are needed for future features but don't block the core settings infrastructure.

**Independent Test**: Can be tested by verifying all external service credentials are loaded and validated according to their format requirements.

**Acceptance Scenarios**:

1. **Given** all external service credentials are set, **When** settings are loaded, **Then** all credentials are accessible and validated
2. **Given** an optional credential (e.g., SENTRY_DSN) is not set, **When** settings are loaded, **Then** the setting is None/empty without causing validation failure

---

### Edge Cases

- What happens when .env file exists but is empty? System should fail fast with clear error about missing required variables
- How does system handle environment variables with extra whitespace? Values should be stripped automatically
- What happens when a secret contains special characters? The system should handle any valid string value
- How are secrets displayed in error messages? Secrets must be masked (show first 8 characters only) in all logs and errors
- What happens when .env file is modified after application startup? Settings remain unchanged (loaded once at startup only)
- What happens when duplicate keys exist in .env file? Last value takes precedence
- What happens if DATABASE_URL uses wrong driver (e.g., postgresql:// instead of postgresql+asyncpg://)? Validation should warn but allow (backward compatibility)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load all configuration from environment variables with a .env file as fallback
- **FR-002**: System MUST validate all required settings at import time and fail fast if any are missing
- **FR-003**: System MUST provide type-safe access to all settings through a single settings singleton
- **FR-004**: System MUST mask secrets in logs and error messages (show first 8 characters only)
- **FR-005**: System MUST load and validate DATABASE_URL with configurable pool size (default: 5, max overflow: 5) and connection timeout (default: 30s)
- **FR-006**: System MUST load and validate REDIS_URL with configurable connection timeout (default: 5s) and max connections (default: 10)
- **FR-007**: System MUST load and validate BOT_TOKEN in format NNNN:AAAA...
- **FR-008**: System MUST load TELETHON_API_ID, TELETHON_API_HASH, and configurable TELETHON_SESSION_NAME
- **FR-009**: System MUST load and validate GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, and ZHIPU_API_KEY as non-empty
- **FR-010**: System MUST load and validate ENCRYPTION_KEY as 44-character base64 string
- **FR-011**: System MUST load and validate SECRET_KEY for JWT/session signing as non-empty
- **FR-012**: System MUST load SHAMCASH_API_KEY and validate CRYPTO_WALLET_ADDRESS in USDT TRC20 format
- **FR-013**: System MUST load optional SENTRY_DSN (skip validation if empty)
- **FR-014**: System MUST provide ENVIRONMENT setting (development/staging/production) and DEBUG boolean flag
- **FR-015**: System MUST NOT have hardcoded defaults for secrets (must come from environment)
- **FR-016**: System MUST provide sensible defaults for non-secret settings (pool sizes, timeouts)
- **FR-017**: System MUST integrate with existing config/ai_models.py for AI model configurations
- **FR-018**: System MUST validate format of environment variables:
  - TELETHON_API_ID must be a valid integer
  - TELETHON_API_HASH must be 32 hexadecimal characters
  - DATABASE_URL must start with postgresql:// or postgresql+asyncpg://
  - REDIS_URL must start with redis://
  - SECRET_KEY must be at least 32 characters long
  - CRYPTO_WALLET_ADDRESS must be exactly 34 alphanumeric characters starting with 'T'
- **FR-019**: System MUST give precedence to environment variables over .env file values when both are present

### Key Entities

- **Settings**: Central configuration container with all application settings grouped by category (database, redis, telegram, ai, security, payment, monitoring)
- **Environment**: Deployment context (development/staging/production) that may influence default values and behavior

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application starts successfully with all required environment variables configured within 2 seconds
- **SC-002**: Missing required configuration is detected and reported with clear error message before any business logic executes
- **SC-003**: 100% of secrets are masked in logs and error messages (no full secret values visible)
- **SC-004**: Zero hardcoded secrets exist in the codebase (verified by code audit)
- **SC-005**: All settings are accessible through a single import (from config.settings import settings)
- **SC-006**: Invalid configuration causes startup failure within 2 seconds with error message clearly identifying the problematic setting name and expected format

## Assumptions

- Development team has access to all required API keys and credentials before implementation
- .env file will be used for local development; environment variables will be used in production
- Existing config/ai_models.py structure will be preserved and integrated
- No runtime configuration changes are needed (settings are loaded once at startup)
- USDT TRC20 wallet address format follows the standard T-prefixed 34-character format
