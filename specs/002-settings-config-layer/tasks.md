# Tasks: Settings & Config Layer

**Input**: Design documents from `/specs/002-settings-config-layer/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/env-vars.md, research.md

**Tests**: Constitution Principle VIII requires unit tests for all service functions. Tests are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project: `config/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies and configure project structure

- [X] T001 Add pydantic>=2.0, pydantic-settings>=2.0, python-dotenv>=1.0, cryptography>=41.0 to project dependencies
- [X] T002 [P] Create config/__init__.py with public exports
- [X] T003 [P] Create tests/config/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core settings infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base Settings class using pydantic-settings BaseSettings in config/settings.py with .env file loading via python-dotenv
- [X] T005 [P] Create DatabaseSettings nested model class in config/settings.py with database_url, pool_size, max_overflow, connection_timeout fields
- [X] T006 [P] Create RedisSettings nested model class in config/settings.py with redis_url, connection_timeout, max_connections fields
- [X] T007 [P] Create TelegramSettings nested model class in config/settings.py with bot_token, telethon_api_id (int), telethon_api_hash, telethon_session_name fields
- [X] T008 [P] Create AISettings nested model class in config/settings.py with gemini_api_key, groq_api_key, openrouter_api_key, zhipu_api_key fields and ai_models import from config/ai_models.py
- [X] T009 [P] Create SecuritySettings nested model class in config/settings.py with encryption_key, secret_key fields
- [X] T010 [P] Create PaymentSettings nested model class in config/settings.py with shamcash_api_key, crypto_wallet_address fields
- [X] T011 [P] Create MonitoringSettings nested model class in config/settings.py with sentry_dsn (optional), environment, debug fields
- [X] T012 Compose Settings root class with all nested models and export singleton `settings` instance in config/settings.py
- [X] T013 Implement secret masking in Settings __repr__ and __str__ methods (show first 8 chars only) in config/settings.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Centralized Settings Module (Priority: P1) 🎯 MVP

**Goal**: Deliver a working config/settings.py module that loads all environment variables with type safety, validation, and fail-fast behavior

**Independent Test**: Import the settings module with a fully configured environment and verify all settings are accessible as typed attributes; import with missing variables and verify clear error messages

### Tests for User Story 1

- [X] T014 [P] [US1] Test successful settings load with all valid env vars in tests/config/test_settings.py
- [X] T015 [P] [US1] Test fail-fast on missing required environment variable in tests/config/test_settings.py
- [X] T016 [P] [US1] Test validation error on invalid format (e.g., wrong type) in tests/config/test_settings.py

### Implementation for User Story 1

- [X] T017 [US1] Add field validators for all required fields (non-empty checks) in config/settings.py (depends on T004-T012)
- [X] T018 [US1] Implement env var precedence (environment > .env file) via pydantic-settings configuration in config/settings.py
- [X] T019 [US1] Add whitespace stripping for all string env values in config/settings.py
- [X] T020 [US1] Verify secret masking works in error messages and repr output (depends on T013)

**Checkpoint**: At this point, User Story 1 should be fully functional - settings load, validate, and mask secrets

---

## Phase 4: User Story 2 - Database Configuration (Priority: P2)

**Goal**: Database connection settings with validated URL format, configurable pool size (default: 5, max overflow: 5), and connection timeout (default: 30s)

**Independent Test**: Set DATABASE_URL with custom pool/timeout values and verify they are loaded correctly; test with invalid URL prefix and verify validation error

### Tests for User Story 2

- [X] T021 [P] [US2] Test DATABASE_URL validation with valid postgresql:// and postgresql+asyncpg:// prefixes in tests/config/test_settings.py
- [X] T022 [P] [US2] Test custom pool_size, max_overflow, and connection_timeout override defaults in tests/config/test_settings.py
- [X] T023 [US2] Test DATABASE_URL with invalid prefix (e.g., mysql://) raises validation error in tests/config/test_settings.py

### Implementation for User Story 2

- [X] T024 [US2] Add field_validator for database_url to validate postgresql:// or postgresql+asyncpg:// prefix in config/settings.py
- [X] T025 [US2] Add field_validator for pool_size (range 1-20), max_overflow (range 0-20), connection_timeout (positive int) in config/settings.py
- [X] T026 [US2] Add backward compatibility warning for postgresql:// (non-asyncpg) driver in config/settings.py

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Security Keys Configuration (Priority: P3)

**Goal**: Security keys (encryption key, secret key) loaded and validated with proper format checks

**Independent Test**: Set valid ENCRYPTION_KEY and SECRET_KEY and verify they load; set invalid formats and verify validation errors

### Tests for User Story 3

- [X] T027 [P] [US3] Test ENCRYPTION_KEY validation with valid 44-char base64 Fernet key in tests/config/test_settings.py
- [X] T028 [P] [US3] Test ENCRYPTION_KEY rejection of invalid base64 or wrong length in tests/config/test_settings.py
- [X] T029 [US3] Test SECRET_KEY validation with minimum 32-character length in tests/config/test_settings.py

### Implementation for User Story 3

- [X] T030 [US3] Add field_validator for encryption_key to validate 44-char base64 and test with cryptography.fernet.Fernet in config/settings.py
- [X] T031 [US3] Add field_validator for secret_key to enforce minimum 32-character length in config/settings.py

**Checkpoint**: User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - External Service Credentials (Priority: P4)

**Goal**: Telegram, AI model, payment, and monitoring credentials loaded and validated according to their format requirements

**Independent Test**: Set all external service credentials and verify they load; test each credential's format validation independently; verify optional SENTRY_DSN can be empty without failure

### Tests for User Story 4

- [X] T032 [P] [US4] Test BOT_TOKEN validation with format NNNN:AAAA... pattern in tests/config/test_settings.py
- [X] T033 [P] [US4] Test TELETHON_API_ID (positive int) and TELETHON_API_HASH (32 hex chars) validation in tests/config/test_settings.py
- [X] T034 [P] [US4] Test all AI API keys (GEMINI, GROQ, OPENROUTER, ZHIPU) loaded and non-empty in tests/config/test_settings.py
- [X] T035 [P] [US4] Test CRYPTO_WALLET_ADDRESS validation (T-prefixed, 34 alphanumeric chars) in tests/config/test_settings.py
- [X] T036 [P] [US4] Test optional SENTRY_DSN accepts empty/None without validation failure in tests/config/test_settings.py
- [X] T037 [US4] Test ENVIRONMENT enum validation (development/staging/production) and DEBUG boolean parsing in tests/config/test_settings.py

### Implementation for User Story 4

- [X] T038 [US4] Add field_validator for bot_token with regex pattern ^\d+:[A-Za-z0-9_-]{35,}$ in config/settings.py
- [X] T039 [US4] Add field_validator for telethon_api_id (positive int) and telethon_api_hash (32 hex chars) in config/settings.py
- [X] T040 [US4] Add field_validator for crypto_wallet_address (T-prefixed, 34 alphanumeric chars) in config/settings.py
- [X] T041 [US4] Add field_validator for environment (Literal["development", "staging", "production"]) and debug (bool parsing) in config/settings.py
- [X] T042 [US4] Add non-empty validators for all AI API keys and SHAMCASH_API_KEY in config/settings.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T043 [P] Add comprehensive docstrings to all settings classes and fields in config/settings.py
- [X] T044 [P] Add integration test with temporary .env file in tests/config/test_settings.py
- [X] T045 [P] Add test for secret masking in error messages (verify no full secrets visible) in tests/config/test_settings.py
- [X] T046 [P] Add test for .env file modification after startup (settings remain unchanged) in tests/config/test_settings.py
- [X] T047 Verify all functions have type hints and follow 20-line max rule per Constitution Principle III
- [X] T048 Run quickstart.md validation to confirm setup instructions work end-to-end
- [X] T049 Verify test coverage meets 80% minimum per Constitution Principle VIII

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses DatabaseSettings from foundation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses SecuritySettings from foundation
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Uses TelegramSettings, AISettings, PaymentSettings, MonitoringSettings from foundation

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Validators before integration
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003)
- All Foundational nested model tasks marked [P] can run in parallel (T005-T011)
- Once Foundational phase completes, all user stories can start in parallel
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Test successful settings load in tests/config/test_settings.py" (T014)
Task: "Test fail-fast on missing env var in tests/config/test_settings.py" (T015)
Task: "Test validation error on invalid format in tests/config/test_settings.py" (T016)

# Launch implementation tasks after tests fail:
Task: "Add field validators for all required fields in config/settings.py" (T017)
Task: "Implement env var precedence in config/settings.py" (T018)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T013) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T014-T020)
4. **STOP and VALIDATE**: Import settings module, verify all env vars load, test fail-fast
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Constitution Principle III: Max 20 lines per function, max 200 lines per file - split validators across helper functions if needed
- Constitution Principle VIII: 80% test coverage minimum required
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
