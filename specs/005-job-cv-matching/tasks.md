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