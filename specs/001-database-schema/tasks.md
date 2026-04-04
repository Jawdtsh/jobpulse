---

description: "Task list for technical debt and security hardening refinement"
---

# Tasks: Technical Debt & Security Hardening (Refinement)

**Input**: Refinement tasks from CodeRabbit review for SPEC-001 implementation
**Prerequisites**: plan.md (required), spec.md (required for context)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Foundation Setup

**Purpose**: Verify environment and prepare for safety-critical changes

- [ ] T001 Backup current database and verify migration state
- [ ] T002 [P] Ensure test environment is isolated from production
- [ ] T003 [P] Verify all dependencies are installed and up to date

## Phase 1: Database Integrity Improvements

**Purpose**: Enhance data integrity through constraints and triggers

- [x] T004 Add CheckConstraint("reward_value > 0") to ReferralReward model in src/models/referral_reward.py
- [x] T005 Implement PostgreSQL trigger for job_reports to auto-archive jobs after 3 unique reports in src/models/job_report.py
- [x] T006 Create migration for HNSW index on jobs.embedding_vector using raw SQL in migrations/versions/
- [x] T007 Update migration script to include HNSW index creation with parameters (m=16, ef_construction=64)

## Phase 2: Security Enhancements

**Purpose**: Prevent IDOR and enforce fail-fast principles

- [x] T008 Update CVRepository.set_active_cv to validate cv_id belongs to user_id before state mutation in src/repositories/cv_repository.py
- [x] T009 Update AbstractRepository.update to raise ValueError if kwargs contain fields not present in model in src/repositories/base.py

## Phase 3: Concurrency Fixes

**Purpose**: Eliminate race conditions with atomic operations

- [x] T010 Replace read-then-write increments with atomic DB-side increments in ChannelRepository.update_stats in src/repositories/channel_repository.py
- [x] T011 Replace read-then-write increments with atomic DB-side increments in TelegramSessionRepository.mark_used in src/repositories/telegram_session_repository.py
- [x] T12 Wrap MatchRepository.create_match in try/except IntegrityError block with SAVEPOINT (begin_nested) instead of session.rollback() in src/repositories/match_repository.py
- [x] T13 Wrap ReferralRewardRepository.create_reward in try/except IntegrityError block with SAVEPOINT (begin_nested) instead of session.rollback() in src/repositories/referral_reward_repository.py
- [x] T14 Fix Quota Race in CoverLetterRepository: Use with_for_update() when counting monthly logs in src/repositories/cover_letter_repository.py

## Phase 4: Performance Optimizations

**Purpose**: Improve query efficiency

- [x] T15 Update InteractionRepository.count_interactions_by_type to use func.count() in single SQL query in src/repositories/interaction_repository.py

## Phase 5: Safety Improvements

**Purpose**: Protect test environment and prevent data loss

- [x] T16 Refactor tests/conftest.py to use urllib.parse for deriving TEST_DATABASE_URL from os.getenv("DATABASE_URL") with fail-fast EnvironmentError
- [x] T17 Ensure TEST_DATABASE_URL hardcodes jobpulse_test (not configurable) to prevent production data leakage, with pool_size=5, max_overflow=10

## Phase 6: Verification

**Purpose**: Validate all acceptance criteria are met

- [x] T18 Run all migrations to verify database integrity improvements apply correctly
- [x] T19 Test ownership validation in CVRepository prevents IDOR
- [x] T20 Verify atomic operations handle concurrent access correctly
- [x] T21 Confirm test environment isolation works properly
- [x] T22 Run full test suite to ensure no regressions

## Phase 7: Polish & Documentation

**Purpose**: Clean up and document changes

- [x] T23 Update docstrings for modified methods to reflect new behavior
- [x] T24 Ensure all changes follow existing code style and conventions
- [x] T25 Run linting and type checking to maintain code quality

## Phase 8: Bugfix - Auto-Archive Trigger Counting Logic

**Purpose**: Fix PostgreSQL trigger that incorrectly archives jobs after 1 report instead of 3 unique reports (US9-AC2 violation)

- [x] T26 Fix PL/pgSQL trigger in migrations/versions/004_job_reports_trigger.py: replace PERFORM+FOUND with DECLARE+SELECT INTO for correct COUNT(DISTINCT reporter_user_id)
- [x] T27 [P] Fix ReportRepository.should_auto_archive and rename count_reports_for_job to count_unique_reporters_for_job using COUNT(DISTINCT) in src/repositories/report_repository.py
- [x] T28 [P] Add integration tests for report repository in tests/integration/test_report_repository.py covering: report creation, duplicate rejection, unique reporter counting, auto-archive threshold (2 reports = no archive, 3 reports = archive)
- [x] T29 [P] Update spec.md US9-AC2 and FR-009 to clarify trigger uses COUNT(DISTINCT reporter_user_id)
- [x] T30 Run unit tests and linting to verify no regressions

## Phase 9: Bugfix - Savepoint for IntegrityError Handlers

**Purpose**: Replace session.rollback() with begin_nested() SAVEPOINTs in IntegrityError handlers to prevent destroying all uncommitted operations in the shared session (Constitution Principle I & IX)

- [x] T31 Replace rollback() with begin_nested() in MatchRepository.create_match in src/repositories/match_repository.py
- [x] T32 [P] Replace rollback() with begin_nested() in ReferralRewardRepository.create_reward in src/repositories/referral_reward_repository.py
- [x] T33 [P] Add integration tests for match repository in tests/integration/test_match_repository.py covering: match creation, duplicate rejection, session survival after duplicate
- [x] T34 [P] Add test_session_survives_duplicate_reward to tests/integration/test_referral_reward_repository.py
- [x] T35 [P] Update spec.md US4-AC1, US6-AC1, and add FR-017 for SAVEPOINT requirement
- [x] T36 Run unit tests and linting to verify no regressions

## Phase 10: Bugfix - Eliminate N+1 Query in find_similar

**Purpose**: Replace N+1 raw SQL + per-row self.get() loop with single pgvector ORM query using cosine_distance (Constitution Principle X — no N+1 queries inside async loops)

- [x] T37 Replace raw text() SQL + loop in JobRepository.find_similar with ORM query using Job.embedding_vector.cosine_distance() in src/repositories/job_repository.py
- [x] T38 [P] Add integration tests for find_similar in tests/integration/test_job_repository.py covering: returns jobs with scores, excludes archived, respects limit, returns empty for no matches
- [x] T39 [P] Update spec.md SC-002 to document single-query ORM approach, add FR-018 for no N+1 queries
- [x] T40 Run unit tests and linting to verify no regressions

## Phase 11: Bugfix - Query Defects in count_by_reason and check_quota_available

**Purpose**: Fix two query defects: (1) count_by_reason fetches all rows into memory instead of using COUNT(*), (2) get_monthly_count uses WITH FOR UPDATE on COUNT which locks nothing; check_quota_available must use get_logs_for_update for proper row locking (Constitution Principle X)

- [x] T41 Replace len(list(result.scalars().all())) with select(func.count()) in ArchivedJobRepository.count_by_reason in src/repositories/archived_job_repository.py
- [x] T42 [P] Remove meaningless with_for_update() from get_monthly_count and refactor check_quota_available to use get_logs_for_update in src/repositories/cover_letter_repository.py
- [x] T43 [P] Update spec.md FR-019 for database-level COUNT and proper row locking
- [x] T44 Run unit tests and linting to verify no regressions

## Phase 12: Bugfix - Replace deprecated datetime.utcnow()

**Purpose**: Replace all 17 occurrences of deprecated `datetime.utcnow()` with timezone-aware `datetime.now(timezone.utc)` across 13 files to comply with FR-015 and Python 3.12+ deprecation

- [x] T45 [P] Fix 5 model files Pattern A (default=datetime.utcnow → default=lambda: datetime.now(timezone.utc)): src/models/job_match.py, src/models/job_report.py, src/models/cover_letter_log.py, src/models/referral_reward.py, src/models/user_interaction.py, src/models/archived_job.py
- [x] T46 [P] Fix 7 repository files Pattern B (datetime.utcnow() → datetime.now(timezone.utc)): src/repositories/match_repository.py, src/repositories/cover_letter_repository.py, src/repositories/referral_reward_repository.py, src/repositories/interaction_repository.py, src/repositories/subscription_repository.py, src/repositories/channel_repository.py, src/repositories/telegram_session_repository.py
- [x] T47 [P] Update spec.md FR-015 to require datetime.now(timezone.utc)
- [x] T48 Run unit tests and linting to verify no regressions

## Phase 13: Bugfix - Inconsistent Encryption Error Messages

**Purpose**: Fix inconsistent error handling between decrypt_data() and decrypt_bytes() — decrypt_bytes() allows cryptic InvalidToken from Fernet to propagate, while decrypt_data() wraps it in a descriptive ValueError (Constitution Principle IX — consistent error messages)

- [x] T49 Wrap fernet.decrypt() in decrypt_bytes() with InvalidToken → ValueError wrapper in src/utils/encryption.py, raising "Decryption failed: ciphertext is corrupted or was encrypted with a different key."
- [x] T50 Run unit tests and linting to verify consistent error messages across both functions

## Phase 14: Bugfix - Inconsistent Encryption Error Messages and Missing DateTime(timezone=True)

**Purpose**: Fix inconsistent error handling between decrypt_data() and decrypt_bytes() (cryptic InvalidToken vs user-friendly ValueError) and add missing DateTime(timezone=True) to datetime columns in job_report and monitored_channel models (Constitution Principle IX and FR-015)

- [x] T51 [P] Add DateTime(timezone=True) to job_report.created_at and monitored_channel.last_scraped_at, import DateTime from sqlalchemy
- [x] T52 [P] Fix TOCTOU race condition in ReportRepository.create_report by replacing check-then-create with begin_nested() + IntegrityError pattern, removing has_user_reported_job call
- [x] T53 [P] Update spec.md FR-020 (Encryption) and add FR-021 (DateTime(timezone=True) consistency)
- [x] T54 Run unit tests and linting to verify no regressions

## Phase 15: Bugfix - Lint and Consistency Fixes

**Purpose**: Fix 11 remaining lint errors across source and test files to comply with Ruff rules and ensure code consistency (Constitution Principle X — Pythonic patterns and readability)

- [x] T55 [P] Fix src/models/telegram_session.py: Remove empty TYPE_CHECKING block and unused TYPE_CHECKING import (Ruff F401, RUF015)
- [x] T56 [P] Fix src/repositories/base.py line 38: SIM118 — replace `kwargs.keys()` with `kwargs` (Ruff SIM118)
- [x] T57 [P] Fix src/repositories/job_repository.py: ANN204 (add -> None to __init__), E712 (replace == False with not) in get_active_jobs and find_similar (Ruff ANN204, E712)
- [x] T58 [P] Fix src/repositories/report_repository.py: ANN204 (add -> None to __init__) (Ruff ANN204)
- [x] T59 [P] Fix src/utils/vectors.py: EPSILON constant and floating-point comparison for reliability (Ruff F841, B002)
- [x] T60 [P] Fix test files: Replace == True/False with direct assertions in test_cover_letter_repository.py (E712), test_cv_repository.py (E712), test_models.py (E712), test_user_repository.py (F401)
- [x] T61 [P] Fix src/repositories/channel_repository.py: E712 in get_active_channels (Ruff E712)
- [x] T62 [P] Fix src/repositories/cv_repository.py: E712 in get_active_cv (Ruff E712)
- [x] T63 [P] Fix src/repositories/match_repository.py: E712 in get_unnotified_matches (Ruff E712)
- [x] T64 [P] Fix src/repositories/telegram_session_repository.py: E712 in get_available_sessions (Ruff E712)
- [x] T65 [P] Update tests/conftest.py event_loop fixture for pytest-asyncio 0.23+ compatibility (Ruff E402)
- [x] T66 Run full ruff check on src/ and tests/ to verify all linting errors are resolved
- [x] T67 Update spec.md to document lint fixes and code quality improvements

---

### Dependencies & Execution Order

#### Phase Dependencies

- **Phase 0 (Setup)**: No dependencies - can start immediately
- **Phase 1 (Database Integrity)**: Depends on Phase 0 completion
- **Phase 2 (Security)**: Depends on Phase 0 completion
- **Phase 3 (Concurrency)**: Depends on Phase 0 completion
- **Phase 4 (Performance)**: Depends on Phase 0 completion
- **Phase 5 (Safety)**: Depends on Phase 0 completion
- **Phase 6 (Verification)**: Depends on completion of Phases 1-5
- **Phase 7 (Polish)**: Depends on Phase 6 completion

#### Parallel Execution Examples

**Database Integrity Phase (can run in parallel)**:
```bash
Task: "Add CheckConstraint to ReferralReward model in src/models/referral_reward.py"
Task: "Implement PostgreSQL trigger for job_reports in src/models/job_report.py"
Task: "Create migration for HNSW index on jobs.embedding_vector"
```

**Concurrency Fixes Phase (can run in parallel)**:
```bash
Task: "Replace increments with atomic operations in ChannelRepository.update_stats"
Task: "Replace increments with atomic operations in TelegramSessionRepository.mark_used"
Task: "Fix Quota Race in CoverLetterRepository with with_for_update()"
```

### Implementation Strategy

#### Safety-First Approach

1. **Isolate Test Environment First**: Begin with Phase 5 (Safety) to ensure no risk to production data
2. **Database Integrity Early**: Implement constraints and triggers to prevent data corruption
3. **Security Before Concurrency**: Fix IDOR vulnerabilities before addressing race conditions
4. **Performance Last**: Optimize queries after correctness is verified
5. **Comprehensive Testing**: Validate all changes before considering complete

#### Validation Checkpoints

- After Phase 5: Test environment protection verified
- After Phase 2: Security enhancements validated
- After Phase 3: Concurrency fixes tested under load
- After Phase 6: All acceptance criteria met