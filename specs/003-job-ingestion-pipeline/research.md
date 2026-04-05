# Research: Job Ingestion Pipeline

## Decision: AI Provider Integration Pattern

**Context**: The pipeline needs to call multiple AI providers (Google Gemini, Groq, OpenRouter, Zhipu) with a fallback chain, unified retry logic, and daily limit tracking.

**Decision**: Use a single `AIProviderService` that wraps all providers behind a common async interface. The service accepts a model type (classifier/extractor/embedder), looks up the fallback chain from `config/ai_models.py`, and iterates through providers with exponential backoff. Each provider call uses the OpenAI-compatible API format where possible (Groq, OpenRouter, Zhipu all support OpenAI-compatible endpoints), with Google Gemini using the native `google-generativeai` SDK.

**Rationale**: 
- Groq, OpenRouter, and Zhipu all expose OpenAI-compatible REST endpoints, so a single `openai.AsyncOpenAI` client with different `base_url` and `api_key` values can handle all three
- Google Gemini requires its own SDK (`google-generativeai`) for optimal usage, but also supports OpenAI-compatible format via its v1beta endpoint
- Centralizing retry/backoff/daily-limit logic in one service eliminates duplication across classifier, extractor, and embedding services
- The `API_PROVIDERS` and `PROVIDER_BASE_URLS` dictionaries in `config/ai_models.py` already provide the mapping infrastructure

**Alternatives considered**:
- Separate service class per provider: Rejected — would duplicate retry/backoff logic across 4+ classes
- Direct SDK calls in each pipeline service: Rejected — violates DRY, makes fallback chain implementation complex
- Third-party library like LiteLLM: Rejected — adds heavy dependency, project already has `openai` and `google-generativeai` which cover all providers

---

## Decision: Celery Beat Scheduling Configuration

**Context**: The pipeline must run every 3 minutes automatically.

**Decision**: Use Celery Beat with a `crontab(minute='*/3')` schedule for the ingestion task. The Celery app is configured with Redis as both broker and result backend. The beat scheduler runs as a separate process alongside the worker.

**Rationale**:
- Celery Beat is already in the project dependencies (Celery 5.4.0)
- Redis is already available as the broker
- `crontab(minute='*/3')` is the standard pattern for 3-minute intervals
- Beat persists schedule state to prevent duplicate runs on restart

**Alternatives considered**:
- APScheduler: Rejected — Celery already in stack, no need for second scheduler
- System cron: Rejected — harder to manage in Docker, no retry integration
- Self-rescheduling task (task calls itself): Rejected — fragile on crash, harder to monitor

---

## Decision: Spam Rule Storage and Caching

**Context**: Spam keywords and scam indicators must be database-stored with caching for runtime updates (per clarification Q4).

**Decision**: Store spam rules in a `spam_rules` PostgreSQL table with columns: `id`, `pattern` (regex or keyword), `rule_type` (spam_keyword/scam_indicator), `is_active`, `created_at`, `updated_at`. Cache rules in Redis with a TTL of 5 minutes. The `JobFilterService` loads from Redis cache on first call per worker process, refreshing when TTL expires. A cache invalidation endpoint (or Redis pub/sub) allows immediate refresh when rules are updated.

**Rationale**:
- Redis is already available in the stack
- 5-minute TTL balances freshness with database load
- Table-based storage allows admin CRUD operations without code changes
- Pattern field supports both exact keyword matching and regex patterns

**Alternatives considered**:
- In-memory cache with periodic DB polling: Rejected — multi-worker environments would have stale caches
- Redis pub/sub for instant invalidation: Added as future enhancement — not critical for v1

---

## Decision: Telegram Session Rotation Strategy

**Context**: When a session is banned or rate-limited, the system must rotate to the next available session.

**Decision**: The `TelegramSessionRepository` provides a `get_next_active_session()` method that returns sessions ordered by `last_used_at` (least recently used first), filtered by `status = 'active'`. The ingestion service catches `FloodWaitError` and `SessionPasswordNeededError` from Telethon, marks the current session as `banned` or `rate_limited`, updates `last_used_at`, and retries with the next session. If all sessions are exhausted, the pipeline pauses and sends an admin alert.

**Rationale**:
- Least-recently-used rotation distributes load across sessions
- Telethon provides specific exception types for rate limiting vs. bans
- Session status tracking in `telegram_sessions` table (SPEC-001) already supports this pattern

**Alternatives considered**:
- Round-robin rotation: Rejected — doesn't account for varying session health
- Random selection: Rejected — could repeatedly select recently-used sessions that are about to be rate-limited

---

## Decision: Structured Data Extraction Schema

**Context**: The extraction service must return JSON with a specific schema: `{title, company, location, salary_min, salary_max, salary_currency, description, requirements: [], skills: []}`.

**Decision**: Use Pydantic v2 `BaseModel` to define a `JobExtractionResult` model with all fields as `Optional`. The Gemini Flash prompt includes the JSON schema in the system message and requests JSON-only output. The extraction service validates the AI response against the Pydantic model, catching validation errors for retry. Missing fields default to `None`. Salary fields are parsed as integers; currency defaults to `USD` if not specified.

**Rationale**:
- Pydantic v2 is already in the project dependencies
- Provides automatic validation, type coercion, and clear error messages
- `Optional` fields handle partial extractions gracefully
- Schema validation catches malformed AI responses before they reach the database

**Alternatives considered**:
- Manual dict validation: Rejected — error-prone, no type coercion
- dataclasses with manual validation: Rejected — Pydantic already available, more features

---

## Decision: Content Hash Normalization

**Context**: SHA-256 deduplication requires consistent text normalization to catch near-duplicates.

**Decision**: Normalize text before hashing by: (1) converting to lowercase, (2) stripping leading/trailing whitespace, (3) collapsing multiple whitespace/newlines into single spaces, (4) removing zero-width characters and common Unicode formatting marks. The normalized text is then hashed with `hashlib.sha256().hexdigest()`. This produces consistent hashes for semantically identical posts with minor formatting differences.

**Rationale**:
- Telegram posts often have inconsistent spacing, line breaks, and emoji
- Normalization catches duplicates that differ only in formatting
- Removing zero-width characters prevents hash evasion via invisible characters
- Simple and deterministic — no ML or fuzzy matching needed for v1

**Alternatives considered**:
- Fuzzy hash (ssdeep): Rejected — overkill for v1, adds dependency
- Semantic similarity via embeddings: Rejected — too expensive for deduplication, use only for matching
- Exact match only (no normalization): Rejected — would miss formatting-only duplicates

---

## Decision: Admin Alert Channel Configuration

**Context**: Critical pipeline failures must trigger alerts to a designated admin Telegram channel (per clarification Q5).

**Decision**: Add `admin_alert_channel_id` to `TelegramSettings` in `config/settings.py`. The alert is sent via a dedicated Telethon client (separate from scraping sessions) using the `SendMessage` API to the configured channel. Alerts are triggered for: all sessions banned, all AI providers exhausted for a batch, or unhandled pipeline crash. Alert messages include timestamp, error type, affected channel/message ID, and recommended action.

**Rationale**:
- Using a dedicated client prevents alert failures when scraping sessions are banned
- Channel ID configuration follows existing settings pattern
- Telethon is already available, no additional dependencies needed
- Structured alert messages enable quick diagnosis

**Alternatives considered**:
- Email alerts: Rejected — slower response time, not aligned with Telegram-first architecture
- Webhook to external monitoring: Rejected — adds complexity, Telegram channel is sufficient for v1
