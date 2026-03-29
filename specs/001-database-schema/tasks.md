---

description: "Task list for database schema implementation"
---

# Tasks: Database Schema & Migrations

**Input**: Design documents from `/specs/001-database-schema/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Foundation Setup

**Purpose**: Core infrastructure required before any models or repositories can be implemented

- [x] T001 Create project directories per implementation plan (src/models/, src/repositories/, src/utils/, migrations/versions/, tests/integration/, tests/unit/)
- [x] T002 [P] Initialize Alembic configuration with async support in migrations/alembic.ini and migrations/env.py
- [x] T003 [P] Create database.py with async engine and session factory in src/database.py
- [x] T004 [P] Create encryption utilities (Fernet helpers) in src/utils/encryption.py
- [x] T005 Create vector utilities (embedding helpers) in src/utils/vectors.py

**Checkpoint**: Foundation ready - models can now be implemented

---

## Phase 1: SQLAlchemy Models (12 Models)

**Purpose**: Create all 12 database table models following data-model.md

### Models for User Stories 1-4 (P1 Priority)

- [x] T006 [P] [US1-US4] Create base.py with declarative base and UUID mixin in src/models/base.py
- [x] T007 [P] [US1] Create user.py model in src/models/user.py
- [x] T008 [P] [US2] Create user_cv.py model with FernetColumn in src/models/user_cv.py
- [x] T009 [P] [US3] Create job.py model in src/models/job.py
- [x] T010 [P] [US4] Create job_match.py model in src/models/job_match.py

### Models for User Stories 5-8 (P2 Priority)

- [x] T011 [P] [US5] Create subscription.py model in src/models/subscription.py
- [x] T012 [P] [US6] Create referral_reward.py model in src/models/referral_reward.py
- [x] T013 [P] [US7] Create cover_letter_log.py model in src/models/cover_letter_log.py
- [x] T014 [P] [US8] Create user_interaction.py model in src/models/user_interaction.py

### Models for User Stories 9-12 (P3 Priority)

- [x] T015 [P] [US9] Create job_report.py model in src/models/job_report.py
- [x] T016 [P] [US10] Create archived_job.py model in src/models/archived_job.py
- [x] T017 [P] [US11] Create telegram_session.py model with FernetColumn in src/models/telegram_session.py
- [x] T018 [P] [US12] Create monitored_channel.py model in src/models/monitored_channel.py

- [x] T019 Create src/models/__init__.py exporting all models

**Checkpoint**: All models created - migrations can now be generated

---

## Phase 2: Database Migrations

**Purpose**: Create Alembic migrations for all tables and indexes

- [x] T020 [P] Generate migration 001_initial_schema.py with all 12 tables (migrations/versions/001_initial_schema.py)
- [x] T021 [P] Generate migration 002_hnsw_indexes.py for vector indexes with m=16, ef_construction=64 (migrations/versions/002_hnsw_indexes.py)
- [x] T022 Generate migration 003_performance_indexes.py for B-tree indexes (migrations/versions/003_performance_indexes.py)

**Checkpoint**: Migrations ready - repositories can now be implemented

---

## Phase 3: Repository Layer (12 Repositories + Base)

**Purpose**: Implement repository pattern per Constitution I - Clean Architecture

### Base Repository

- [x] T023 [P] Create AbstractRepository base class with async CRUD in src/repositories/base.py

### Repositories for User Stories 1-4 (P1 Priority)

- [x] T024 [P] [US1] Create UserRepository in src/repositories/user_repository.py
- [x] T025 [P] [US2] Create CVRepository with encryption methods in src/repositories/cv_repository.py
- [x] T026 [P] [US3] Create JobRepository with vector similarity search in src/repositories/job_repository.py
- [x] T027 [P] [US4] Create MatchRepository in src/repositories/match_repository.py

### Repositories for User Stories 5-8 (P2 Priority)

- [x] T028 [P] [US5] Create SubscriptionRepository in src/repositories/subscription_repository.py
- [x] T029 [P] [US6] Create ReferralRewardRepository with unique constraint handling in src/repositories/referral_reward_repository.py
- [x] T030 [P] [US7] Create CoverLetterRepository with quota enforcement in src/repositories/cover_letter_repository.py
- [x] T031 [P] [US8] Create InteractionRepository in src/repositories/interaction_repository.py

### Repositories for User Stories 9-12 (P3 Priority)

- [x] T032 [P] [US9] Create ReportRepository in src/repositories/report_repository.py
- [x] T033 [P] [US10] Create ArchivedJobRepository in src/repositories/archived_job_repository.py
- [x] T034 [P] [US11] Create TelegramSessionRepository with rotation logic in src/repositories/telegram_session_repository.py
- [x] T035 [P] [US12] Create ChannelRepository in src/repositories/channel_repository.py

- [x] T036 Create src/repositories/__init__.py exporting all repositories

**Checkpoint**: All repositories implemented - testing can begin

---

## Phase 4: Testing

**Purpose**: Ensure 80% test coverage per Constitution VIII - Testing Requirements

### Unit Tests

- [x] T037 [P] Setup test fixtures and conftest.py in tests/conftest.py
- [x] T038 [P] Write unit tests for models in tests/unit/test_models.py
- [x] T039 Write unit tests for encryption utilities in tests/unit/test_encryption.py

### Integration Tests

- [x] T040 [P] Write integration tests for UserRepository in tests/integration/test_user_repository.py
- [x] T041 [P] Write integration tests for CVRepository (encryption + vectors) in tests/integration/test_cv_repository.py
- [x] T042 Write integration tests for JobRepository (vector search) in tests/integration/test_job_repository.py
- [x] T043 Write integration tests for quota enforcement (race conditions) in tests/integration/test_cover_letter_repository.py
- [x] T044 Write integration tests for referral rewards (unique constraints) in tests/integration/test_referral_reward_repository.py

**Checkpoint**: Tests complete - verification can begin

---

## Phase 5: Verification

**Purpose**: Validate all success criteria from spec.md

- [x] T045 Run all migrations up and down (verify rollback) - alembic upgrade head && alembic downgrade -1
- [x] T046 Verify vector similarity queries return results within 500ms benchmark (per SC-002)
- [x] T047 Run full test suite and verify >80% coverage (per Constitution VIII)
- [x] T048 Verify all Constitution checks pass

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and cleanup

- [x] T049 Update src/models/__init__.py with proper exports
- [x] T050 Update src/repositories/__init__.py with proper exports
- [x] T051 Add remaining integration tests for other repositories if needed
- [x] T052 Code cleanup and refactoring per Constitution III
- [x] T053 Run lint and typecheck per Constitution III

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup)**: No dependencies - can start immediately
- **Phase 1 (Models)**: Depends on Phase 0 completion - BLOCKS migrations and repositories
- **Phase 2 (Migrations)**: Depends on Phase 1 completion - BLOCKS verification
- **Phase 3 (Repositories)**: Depends on Phase 2 completion (needs migrations for FK checks)
- **Phase 4 (Testing)**: Depends on Phase 3 completion
- **Phase 5 (Verification)**: Depends on Phase 4 completion
- **Phase 6 (Polish)**: Depends on Phase 5 completion

### Within Each Phase

- Phase 0 tasks marked [P] can run in parallel
- Phase 1 models marked [P] can run in parallel
- Phase 2 migrations can run in parallel where independent
- Phase 3 repositories marked [P] can run in parallel

---

## Parallel Example: Phase 1 Models

```bash
# Launch all P1 model tasks together:
Task: "Create user.py model in src/models/user.py"
Task: "Create user_cv.py model in src/models/user_cv.py"
Task: "Create job.py model in src/models/job.py"
Task: "Create job_match.py model in src/models/job_match.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-4 - P1)

1. Complete Phase 0: Setup
2. Complete Phase 1: Models (US1-US4)
3. Complete Phase 2: Migrations
4. Complete Phase 3: Repositories (US1-US4)
5. **STOP and VALIDATE**: Test core data layer works

### Incremental Delivery

1. P1 stories complete → Core data layer functional
2. P2 stories complete → Billing and tracking features
3. P3 stories complete → Full feature set
4. Phase 4: Tests pass
5. Phase 5: All success criteria met

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 together
2. Once Phase 0 is done:
   - Developer A: US1-US2 models + repositories
   - Developer B: US3-US4 models + repositories
   - Developer C: US5-US8 models + repositories
   - Developer D: US9-US12 models + repositories
3. Phase 3: Repositories and testing in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- Each phase should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Avoid: vague tasks, same file conflicts, cross-phase dependencies that break independence
