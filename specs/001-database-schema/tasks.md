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
- [x] T12 Wrap MatchRepository.create_match in try/except IntegrityError block with session rollback in src/repositories/match_repository.py
- [x] T13 Wrap ReferralRewardRepository.create_reward in try/except IntegrityError block with session rollback in src/repositories/referral_reward_repository.py
- [x] T14 Fix Quota Race in CoverLetterRepository: Use with_for_update() when counting monthly logs in src/repositories/cover_letter_repository.py

## Phase 4: Performance Optimizations

**Purpose**: Improve query efficiency

- [x] T15 Update InteractionRepository.count_interactions_by_type to use func.count() in single SQL query in src/repositories/interaction_repository.py

## Phase 5: Safety Improvements

**Purpose**: Protect test environment and prevent data loss

- [x] T16 Refactor tests/conftest.py to use urllib.parse for deriving TEST_DATABASE_URL in tests/integration/conftest.py
- [x] T17 Ensure TEST_DATABASE_URL only replaces DB name with jobpulse_test to prevent production data leakage

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