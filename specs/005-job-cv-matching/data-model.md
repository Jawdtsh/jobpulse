# Data Model: Job-CV Matching Engine

## Entities

### JobMatch

Represents a match between a user's CV and a job.

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | Primary Key | Auto-generated |
| job_id | UUID | Foreign Key → jobs.id | Required |
| user_id | UUID | Foreign Key → users.id | Required |
| cv_id | UUID | Foreign Key → user_cvs.id | Required | **NEW in SPEC-005** - Tracks which CV matched (for Pro users with 2 CVs) |
| similarity_score | FLOAT | 0.00-1.00 | Cosine similarity |
| is_notified | BOOLEAN | Default: false | |
| notified_at | TIMESTAMP | Nullable | Set when notification sent |
| is_clicked | BOOLEAN | Default: false | |
| clicked_at | TIMESTAMP | Nullable | Set when user clicks |
| created_at | TIMESTAMP | Default: NOW() | |
| updated_at | TIMESTAMP | Auto update | |

**Unique Constraint**: (job_id, user_id, cv_id)

### JobCategory

Category classification for jobs with default similarity threshold.

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | Primary Key | Auto-generated |
| name | VARCHAR(100) | Unique, Not Null | e.g., "Backend", "Frontend" |
| similarity_threshold | FLOAT | Default: 0.80, 0.00-1.00 | Admin configurable |
| created_at | TIMESTAMP | Default: NOW() | |
| updated_at | TIMESTAMP | Auto update | |

### UserPreferences

User-specific settings for matching behavior.

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | Primary Key | Auto-generated |
| user_id | UUID | Foreign Key → users.id, Unique | Required |
| similarity_threshold | FLOAT | Check: 0.60-1.00 | User configurable |
| created_at | TIMESTAMP | Default: NOW() | |
| updated_at | TIMESTAMP | Auto update | |

**Check Constraint**: `CHECK (similarity_threshold BETWEEN 0.60 AND 1.00)`

## State Transitions

### JobMatch Lifecycle

```
CREATED → NOTIFIED → CLICKED
  ↓         ↓          ↓
  |    notification  click
  |      sent        event
  ↓         
[DELETED - if CV or job deleted - cascades]
```

## Relationships

```
User ←→ JobMatch ←→ Job
  ↓          ↑
UserCV   (via cv_id)
  ↓
UserPreferences (one-to-one)

Job ←→ JobCategory (many-to-one)
```

## Validation Rules

- similarity_score MUST be between 0.00 and 1.00
- User preference similarity_threshold MUST be between 0.60 and 1.00
- Job category similarity_threshold MUST be between 0.00 and 1.00
- UNIQUE(job_id, user_id, cv_id) in job_matches table

## Redis Data Structures

### NotificationQueue (Sorted Set)

**Key Pattern**: `notification_queue`

**Score**: Unix timestamp of notification time (when notification should be sent)

**Value**: JSON object containing:
```json
{
  "match_id": "uuid",
  "user_id": "uuid",
  "job_id": "uuid",
  "cv_id": "uuid",
  "tier": "free|basic|pro",
  "batch_key": "job_publication_timestamp_rounded_to_3min"
}
```

**Operations**:
- `ZADD notification_queue <notification_time> <json_value>` - Add notification
- `ZRANGEBYSCORE notification_queue -inf <current_time>` - Fetch due notifications
- `ZREM notification_queue <json_value>` - Remove after send

**TTL**: Notifications auto-expire after 7 days if not sent (data retention policy)

## Migration Required

**Migration Number**: `006_matching_engine_tables.py`

**Dependencies**: 
- SPEC-001 (users, jobs, user_cvs tables)
- SPEC-004 (user_cvs.embedding_vector)

**Operations**:
1. CREATE TABLE job_categories
2. CREATE TABLE user_preferences
3. ALTER TABLE job_matches ADD COLUMN cv_id UUID REFERENCES user_cvs(id)
4. CREATE UNIQUE INDEX idx_job_matches_unique ON job_matches(job_id, user_id, cv_id)
5. CREATE INDEX idx_job_matches_cv_id ON job_matches(cv_id)

**Downgrade**: DROP tables in reverse order