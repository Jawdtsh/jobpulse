# Tasks: Job Ingestion Pipeline

**Input**: Design documents from `/specs/003-job-ingestion-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

### Prerequisites

Before starting, verify these reference documents exist and are current:

1. **Security_AntiSpam.md** — specifically §2 BLACKLIST_PATTERNS and §2.1 scam indicator patterns, needed for T001 seed data
2. **config/ai_models.py** — ACTIVE_MODELS, FALLBACK_CHAIN, and DAILY_LIMITS dicts, needed by T011 AIProviderService
3. **config/settings.py** — must include admin_alert_channel_id field (added in SPEC-002)

If Security_AntiSpam.md sections are empty or the file doesn't exist, fall back to minimal seed set:
- **spam_keywords**: ['إعلان', 'برعاية', 'مسابقة', 'تابعونا', 'اشترك', 'ربح', 'اكسب', 'دخل', 'تسويق', 'شبكي']
- **scam_indicators**: ['رسوم تسجيل', 'تحويل أموال', 'دفع مقدم', 'ادفع الآن', 'استثمر', 'ارباح يومية']

All seeded rules should have is_active=True.

**Tests**: The feature specification and constitution require unit tests for all service functions and integration tests for all repository functions (Constitution VIII). Tests are included below.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Project uses `src/` structure with `models/`, `repositories/`, `services/`, `utils/`
- Celery workers in `workers/` directory

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — database migration and Docker configuration

- [x] T001 Create Alembic migration 005 for spam_rules table in migrations/versions/005_spam_rules_table.py with CREATE TABLE, CHECK constraint on rule_type, UNIQUE constraint on (pattern, rule_type), seed data for initial spam keywords and scam indicators, and downgrade support. Seed data MUST be sourced directly from Security_AntiSpam.md §2 BLACKLIST_PATTERNS (spam keywords) and §2.1 (scam indicator phrases). If the reference document sections are empty or the file doesn't exist, fall back to a minimal seed set: spam_keywords=['إعلان', 'برعاية', 'مسابقة', 'تابعونا', 'اشترك', 'ربح', 'اكسب', 'دخل', 'تسويق', 'شبكي'], scam_indicators=['رسوم تسجيل', 'تحويل أموال', 'دفع مقدم', 'ادفع الآن', 'استثمر', 'ارباح يومية']. All marked is_active=True.
- [x] T002 [P] Update docker-compose.yml to add Celery worker service (workers.celery_app worker --pool=asyncio) and Celery Beat service (workers.celery_app beat) with Redis and PostgreSQL dependencies

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Create SpamRule model in src/models/spam_rule.py with fields: id (UUID PK), pattern (String 500), rule_type (String 20), is_active (Boolean default True), created_at, updated_at; add CHECK constraint on rule_type enum
- [x] T004 [P] Create custom exceptions in src/services/exceptions.py: AIServiceUnavailableError, DailyLimitReachedError, InvalidModelTypeError, InvalidEmbeddingDimensionsError, PipelineError, SessionExhaustedError, ChannelInaccessibleError
- [x] T005 [P] Create text normalizer utility in src/utils/text_normalizer.py with normalize_text() function: lowercase, strip whitespace, collapse multiple whitespace/newlines into single spaces, remove zero-width characters and Unicode formatting marks, remove all URLs (http:// and https:// links) before hashing to prevent same-job-different-URL deduplication failures
- [x] T006 [P] Create content hasher utility in src/utils/content_hasher.py with compute_content_hash() function: accepts raw text, calls normalize_text(), returns hashlib.sha256().hexdigest()
- [x] T007 Create SpamRuleRepository in src/repositories/spam_rule_repository.py extending AbstractRepository[SpamRule] with get_active_rules() method returning all rules where is_active=True
- [x] T008 Add get_next_active_session() method to existing src/repositories/telegram_session_repository.py returning sessions ordered by last_used_at ASC nulls_first, filtered by is_active AND NOT is_banned
- [x] T009 Add increment_jobs_found() and increment_false_positives() atomic update methods to existing src/repositories/channel_repository.py using DB-side increments
- [x] T010 Add admin_alert_channel_id field to TelegramSettings in config/settings.py with optional String type and whitespace stripping validation
- [x] T011 Create AIProviderService in src/services/ai_provider_service.py with call_model(), generate_embedding(), check_daily_limit(), increment_usage() methods; implements fallback chain iteration from config/ai_models.py, exponential backoff (1s/2s/4s, max 3 retries), 30s timeout, daily limit tracking via Redis keys ai_daily_usage:{model}:{date}, OpenAI-compatible client for Groq/OpenRouter/Zhipu, native google-generativeai SDK for Gemini
- [x] T012 Create unit tests for AIProviderService in tests/unit/test_ai_provider_service.py covering: fallback chain iteration, exponential backoff timing, daily limit enforcement, timeout handling, provider client creation
- [x] T013 Create unit tests for text normalizer in tests/unit/test_text_normalizer.py covering: lowercase conversion, whitespace collapsing, zero-width character removal, Unicode formatting removal, empty string handling
- [x] T014 Create unit tests for content hasher in tests/unit/test_content_hasher.py covering: deterministic output, normalization before hashing, identical inputs produce same hash, different inputs produce different hash
- [x] T015 Create integration tests for SpamRuleRepository in tests/integration/test_spam_rule_repository.py covering: CRUD operations, get_active_rules filtering, unique constraint enforcement, rule_type validation

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Scrape and Filter Incoming Messages (Priority: P1) 🎯 MVP

**Goal**: Fetch messages from monitored Telegram channels and filter out spam/irrelevant posts, delivering a clean stream of candidate posts for downstream processing

**Independent Test**: Can be fully tested by connecting to a monitored Telegram channel, fetching messages, and verifying that spam/short posts are filtered while valid-length posts pass through

### Tests for User Story 1

- [x] T016 [P] [US1] Create unit tests for JobFilterService in tests/unit/test_job_filter_service.py covering: spam keyword matching (case-insensitive), scam indicator matching, minimum length enforcement (50 chars), text-only extraction (media-only posts skipped), database-loaded rule caching. Tests MUST mock the Redis cache layer (key 'spam_rules:all', TTL 300s) to return known rule sets. Use monkeypatch or fixture to intercept Redis calls — do not rely on a running Redis instance for unit tests. Verify both cache-hit and cache-miss paths.
- [x] T017 [P] [US1] Create integration test for scrape-and-filter flow in tests/integration/test_job_ingestion_pipeline.py covering: end-to-end scrape → filter pipeline with mock Telethon client, session rotation on ban, channel deactivation on inaccessible

### Implementation for User Story 1

- [x] T018 [P] [US1] Create JobFilterService in src/services/job_filter_service.py with filter_message(text: str) -> bool method: loads spam rules from Redis cache (key spam_rules:all, TTL 300s), falls back to DB cache miss, checks text against spam_keyword patterns (case-insensitive substring match), checks against scam_indicator patterns, enforces minimum 50-character length, returns True if message passes all filters
- [x] T019 [US1] Create Telethon scraper helper in src/services/telegram_scraper_service.py with connect_session(session_string, api_id, api_hash), fetch_messages(channel_username, batch_size=100, after_message_id), extract_text(message) methods; handles FloodWaitError by marking session rate-limited, handles ChannelPrivateError/ChannelInvalidError by deactivating channel, extracts text content only (ignores media-only messages)
- [x] T020 [US1] Create JobIngestionService in src/services/job_ingestion_service.py with run_pipeline() method: orchestrates scrape stage (iterate active channels via ChannelRepository.get_active_channels(), fetch batches of 100 via scraper, track last_scraped_at), applies filter stage (JobFilterService.filter_message()), implements session rotation (catch Telethon errors, mark session via TelegramSessionRepository, retry with next from get_next_active_session()), handles channel deactivation (ChannelRepository.deactivate() on inaccessible errors), returns metrics dict (channels_processed, messages_scraped, messages_filtered)

⚠️ COMPLEXITY WARNING: This is the most complex task in the spec. Consider splitting into sub-tasks if implementation exceeds 2 hours: (1) scrape-only orchestration, (2) filter integration, (3) error handling and session rotation, (4) structured logging. Each sub-task should be independently testable before combining.
- [x] T021 [US1] Add validation and error handling to JobIngestionService.run_pipeline(): catch and log all Telethon exceptions, increment channel counters via ChannelRepository.update_stats(), send admin alert via TelegramScraperService when all sessions exhausted

⚠️ COMPLEXITY WARNING: This is the most complex task in the spec. Consider splitting into sub-tasks if implementation exceeds 2 hours: (1) scrape-only orchestration, (2) filter integration, (3) error handling and session rotation, (4) structured logging. Each sub-task should be independently testable before combining.
- [x] T022 [US1] Add structured logging for scrape/filter operations in src/services/job_ingestion_service.py with context (channel_id, channel_username, message_id, filter_reason)

**Checkpoint**: At this point, User Story 1 should be fully functional — pipeline can scrape channels and filter spam independently

---

## Phase 4: User Story 2 - Classify Posts as Job or Not Job (Priority: P2)

**Goal**: Use AI to determine whether a filtered post is a job posting, preventing waste of extraction/embedding resources on non-job content

**Independent Test**: Can be fully tested by passing pre-filtered posts through the classification service and verifying that job posts are classified as "yes" and non-job posts as "no"

### Tests for User Story 2

- [x] T023 [P] [US2] Create unit tests for JobClassifierService in tests/unit/test_job_classifier_service.py covering: binary response parsing (yes/no), fallback chain invocation on failure, daily limit pause behavior, invalid response retry, timeout handling

### Implementation for User Story 2

- [x] T024 [P] [US2] Create JobClassifierService in src/services/job_classifier_service.py with classify_post(text: str) -> bool method: constructs prompt "Is this a job posting? Answer only yes or no: {text}", calls AIProviderService.call_model(model_type="classifier", prompt=prompt, timeout=30), parses response as binary (yes → True, no → False), raises AIServiceUnavailableError on all-provider failure
- [x] T025 [US2] Integrate JobClassifierService into JobIngestionService.run_pipeline(): after filter stage, pass each filtered message through classify_post(), only proceed to extraction for True responses, track messages_classified count in metrics

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — pipeline scrapes, filters, and classifies posts

---

## Phase 5: User Story 3 - Extract Structured Job Data (Priority: P3)

**Goal**: Parse structured job information from classified job posts so that jobs have searchable metadata for matching

**Independent Test**: Can be fully tested by passing confirmed job postings through the extraction service and verifying that key fields (title, company, description, skills) are correctly parsed into structured data

### Tests for User Story 3

- [x] T026 [P] [US3] Create unit tests for JobExtractorService in tests/unit/test_job_extractor_service.py covering: full JSON extraction with all fields, partial extraction with missing fields (null defaults), invalid JSON response retry, non-English language handling, Pydantic validation error handling

### Implementation for User Story 3

- [x] T027 [P] [US3] Create JobExtractionResult Pydantic model in src/services/job_extractor_service.py with fields: title (Optional[str]), company (Optional[str]), location (Optional[str]), salary_min (Optional[int]), salary_max (Optional[int]), salary_currency (Optional[str], default "USD"), description (Optional[str]), requirements (Optional[list[str]]), skills (Optional[list[str]])
- [x] T028 [US3] Create JobExtractorService in src/services/job_extractor_service.py with extract_job_data(text: str) -> JobExtractionResult method: constructs system prompt with JSON schema definition, calls AIProviderService.call_model(model_type="extractor", prompt=text, system_prompt=system_prompt, response_format=json_schema, timeout=30), parses JSON response, validates against JobExtractionResult Pydantic model, retries on JSON parse error or validation error with exponential backoff, logs language detection warning for non-Arabic/English text
- [x] T029 [US3] Integrate JobExtractorService into JobIngestionService.run_pipeline(): after classification, call extract_job_data() for each classified job, handle partial extractions (null fields accepted), track jobs_extracted count in metrics

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work — pipeline scrapes, filters, classifies, and extracts structured data

---

## Phase 6: User Story 4 - Deduplicate and Store Jobs (Priority: P4)

**Goal**: Check for duplicate jobs using content hashing, generate vector embeddings, and store unique jobs for semantic matching

**Independent Test**: Can be fully tested by processing identical job posts and verifying that only the first is stored while duplicates are detected and skipped; embedding output validated for correct dimensionality

### Tests for User Story 4

- [x] T030 [P] [US4] Create unit tests for JobEmbeddingService in tests/unit/test_job_embedding_service.py covering: 768-dim vector generation, dimension validation (reject wrong size), retry on dimension mismatch, null return on all-provider failure
- [x] T031 [P] [US4] Create integration test for deduplication and storage in tests/integration/test_job_ingestion_pipeline.py covering: duplicate detection via content hash across channels, unique job insertion with all fields, embedding storage, channel counter increments

### Implementation for User Story 4

- [x] T032 [P] [US4] Create JobEmbeddingService in src/services/job_embedding_service.py with generate_embedding(text: str) -> list[float] | None method: calls AIProviderService.generate_embedding(text, expected_dimensions=768), validates returned vector length is exactly 768, retries up to 3 times on dimension mismatch, returns None if all attempts fail (caller proceeds without embedding)
- [x] T033 [US4] Add deduplication and storage to JobIngestionService.run_pipeline(): compute content hash via content_hasher.compute_content_hash(raw_text), check against existing jobs via JobRepository.get_by_content_hash(), skip insert and increment false_positives on match, create job via JobRepository.create() with all extracted fields, generate embedding via JobEmbeddingService, store embedding via JobRepository.update_embedding(), increment jobs_found counter via ChannelRepository.update_stats()
- [x] T034 [US4] Create Celery Beat task in workers/tasks/ingestion_tasks.py: define run_ingestion_pipeline task with name="ingestion.run_pipeline", bind=True, acks_late=True, reject_on_worker_lost=True, configure beat_schedule with crontab(minute="*/3"), implement Redis distributed lock (pipeline:lock, 180s TTL) to prevent concurrent runs, return metrics dict with status/channels_processed/messages_scraped/messages_filtered/messages_classified/jobs_extracted/jobs_deduplicated/jobs_stored/errors/duration_seconds
- [x] T035 [US4] Create Celery app configuration in workers/celery_app.py: initialize Celery with Redis broker and result backend from settings, configure async pool, configure beat schedule, set task serializer, result serializer, timezone
- [x] T036 [US4] Add admin alert service in src/services/admin_alert_service.py with send_alert(error_type: str, details: dict) method: creates dedicated Telethon client, sends formatted alert message to admin_alert_channel_id from settings, includes timestamp, error type, affected channel/message ID, recommended action
- [x] T037 [US4] Integrate admin alerts into JobIngestionService.run_pipeline(): send alert when all sessions banned, send alert when all AI providers exhausted for a batch, send alert on unhandled pipeline crash

**Checkpoint**: All user stories should now be independently functional — complete 7-stage pipeline with scheduling and alerting

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T038 [P] Update src/services/__init__.py to export all new services (JobIngestionService, JobFilterService, JobClassifierService, JobExtractorService, JobEmbeddingService, AIProviderService, AdminAlertService)
- [x] T039 [P] Update src/repositories/__init__.py to export SpamRuleRepository
- [x] T040 [P] Update workers/__init__.py to export Celery app
- [x] T041 Run full integration test suite and verify 80% coverage minimum on new service files
- [x] T042 Run quickstart.md validation: execute migration, start Celery worker + beat, verify pipeline runs and stores jobs
- [x] T043 Code cleanup: verify all files under 200 lines, all functions under 20 lines, all functions have type hints, no magic numbers, no hardcoded secrets
- [x] T044 Fix test quality: patch _spam_rule_repo.get_active_rules as AsyncMock in pipeline integration test, ensure async methods use async mocks
- [x] T045 Fix test quality: strengthen pipeline assertions to exact counts (channels_processed == 1, messages_scraped >= 1), remove unused fixtures and imports
- [x] T046 Fix test quality: spam_rule_repository duplicate test — exactly one statement inside pytest.raises (await repo.create)
- [x] T047 Fix test quality: text_normalizer — replace duplicate test_none_like_empty with distinct test_whitespace_only_string
- [x] T048 Fix test quality: ai_provider_service — assert call_count == 9 for full fallback chain failure, call_count == 1 for regex skip
- [x] T049 Fix test quality: job_filter_service — add mock_redis.setex.assert_awaited_once() to cache miss test
- [x] T050 Add migration 006 for monitored_channels.last_message_id column (BigInteger, nullable)
- [x] T051 Rewrite corrupted job_embedding_service.py — remove redundant dimension check, use logger.exception()
- [x] T052 Rewrite corrupted job_extractor_service.py — fix imports, add _parse_response method, narrow exception catch
- [x] T053 Fix spec doc: spec.md FR-020 — settings.monitoring.admin_telegram_chat_id → settings.telegram.admin_alert_channel_id
- [x] T054 Fix spec doc: quickstart.md — get_session → get_async_session
- [x] T055 Fix spec doc: data-model.md — add text language specifiers to fenced code blocks
- [x] T056 Fix spec doc: contracts/ingestion-task.md — add blank line before fenced code block, fix duplicate line
- [x] T057 Fix spec doc: research.md — clean up bot token auth description (remove empty StringSession references)
- [x] T058 Fix job_filter_service.py: move module-level _redis/_ensure_redis/_get_redis to instance attributes, add _rules_cache and _settings to __init__, remove _load_rules_from_db() and inline into _get_rules(), remove redis.close() calls, fix test_cache_hit_path message, update integration test mocking
- [x] T059 Fix admin_alert_service.py: replace StringSession() with file-based session "admin_alert_session" for bot auth, remove telethon.sessions.StringSession import, update logger.exception to use exc_info=e, update tests to verify TelegramClient constructor args
- [x] T060 Fix ai_provider_service.py: convert module-level _handle_provider_error() to instance method _log_provider_error(), remove redis.close() from tests, ensure no connection thrashing
- [x] T061 Fix test quality: strengthen test_ai_provider_service.py — verify regex_only not in attempted models for both fallback-chain tests, verify exact call_count; verify test_spam_rule_repository.py pytest.raises single statement; verify test_job_ingestion_pipeline.py concrete assertions (channels_processed == 1, messages_scraped >= 1)
- [x] T062 Fix test_text_normalizer.py: replace duplicate test_whitespace_only_string with test_normalize_none_returns_empty_string (asserts normalize_text(None) == ""), add test_normalize_order_is_stable verifying whitespace collapse and case normalization
- [x] T063 Fix job_ingestion_service.py: add await to self._filter.filter_message() call in _filter_messages(), make _filter_messages async, update caller _process_channel to await _filter_messages(); remove redundant import of get_settings inside _get_active_session() (already imported at module level); update integration test to assert filtered < scraped counts; add TQ-007 to spec.md
- [x] T064 Fix ai_provider_service.py fallback chain: change _try_fallback_chain to continue to next model on daily limit instead of raising DailyLimitReachedError; change generate_embedding to continue to next model on daily limit instead of returning None immediately; update test_raises_when_limit_reached → test_raises_unavailable_when_all_limits_reached (asserts AIServiceUnavailableError); add test_falls_through_to_next_on_daily_limit; update test_skips_regex_only_in_chain to use patched chain ["regex_only", "glm-4.7-flash"] and verify only real provider attempted; update spec.md FR-010, FR-013, add TQ-008
- [x] T065 Fix job_ingestion_service.py error handling: (A) FloodWaitError now handled by _handle_flood_wait (temporary, no mark_banned) instead of _handle_session_ban; (B) _extract_jobs now re-raises DailyLimitReachedError instead of swallowing in catch-all Exception handler; (C) _process_channel refactored under 20 lines by extracting _scrape_channel + _handle_scrape_exception; update spec.md FR-009, edge cases, add TQ-009
- [x] T066 Rewrite migration 005_spam_rules_table.py: expand seed data from 10→25 spam_keywords and 6→18 scam_indicators (per data-model.md ~20-30 keywords, ~15-20 indicators); replace op.execute/UNNEST with op.bulk_insert per spec requirement; fix downgrade to use CASCADE (DROP TABLE spam_rules CASCADE)
- [x] T067 Add Redis distributed lock to run_pipeline(): acquire SET pipeline:lock NX EX 180 before pipeline execution, return early with status="skipped" if lock already held, release lock in finally block via DEL pipeline:lock; add _get_redis() instance method following job_filter_service.py pattern; update integration test to mock Redis lock (svc._redis.set.return_value=True, assert delete awaited)
- [x] T068 Verify workers/celery_app.py and workers/tasks/ingestion_tasks.py exist; remove duplicate Redis lock from ingestion_tasks.py (lock now handled inside run_pipeline() per T067); keep task as thin orchestrator that wires dependencies and delegates to JobIngestionService.run_pipeline()
- [x] T069 Fix test quality issues: (1) remove unused channel_repo fixture from test_job_ingestion_pipeline.py; (2) add test_invalid_rule_type_rejected to TestRuleTypeValidation in test_spam_rule_repository.py (asserts IntegrityError on invalid rule_type); (3) change messages_scraped >= 1 to == 2 (exact count per TQ-002); (4) test_skips_regex_only_in_chain already uses patched chain ["regex_only", "glm-4.7-flash"] and verifies only real provider attempted (T064)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 infrastructure (JobIngestionService orchestration) — integrates into run_pipeline() after filter stage
- **User Story 3 (P3)**: Depends on US2 (classification must pass before extraction) — integrates into run_pipeline() after classify stage
- **User Story 4 (P4)**: Depends on US3 (extraction must complete before storage) — integrates into run_pipeline() as final stages

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/utilities before services
- Services before orchestration integration
- Core implementation before cross-cutting concerns
- Story complete before moving to next priority

### Parallel Opportunities

- T001 (migration) and T002 (docker-compose) can run in parallel
- T003 through T010 (all foundational model/util/exception/repo tasks) can run in parallel — different files, no interdependencies
- T011 (AIProviderService) depends on T004 (exceptions) — cannot parallelize with T004
- T012, T013, T014, T015 (all foundational tests) can run in parallel after their implementations exist
- T016, T017 (US1 tests) can run in parallel
- T018 (JobFilterService) and T019 (TelegramScraperService) can run in parallel — different files
- T023 (US2 tests) can run in parallel with T024 (US2 implementation) if TDD approach
- T026 (US3 tests) can run in parallel with T027, T028 (US3 implementation) if TDD approach
- T030, T031 (US4 tests) can run in parallel
- T032 (JobEmbeddingService) and T034 (Celery task) can run in parallel — different files
- T038, T039, T040 (init exports) can all run in parallel

---

## Parallel Example: Foundational Phase

```bash
# Launch all independent foundational tasks together:
Task: "Create SpamRule model in src/models/spam_rule.py"
Task: "Create custom exceptions in src/services/exceptions.py"
Task: "Create text normalizer in src/utils/text_normalizer.py"
Task: "Create content hasher in src/utils/content_hasher.py"
Task: "Add admin_alert_channel_id to config/settings.py"

# After those complete, launch in parallel:
Task: "Create SpamRuleRepository in src/repositories/spam_rule_repository.py"
Task: "Create AIProviderService in src/services/ai_provider_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration + docker-compose)
2. Complete Phase 2: Foundational (all 13 tasks — CRITICAL, blocks all stories)
3. Complete Phase 3: User Story 1 (scrape + filter)
4. **STOP and VALIDATE**: Test pipeline scrapes channels and filters spam
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Scrape and filter working → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Classification working → Test independently → Deploy/Demo
4. Add User Story 3 → Extraction working → Test independently → Deploy/Demo
5. Add User Story 4 → Deduplication, embedding, storage, scheduling working → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (scrape/filter)
   - Developer B: Can begin US2 classification in parallel (uses AIProviderService foundation)
   - Developer C: Can begin US4 embedding service in parallel (uses AIProviderService foundation)
3. US3 and US4 integrate sequentially into the pipeline after US1/US2 complete
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution III requires max 20 lines per function, max 200 lines per file — enforce during T043
- Constitution V requires all AI model names from config/ai_models.py only — no hardcoded model names in service code
- Constitution X requires async/await throughout — no blocking operations in async functions
