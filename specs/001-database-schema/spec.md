# Feature Specification: Database Schema & Migrations

**Feature Branch**: `001-database-schema`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: Foundation spec for JobPulse AI database schema supporting user management, CV storage with vector embeddings, job postings, matching engine, and security features.

## User Scenarios & Testing *(mandatory)*

This foundation spec establishes the data layer for JobPulse AI. All other features depend on these tables being in place.

### User Story 1 - Users Table with Subscription Management (Priority: P1)

As a system, I need a users table to store user profiles, subscription status, and referral codes so that user management and subscription tiers can be enforced.

**Why this priority**: User management is the foundation of the entire system. Without users, nothing else functions.

**Independent Test**: Can verify table creation and constraints independently. Provides core identity management for all other features.

**Acceptance Scenarios**:

1. **Given** a new user registration, **When** the user record is created, **Then** a unique referral code is auto-generated and subscription tier defaults to 'free'.
2. **Given** an existing user, **When** updating subscription status, **Then** the tier field reflects the current plan (Free/Basic/Pro).

---

### User Story 2 - CV Storage with Vector Embeddings (Priority: P1)

As a system, I need a user_cvs table to store CV data with vector embeddings so that job matching can be performed using cosine similarity.

**Why this priority**: CV data is the core input for the matching engine. Vector embeddings enable semantic job matching.

**Independent Test**: Can verify table creation, encryption, and vector column existence independently. Enables matching functionality.

**Acceptance Scenarios**:

1. **Given** a user uploads a CV, **When** the CV is stored, **Then** content is encrypted using Fernet before storage.
2. **Given** CV embeddings need to be searched, **When** similarity queries are executed, **Then** HNSW index enables fast cosine similarity search.

---

### User Story 3 - Job Posts with Vector Embeddings (Priority: P1)

As a system, I need a jobs table to store job posts with vector embeddings so that job data can be matched against user CVs.

**Why this priority**: Job postings are the other core input for the matching engine.

**Independent Test**: Can verify table creation, vector columns, and indexes independently. Enables job storage and retrieval.

**Acceptance Scenarios**:

1. **Given** a new job is scraped or posted, **When** the job is stored, **Then** vector embedding is generated and content hash enables deduplication.
2. **Given** jobs need to be found by similarity, **When** vector search is performed, **Then** HNSW index provides fast results.

---

### User Story 4 - Job Matching Tracking (Priority: P1)

As a system, I need a job_matches table to track which jobs matched which users so that users can be notified of relevant opportunities.

**Why this priority**: The matching engine needs to persist match results for user notifications and history.

**Independent Test**: Can verify foreign key relationships and similarity score storage independently.

**Acceptance Scenarios**:

1. **Given** a match is found between a job and user, **When** the match is recorded, **Then** similarity score (0.0-1.0) is stored.
2. **Given** user needs to see match history, **When** querying job_matches, **Then** notification timestamps indicate which matches were sent to the user.

---

### User Story 5 - Subscription Payment Tracking (Priority: P2)

As a system, I need a subscriptions table to track payment history and active periods so that subscription tier access can be enforced.

**Why this priority**: Revenue generation depends on accurate subscription tracking.

**Independent Test**: Can verify payment record creation and status tracking independently. Enables billing features.

**Acceptance Scenarios**:

1. **Given** a user purchases a subscription, **When** payment is processed, **Then** a subscription record is created with active status and validity dates.
2. **Given** a subscription expires, **When** validity end date passes, **Then** status changes to expired automatically.

---

### User Story 6 - Referral Reward Tracking (Priority: P2)

As a system, I need a referral_rewards table to prevent duplicate reward claims and track referral bonuses.

**Why this priority**: Referral system requires preventing duplicate rewards and tracking reward status.

**Independent Test**: Can verify unique constraints prevent duplicate rewards. Enables referral program integrity.

**Acceptance Scenarios**:

1. **Given** a user refers another user, **When** a reward is claimed, **Then** UNIQUE constraint prevents duplicate (referrer_id, referred_user_id, reward_type) combinations.
2. **Given** a referral reward is processed, **When** status changes, **Then** reward can be marked as pending, applied, or expired.

---

### User Story 7 - Cover Letter Generation Quota Tracking (Priority: P2)

As a system, I need a cover_letter_logs table to enforce monthly quota limits on AI-generated cover letters.

**Why this priority**: Subscription tier quotas need to be enforced for cover letter generation.

**Independent Test**: Can verify quota counting per user per month. Enables quota enforcement.

**Acceptance Scenarios**:

1. **Given** a user generates a cover letter, **When** the request is made, **Then** a log entry records timestamp for monthly counting.
2. **Given** concurrent requests for the same user, **When** quota is checked, **Then** SELECT FOR UPDATE prevents race conditions.

---

### User Story 8 - Anti-Spam User Interaction Tracking (Priority: P2)

As a system, I need a user_interactions table for anti-spam detection so that suspicious activity can be identified and blocked.

**Why this priority**: Telegram bot security requires tracking user actions to detect and prevent spam.

**Independent Test**: Can verify interaction logging and query performance. Enables spam detection.

**Acceptance Scenarios**:

1. **Given** a user performs an action, **When** the action is logged, **Then** IP address and user agent are recorded for fraud detection.
2. **Given** spam analysis is needed, **When** querying recent interactions, **Then** indexes on user_id and timestamp provide fast results.

---

### User Story 9 - Community-Based Scam Detection (Priority: P3)

As a system, I need a job_reports table so that users can report suspicious job postings and scams can be identified.

**Why this priority**: Community moderation helps identify fraudulent job postings.

**Independent Test**: Can verify report creation and aggregation. Enables scam detection workflow.

**Acceptance Scenarios**:

1. **Given** a user reports a job, **When** the report is submitted, **Then** report reason and timestamp are stored.
2. **Given** a job receives multiple reports, **When** 3 unique users report the same job, **Then** the job is auto-archived.

---

### User Story 10 - Job Data Retention (Priority: P3)

As a system, I need an archived_jobs table for data retention policy so that old jobs are preserved for statistics without affecting matching.

**Why this priority**: Jobs older than 7 days should not appear in matching but historical data is valuable.

**Independent Test**: Can verify archived jobs structure matches active jobs. Enables retention policy.

**Acceptance Scenarios**:

1. **Given** a job is 7 days old, **When** retention policy runs, **Then** job is moved to archived_jobs table.
2. **Given** historical statistics are needed, **When** querying archived_jobs, **Then** full job data is available for analytics.

---

### User Story 11 - Telegram Session Management (Priority: P3)

As a system, I need a telegram_sessions table to rotate scraping accounts so that rate limits and bans are managed.

**Why this priority**: Job scraping requires managing multiple Telegram accounts to avoid detection.

**Independent Test**: Can verify encrypted session storage and rotation tracking. Enables scraping operations.

**Acceptance Scenarios**:

1. **Given** a Telegram session is stored, **When** saved to database, **Then** session string is encrypted using Fernet.
2. **Given** a session needs to be rotated, **When** selecting next available session, **Then** last_used timestamp and ban status are considered.

---

### User Story 12 - Monitored Channels Tracking (Priority: P3)

As a system, I need a monitored_channels table to track data sources so that scraping performance can be measured.

**Why this priority**: Channel performance metrics help optimize job scraping coverage.

**Independent Test**: Can verify channel tracking and performance metrics. Enables source management.

**Acceptance Scenarios**:

1. **Given** a channel is added as a source, **When** monitoring begins, **Then** channel details are stored with active status.
2. **Given** channel performance is evaluated, **When** statistics are queried, **Then** jobs_found and false_positives counters inform decisions.

---

### Edge Cases

- What happens when vector dimensions exceed 768 during embedding generation?
- How does the system handle duplicate job content hashes?
- What occurs when a user is deleted - should all related CVs, matches, and logs be cascade deleted?
- How are timezone differences handled when storing UTC timestamps?
- What happens when pgvector extension is not available in the PostgreSQL instance?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create users table with fields for id, telegram_id, username, first_name, last_name, referral_code, subscription_tier, referred_by, created_at, updated_at
- **FR-002**: System MUST create user_cvs table with encrypted content storage and 768-dimensional vector embedding column
- **FR-003**: System MUST create jobs table with all job metadata fields and 768-dimensional vector embedding column
- **FR-004**: System MUST create job_matches table with composite foreign keys (job_id, user_id) and similarity score
- **FR-005**: System MUST create subscriptions table linking to users with plan type, amount, payment method, validity dates, and status
- **FR-006**: System MUST create referral_rewards table with UNIQUE constraint on (referrer_id, referred_user_id, reward_type)
- **FR-007**: System MUST create cover_letter_logs table with timestamp for monthly quota counting
- **FR-008**: System MUST create user_interactions table with IP address and user agent for fraud detection
- **FR-009**: System MUST create job_reports table with auto-archive trigger after 3 unique reports
- **FR-010**: System MUST create archived_jobs table matching jobs structure for data retention
- **FR-011**: System MUST create telegram_sessions table with encrypted session strings and rotation tracking
- **FR-012**: System MUST create monitored_channels table with performance metrics (jobs_found, false_positives)
- **FR-013**: System MUST use HNSW index with m=16, ef_construction=64 on all vector columns
- **FR-014**: System MUST use Alembic for all schema migrations
- **FR-015**: System MUST store all timestamps in UTC
- **FR-016**: System MUST implement Fernet encryption for CV content and Telegram session strings

### Key Entities *(include if feature involves data)*

- **User**: Represents system users with Telegram identity, subscription status, and referral tracking
- **UserCV**: Represents user CV documents with encrypted content and vector embeddings
- **Job**: Represents job postings with metadata and vector embeddings
- **JobMatch**: Represents the relationship between jobs and users with similarity scores
- **Subscription**: Represents payment records and subscription periods
- **ReferralReward**: Represents referral bonuses with status tracking
- **CoverLetterLog**: Represents cover letter generation events for quota tracking
- **UserInteraction**: Represents user actions for anti-spam analysis
- **JobReport**: Represents user-submitted job reports for scam detection
- **ArchivedJob**: Represents historical job data for retention and analytics
- **TelegramSession**: Represents Telegram account sessions for scraping rotation
- **MonitoredChannel**: Represents data source channels for scraping management

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 12 tables can be created via Alembic migration without errors
- **SC-002**: Vector similarity search on jobs and user_cvs returns results within 500ms for datasets up to 100,000 records
- **SC-003**: Referral reward UNIQUE constraint prevents duplicate rewards under concurrent load
- **SC-004**: User interaction queries perform efficiently with indexes supporting sub-second response for fraud detection
- **SC-005**: Job archive process completes within 5 minutes for batches of up to 10,000 jobs

## Assumptions

- PostgreSQL 16 with pgvector extension is available and properly configured
- Fernet encryption keys are managed via environment variables as per security requirements
- Database connection pooling is handled at the application layer
- Telegram scraping is conducted in compliance with platform terms of service
- Migration rollback capability is maintained for all schema changes
