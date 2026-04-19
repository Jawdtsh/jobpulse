# Data Model: AI Cover Letter Generation

**Feature**: 008-ai-cover-letter-gen  
**Date**: 2026-04-19  
**Source**: spec.md, research.md

## Entities

### CoverLetter (existing, needs enhancement)

**Purpose**: Stores generated cover letters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| user_id | UUID | Yes | FK to users |
| job_id | UUID | Yes | FK to jobs |
| cv_id | UUID | Yes | FK to user_cvs |
| content | TEXT | Yes | Full cover letter text |
| tone | VARCHAR(20) | Yes | formal/casual/professional |
| length | VARCHAR(10) | Yes | short/medium/long |
| focus_area | VARCHAR(20) | Yes | skills/experience/education/all |
| language | VARCHAR(20) | Yes | arabic/english/bilingual |
| ai_model | VARCHAR(50) | Yes | Which Gemini model used |
| generation_count | INT | Yes | Regeneration count (default 1) |
| generated_at | DATETIME | Yes | Timestamp |
| counted_in_quota | BOOLEAN | Yes | True for normal, false for admin |

**Relationships**:
- Many-to-One with User
- Many-to-One with Job
- Many-to-One with UserCV

---

### UserQuotaTracking (new)

**Purpose**: Tracks daily quota usage per user

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Primary key |
| user_id | UUID | Yes | FK to users (unique per day) |
| date | DATE | Yes | Damascus date |
| daily_used | INT | Yes | Count used today |
| purchased_extra | INT | Yes | Extra generations purchased |
| tier_at_generation | VARCHAR(20) | No | Tier when last generated |

**Unique constraint**: (user_id, date)

**Relationships**:
- Many-to-One with User

---

### SubscriptionTier (reference)

**Purpose**: Defines tier limits (not a DB table, configuration)

| Tier Name | Daily Limit |
|-----------|-------------|
| Free | 3 |
| Basic | 15 |
| Pro | 50 |

---

### PurchasePack (reference)

**Purpose**: Defines purchase options (not a DB table, configuration)

| Pack ID | Price | Generations |
|---------|-------|-------------|
| small | $0.50 | 5 |
| medium | $1.00 | 12 |
| large | $3.00 | 40 |

---

## State Transitions

### CoverLetter States

```
Created → Displayed → (Optional) Regenerated → Archived
```

- **Created**: After successful Gemini API generation
- **Displayed**: Shown to user in Telegram
- **Regenerated**: New CoverLetter created with incremented generation_count
- **Archived**: Soft-delete after 90 days (optional future)

---

### UserQuotaTracking States

```
No Record → Active Day → Reset at Midnight
```

- **No Record**: User never generated (no tracking row)
- **Active Day**: Daily counter > 0
- **Reset**: New row created for next day with daily_used=0

---

## Validation Rules

### CoverLetter Creation
- user_id: Required, must exist
- job_id: Required, must exist
- cv_id: Required, must exist
- content: Required, max 10000 chars
- tone: Must be in [formal, casual, professional]
- length: Must be in [short, medium, long]
- focus_area: Must be in [skills, experience, education, all]
- language: Must be in [arabic, english, bilingual]
- ai_model: Must reference valid model from config/ai_models.py
- generation_count: Default 1, max 10
- counted_in_quota: Boolean, default true

### Quota Validation
- Before generation: daily_used < daily_limit + purchased_extra
- Increment: daily_used += 1 only on success
- Reset: At midnight Damascus time, create new row or update date

---

## Database Changes Required

1. **Enhance cover_letter_logs table** (existing):
   - Add: cv_id, content, tone, length, focus_area, language, ai_model, generation_count, counted_in_quota

2. **Create user_quota_tracking table** (new):
   - Columns: id, user_id, date, daily_used, purchased_extra, tier_at_generation
   - Index on (user_id, date) for efficient lookups

### Indexes

| Index Name | Table | Type | Columns | Description |
|-----------|-------|------|---------|------------|
| idx_quota_user_date | user_quota_tracking | UNIQUE INDEX | (user_id, date) | Prevent duplicate daily entries |
| idx_quota_date | user_quota_tracking | BTREE INDEX | (date) | Query by date for reset tasks |
| idx_cover_letter_user | cover_letter_logs | BTREE INDEX | (user_id) | Users cover letters |
| idx_cover_letter_job | cover_letter_logs | BTREE INDEX | (job_id) | Jobs cover letters |

### Foreign Key Constraints

| Table | Column | References | On Delete | Description |
|-------|--------|-----------|-----------|-----------|
| cover_letter_logs | user_id | users.id | CASCADE | Remove logs when user deleted |
| cover_letter_logs | job_id | jobs.id | SET NULL | Null job reference if job deleted |
| cover_letter_logs | cv_id | user_cvs.id | CASCADE | Remove logs when CV deleted |
| user_quota_tracking | user_id | users.id | CASCADE | Remove tracking when user deleted |

### Migrations (Alembic)

| Migration | Name | Description |
|-----------|------|------------|
| 015 | Add cover_letter_logs fields | Add cv_id, content, tone, length, focus_area, language, ai_model, generation_count, counted_in_quota to cover_letter_logs |
| 016 | Create user_quota_tracking | Create user_quota_tracking table with unique index on (user_id, date) |

---

## Related Models

### User (existing)
```python
cover_letter_logs: List[CoverLetterLog]
```

### Job (existing)
```python
cover_letter_logs: List[CoverLetterLog]
```

### UserCV (existing, from SPEC-004)
```python
id: UUID
user_id: UUID
parsed_text: TEXT (encrypted)
completeness_score: FLOAT
skills: List[str]
```