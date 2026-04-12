# Tasks: Job-CV Matching Engine

**Feature**: Job-CV Matching Engine  
**Branch**: `005-job-cv-matching`  
**Spec**: `specs/005-job-cv-matching/spec.md`  
**Plan**: `specs/005-job-cv-matching/plan.md`

## Implementation Phases

### Phase 1: Setup

Project initialization and configuration.

- [x] T001 Create Alembic migration 006_matching_engine in migrations/versions/ for:
  - CREATE TABLE job_categories
  - CREATE TABLE user_preferences  
  - ALTER TABLE job_matches ADD COLUMN cv_id UUID REFERENCES user_cvs(id)
  - CREATE UNIQUE INDEX idx_job_matches_unique ON job_matches(job_id, user_id, cv_id)
- [x] T002 Create matching configuration in config/settings.py (MATCHING_THRESHOLD_DEFAULT, NOTIFICATION_BATCH_WINDOW, TIER_DELAYS)
- [x] T003 Add matching dependencies to requirements.txt (pgvector, redis, celery)

### Phase 2: Foundational (Blocking Prerequisites)

Tasks that MUST complete before any user story implementation.

- [x] T004 Create JobMatch SQLAlchemy model in src/models/job_match.py
- [x] T005 Create JobCategory SQLAlchemy model in src/models/job_category.py
- [x] T006 Create UserPreferences SQLAlchemy model in src/models/user_preferences.py
- [x] T007 Create custom exceptions in src/exceptions/matching.py (JobNotFoundError, EmbeddingNotAvailableError, ProTierRequiredError, ThresholdOutOfRangeError)

### Phase 3: US1 - Real-time Job Matching (P1)

**Independent Test**: A new job is stored. Within 5 seconds, match records created and notifications queued.

**Story Goal**: Match new jobs against all active CVs using pgvector cosine similarity.

- [x] T008 [P] [US1] Implement JobMatchRepository in src/repositories/job_match_repository.py
- [x] T009 [P] [US1] Implement get_active_cvs query in src/repositories/user_cv_repository.py
- [x] T010 [P] [US1] Implement get_job_with_embedding query in src/repositories/job_repository.py
- [x] T011 [US1] Implement MatchingService with pgvector cosine similarity in src/services/matching_service.py
- [x] T012 [US1] Create Celery task match_job_task in src/workers/matching_tasks.py
- [x] T013 [US1] Integrate matching trigger after job ingestion in SPEC-003 pipeline

### Phase 4: US2 - Tiered Notification Delivery (P1)

**Independent Test**: Job published at 14:30. Free at ~15:30, Basic at ~14:40, Pro immediately.

**Story Goal**: Send notifications with tier-based delays.

- [x] T014 [P] [US2] Implement NotificationQueue Redis client in src/services/notification_queue.py
- [x] T015 [US2] Implement NotificationService with tier delays in src/services/notification_service.py
- [x] T016 [US2] Create Celery Beat task process_notifications in src/workers/matching_tasks.py
- [x] T017 [US2] Implement Telegram notification sender in src/bot/notification_sender.py
- [x] T018 [US2] Add inline keyboard buttons [View Details] [Generate Cover Letter]

### Phase 5: US3 - Configurable Similarity Thresholds (P2)

**Independent Test**: Personal threshold 0.85, category 0.75, system 0.80. System uses highest priority.

**Story Goal**: Support configurable thresholds per user and category.

- [x] T019 [P] [US3] Implement ThresholdService in src/services/threshold_service.py
- [x] T020 [US3] Implement admin threshold configuration in src/services/admin_threshold_service.py

### Phase 6: US4 - Historical Job Matching (P2)

**Independent Test**: User triggers /search_history 7. Matches jobs from past 7 days.

**Story Goal**: Pro users can search historical jobs.

- [x] T021 [P] [US4] Implement historical job query in src/repositories/job_repository.py
- [x] T022 [US4] Implement match_historical in src/services/matching_service.py
- [x] T023 [US4] Add /search_history command handler in src/bot/handlers.py

### Phase 7: US5 - Match History & Tracking (P2)

**Independent Test**: User runs /my_jobs. Sees list with similarity scores and dates.

**Story Goal**: Users can view and track their job matches.

- [x] T024 [P] [US5] Implement get_user_matches query in src/repositories/job_match_repository.py
- [x] T025 [US5] Implement mark_clicked in src/repositories/job_match_repository.py
- [x] T026 [US5] Add /my_jobs command handler in src/bot/handlers.py
- [x] T027 [US5] Add callback query handler for inline button clicks

### Phase 8: US6 - Match Quality Metrics (P3)

**Independent Test**: System calculates CTR per threshold. Flags low-performing thresholds.

**Story Goal**: Track match quality for improvement.

- [x] T028 [US6] Implement metrics calculation in src/services/metrics_service.py
- [x] T029 [US6] Create Celery Beat task calculate_metrics in src/workers/matching_tasks.py
- [x] T029-1 [P] [US6] Add unit tests for MatchingService in tests/unit/test_matching_service.py
- [x] T029-2 [P] [US6] Add unit tests for NotificationService in tests/unit/test_notification_service.py
- [x] T029-3 [P] [US6] Add unit tests for ThresholdService in tests/unit/test_threshold_service.py
- [x] T029-4 [P] [US6] Add unit tests for MetricsService in tests/unit/test_metrics_service.py

### Phase 9: Polish & Cross-Cutting Concerns

Final integration and cleanup.

- [x] T030 [P] Implement CV deactivation cancellation in src/services/notification_service.py
- [x] T031 [P] Add Redis fallback for notification failures in src/services/notification_service.py
- [x] T032 Add integration test test_matching_pipeline in tests/integration/ covering:
  - End-to-end: Job ingested → CVs matched → Notifications queued
  - Multi-CV scenario: Pro user with 2 CVs matching same job
  - Tier delays: Free/Basic/Pro notification timing
  - Historical matching: /search_history command flow
  - Threshold priority: User > Category > System default
- [x] T033 Run lint and typecheck per AGENTS.md
- [x] T034 Verify test coverage meets 80% threshold using pytest --cov
- [x] T035 Implement tier upgrade handler in src/services/notification_service.py (recalculate Redis queue score on subscription change)

### Phase 10: Performance Fix — pgvector Native Cosine Similarity

Fix catastrophic performance violation: replace Python for-loop cosine similarity with native pgvector SQL query.

- [x] T036 Add find_similar_cvs method to CVRepository in src/repositories/cv_repository.py using pgvector cosine_distance in a single SQL query
- [x] T037 Refactor MatchingService.match_new_job to use find_similar_cvs with system default threshold, then filter client-side by per-user effective thresholds via ThresholdService
- [x] T038 Remove _cosine_similarity static method and _get_all_active_cvs from MatchingService
- [x] T039 Refactor MatchingService.match_historical to use find_similar_cvs instead of Python cosine loop
- [x] T040 Update unit tests in tests/unit/test_matching_service.py: remove TestCosineSimilarity, add pgvector query test with per-user threshold filtering
- [x] T041 Update spec.md FR-002 to mandate pgvector native cosine_distance

### Phase 11: Performance Fix — Bulk Existing Match Lookup

Eliminate N+1 query in historical matching by replacing per-match get_by_job_and_user calls with a single bulk query.

- [x] T042 Add get_existing_match_keys method to MatchRepository in src/repositories/match_repository.py using single bulk query with IN clauses
- [x] T043 Refactor MatchingService.match_historical to use get_existing_match_keys set lookup instead of per-match DB calls
- [x] T044 Update spec.md FR-036 to mandate bulk match existence checking

### Phase 12: Data Integrity & Notification Timestamp Fix

Enforce cv_id NOT NULL, add telegram_published_at for accurate notification timing, add threshold check constraint.

- [x] T045 Make cv_id NOT NULL in JobMatch model (src/models/job_match.py) and update relationship type
- [x] T046 Add telegram_published_at column to Job model (src/models/job.py) as nullable DateTime(timezone=True)
- [x] T047 Add CHECK constraint ck_category_threshold_range to JobCategory model (src/models/job_category.py)
- [x] T048 Create Alembic migration 009: cv_id NOT NULL (with data migration), telegram_published_at column, threshold check constraint
- [x] T049 Update NotificationService.queue_match_notification to use telegram_published_at with created_at fallback (FR-007 compliance)
- [x] T050 Update spec.md: FR-005 cv_id NOT NULL, FR-007 telegram_published_at, FR-037/FR-038 new constraints

### Phase 13: Notification Queue Data Integrity & Resilience

Preserve match records on CV deactivation, add job_published_at to queue payload, improve tier upgrade score recalculation, add Redis fetch error handling.

- [x] T051 Remove match record deletion from cancel_notifications_for_cv — only remove from Redis queue, preserve match history
- [x] T052 Add job_published_at field to enqueue payload in NotificationQueue for accurate tier upgrade score recalculation
- [x] T053 Update update_score_by_user to use job_published_at from queue payload for score recalculation, with fallback to current score adjustment
- [x] T054 Pass job_published_at from NotificationService.queue_match_notification to enqueue
- [x] T055 Add try/except around fetch_due in process_due_notifications — log error with exc_info, return 0 to let next beat tick retry
- [x] T056 Update spec.md FR-030/031/033/035 for match preservation, job_published_at in queue, and Redis error handling

### Phase 14: Bot Handler Bug Fixes

Fix broken Celery task import, fix user_id type mismatch (Telegram ID vs DB UUID), add Pro tier guard before UI display.

- [x] T057 Fix search_history callback handler: replace non-existent workers.tasks.matching_tasks import with direct MatchingService.match_historical call using DB session
- [x] T058 Fix search_history callback handler: replace str(callback.from_user.id) with UserRepository.get_by_telegram_id lookup to get DB UUID
- [x] T059 Add Pro tier check to cmd_search_history handler before displaying days selection UI — non-Pro users see upgrade message with inline button
- [x] T060 Update spec.md US4 acceptance scenario 6 for upgrade button in rejection message

### Phase 15: Service Consolidation & IntegrityError Handling

Move set_category_threshold into ThresholdService, delete admin_threshold_service, replace MATCHING_THRESHOLD_DEFAULT with DEFAULT_THRESHOLD from threshold_service, make IntegrityError handling specific to unique violations only.

- [x] T061 Add set_category_threshold method to ThresholdService with validation (0.00-1.00 range) and upsert logic
- [x] T062 Delete src/services/admin_threshold_service.py — functionality moved to ThresholdService
- [x] T063 Remove MATCHING_THRESHOLD_DEFAULT from matching_service.py, use DEFAULT_THRESHOLD from threshold_service
- [x] T064 Make IntegrityError handling in MatchRepository.create_match specific to pgcode 23505 (unique violation) — re-raise all other IntegrityErrors
- [x] T065 Update spec.md FR-006 for specific IntegrityError handling

## Dependencies

```
US1 ─┬─→ US2 (notification depends on matching)
     ├─→ US3 (threshold service used in matching)
     ├─→ US4 (uses matching service)
     └─→ US5 (uses job_match repository)

US2 ─┬─→ US1 (needs matches to notify)
     └─→ US5 (click tracking on notifications)

US3 → US1 (uses threshold in matching)

US4 → US1 (uses matching service)

US5 ─┐
     └─→ US2 (notifications have click tracking)

US6 → US1, US2 (uses match data for metrics)
```

## Parallel Execution Opportunities

| Tasks | File Paths | Reason |
|------|-----------|-------|
| T008, T009, T010 | Different repository files | No dependencies between |
| T014, T019, T021, T024 | Different service files | Independent services |
| T030, T031 | Independent handlers | No shared state |

## MVP Scope

**Recommended MVP**: US1 (Real-time Job Matching) with US2 (Tiered Notification Delivery)

This provides the core value:
- Jobs automatically matched against CVs using similarity
- Notifications sent with tier-based delays

Additional US3 (Thresholds) can be included if quick to implement.

## Implementation Strategy

1. **Phase 1-2 First**: Database setup + core models (blocking prerequisites)
2. **US1 Priority**: Matching engine - core value proposition
3. **US2 Next**: Notification delivery - tiered delays define tier value
4. **Incremental Delivery**: Each user story is independently testable