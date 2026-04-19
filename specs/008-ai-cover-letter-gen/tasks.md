# Tasks: AI Cover Letter Generation

**Feature**: 008-ai-cover-letter-gen  
**Date**: 2026-04-19  
**Plan**: plan.md  
**Spec**: spec.md

## Phase 1: Setup

- [x] T001 Create prompt template at config/prompts/cover_letter_prompt.txt with placeholders including startup validation:
  Placeholders required: {job_title}, {company}, {location}, {job_description}, {cv_content}, {user_name}, {tone}, {length}, {focus}, {language}
  Validation: CoverLetterService.__init__ reads template, validates all placeholders exist, logs to Sentry and falls back to embedded default if invalid.

## Phase 2: Foundational

- [x] T002 Create UserQuotaTracking model in src/models/user_quota_tracking.py
- [x] T003 Create UserQuotaTrackingRepository in src/repositories/user_quota_tracking_repository.py
- [x] T004 [P] Create quota service in src/services/quota_service.py
- [x] T005 [P] Add config settings for cover letter in config/settings.py

## Phase 3: User Story 1 - Generate Cover Letter from Job Notification

**Independent Test**: Trigger job notification, click Cover Letter button, verify customization form, generate letter, verify quota increment. Delivers immediate value by providing a ready-to-use cover letter.

- [x] T006 [P] [US1] Enhance CoverLetterLog model in src/models/cover_letter_log.py with new fields
- [x] T007 [P] [US1] Enhance CoverLetterLogRepository in src/repositories/cover_letter_repository.py
- [x] T008 [US1] Create CoverLetterService in src/services/cover_letter_service.py
- [x] T009 [US1] Create cover letter keyboard layouts in src/bot/keyboards.py
- [x] T010 [US1] Create cover_letter FSM states in src/bot/states.py
- [x] T011 [US1] Create cover letter handler in src/bot/handlers/cover_letter.py
- [x] T012 [US1] Register cover letter router in src/bot/router.py

## Phase 4: User Story 2 - Generate Cover Letter from Saved Jobs

**Independent Test**: Save job, navigate to /my_jobs, click Cover Letter button, verify same customization flow as notifications.

- [x] T013 [US2] Add Cover Letter button to saved job keyboard in src/bot/handlers/saved_jobs.py
- [x] T014 [US2] Reuse cover letter handler flow for /my_jobs entry point

## Phase 5: User Story 3 - Regenerate with Different Settings

**Independent Test**: Generate cover letter, click Regenerate, change settings, verify new letter generated and quota incremented again.

- [x] T015 [US3] Add regenerate callback handler in src/bot/handlers/cover_letter.py
- [x] T016 [US3] Implement pre-fill customization form with previous settings

## Phase 6: User Story 4 - Daily Quota Reset at Midnight Damascus Time

**Independent Test**: Set system time to 23:59 Damascus time, exhaust quota, wait 2 minutes, verify quota resets at 00:00.

- [x] T017 [US4] Create scheduled task for quota reset in src/services/quota_reset_task.py
- [x] T018 [US4] Configure TaskIQ cron job for midnight Damascus reset

## Phase 7: User Story 5 - Purchase Extra Generations

**Independent Test**: Exhaust quota, click Purchase, select pack, verify UI shows payment flow (deferred to SPEC-009).

- [x] T019 [US5] Create quota exceeded keyboard with purchase options in src/bot/keyboards.py
- [x] T020 [US5] Add purchase callback placeholder in src/bot/handlers/cover_letter.py

## Phase 8: User Story 6 - Copy Generated Cover Letter

**Independent Test**: Generate cover letter, click Copy Text, verify text is displayed in monospace/code block for easy copying.

- [x] T021 [US6] Add copy callback handler in src/bot/handlers/cover_letter.py

## Phase 9: User Story 7 - Handle Insufficient CV Data Gracefully

**Independent Test**: Upload minimal CV, attempt generation, verify warning and choice prompt.

- [x] T022 [US7] Implement CV completeness check in src/services/cover_letter_service.py
- [x] T023 [US7] Add warning display logic in cover letter handler

## Phase 10: Polish & Cross-Cutting

- [x] T024 Add error handling for API failures in src/bot/handlers/cover_letter.py
- [x] T025 Add countdown to midnight Damascus in quota exhausted message
- [x] T026 Add i18n messages in src/bot/utils/i18n.py
- [x] T027a Create Alembic migration 015 for cover_letter_logs enhancements (cv_id, content, tone, length, focus_area, language, ai_model, generation_count, counted_in_quota)
- [x] T027b Create Alembic migration 016 for user_quota_tracking table with unique index on (user_id, date)

## Summary

| Phase | User Story | Tasks |
|-------|-----------|-------|
| 1 | Setup | 1 |
| 2 | Foundational | 4 |
| 3 | US1: Generate from Notification | 7 |
| 4 | US2: Generate from Saved Jobs | 2 |
| 5 | US3: Regenerate | 2 |
| 6 | US4: Daily Reset | 2 |
| 7 | US5: Purchase Extra | 2 |
| 8 | US6: Copy Text | 1 |
| 9 | US7: CV Warning | 2 |
| 10 | Polish | 4 |
| 11 | Tests (Constitution VIII) | 16+2=18 |
| | **Total** | **48** |

## Story Dependencies

- **US2**: Depends on US1 completing (shares same handler flow)
- **US3**: Depends on US1 completing (needs existing cover letter to regenerate)
- **US4**: Independent (infrastructure task)
- **US5**: Independent (UI enhancement)
- **US6**: Depends on US1 completing (needs cover letter to copy)
- **US7**: Independent (service enhancement)

## Parallel Execution Opportunities

| Tasks | Can Run In Parallel |
|-------|---------------------|
| T002, T003, T004, T005 | Yes - Different files, no dependencies |
| T006, T007 | Yes - Model and repository in parallel |
| T009, T010 | Yes - Keyboard and states in parallel |
| T017, T018 | No - T017 must complete first |
| T019, T020 | Yes - Different aspects of purchase feature |
| T024, T025, T026 | Yes - Polish tasks in parallel |

## MVP Scope (User Story 1 Only)

For fastest delivery, implement first:
1. T001-T005 (Setup + Foundational)
2. T006-T012 (US1 complete flow)

After MVP: Continue with remaining user stories in priority order.

## Tests

Per Constitution VIII (Testing Requirements), add test tasks. Tests are MANDATORY:

### Test Phase 1: Service Tests (US1)

- [ ] UT001 [US1] Unit test CoverLetterService.generate() - success path in src/tests/unit/services/test_cover_letter_service.py
- [ ] UT002 [US1] Unit test CoverLetterService._validate_quota() - sufficient quota in src/tests/unit/services/test_cover_letter_service.py
- [ ] UT003 [US1] Unit test CoverLetterService._validate_quota() - insufficient quota in src/tests/unit/services/test_cover_letter_service.py
- [ ] UT004 [US1] Unit test QuotaService.increment_daily_used() in src/tests/unit/services/test_quota_service.py

### Test Phase 2: Repository Tests (US1)

- [ ] UT005 [US1] Integration test UserQuotaTrackingRepository in src/tests/integration/test_cover_letter_repository.py

### Test Phase 3: Handler Tests (US1)

- [ ] UT006 [US1] Integration test cover_letter handler callback in src/tests/integration/test_cover_letter_handler.py

## Additional Test Tasks for QA Gate (Constitution VIII)

- [ ] UT007 Test coverage minimum 80% enforcement via pytest-cov
- [ ] UT008 Each test case tests one behavior (naming convention check)
- [ ] UT009 Performance validation: SC-001 10s p95 latency check
- [ ] UT010 Quota accuracy: SC-005 zero double-counting validation
- [ ] UT011 Quota reset timing: SC-003 60-second midnight reset validation
- [ ] UT012 Word count validation: SC-004 200/400/600 words based on length
- [ ] UT013 Purchased persist: SC-006 extra generations survive daily reset
- [ ] UT014 DST handling: SC-007 Damascus timezone accuracy year-round (test with mocked zoneinfo for spring forward/last Friday March 3:00:01 AM UTC+3 and fall back/last Friday October 2:00:00 AM UTC+2)

### Integration Tests

- [ ] IT001 End-to-end flow: Job notification → Cover Letter button → Customization form → Generate → Display in src/tests/integration/
- [ ] IT002 Saved jobs flow: /my_jobs → Cover Letter button → Same flow as IT001 in src/tests/integration/
- [ ] IT003 Regenerate flow: Generate → Regenerate with different settings → Existing cover letter updated in-place in src/tests/integration/
- [ ] IT004 Quota exhausted flow: Exhaust quota → Purchase/Wait/Upgrade options displayed in src/tests/integration/
- [ ] IT005 No CV flow: No CV uploaded → Block with redirect message in src/tests/integration/
- [ ] IT006 Concurrent generation lock: User clicks Generate twice → Second click shows "Already generating..." in src/tests/integration/
- [ ] IT007 CV warning flow: Upload minimal CV → Generate → Warning displayed → Generate Anyway in src/tests/integration/

## Logging Test (FR-040)

- [ ] UT015 Verify error logging to Sentry for failed API calls in src/tests/unit/services/
- [ ] UT016 Verify metrics service receives operation counts (attempts, successes, failures) in src/tests/unit/services/