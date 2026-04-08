# Feature Specification: Job Ingestion Pipeline

**Feature Branch**: `003-job-ingestion-pipeline`  
**Created**: 2026-04-05  
**Status**: Draft  
**Input**: User description: "Core feature of JobPulse AI - a 7-stage job ingestion pipeline that scrapes job postings from Telegram channels, classifies them using AI, extracts structured data, deduplicates, generates embeddings, and stores them for semantic matching"

## Clarifications

### Session 2026-04-05

- Q: Should the pipeline handle only text messages, or also process messages containing attachments? → A: Text only - extract text from posts regardless of attached media; ignore posts with media but no text
- Q: Should the pipeline run on a fixed schedule, or be triggered manually/on-demand? → A: Fixed schedule every 3 minutes automatically
- Q: Should duplicate detection be global (across all channels) or per-channel only? → A: Global - detect duplicates across all monitored channels
- Q: Should spam keywords be hardcoded in the application, or stored in the database for runtime updates? → A: Database-stored with caching - updateable at runtime
- Q: Should the system alert administrators when pipeline failures occur, and through what channel? → A: Telegram notification - send alerts to a designated admin Telegram channel on critical failures

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Scrape and Filter Incoming Messages (Priority: P1)

As the system, I need to fetch new messages from monitored Telegram channels and filter out spam and irrelevant posts so that only potentially valid job content proceeds to AI processing.

**Why this priority**: This is the entry point of the entire pipeline. Without scraping and filtering, no jobs can be discovered. It is independently testable by running the scraper against known channels and verifying filtered output.

**Independent Test**: Can be fully tested by connecting to a monitored Telegram channel, fetching messages, and verifying that spam/short posts are filtered while valid-length posts pass through. Delivers a clean stream of candidate posts.

**Acceptance Scenarios**:

1. **Given** the system has active Telegram sessions and monitored channels configured, **When** the pipeline runs, **Then** messages are fetched in batches of 100 per channel starting from the last tracked message ID
2. **Given** a fetched message contains text (with or without attached media), **When** the scraper evaluates it, **Then** only the text content is extracted for processing
3. **Given** a fetched message contains only media with no text, **When** the scraper evaluates it, **Then** the message is ignored and skipped
4. **Given** a fetched message contains spam keywords or scam indicators loaded from the database, **When** the filter evaluates it, **Then** the message is blocked and does not proceed to classification
3. **Given** a fetched message is shorter than 50 characters, **When** the filter evaluates it, **Then** the message is skipped as irrelevant
4. **Given** the current Telegram session is banned or rate-limited, **When** a scrape attempt fails, **Then** the system rotates to the next available session and retries
5. **Given** a channel has been deleted or made private, **When** the system attempts to fetch messages, **Then** the channel is marked inactive and processing continues with other channels

---

### User Story 2 - Classify Posts as Job or Not Job (Priority: P2)

As the system, I need to use AI to determine whether a filtered post is actually a job posting so that only job-related content proceeds to data extraction.

**Why this priority**: Classification prevents wasting expensive extraction and embedding resources on non-job content. It is independently testable by feeding known job and non-job posts and verifying binary classification accuracy.

**Independent Test**: Can be fully tested by passing pre-filtered posts through the classification service and verifying that job posts are classified as "yes" and non-job posts as "no". Delivers a refined set of confirmed job postings.

**Acceptance Scenarios**:

1. **Given** a filtered post passes the spam/length filter, **When** the classification service sends it to the AI model, **Then** the response is parsed as binary (yes/no) and only "yes" responses proceed
2. **Given** the primary AI provider is unavailable, **When** classification fails, **Then** the system retries with exponential backoff (1s, 2s, 4s) up to 3 times, then falls back to the next provider in the chain
3. **Given** all AI providers in the fallback chain fail, **When** classification cannot be completed, **Then** the post is logged as an error and skipped without crashing the pipeline
4. **Given** the daily API limit for the classification model is reached, **When** a classification request is made, **Then** the pipeline pauses and resumes when the limit resets

---

### User Story 3 - Extract Structured Job Data (Priority: P3)

As the system, I need to parse structured job information (title, company, location, salary, skills, etc.) from classified job posts so that jobs have searchable metadata for matching.

**Why this priority**: Structured extraction enables meaningful job search and matching. It is independently testable by feeding classified job posts and verifying the extracted JSON fields match expected values.

**Independent Test**: Can be fully tested by passing confirmed job postings through the extraction service and verifying that key fields (title, company, description, skills) are correctly parsed into structured data. Delivers enriched job records ready for storage.

**Acceptance Scenarios**:

1. **Given** a post is classified as a job, **When** the extraction service processes it, **Then** structured data is returned with fields: title, company, location, salary range, description, requirements, and skills
2. **Given** some fields cannot be extracted from the post text, **When** extraction completes, **Then** missing fields are set to null and the job record is still valid
3. **Given** the AI response is invalid JSON, **When** parsing fails, **Then** the system retries with exponential backoff and fallback providers
4. **Given** the post is in a language other than Arabic or English, **When** extraction runs, **Then** available fields are extracted and a language detection warning is logged

---

### User Story 4 - Deduplicate and Store Jobs (Priority: P4)

As the system, I need to check for duplicate jobs using content hashing and store unique jobs with vector embeddings so that semantic matching works without duplicate alerts.

**Why this priority**: Deduplication prevents redundant job alerts and storage waste. Embedding generation enables the core semantic matching feature. Independently testable by inserting duplicate posts and verifying only unique ones are stored.

**Independent Test**: Can be fully tested by processing identical job posts and verifying that only the first is stored while duplicates are detected and skipped. Embedding output can be validated for correct dimensionality. Delivers a clean, searchable job database.

**Acceptance Scenarios**:

1. **Given** a job's content hash matches an existing record in any monitored channel, **When** deduplication runs, **Then** the job is skipped and the source channel's false_positives counter is incremented
2. **Given** a job is unique, **When** the storage service saves it, **Then** all extracted fields are stored along with the source channel ID and Telegram message ID
3. **Given** a job is stored, **When** the embedding service generates a vector, **Then** a 768-dimensional vector is computed and stored with the job record
4. **Given** the embedding API returns a vector of incorrect dimensions, **When** validation fails, **Then** the system retries and stores null if all attempts fail (the job is still saved)
5. **Given** a job is successfully stored, **When** the operation completes, **Then** the source channel's jobs_found counter is incremented

---

### Edge Cases

- **Telegram session rate-limited (FloodWaitError)**: System logs the temporary wait period, does NOT mark session as permanently banned, and continues processing other channels with the next available session
- **Telegram session banned**: System rotates to next available session from the session pool; if all sessions are banned, pipeline pauses and sends an alert to the designated admin Telegram channel
- **Post in unsupported language**: System extracts what is possible from the text and logs a language detection warning; the job is still stored with partial data
- **Embedding returns wrong dimensions**: Vector length is validated (must be 768); if wrong, the system retries; if all retries fail, the job is saved with a null embedding
- **Multi-part job posts split across messages**: Out of scope for v1 - each message is treated independently as a separate candidate
- **Channel deleted or made private**: Channel is marked inactive in the database, error is logged, and processing continues with remaining active channels
- **AI API rate limit reached**: Pipeline respects daily limits; when a limit is hit, processing pauses for that model and resumes when the daily window resets
- **Network timeout during AI call**: 30-second timeout enforced; exponential backoff (1s, 2s, 4s) with max 3 retries before falling back to next provider

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to Telegram using configured user-bot credentials and fetch messages from all active monitored channels
- **FR-001a**: System MUST extract text content from messages regardless of attached media (photos, videos, documents); messages containing ONLY media with NO text content MUST be ignored and skipped from processing
- **FR-002**: System MUST retrieve messages in batches of 100 per channel, tracking the last processed message ID per channel via `monitored_channels.last_message_id` column
- **FR-003**: System MUST filter out posts containing spam keywords or scam indicators loaded from spam_rules table; spam rules MUST be cached in Redis with 300-second TTL and automatically reloaded on cache expiry; posts shorter than 50 characters MUST be skipped regardless of content
- **FR-004**: System MUST classify filtered posts as "job" or "not job" using AI with a binary yes/no response
- **FR-005**: System MUST extract structured data (title, company, location, salary range, description, requirements, skills) from classified job posts in JSON format
- **FR-006**: System MUST compute SHA-256 content hash from normalized post text (normalization steps: convert to lowercase, strip leading/trailing whitespace, collapse multiple consecutive spaces to single space, remove all URLs, remove all emojis and special characters) and check hash against jobs.content_hash column across all channels to prevent global duplicates
- **FR-007**: System MUST generate a 768-dimensional vector embedding for each unique job post for semantic matching
- **FR-008**: System MUST store unique jobs with all extracted fields, content hash, embedding vector, source channel reference, and Telegram message ID
- **FR-009**: System MUST handle FloodWaitError as a temporary rate limit (log wait period, continue with next session, do NOT mark session as banned) and rotate to a new session when the current session is permanently banned
- **FR-010**: System MUST implement a fallback chain for AI failures, trying providers in order until one succeeds or all are exhausted; when a model's daily limit is reached, the chain MUST continue to the next model rather than aborting immediately
- **FR-011**: System MUST enforce exponential backoff (1s, 2s, 4s) with a maximum of 3 retries for failed AI requests
- **FR-012**: System MUST enforce 30-second timeouts on all AI classification, extraction, and embedding requests
- **FR-013**: System MUST respect daily API usage limits for each AI model; when a model's limit is reached the system MUST attempt the next model in the fallback chain; processing pauses only when ALL models in the chain have exhausted their limits
- **FR-014**: System MUST increment channel-level counters (jobs_found, false_positives) based on pipeline outcomes
- **FR-015**: System MUST mark channels as inactive when they become inaccessible (deleted, private, or permission errors)
- **FR-016**: System MUST log all AI responses and pipeline errors for debugging and monitoring
- **FR-017**: System MUST process messages in parallel batches using asyncio.gather with maximum 5 concurrent AI API calls PER PIPELINE STAGE (5 concurrent classifications, 5 concurrent extractions, 5 concurrent embeddings) to balance throughput with API provider rate limits
- **FR-018**: System MUST handle partial extractions gracefully, storing null for any fields that cannot be parsed from the post text
- **FR-019**: System MUST execute the ingestion pipeline automatically on a fixed 3-minute interval via the Celery task scheduler
- **FR-020**: System MUST send alerts to admin Telegram channel (chat ID loaded from settings.telegram.admin_alert_channel_id (from TelegramSettings in config/settings.py)) when critical pipeline failures occur; alert message format: "🚨 [SEVERITY] Pipeline Alert\n\n{error_details}\n\nTimestamp: {iso_timestamp}"; CRITICAL severity triggers: all Telegram sessions banned, all AI providers exhausted after fallback chain, or pipeline worker crash; individual job extraction failures MUST be logged only without alert
- **FR-021**: System MUST acquire a Redis distributed lock (key=`pipeline:lock`, TTL=180s) before starting pipeline execution using SET NX EX; if the lock is already held, the pipeline MUST skip the current cycle and return early with status "skipped"; the lock MUST be released in a finally block after pipeline completion to prevent concurrent pipeline runs and duplicate job inserts

### Key Entities

- **Job Posting**: A structured record representing a job opportunity with fields for title, company, location, salary range, description, requirements, skills, content hash, embedding vector, source channel reference, and Telegram message ID
- **Monitored Channel**: A Telegram channel being watched for job postings, with metadata including channel identifier, active status, last scraped message ID, jobs found count, and false positives count
- **Telegram Session**: A user-bot session credential used to access Telegram, with status tracking (active, banned, rate-limited) for session rotation
- **Pipeline Run**: An execution instance of the ingestion pipeline that processes a batch of messages and produces metrics (jobs scraped, filtered, classified, extracted, deduplicated, stored)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The pipeline processes at least 500 unique job postings per day from monitored channels under normal operating conditions
- **SC-002**: Duplicate job postings are detected and prevented with 99% accuracy (no more than 1% of stored jobs are duplicates)
- **SC-003**: Job classification precision is at least 85% as measured by manual review of 100 randomly sampled posts classified as "job" per week (85% of sampled posts are confirmed as actual job postings by human reviewer)
- **SC-004**: The pipeline completes a full scrape-classify-extract-store cycle for a batch of 100 messages within 10 minutes
- **SC-005**: AI provider fallback succeeds in at least 95% of cases when the primary provider fails (pipeline continues without manual intervention)
- **SC-006**: System handles Telegram session rotation automatically within 30 seconds of detecting a banned session
- **SC-007**: At least 85% of stored jobs have valid 768-dimensional embeddings (embedding failures do not prevent job storage)
- **SC-008**: Structured data extraction populates at least 3 core fields (title, description, company) for 80% of processed jobs

## Assumptions

- Telegram channels being monitored are public or the system has been granted access credentials for private channels
- AI model API keys are properly configured and have sufficient quota for expected daily volume
- The database schema (SPEC-001) is already implemented with the jobs table, monitored_channels table, and telegram_sessions table
- Settings and configuration layer (SPEC-002) is in place with AI model names, fallback chain, and daily limits defined
- Posts are primarily in Arabic and English; other languages may have reduced extraction quality
- Each Telegram message is treated as an independent unit; multi-message job posts are not reconstructed in v1
- The Celery task queue infrastructure is available for background job processing
- Vector similarity search (HNSW index) is configured at the database level per SPEC-001
- Redis is available and configured as Celery message broker (per settings.redis_url from SPEC-002)
- Celery Beat scheduler is running and configured for 3-minute periodic task execution
- Server has sufficient resources (minimum 2 CPU cores, 4GB RAM) to handle 5 concurrent async AI API calls per pipeline stage

## Test Quality Standards

- **TQ-001**: All async methods MUST be tested with async mocks (e.g., `new_callable=AsyncMock`); never use sync mocks for async functions
- **TQ-002**: Integration tests MUST seed exact data and assert exact counts (e.g., `metrics["channels_processed"] == 1` when one channel is seeded)
- **TQ-003**: `pytest.raises()` blocks MUST contain exactly one statement — the call expected to raise
- **TQ-004**: Duplicate test cases MUST be replaced with distinct edge-case scenarios (no two tests assert the same behavior)
- **TQ-005**: Cache miss tests MUST assert both the DB fallback call and the cache write (e.g., `setex.assert_awaited_once()`)
- **TQ-006**: Fallback chain tests MUST assert the exact number of provider attempts (e.g., `call_count == 9` for 3 models × 3 retries)
- **TQ-007**: All async service calls in orchestration code MUST use `await`; unawaited coroutines are always truthy and silently bypass filtering/classification logic (Constitution Principle X — Async Best Practices)
- **TQ-008**: Fallback chain daily-limit tests MUST verify the chain continues to the next model when a model's limit is reached; tests MUST NOT assert DailyLimitReachedError on the first model in the chain (Constitution Principle II — Open/Closed; Constitution Principle IX — Error Handling)
- **TQ-009**: FloodWaitError MUST be handled as a temporary condition (no mark_banned); DailyLimitReachedError MUST propagate immediately from extraction/classification loops, not be swallowed by catch-all Exception handlers (Constitution Principle IX — Error Handling)
