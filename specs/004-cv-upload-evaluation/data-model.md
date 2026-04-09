# Data Model: CV Upload & Evaluation

**Feature**: SPEC-004 - CV Upload & Evaluation  
**Date**: 2026-04-08

## Entities

### UserCV (Extended)

Represents a user's uploaded CV with evaluation data.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, not null | Unique identifier |
| user_id | UUID | FK→users.id, not null | Owner user |
| title | String(255) | not null | CV display name |
| content | BYTEA | not null | Encrypted CV text |
| embedding_vector | Vector(768) | nullable | 768-dim semantic embedding |
| is_active | Boolean | default=true | Active for matching |
| skills | JSON | nullable | Extracted skills list |
| experience_summary | Text | nullable | AI-generated summary |
| completeness_score | Numeric(5,2) | nullable | 0-100 percentage |
| improvement_suggestions | JSON | nullable | List of suggestions |
| evaluated_at | Timestamp | nullable | Last evaluation time |
| created_at | Timestamp | not null | Upload timestamp |
| updated_at | Timestamp | not null | Last modification |

**Relationships**:
- User (1:N) - One user can have multiple CVs

**State Transitions**:
### CV Lifecycle States
┌──────────────────────────────────────────────────────────────────┐
│                     CV State Machine                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [New Upload]                                                     │
│       │                                                           │
│       ▼                                                           │
│   ┌─────────┐                                                     │
│   │ PENDING │ (CV uploaded, text extracted, awaiting evaluation) │
│   └─────────┘                                                     │
│       │                                                           │
│       │ (AI evaluation complete)                                 │
│       ▼                                                           │
│   ┌────────┐                                                      │
│   │ ACTIVE │ (is_active=true, used in job matching)              │
│   └────────┘                                                      │
│       │                                                           │
│       ├─────────┐ (user deactivates OR new CV becomes active)    │
│       │         ▼                                                 │
│       │    ┌──────────┐                                           │
│       │    │ INACTIVE │ (is_active=false, excluded from matching)│
│       │    └──────────┘                                           │
│       │         │                                                 │
│       │         │ (user reactivates)                              │
│       │         └──────────┐                                      │
│       │                    ▼                                      │
│       │              [returns to ACTIVE]                          │
│       │                                                           │
│       │ (user deletes)                                            │
│       ▼                                                           │
│   ┌─────────┐                                                     │
│   │ DELETED │ (soft delete, data retained, never shown to user)  │
│   └─────────┘                                                     │
│       │                                                           │
│       ▼                                                           │
│   [End State] (data persisted for audit/legal compliance)        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

### Transition Rules

| From State | To State | Trigger | Database Change |
|-----------|----------|---------|-----------------|
| - | PENDING | User uploads CV file | `INSERT INTO user_cvs (is_active=false, evaluated_at=null)` |
| PENDING | ACTIVE | First AI evaluation completes | `UPDATE user_cvs SET is_active=true, evaluated_at=NOW(), completeness_score=X` |
| ACTIVE | INACTIVE | User deactivates manually | `UPDATE user_cvs SET is_active=false` |
| ACTIVE | INACTIVE | New CV uploaded (auto-deactivate old) | `UPDATE user_cvs SET is_active=false WHERE user_id=X AND id != new_cv_id` |
| INACTIVE | ACTIVE | User reactivates via /activatecv | `UPDATE user_cvs SET is_active=true; UPDATE user_cvs SET is_active=false WHERE user_id=X AND id != reactivated_id` |
| ACTIVE | DELETED | User deletes via /deletecv | `UPDATE user_cvs SET is_active=false, deleted_at=NOW()` (soft delete) |
| INACTIVE | DELETED | User deletes via /deletecv | `UPDATE user_cvs SET deleted_at=NOW()` (soft delete) |

### Business Rules

1. **Only ONE active CV per user at any time** (enforced by application logic before UPDATE)
2. **PENDING state exists only between upload and first evaluation** (typically <30 seconds)
3. **DELETED CVs are never physically removed** (GDPR compliance requires audit trail)
4. **Pro users with 2 CVs**: Each CV has independent state, only one can be ACTIVE at a time (user must explicitly switch)

### State Checks in Code

```python
# Example: Check if CV can be activated
def can_activate_cv(cv: UserCV, user: User) -> bool:
    if cv.deleted_at is not None:
        raise CVDeletedError("Cannot activate deleted CV")
    
    active_count = count_active_cvs(user.id)
    if active_count >= user.subscription_tier.max_active_cvs:
        raise CVLimitExceededError(f"Max {user.subscription_tier.max_active_cvs} active CV allowed")
    
    return True
```
### CV Evaluation Quota (Redis)

Monthly evaluation quota per user.

| Key Pattern | Value Type | Description |
|-------------|------------|-------------|
| cv_eval_quota:{user_id}:{year}-{month} | Integer | Current month usage |

**TTL**: End of month (calculate days remaining)
# First day of next month - current timestamp
next_month = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1)
ttl_seconds = int((next_month - datetime.now()).total_seconds())

## Validation Rules

### CV Upload
- File size: ≤ 5MB
- File format: PDF, DOCX, or TXT only
- Extracted text: ≥ 100 characters

### Evaluation
- Completeness score: 0-100 (weighted: contact20%, skills25%, experience30%, education15%, summary10%)
- Threshold for referral: ≥ 40%

### Subscription Limits
- Free tier: 1 active CV
- Basic tier: 1 active CV  
- Pro tier: 2 active CVs

### Quota Enforcement
- Free: 1 evaluation/month
- Basic: 5 evaluations/month
- Pro: 10 evaluations/month

## Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| idx_user_cvs_user_id | user_id | List user's CVs |
| idx_user_cvs_active | user_id, is_active | Find active CV |
| idx_user_cvs_embedding | embedding_vector | Vector similarity search |

## Migration Required

Alembic migration needed to add columns to user_cvs table:
- skills (JSON)
- experience_summary (TEXT)
- completeness_score (NUMERIC)
- improvement_suggestions (JSON)
- evaluated_at (TIMESTAMP)