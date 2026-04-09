# Tasks: CV Upload & Evaluation

**Feature**: SPEC-004 - CV Upload & Evaluation  
**Branch**: `004-cv-upload-evaluation`  
**Date**: 2026-04-08

## Implementation Strategy

MVP First: User Story 1 (CV Upload) - enables core functionality  
Incremental Delivery: Each user story independently testable

## Phase 1: Setup

- [X] T001 Create Alembic migration to add evaluation columns to user_cvs table in migrations/versions/
- [X] T002 Add CV evaluation model config in config/ai_models.py (gemini-2.5-pro)

## Phase 2: Foundational

- [X] T003 [P] Add skills, experience_summary, completeness_score, improvement_suggestions, evaluated_at columns to src/models/user_cv.py
- [X] T004 [P] Extend src/repositories/cv_repository.py with get_active_cvs, count_by_user methods
- [X] T004a [P] Create custom exceptions in src/services/exceptions.py (CVFileSizeExceededError, CVFormatNotSupportedError, CVTextExtractionError, CVQuotaExceededError, CVLimitExceededError) to comply with Constitution Principle IX.

## Phase 3: User Story 1 - Upload CV via Telegram (P1)

**Goal**: Users can upload PDF/DOCX/TXT files via Telegram and text is extracted

**Independent Test**: Send a CV file to bot, verify text extracted and stored (encrypted)

- [X] T005 [P] [US1] Create CV parser service in src/services/cv_parser.py (extract PDF/DOCX/TXT text)
- [X] T006 [P] [US1] Add file validation (5MB max, PDF/DOCX/TXT only) in src/services/cv_service.py
- [X] T007 [US1] Implement extract_text with fallback (PyPDF2 → pdfplumber) in src/services/cv_parser.py
- [X] T008 [US1] Create upload_cv method in src/services/cv_service.py (validation → extraction → encryption → storage)
- [X] T009 [US1] Create Telegram bot document handler in src/bot/handlers/cv_handlers.py (handle file uploads)
- [X] T010 [US1] Add error handling for extraction failures in src/services/cv_service.py
- [X] T011 [US1] Implement contextual error logging via Sentry/logger in src/services/cv_service.py. All CV exceptions MUST include context kwargs: user_id, cv_id, file_size, and file_format.

## Phase 4: User Story 2 & 3 - AI Evaluation + Completeness (P1)

**Goal**: CVs are evaluated by AI, completeness scored, results shown to user

**Independent Test**: Upload CV, verify AI returns skills/summary/score/suggestions

- [X] T012 [P] [US2] Create CV evaluator service in src/services/cv_evaluator.py (Gemini Pro evaluation)
- [X] T013 [P] [US3] Implement completeness scoring (contact20%, skills25%, experience30%, education15%, summary10%) in src/services/cv_evaluator.py
- [X] T014 [US2] Create evaluate_cv method in src/services/cv_service.py (call evaluator → save results)
- [X] T015 [US2] Add structured JSON response parsing in src/services/cv_evaluator.py (skills, suggestions)
- [X] T016 [US3] Add referral ineligibility warning (below 40%) in src/services/cv_evaluator.py
- [X] T017 [US2] Display evaluation results in readable format in src/bot/handlers/cv_handlers.py
- [X] T018 [US2] Persist evaluation to database in src/repositories/cv_repository.py

## Phase 5: User Story 4 - Generate CV Embeddings (P2)

**Goal**: 768-dim vector generated for semantic job matching

**Independent Test**: Upload CV, verify 768-dim vector stored (or null on failure)

- [X] T019 [US4] Create cv_embedding service in src/services/cv_embedding.py (wrap AIProviderService)
- [X] T020 [US4] Trigger embedding generation via Celery background task (`send_task`) on successful CV upload to ensure the Telegram bot response is not blocked.
- [X] T021 [US4] Handle embedding failure gracefully (log error, store null) in src/services/cv_embedding.py

## Phase 6: User Story 5 - Encrypted CV Storage (P1)

**Already Implemented**: Fernet encryption exists in src/utils/encryption.py

- [X] T022 [US5] Verify encryption works correctly (existing integration test)

## Phase 7: User Story 6 - Subscription Tier CV Limits (P1)

**Goal**: CV count limits enforced per tier (Free/Basic=1, Pro=2)

**Independent Test**: Tier user at limit sees upgrade prompt when exceeding

- [X] T023 [US6] Get user subscription tier in src/services/cv_service.py (from user/subscription)
- [X] T024 [US6] Check CV count before upload in src/services/cv_service.py
- [X] T025 [US6] Return upgrade prompt on limit exceeded in src/bot/handlers/cv_handlers.py
- [X] T026 [US6] Implement CV replace (mark old inactive, create new) in src/services/cv_service.py

## Phase 8: User Story 7 - Manage Uploaded CVs (P2)

**Goal**: Users can list, activate, deactivate, delete their CVs

**Independent Test**: Multiple CVs managed through bot commands

- [X] T027 [US7] Add list_user_cvs method in src/services/cv_service.py (return all CVs with status)
- [X] T028 [US7] Add activate_cv method in src/services/cv_service.py (set active, deactivate others)
- [X] T029 [US7] Add deactivate_cv method in src/services/cv_service.py (set is_active=false)
- [X] T030 [US7] Add delete_cv method in src/services/cv_service.py (soft delete)
- [X] T031 [US7] Create CV management bot commands in src/bot/commands/cv_commands.py (/mycvs, /activatecv, /deletecv)
- [X] T032 [US7] Trigger a background Celery task (`match_active_cv_to_recent_jobs`) whenever a CV's state changes to ACTIVE (either on new upload or manual activation). The task must evaluate the CV against jobs from the last 7 days.

## Phase 9: User Story 8 - CV Evaluation Quota Tracking (P2)

**Goal**: Monthly evaluation quotas enforced (Free=1, Basic=5, Pro=10)

**Independent Test**: User at quota limit sees upgrade prompt

- [X] T033 [US8] Create Redis-based quota tracker in src/services/cv_quota_service.py (monthly counters)
- [X] T034 [US8] Check quota before evaluation in src/services/cv_service.py
- [X] T035 [US8] Increment quota on each evaluation in src/services/cv_quota_service.py
- [X] T036 [US8] Show upgrade prompt on quota exceeded in src/bot/handlers/cv_handlers.py

## Test Quality Standards

- **TQ-001**: All async methods MUST be tested with async mocks
- **TQ-002**: Integration tests MUST seed exact data and assert exact counts
- **TQ-003**: pytest.raises() blocks MUST contain exactly one statement
- **TQ-004**: Duplicate test cases MUST be replaced with distinct scenarios

## Phase 10: Admin & Encryption Key Rotation (FR-033)

**Goal**: Support encryption key rotation by re-encrypting all existing CV content

**Independent Test**: Admin can trigger re-encryption via CLI command

- [X] T041a [Admin] Create CV re-encryption logic in src/services/admin_service.py. Must acquire Redis lock 'cv:reencryption:lock' (TTL 1 hour), decrypt/re-encrypt user_cvs records in batches of 100, and log progress.
- [X] T041b [Admin] Add Telegram CLI command '/admin reencrypt-cvs --old-key-file=...' in src/bot/commands/admin_commands.py to trigger the rotation process.

## Phase 11: Polish & Cross-Cutting Concerns

- [X] T035 [P] Add unit tests for cv_parser in tests/unit/test_cv_parser.py
- [X] T036 [P] Add unit tests for cv_evaluator in tests/unit/test_cv_evaluator.py
- [X] T037 [P] Add unit tests for cv_service in tests/unit/test_cv_service.py
- [X] T038 Add integration tests for CV repository in tests/integration/test_cv_repository.py
- [X] T039 Verify all tests pass (pytest)
- [X] T040 Run lint and typecheck (ruff check . && ruff format .)
- [X] T041 Verify integration: newly activated CVs successfully trigger the matching engine for the last 7 days of jobs.
## Dependencies

```
US1 (CV Upload)
    ↑
US2 (AI Evaluation)
    ↑
US3 (Completeness)
    ↓
US4 (Embeddings)  [parallel with US2/US3]

US5 (Encrypted Storage) ← Already implemented

US6 (Subscription Limits) ← Depends on US1
US7 (CV Management) ← Depends on US1
US8 (Quota Tracking) ← Depends on US2
```

## Parallel Execution Opportunities

- T003, T004: Can run in parallel (foundational)
- T005, T006: Can run in parallel (US1 setup)
- T011, T012: Can run in parallel (US2/US3 evaluation setup)
- T035, T036, T037: Can run in parallel (test files)

## Independent Test Criteria

| User Story | Test Criteria |
|-----------|-------------|
| US1 | Send PDF/DOCX/TXT file to bot → text extracted, encrypted, stored |
| US2 | Upload CV → AI returns skills, experience, suggestions |
| US3 | Upload CV → completeness scored 0-100%, missing sections shown |
| US4 | Upload CV → 768-dim vector stored (or null on failure) |
| US5 | Upload CV → retrieve → decrypts correctly |
| US6 | Free user at limit → sees upgrade prompt |
| US7 | Multiple CVs → list/activate/deactivate/delete works |
| US8 | At quota → sees upgrade prompt |

## Task Dependencies

| Phase | Depends On | Can Parallelize |
|-------|-----------|-----------------|
| Phase 1 (Setup) | - | No (migration must run first) |
| Phase 2 (Foundational) | Phase 1 | T003, T004 can parallelize |
| Phase 3 (US1) | Phase 2 | T005, T006 can parallelize |
| Phase 4 (US2/US3) | Phase 3 | T011, T012 can parallelize |
| Phase 5 (US4) | Phase 3 | Can run parallel with Phase 4 |

## Summary

**Total Tasks**: 46  
**User Stories**: 8 (US1-US8)  
**MVP Scope**: Phase 3 (US1 - CV Upload)

**Suggested Start**: Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2/US3)