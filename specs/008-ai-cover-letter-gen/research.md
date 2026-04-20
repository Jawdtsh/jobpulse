# Research: AI Cover Letter Generation

**Feature**: 008-ai-cover-letter-gen  
**Date**: 2026-04-19  
**Source**: spec.md, existing codebase

## Decisions

### Decision 1: Damascus Timezone Implementation

**Chosen**: Use Python `zoneinfo` with `ZoneInfo("Asia/Damascus")` for automatic DST handling.

**Rationale**: Python 3.9+ `zoneinfo` handles daylight saving time transitions automatically. Damascus observes DST (UTC+3 summer, UTC+2 winter). Using the timezone name directly ensures correct offset year-round.

**Alternatives considered**:
- Manual UTC offset calculation: Error-prone, requires tracking DST manually
- Fixed UTC+2: Incorrect during summer months
-第三方库 (pytz): Deprecated in favor of zoneinfo

---

### Decision 2: Gemini API Integration

**Chosen**: Use `google-generativeai` library with structured prompt engineering.

**Rationale**: Existing codebase already uses `google-generativeai` (see ai_provider_service.py). The library supports both flash and pro models. Will use config/ai_models.py for model names per Constitution.

**Alternatives considered**:
- OpenAI fallback: Not needed per spec (Gemini only)
- Direct REST API: More error-prone, less support

---

### Decision 3: Cover Letter Prompt Template Storage

**Chosen**: Store prompt template in `config/prompts/cover_letter_prompt.txt`.

**Rationale**: Constitution requires all configuration in config/ directory. Text file allows easy editing without code changes (FR-015).

**Alternatives considered**:
- Database storage: Overkill for configuration
- Hardcoded in service: Violates Constitution (no hardcoded config)

---

### Decision 4: Quota Reset Mechanism

**Chosen**: Use scheduled task (Celery/TaskIQ) that runs at midnight Damascus time to reset daily counters.

**Rationale**: Existing project uses TaskIQ (from migration spec). Scheduled task can trigger reset for all users at once. Alternative of checking/resetting per-request adds complexity.

**Alternatives considered**:
- Per-request reset check: Adds latency to every generation request
- Database-triggered reset: More complex to implement

---

### Decision 5: CV Data Handling

**Chosen**: Use existing encrypted CV data from SPEC-004, send to Gemini API for generation, do not store CV in cover_letters table.

**Rationale**: Constitution requires Fernet encryption for CV data at rest. Existing CV service already provides parsed text. Privacy clarified: store with user consent, process with awareness.

**Alternatives considered**:
- Store CV in cover_letter: Creates duplicate, increases risk
- Re-parse each time: Unnecessary overhead

---

## Research Tasks Completed

| Task | Status | Notes |
|------|--------|-------|
| Damascus timezone handling | DONE | Use zoneinfo.ZoneInfo("Asia/Damascus") |
| Gemini API patterns | DONE | Follow existing ai_provider_service.py pattern |
| Prompt template storage | DONE | config/prompts/cover_letter_prompt.txt |
| Quota reset mechanism | DONE | TaskIQ scheduled task at midnight |
| CV data flow | DONE | Reuse existing CV service with encryption |

---

## Key Dependencies

- `google-generativeai` - Already in use
- `zoneinfo` - Python standard library (3.9+)
- TaskIQ - Already in use for async tasks
- SQLAlchemy - Already in use with async support
- Redis - Already in use for caching

---

## Implementation Notes

1. Model selection by tier: Free/Basic → gemini-1.5-flash, Pro → gemini-1.5-pro (from config/ai_models.py)
2. Prompt template should include placeholders: {job_title}, {company}, {location}, {job_description}, {cv_content}, {user_name}, {tone}, {length}, {focus}, {language}
3. Quota tracking requires new table or extension of existing cover_letter_logs
4. Test with both UTC+2 and UTC+3 Damascus times to verify DST handling