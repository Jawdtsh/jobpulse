# Feature Specification: Job-CV Matching Engine

**Feature Branch**: `005-job-cv-matching`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: User description: "Build a semantic job matching system that: 1. Matches new jobs against all active CVs using pgvector cosine similarity 2. Creates match records in job_matches table 3. Queues notifications with tier-based delays (Free=60min, Basic=10min, Pro=instant) 4. Supports configurable similarity thresholds (admin per-category, user 0.60-1.00) 5. Handles user-triggered historical job matching (1-7 days back) 6. Sends notifications via Telegram with inline buttons"

## Clarifications

### Session 2026-04-12

- Q: How is notification delay calculated? → A: From job publication time (job.created_at), NOT ingestion time. Example: Job published at 14:30, ingested at 14:45. Free user notified at 15:30 (60min from 14:30).

- Q: How are jobs batched for notifications? → A: Jobs published within 3-minute window are batched into single notification. Uses Redis Sorted Set with score=notification_timestamp.

- Q: What is the similarity threshold priority? → A: 1. User preference (0.60-1.00), 2. Job category default, 3. System default (0.80).

- Q: How do Pro users with 2 CVs receive notifications? → A: If both CVs match same job, single notification with both scores: "Backend CV: 85%, Frontend CV: 78%".

- Q: When does historical matching run? → A: User-triggered via /search_history <days> (1-7). User can choose to re-send already received jobs or skip duplicates.

- Q: What happens when CV is deactivated after match created? → A: Pending notifications for that CV are cancelled and removed from Redis queue.

- Q: What happens when user upgrades tier while notification is queued? → A: Re-calculate notification time and update Redis score immediately.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Job Matching (Priority: P1)

As the system, when a new job is ingested into the system, I need to automatically match it against all active CVs stored by users, create match records, and queue notifications based on each user's subscription tier.

**Why this priority**: This is the core value proposition - without real-time matching, users miss job opportunities. This must work immediately after job ingestion.

**Independent Test**: A new job is stored in the system. Within 5 seconds, all active CVs that meet similarity thresholds should have match records created and notifications queued.

**Acceptance Scenarios**:

1. **Given** a new job is ingested with valid embedding, **When** the matching pipeline runs, **Then** all active CVs with similarity >= threshold have job_matches records created

2. **Given** a CV is inactive (is_active=false) or deleted (deleted_at set), **When** matching runs, **Then** that CV is excluded from matching

3. **Given** an embedding is null for a CV or job, **When** matching runs, **Then** that CV/job is skipped with a warning logged

4. **Given** a user has an active CV, **When** a matching job is found, **Then** the notification time is calculated from job publication time (job.created_at), not ingestion time

---

### User Story 2 - Tiered Notification Delivery (Priority: P1)

As a user, I need to receive job notifications according to my subscription tier delays - Free users get 60 minutes, Basic get 10 minutes, Pro get instant notifications.

**Why this priority**: This is a key business differentiator. The notification delay must be accurate to maintain user trust and demonstrate tier value.

**Independent Test**: A job published at 14:30 is matched. Free user receives notification at approximately 15:30, Basic at ~14:40, Pro immediately.

**Acceptance Scenarios**:

1. **Given** a Free tier user with matching job, **When** notification time arrives, **Then** notification is delivered 60 minutes after job's publication time (job.created_at)

2. **Given** a Basic tier user with matching job, **When** notification time arrives, **Then** notification is delivered 10 minutes after job's publication time

3. **Given** a Pro tier user with matching job, **When** job is matched, **Then** notification is delivered immediately (within 1 minute)

4. **Given** multiple jobs are published within 3-minute window, **When** notifications are ready, **Then** they are batched into a single notification for that batch window

---

### User Story 3 - Configurable Similarity Thresholds (Priority: P2)

As an admin, I need to configure default similarity thresholds per job category. As a user, I want to adjust my personal threshold (0.60-1.00) to control how many notifications I receive.

**Why this priority**: Different users have different job preferences. Some want fewer, more relevant matches; others want all possible opportunities.

**Independent Test**: Admin sets category threshold to 0.75. User sets personal threshold to 0.85. System uses 0.85 for that user in that category.

**Acceptance Scenarios**:

1. **Given** a user has set personal threshold to 0.85, **When** matching runs, **Then** user only receives matches with similarity >= 0.85

2. **Given** a user has NOT set personal threshold, **When** matching runs in category with threshold 0.75, **Then** category threshold is used

3. **Given** neither user nor category threshold is set, **When** matching runs, **Then** system default (0.80) is used

4. **Given** a user attempts to set threshold outside 0.60-1.00 range, **When** /set_threshold command is used, **Then** system rejects with validation error

---

### User Story 4 - Historical Job Matching (Priority: P2)

As a Pro user who just uploaded a new CV, I want to search historical jobs from the past 1-7 days to find opportunities I may have missed.

**Why this priority**: Enables users who join late or upload new CVs to catch up on opportunities. Only Pro users get this feature.

**Independent Test**: User uploads new CV, triggers /search_history 7. System finds all jobs from past 7 days and matches against their active CVs.

**Acceptance Scenarios**:

1. **Given** a Pro user triggers /search_history with invalid days (0 or >7), **When** command is executed, **Then** system rejects with validation error

2. **Given** a Pro user triggers /search_history with valid days, **When** system processes, **Then** user is asked "Re-send jobs you already received?"

3. **Given** user selects "No", **When** matching runs, **Then** only new matches (not in job_matches table) are sent

4. **Given** user selects "Yes", **When** matching runs, **Then** all matches are sent (including duplicates)

5. **Given** historical matching completes, **When** notifications are ready, **Then** they are sent immediately (no delay queue)

6. **Given** a Free or Basic user triggers /search_history, **When** command is executed, **Then** system rejects with "This feature is Pro-only. Upgrade to access historical search." and shows an upgrade button — before any days selection UI

---

### User Story 5 - Match History & Tracking (Priority: P2)

As a user, I want to see my job matches with click tracking to understand which opportunities I've pursued.

**Why this priority**: Users need to track their job search progress. Click tracking provides engagement analytics.

**Independent Test**: User runs /my_jobs and sees list of matched jobs with similarity scores and dates.

**Acceptance Scenarios**:

1. **Given** a user runs /my_jobs, **When** command is executed, **Then** system shows list: job title, company, similarity score, notification date

2. **Given** a user clicks "View Details" button, **When** notification is clicked, **Then** is_clicked=true and clicked_at is recorded

3. **Given** a user has clicked a job, **When** they view /my_jobs, **Then** clicked jobs are marked as clicked

---

### User Story 6 - Match Quality Metrics (Priority: P3)

As the system, I need to track match quality metrics to identify issues and improve accuracy over time.

**Why this priority**: Data-driven improvement. Low-performing thresholds need to be identified and adjusted.

**Independent Test**: System calculates CTR (clicked/notified) for all matches. Identifies thresholds with CTR < 5%.

**Acceptance Scenarios**:

1. **Given** matches exist for a threshold setting, **When** metrics are calculated, **Then** CTR is tracked per threshold

2. **Given** similarity score distribution is analyzed, **When** report runs, **Then** distribution is logged for analysis

3. **Given** a threshold has CTR < 5%, **When** report runs, **Then** threshold is flagged as low-performing

---

### Edge Cases

- What happens when a job is deleted after matching but before notification is sent? → Send notification anyway (job data may still be useful to user)
- What happens when user deactivates CV after match created but before notification sent? → Cancel pending notifications for that CV
- What happens when user has multiple CVs matching same job? → Send single notification listing all matching CVs with their scores
- What happens when similarity scores are identical across multiple users? → All notified equally (no priority order)
- What happens when Redis queue fails? → Fallback to immediate notification and log error

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST match new jobs against ALL active CVs immediately after job storage
- **FR-002**: System MUST calculate similarity using pgvector native cosine_distance function at the database level (NOT Python-level computation). Matching MUST use a single SQL query with `1 - (embedding_vector <=> job_embedding::vector)` for performance per SC-001
- **FR-003**: System MUST skip CVs or jobs where embedding vector is null
- **FR-004**: System MUST apply similarity threshold with priority: user preference > job category default > system default (0.80)
- **FR-005**: System MUST create job_matches record for each match containing similarity_score, user_id, job_id, and cv_id (NOT NULL — every match must reference a specific CV)
- **FR-006**: System MUST enforce uniqueness on (job_id, user_id, cv_id) to prevent duplicate matches — silently skip on unique violation (pgcode 23505), propagate all other IntegrityErrors

- **FR-007**: System MUST calculate notification time from job's telegram_published_at timestamp if available, otherwise fall back to job.created_at. This ensures notification delay starts from the actual Telegram publication time, not ingestion time
- **FR-008**: System MUST queue notifications with tier-specific delays: Free=60min, Basic=10min, Pro=instant
- **FR-009**: System MUST use Redis Sorted Set for notification queue with notification_time as score
- **FR-010**: System MUST batch jobs published within 3-minute window into single notification
- **FR-011**: System MUST run periodic check every 1 minute to process due notifications

- **FR-012**: System MUST fetch notifications where notification_time <= current_time from queue
- **FR-013**: System MUST send Telegram message containing job title, company, salary range, and similarity score
- **FR-014**: System MUST include inline buttons for [View Details] and [Generate Cover Letter]
- **FR-015**: System MUST mark job_matches.is_notified=true and notified_at=NOW() after successful send
- **FR-016**: System MUST remove notification from queue after successful send

- **FR-017**: System MUST detect when multiple CVs from same user match same job
- **FR-018**: System MUST send single notification listing all matching CVs with their scores
- **FR-019**: System MUST format multi-CV notification as "CV Name: XX%, CV Name: YY%"

- **FR-020**: System MUST validate days parameter is between 1-7 for historical matching
- **FR-021**: System MUST query jobs from NOW() minus specified days for historical matching
- **FR-022**: System MUST ask user "Re-send jobs you already received?" before processing
- **FR-023**: System MUST exclude already-matched jobs if user selects "No"
- **FR-024**: System MUST include all matches if user selects "Yes"
- **FR-025**: System MUST send historical matches immediately without delay queue

- **FR-026**: System MUST allow admin to set job_categories.similarity_threshold via database
- **FR-027**: System MUST allow users to set user_preferences.similarity_threshold via bot command
- **FR-028**: System MUST validate user threshold is between 0.60 and 1.00
- **FR-029**: System MUST enforce constraint on user_preferences table

- **FR-030**: System MUST cancel pending notifications when CV is deactivated (remove from Redis queue only — match records are preserved for history)
- **FR-031**: System MUST cancel pending notifications when CV is deleted (remove from Redis queue only — match records are preserved for history)
- **FR-032**: System MUST remove cancelled notifications from Redis queue
- **FR-033**: System MUST update notification time in Redis queue when user upgrades subscription tier (recalculate delay using job_published_at from queue payload and update score)
- **FR-034**: System MUST restrict /search_history command to Pro tier users only
- **FR-035**: System MUST return early from process_due_notifications if Redis queue fetch fails (log error with traceback for Sentry, let next Celery beat tick retry)
- **FR-036**: System MUST use a single bulk query (get_existing_match_keys) to check for existing matches in historical matching, avoiding N+1 query patterns
- **FR-037**: cv_id in job_matches MUST be NOT NULL — every match references a specific CV
- **FR-038**: Job categories MUST have a CHECK constraint ensuring similarity_threshold is between 0.00 and 1.00
### Key Entities *(include if feature involves data)*

- **JobMatch**: Represents a match between a user's CV and a job. Contains: job_id, user_id, cv_id, similarity_score, is_notified, notified_at, is_clicked, clicked_at

- **NotificationQueue**: System queue holding pending notifications. Uses notification_time as delivery timestamp for sorting

- **JobCategory**: Category classification for jobs with configurable similarity threshold (default 0.80)

- **UserPreferences**: User-specific settings including optional similarity_threshold (range 0.60-1.00)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Matching completes within 5 seconds for 10,000 active CVs
- **SC-002**: Notification delay accuracy within ±30 seconds of target time
- **SC-003**: 99% of matches have similarity score >= configured threshold
- **SC-004**: Historical matching processes 7 days of jobs within 10 seconds
- **SC-005**: Multi-CV notifications correctly display all matching CV scores in single message

- **SC-006**: Click-through rate is tracked for all notifications
- **SC-007**: Users can view their match history via bot command
- **SC-008**: User threshold settings persist and are applied correctly

## Assumptions

- Job publication time (job.created_at) is accurate and available from the job ingestion pipeline
- User subscription tier is available and up-to-date
- All users have at least one active CV before being matched against jobs
- Telegram bot is configured and can send messages with inline buttons
- Redis is available for notification queue
- Database supports vector similarity search with acceptable performance