# Data Model: Database Schema & Migrations

This document defines the 12 database tables for JobPulse AI, following the Database_Schema.md v3.0 structure.

## Entities

### 1. User

Represents system users with Telegram identity and subscription management.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique user identifier |
| telegram_id | BIGINT | UNIQUE, NOT NULL | Telegram user ID |
| username | VARCHAR(255) | NULL | Telegram username |
| first_name | VARCHAR(255) | NOT NULL | First name |
| last_name | VARCHAR(255) | NULL | Last name |
| referral_code | VARCHAR(12) | UNIQUE, NOT NULL | Auto-generated referral code |
| subscription_tier | VARCHAR(20) | DEFAULT 'free' | Subscription level |
| referred_by | UUID | FOREIGN KEY (users.id) | Referrer user |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Last update timestamp |

**State transitions**: subscription_tier: free → basic → pro (via subscription payments)

---

### 2. UserCV

Represents user CV documents with encrypted content and vector embeddings.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique CV identifier |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Owner user |
| title | VARCHAR(255) | NOT NULL | CV title |
| content | BYTEA | NOT NULL | Encrypted CV content (Fernet) |
| embedding_vector | VECTOR(768) | NULL | 768-dim vector embedding |
| is_active | BOOLEAN | DEFAULT TRUE | Active CV for matching |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Last update timestamp |

**Relationships**: 
- Many-to-one with User
- CASCADE delete: deleting user removes all their CVs

---

### 3. Job

Represents job postings with metadata and vector embeddings.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique job identifier |
| source_channel_id | UUID | FOREIGN KEY (monitored_channels.id) | Source channel |
| telegram_message_id | BIGINT | NOT NULL | Original Telegram message ID |
| title | VARCHAR(500) | NOT NULL | Job title |
| company | VARCHAR(255) | NOT NULL | Company name |
| location | VARCHAR(255) | NULL | Job location |
| salary_min | INTEGER | NULL | Minimum salary |
| salary_max | INTEGER | NULL | Maximum salary |
| salary_currency | VARCHAR(3) | DEFAULT 'USD' | Salary currency |
| description | TEXT | NOT NULL | Full job description |
| requirements | JSONB | DEFAULT '[]' | List of requirements |
| skills | JSONB | DEFAULT '[]' | List of skills |
| embedding_vector | VECTOR(768) | NULL | 768-dim vector embedding |
| content_hash | VARCHAR(64) | UNIQUE | SHA-256 for deduplication |
| is_archived | BOOLEAN | DEFAULT FALSE | Archive flag |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Last update timestamp |

**Relationships**:
- Many-to-one with MonitoredChannel
- One-to-many with JobMatch
- One-to-many with JobReport

---

### 4. JobMatch

Represents the relationship between jobs and users with similarity scores.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique match identifier |
| job_id | UUID | FOREIGN KEY (jobs.id), NOT NULL | Matched job |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Matched user |
| similarity_score | REAL | NOT NULL, CHECK (0.0-1.0) | Cosine similarity score |
| is_notified | BOOLEAN | DEFAULT FALSE | User notification sent |
| notified_at | TIMESTAMP | NULL | Notification timestamp |
| is_clicked | BOOLEAN | DEFAULT FALSE | User clicked the job |
| clicked_at | TIMESTAMP | NULL | Click timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Match creation timestamp |

**Relationships**:
- Many-to-one with Job
- Many-to-one with User
- Composite unique: (job_id, user_id)
- CASCADE delete: deleting job or user removes matches

---

### 5. Subscription

Represents payment records and subscription periods.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique subscription identifier |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Subscriber user |
| plan_type | VARCHAR(20) | NOT NULL | Plan: basic, pro |
| amount | INTEGER | NOT NULL | Payment amount in cents |
| currency | VARCHAR(3) | DEFAULT 'USD' | Payment currency |
| payment_method | VARCHAR(50) | NOT NULL | Payment provider |
| payment_id | VARCHAR(255) | UNIQUE | External payment ID |
| valid_from | TIMESTAMP | NOT NULL | Subscription start |
| valid_until | TIMESTAMP | NOT NULL | Subscription end |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, expired, cancelled |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Last update timestamp |

**Relationships**:
- Many-to-one with User
- CASCADE delete: deleting user removes subscription history

**State transitions**: active → expired (on valid_until), active → cancelled

---

### 6. ReferralReward

Represents referral bonuses with status tracking.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique reward identifier |
| referrer_id | UUID | FOREIGN KEY (users.id), NOT NULL | Referring user |
| referred_user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Referred user |
| reward_type | VARCHAR(50) | NOT NULL | Type: credits, subscription_month |
| reward_value | INTEGER | NOT NULL | Reward value |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending, applied, expired |
| applied_at | TIMESTAMP | NULL | When reward was applied |
| expires_at | TIMESTAMP | NOT NULL | Expiration timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Creation timestamp |

**Relationships**:
- Many-to-one with User (referrer)
- Many-to-one with User (referred_user)
- Unique constraint: (referrer_id, referred_user_id, reward_type)

---

### 7. CoverLetterLog

Represents cover letter generation events for quota tracking.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique log identifier |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | User who generated |
| job_id | UUID | FOREIGN KEY (jobs.id), NOT NULL | Job applied to |
| generated_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Generation timestamp |

**Relationships**:
- Many-to-one with User
- Many-to-one with Job
- CASCADE delete: deleting user or job removes logs

**Quota enforcement**: Monthly count per user. Use SELECT FOR UPDATE for race condition prevention.

---

### 8. UserInteraction

Represents user actions for anti-spam analysis.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique interaction identifier |
| user_id | UUID | FOREIGN KEY (users.id), NOT NULL | User who acted |
| action_type | VARCHAR(50) | NOT NULL | Command, button_click, message |
| action_data | JSONB | DEFAULT '{}' | Action details |
| ip_address | INET | NULL | User IP address |
| user_agent | TEXT | NULL | Browser/device user agent |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Action timestamp |

**Relationships**:
- Many-to-one with User
- CASCADE delete: deleting user removes interaction history

**Indexes**: user_id, created_at (for fraud detection queries)

---

### 9. JobReport

Represents user-submitted job reports for scam detection.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique report identifier |
| job_id | UUID | FOREIGN KEY (jobs.id), NOT NULL | Reported job |
| reporter_user_id | UUID | FOREIGN KEY (users.id), NOT NULL | Reporting user |
| reason | VARCHAR(100) | NOT NULL | Report reason |
| details | TEXT | NULL | Additional details |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Report timestamp |

**Relationships**:
- Many-to-one with Job
- Many-to-one with User
- Unique: (job_id, reporter_user_id) - one report per user per job

**Auto-archive**: After 3 unique reports, job is moved to archived_jobs

---

### 10. ArchivedJob

Represents historical job data for retention and analytics.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Archived job identifier |
| original_job_id | UUID | NOT NULL | Original job ID |
| source_channel_id | UUID | FOREIGN KEY (monitored_channels.id) | Source channel |
| telegram_message_id | BIGINT | NOT NULL | Original message ID |
| title | VARCHAR(500) | NOT NULL | Job title |
| company | VARCHAR(255) | NOT NULL | Company name |
| location | VARCHAR(255) | NULL | Job location |
| salary_min | INTEGER | NULL | Minimum salary |
| salary_max | INTEGER | NULL | Maximum salary |
| salary_currency | VARCHAR(3) | DEFAULT 'USD' | Salary currency |
| description | TEXT | NOT NULL | Full job description |
| requirements | JSONB | DEFAULT '[]' | List of requirements |
| skills | JSONB | DEFAULT '[]' | List of skills |
| content_hash | VARCHAR(64) | NOT NULL | Original content hash |
| archived_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Archive timestamp |
| archive_reason | VARCHAR(50) | NOT NULL | Reason: retention, reported, manual |

**Note**: No vector embedding - archived jobs are for statistics only

---

### 11. TelegramSession

Represents Telegram account sessions for scraping rotation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique session identifier |
| session_string | BYTEA | NOT NULL | Encrypted session data (Fernet) |
| phone_number | VARCHAR(20) | NOT NULL | Account phone number |
| is_active | BOOLEAN | DEFAULT TRUE | Session active flag |
| is_banned | BOOLEAN | DEFAULT FALSE | Account banned flag |
| ban_reason | TEXT | NULL | Ban explanation |
| last_used_at | TIMESTAMP | NULL | Last usage timestamp |
| use_count | INTEGER | DEFAULT 0 | Total uses |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Last update timestamp |

**Rotation logic**: SELECT where is_active=TRUE AND is_banned=FALSE ORDER BY use_count ASC, last_used_at ASC

---

### 12. MonitoredChannel

Represents data source channels for scraping management.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique channel identifier |
| username | VARCHAR(255) | UNIQUE, NOT NULL | Telegram username |
| title | VARCHAR(500) | NOT NULL | Channel title |
| member_count | INTEGER | NULL | Last known member count |
| is_active | BOOLEAN | DEFAULT TRUE | Monitoring active flag |
| jobs_found | INTEGER | DEFAULT 0 | Total jobs found |
| false_positives | INTEGER | DEFAULT 0 | Invalid job posts |
| last_scraped_at | TIMESTAMP | NULL | Last scrape timestamp |
| created_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT UTC NOW | Last update timestamp |

---

## Indexes

### HNSW Vector Indexes

| Table | Column | Index Name | Parameters |
|-------|--------|------------|------------|
| user_cvs | embedding_vector | idx_user_cvs_vector | m=16, ef_construction=64 |
| jobs | embedding_vector | idx_jobs_vector | m=16, ef_construction=64 |

### B-Tree Indexes

| Table | Columns | Index Name | Purpose |
|-------|---------|------------|---------|
| users | telegram_id | idx_users_telegram | User lookup |
| users | referral_code | idx_users_referral | Referral lookup |
| user_cvs | user_id | idx_user_cvs_user | User's CVs |
| jobs | source_channel_id | idx_jobs_channel | Channel jobs |
| jobs | content_hash | idx_jobs_hash | Deduplication |
| jobs | is_archived | idx_jobs_archived | Archive filter |
| job_matches | user_id | idx_matches_user | User matches |
| job_matches | job_id | idx_matches_job | Job matches |
| subscriptions | user_id | idx_subs_user | User subscriptions |
| subscriptions | status | idx_subs_status | Status filter |
| user_interactions | user_id, created_at | idx_interactions_user_time | Fraud queries |
| job_reports | job_id | idx_reports_job | Job reports |
| telegram_sessions | is_active, is_banned | idx_sessions_available | Session selection |

---

## Entity Relationships

```
User (1) ──── (N) UserCV
User (1) ──── (N) JobMatch
User (1) ──── (N) Subscription
User (1) ──── (N) ReferralReward (referrer)
User (1) ──── (N) ReferralReward (referred)
User (1) ──── (N) CoverLetterLog
User (1) ──── (N) UserInteraction
User (1) ──── (N) JobReport

Job (1) ──── (N) JobMatch
Job (1) ──── (N) JobReport
Job (1) ──── (N) CoverLetterLog

MonitoredChannel (1) ──── (N) Job

MonitoredChannel (1) ──── (N) ArchivedJob
```

---

## Migration Structure

Per technical requirements, migrations will be split:

1. **Initial schema**: All 12 tables without indexes
2. **HNSW indexes**: Vector similarity indexes
3. **Additional indexes**: Performance indexes

All timestamps stored in UTC. All foreign keys use CASCADE deletes where appropriate.
