# Data Model: Job Ingestion Pipeline

## New Entities

### SpamRule

Stores spam keywords and scam indicators for database-driven filtering.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| pattern | String(500) | NOT NULL | The keyword or regex pattern to match |
| rule_type | String(20) | NOT NULL, CHECK | Either `spam_keyword` or `scam_indicator` |
| is_active | Boolean | NOT NULL, default True | Whether the rule is currently enforced |
| created_at | DateTime | NOT NULL, auto | When the rule was created |
| updated_at | DateTime | NOT NULL, auto | When the rule was last modified |

**Validation Rules**:
- `pattern` must not be empty
- `rule_type` must be one of: `spam_keyword`, `scam_indicator`
- Unique constraint on `(pattern, rule_type)` to prevent duplicate rules

**Relationships**: None (standalone reference data)

## Existing Entities (referenced, not modified)

### Job (src/models/job.py)

Already defined in SPEC-001. Used by the pipeline for:
- `content_hash` lookup during deduplication (unique index exists)
- `embedding_vector` storage (Vector(768), HNSW index exists)
- `source_channel_id` FK to monitored_channels
- `telegram_message_id` for reference tracking

### MonitoredChannel (src/models/monitored_channel.py)

Already defined in SPEC-001. Used by the pipeline for:
- Fetching list of active channels to scrape
- Tracking `last_scraped_at` for incremental scraping
- Incrementing `jobs_found` and `false_positives` counters
- Marking `is_active = false` when channel becomes inaccessible

### TelegramSession (src/models/telegram_session.py)

Already defined in SPEC-001. Used by the pipeline for:
- Session rotation via `is_active`, `is_banned`, `last_used_at` fields
- Tracking session health and usage

## State Transitions

### Pipeline Message Lifecycle

```
Raw Message → Filtered → Classified (job) → Extracted → Deduplicated → Embedded → Stored
                  ↓            ↓               ↓              ↓
               (blocked)  (not a job)    (parse error)   (duplicate → skip)
```

### Channel Status Transition

```
Active → Inactive (when deleted/private/permission error)
```

No reverse transition in v1 (requires manual admin action).

### Session Status Transition

```
Active → Rate Limited (temporary, auto-recoverable after cooldown)
Active → Banned (permanent, requires manual review)
Banned → Active (manual admin reactivation)
```

## Database Migration Required

One new Alembic migration: `005_spam_rules_table.py`

- Creates `spam_rules` table with columns as defined above
- Adds CHECK constraint on `rule_type` (must be 'spam_keyword' or 'scam_indicator')
- Adds UNIQUE constraint on `(pattern, rule_type)`
- Seeds initial spam rules from Security_AntiSpam.md:
  * Approximately 20-30 spam_keyword patterns (e.g., "إعلان", "برعاية", "مسابقة")
  * Approximately 15-20 scam_indicator patterns (e.g., "رسوم تسجيل", "تحويل أموال", "دفع مقدم")
  * All seeded rules have is_active=True by default
- Includes downgrade function (DROP TABLE spam_rules CASCADE)

## Redis Cache Keys

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `spam_rules:all` | 300s | Cached list of all active spam rules (reloaded on expiry or manual flush) |
| `ai_daily_usage:{model}:{date}` | 86400s | Daily API call counter per model; {date} format YYYY-MM-DD in UTC; auto-expires at midnight UTC; incremented on each API call and checked before new calls to enforce daily limits |
| `pipeline:lock` | 180s | Distributed lock to prevent concurrent pipeline runs; TTL = 180s (60s buffer over expected 120s max execution time per batch); auto-expires if pipeline hangs to allow next cycle |
