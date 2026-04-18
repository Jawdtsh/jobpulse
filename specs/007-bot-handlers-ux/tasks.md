# Tasks: Bot Handlers & UX Flow

**Input**: Design documents from `/specs/007-bot-handlers-ux/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create bot directory structure: src/bot/handlers/, src/bot/utils/
- [X] T002 [P] Create services directory structure: src/services/
- [X] T003 [P] Create repositories directory structure: src/repositories/
- [X] T004 Install aiogram 3.x and redis dependencies

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create SavedJob model in src/models/saved_job.py
- [X] T006 [P] Create SavedJobRepository in src/repositories/saved_job_repository.py
- [X] T007 Create BotSessionService for Redis-backed session FSM in src/services/bot_session_service.py
- [X] T008 Create SavedJobService in src/services/saved_job_service.py
- [X] T009 [P] Create i18n utility for bilingual messages in src/bot/utils/i18n.py - must load messages from JSON file (src/bot/locales/messages.json), support 'ar' and 'en' locales (default to Arabic), format: `{key: {"ar": "...", "en": "..."}}`
- [X] T010 Create inline keyboard builders in src/bot/keyboards.py
- [X] T011 [P] Create middlewares (auth, rate limit, callback validation) in src/bot/middlewares.py - Rate Limiter middleware must implement queue with exponential backoff for 30 msg/s limit; Callback Validation must verify callback.from_user == message.from_user for all inline buttons
- [X] T011c [P] Configure application structured logging and Sentry integration (e.g., in src/bot/utils/logger.py) to fulfill observability requirements [SC-014]
- [X] T011d [P] Implement a basic /health HTTP endpoint (running alongside the bot webhook) to verify bot status, Redis connection, and Database connectivity for uptime monitoring [SC-013]
- [X] T012 Create FSM states definition in src/bot/states.py
- [X] T013 [P] Create Alembic migration `alembic/versions/008_add_is_dismissed.py` to add is_dismissed column to JobMatch table (BOOLEAN NOT NULL DEFAULT FALSE)
- [X] T014 [P] Create Alembic migration `alembic/versions/009_create_saved_jobs.py` for the saved_jobs table with columns (id UUID PK, user_id UUID FK → users.id ON DELETE CASCADE, job_id UUID FK → jobs.id ON DELETE SET NULL, saved_at TIMESTAMP, created_at TIMESTAMP, updated_at TIMESTAMP), unique constraint on (user_id, job_id)
- [X] T014a [P] Create Language model in src/models/language.py and Alembic migration `alembic/versions/010_create_languages_table.py` (include seed data for 'ar' and 'en')
- [X] T014b [P] Create Alembic migration `alembic/versions/011_add_language_fk_and_notifications.py` to add `language_id` (FK → languages.id) to users table and `notification_enabled` (BOOLEAN DEFAULT TRUE) to user_preferences table
- [X] T014c [P] Implement Redis session cleanup job in src/services/bot_session_service.py to remove expired sessions older than 15 minutes, scheduled via TaskIQ

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - User Registration & Onboarding (Priority: P1) 🎯 MVP

**Goal**: Users can register via /start and see main menu with 4 buttons; /help shows commands

**Independent Test**: Send /start to bot, verify user record created, welcome message with menu buttons displayed

### Implementation for User Story 1

- [X] T015 [P] [US1] Create registration handler in src/bot/handlers/registration.py (/start, /help)
- [X] T016 [P] [US1] Implement language detection from Telegram user settings
- [X] T017 [P] [US1] Implement 12-character referral code generation
- [X] T018 [US1] Implement main menu keyboard with 4 buttons (Upload CV, My Jobs, Invite Friends, Settings)
- [X] T019 [US1] Implement /help command showing all available commands
- [X] T020 [US1] Handle referral parameter in /start (track referred_by)

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CV Upload & Evaluation Display (Priority: P1)

**Goal**: Users can upload CVs, see validation errors, processing status, and evaluation results

**Independent Test**: Upload a valid PDF/DOCX/TXT file, verify evaluation results displayed; upload invalid file, verify specific error

### Implementation for User Story 2

- [X] T021 [P] [US2] Create CV upload handler in src/bot/handlers/cv_upload.py
- [X] T022 [P] [US2] Implement file validation (PDF, DOCX, TXT only, max 5MB)
- [X] T023 [P] [US2] Implement processing status message display
- [X] T024 [US2] Integrate with existing CV evaluation service
- [X] T025 [US2] Implement tier-based CV limit checking (Free/Basic=1, Pro=2)
- [X] T026 [US2] Implement replacement prompt for Free/Basic users with existing CV
- [X] T027 [US2] Implement automatic CV activation when no active CV exists
- [X] T028 [US2] Add FSM state transitions for CV upload flow

**Checkpoint**: User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 2.1 - CV Deletion & Management (Priority: P1)

**Goal**: Users can view their CVs via /my_cvs and delete them with confirmation

**Independent Test**: Upload CV, send /my_cvs, click Delete, confirm, verify CV removed; test prompt to activate replacement when deleting active CV

### Implementation for User Story 2.1

- [X] T029 [P] [US2.1] [FR-014a] Create CV management handler in src/bot/handlers/cv_management.py
- [X] T030 [US2.1] [FR-014a] Implement /my_cvs command listing all user CVs with status, date, score
- [X] T031 [US2.1] [FR-014b] Implement Delete button with confirmation prompt
- [X] T032 [US2.1] [FR-014c] Implement prompt to activate replacement CV when deleting active CV
- [X] T033 [US2.1] [FR-014d] Implement "job matching paused" message when deleting only CV

**Checkpoint**: User Story 2.1 should be fully functional and testable independently

---

## Phase 6: User Story 3 - Job Match Notifications (Priority: P1)

**Goal**: Users receive rich job notifications with action buttons; Save, Dismiss, Full Details work

**Independent Test**: Trigger match notification, verify content and buttons; click Save, verify saved; click Dismiss, verify marked

### Implementation for User Story 3

- [X] T034 [P] [US3] Create job notification handler in src/bot/handlers/job_notifications.py
- [X] T035 [P] [US3] Implement rich notification message format (title, company, location, salary, match %, description preview)
- [X] T036 [P] [US3] Implement Save button callback and SavedJobService.save() call
- [X] T037 [US3] Implement "Already saved" handling for duplicates
- [X] T038 [US3] Implement Full Details button showing full job description
- [X] T039 [US3] Implement Dismiss button marking is_dismissed=true
- [X] T040 [US3] Implement Pro tier multi-CV notification showing scores for each CV
- [X] T041 [US3] Implement notification skip for users with no active CVs

**Checkpoint**: User Story 3 should be fully functional and testable independently

---

## Phase 7: User Story 4 - Saved Jobs Management (Priority: P2)

**Goal**: Users can browse saved/notified/dismissed jobs with filters and pagination

**Independent Test**: Save jobs via notifications, browse /my_jobs, switch views, apply filters, navigate pages

### Implementation for User Story 4

- [X] T042 [P] [US4] Create saved jobs handler in src/bot/handlers/saved_jobs.py
- [X] T043 [P] [US4] Implement /my_jobs with view selector (Saved, All Notified, Dismissed)
- [X] T044 [US4] Implement job card display with title, company, match %, relative date
- [X] T045 [US4] Implement pagination (5 jobs/page, Prev/Next buttons)
- [X] T046 [US4] Implement similarity filters (>80%, >70%, All)
- [X] T047 [US4] Implement date range filters (7, 14, 30 days)
- [X] T048 [US4] Implement filter persistence across page navigation
- [X] T049 [US4] Implement empty state messages
- [X] T050 [US4] Implement Unsave/Remove button for saved jobs

**Checkpoint**: User Story 4 should be fully functional and testable independently

---

## Phase 8: User Story 5 - Settings & Preferences (Priority: P2)

**Goal**: Users can view and edit their similarity threshold, notification toggle, view referral stats

**Independent Test**: Send /settings, verify all fields displayed; change threshold, verify persisted; toggle notifications, verify state change

### Implementation for User Story 5

- [X] T051 [P] [US5] Create settings handler in src/bot/handlers/settings.py
- [X] T052 [P] [US5] Implement /settings display with threshold, notifications, language, tier, referral code
- [X] T053 [US5] Implement threshold editing (60%-100% range validation)
- [X] T054 [US5] Implement notification toggle with immediate persistence
- [X] T055 [US5] Implement Copy and Share buttons for referral code
- [X] T056 [US5] Implement referral statistics display (total invites, successful, progress)
- [X] T057 [US5] Implement Upgrade Plan button linking to /subscribe

**Checkpoint**: User Story 5 should be fully functional and testable independently

---

## Phase 9: User Story 6 - Referral System UI (Priority: P2)

**Goal**: Users can invite friends and track referral rewards

**Independent Test**: Click Invite Friends, verify pre-filled share message; share link, verify referral tracked

### Implementation for User Story 6

- [X] T058 [P] [US6] Create referral handler in src/bot/handlers/referral.py
- [X] T059 [US6] Implement /invite command with pre-filled referral message
- [X] T060 [US6] Implement referral link generation (https://t.me/{bot}?start=ref_{code})
- [X] T061 [US6] Implement Share Link using platform's native share interface
- [X] T062 [US6] Integrate referral tracking into /start handler (referred_by field)

**Checkpoint**: User Story 6 should be fully functional and testable independently

---

## Phase 10: User Story 7 - Subscription Plans Preview (Priority: P3)

**Goal**: Users can view subscription tiers and see their current plan highlighted

**Independent Test**: Send /subscribe, verify Free/Basic/Pro tiers displayed with correct features; current tier highlighted

### Implementation for User Story 7

- [X] T063 [P] [US7] Create subscription handler in src/bot/handlers/subscription.py
- [X] T064 [US7] Implement /subscribe displaying Free, Basic ($7/mo), Pro ($12/mo)
- [X] T065 [US7] Display feature comparison (CV limits, notification delays, cover letter quotas)
- [X] T066 [US7] Highlight user's current tier with checkmark
- [X] T067 [US7] Add Choose Plan buttons (non-functional placeholders)

**Checkpoint**: User Story 7 should be fully functional and testable independently

---

## Phase 11: User Story 8 - Error Handling & Recovery (Priority: P3)

**Goal**: Users receive clear error messages and can cancel in-progress operations

**Independent Test**: Start flow, send /cancel, verify returns to main menu; trigger error, verify appropriate message

### Implementation for User Story 8

- [X] T068 [P] [US8] Create error handler in src/bot/handlers/errors.py
- [X] T069 [P] [US8] Implement /cancel command stopping current operation and returning to main menu
- [X] T070 [US8] Implement BotSession expiry after 10 minutes inactivity (within 5 seconds of threshold)
- [X] T071 [US8] Implement generic error message ("حدث خطأ. حاول لاحقاً.")
- [X] T072 [US8] Implement retry button for recoverable errors (network failures)

**Checkpoint**: User Story 8 should be fully functional and testable independently

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T075 [P] Run ruff linting and fix any issues
- [X] T076 [P] Run mypy type checking and fix any issues
- [X] T077 Write unit tests for BotSessionService in tests/unit/services/
- [X] T078 Write unit tests for SavedJobService in tests/unit/services/
- [X] T079 Write unit tests for registration handler in tests/unit/bot/
- [X] T080 Write unit tests for cv_upload handler in tests/unit/bot/
- [X] T081 Integrate all handlers into main bot router in src/bot/router.py
- [X] T082 Run quickstart.md validation
- [X] T082a [P] Write integration test for full registration flow in tests/integration/test_registration_flow.py
- [X] T082b [P] Write integration test for CV upload -> evaluation -> activation flow in tests/integration/test_cv_upload_flow.py
- [X] T082c [P] Write integration test for job notification -> save -> /my_jobs retrieval in tests/integration/test_job_notification_flow.py
- [X] T082d [P] Write integration test for filter persistence across pagination in tests/integration/test_filter_persistence.py
- [X] T083 Write performance integration tests to verify SC-001 (<2s registration), SC-004 (<1s list load), SC-006 (<500ms button response), and SC-012 (Session expiry within 5s)

---

## Phase 13: Bug Fixes — Spec Violations & Runtime Crashes

**Purpose**: Fix four critical spec violations causing runtime crashes and incorrect UX behavior

- [X] T084 Fix i18n get_locale() default to "ar" (FR-003) and logger.error → logger.exception (TRY400) in src/bot/utils/i18n.py
- [X] T085 Fix SavedJob ondelete="SET NULL" → "CASCADE" with nullable=False and Mapped["Job | None"] → Mapped["Job"] in src/models/saved_job.py
- [X] T086 Create Alembic migration 014_saved_job_cascade_fk.py to update FK constraint
- [X] T087 Fix toggle notification handler: new_state=True → False when prefs is None (FR-034) in src/bot/handlers/settings.py
- [X] T088 Extract _render_settings() helper to avoid unsafe callback.message.from_user mutation in src/bot/handlers/settings.py
- [X] T089 Remove dead code in callback_upgrade_plan (RUF034) in src/bot/handlers/settings.py
- [X] T090 Fix callback_back_to_menu hardcoding tier="Free" — fetch real tier from DB (FR-036) in src/bot/handlers/registration.py
- [X] T091 Write unit tests for i18n fixes in tests/unit/bot/test_i18n.py
- [X] T092 Write unit tests for settings fixes in tests/unit/bot/test_settings.py
- [X] T093 Write unit tests for registration back_to_menu fix in tests/unit/bot/test_registration.py

---

## Phase 14: Bug Fixes — Dead Filter Parameters, Query Optimization, Null Safety

**Purpose**: Fix dead filter parameters, optimize queries, and add defensive null checks in notification handlers

- [X] T094 Remove dead min_similarity parameter and implement days filter in SavedJobRepository.get_saved_by_user (FR-026) in src/repositories/saved_job_repository.py
- [X] T095 Optimize unsave_job from SELECT-then-DELETE to single delete().where() in src/repositories/saved_job_repository.py
- [X] T096 Add exclude_dismissed parameter to MatchRepository.get_notified_matches_by_user to fix pagination bug in src/repositories/match_repository.py
- [X] T097 Remove client-side dismissed filter from notified view in src/bot/handlers/saved_jobs.py
- [X] T098 Remove dead _total_pages variable in src/bot/handlers/saved_jobs.py
- [X] T099 Add logger.debug in edit-text fallback except block in src/bot/handlers/saved_jobs.py
- [X] T100 Add null safety for job.description in callback_job_details in src/bot/handlers/job_notifications.py
- [X] T101 Replace hardcoded "✅" with localized t("job_unsaved", locale) in unsave callback + add messages.json key
- [X] T102 Replace try/except/pass with contextlib.suppress(Exception) in unsave and dismiss callbacks (SIM105, BLE001, S110)
- [X] T103 Write unit tests for saved_job_repository days filter and unsave optimization
- [X] T104 Write unit tests for match_repository exclude_dismissed parameter
- [X] T105 Write unit tests for job_notifications null safety and localization fixes

---

## Phase 15: Bug Fixes — Dead Middleware, Inconsistent Constants, Lint Issues

**Purpose**: Remove dead middleware, fix inconsistent constants, and resolve lint issues in infrastructure files

- [X] T106 Delete empty CallbackValidationMiddleware class from src/bot/middlewares.py
- [X] T107 Remove unused _queue dict from RateLimiterMiddleware.__init__ in src/bot/middlewares.py
- [X] T108 Replace unbounded _user_timestamps dict with cachetools.TTLCache(maxsize=10000, ttl=60) in src/bot/middlewares.py
- [X] T109 Add cachetools>=5.5.0 to requirements.txt
- [X] T110 Replace hardcoded 900 with CLEANUP_THRESHOLD = SESSION_TTL + 300 in src/services/bot_session_service.py
- [X] T111 Fix RUF006: store health_task reference and cancel after polling in main.py
- [X] T112 Replace __import__("sqlalchemy").text("SELECT 1") with proper import in src/bot/health.py
- [X] T113 Write unit tests for middleware TTLCache and deleted CallbackValidationMiddleware
- [X] T114 Write unit tests for bot_session_service CLEANUP_THRESHOLD constant
- [X] T115 Write unit tests for health.py proper sqlalchemy import

---

## Phase 16: Bug Fixes — Lint Violations, Wrong Locale Keys, Hardcoded Values

**Purpose**: Fix all remaining lint violations, wrong locale keys, hardcoded values, and fragile code patterns across bot handlers

- [X] T116 Fix RET505: remove unnecessary else after return in cv_upload.py
- [X] T117 Fix RUF059: rename unused unpacked variables to _title, _text in cv_upload.py (2 locations)
- [X] T118 Fix ANN202: add -> None return type to _process_upload in cv_upload.py
- [X] T119 Fix ARG001: rename unused state to _state in handle_invalid_file in cv_upload.py
- [X] T120 Fix wrong locale key: t("no_jobs") → t("no_cvs") in cv_management.py
- [X] T121 Replace fragile t("help").split("\\n")[0] with t("cv_list_header") in cv_management.py (2 locations)
- [X] T122 Add "no_cvs" and "cv_list_header" keys to messages.json
- [X] T123 Fix typo "سيرات CV" → "سير ذاتية" in subscribe messages (3 occurrences)
- [X] T124 Fix FR-003: replace hardcoded locale="ar" with get_locale() from update object in errors.py
- [X] T125 Add state.clear() in error handler to prevent stuck FSM states in errors.py
- [X] T126 Remove dead if-else "subscribe_free" if tier=="free" else "subscribe_free" in subscription.py
- [X] T127 Replace fragile index-based lines manipulation with loop in subscription.py
- [X] T128 Replace hardcoded "jobpulse_bot" with bot username from settings in referral.py
- [X] T129 Add bot_username field to TelegramSettings in config/settings.py
- [X] T130 Fix FBT001: make bool params keyword-only in keyboards.py (settings_keyboard, cv_details_keyboard, job_card_keyboard)
- [X] T131 Update all call sites for keyword-only keyboard params (settings.py, cv_management.py)
- [X] T132 Write tests for lint fixes and locale key corrections
- [X] T133 Replace hardcoded "jobpulse_bot" with get_settings().telegram.bot_username in settings.py callback_share_referral
- [X] T134 Fix async mock for scan_iter in test_cleanup_expired_sessions test

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Uses existing CV service
- **User Story 2b (P1)**: Can start after Foundational - Uses existing CV service
- **User Story 3 (P1)**: Can start after Foundational - Uses SavedJobService (T008)
- **User Story 4 (P2)**: Can start after Foundational - Uses SavedJobService
- **User Story 5 (P2)**: Can start after Foundational - Uses existing preferences
- **User Story 6 (P2)**: Can start after Foundational - Integrates with US1
- **User Story 7 (P3)**: Can start after Foundational - Uses existing subscription data
- **User Story 8 (P3)**: Can start after Foundational - Uses BotSessionService

### Within Each User Story

- Models before services (Phase 2)
- Services before handlers
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all P1 user stories can start in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch registration handler work:
Task: "Create registration handler in src/bot/handlers/registration.py"
Task: "Implement language detection from Telegram user settings"
Task: "Implement 12-character referral code generation"
Task: "Implement main menu keyboard with 4 buttons"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Stories 2, 2b, 3 → Test independently → Deploy/Demo
4. Add User Stories 4, 5, 6 → Test independently → Deploy/Demo
5. Add User Stories 7, 8 → Test independently → Deploy/Demo

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Registration)
   - Developer B: User Story 2 (CV Upload) + 2b (CV Management)
   - Developer C: User Story 3 (Notifications)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
