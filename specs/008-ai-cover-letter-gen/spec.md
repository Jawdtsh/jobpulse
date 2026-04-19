# Feature Specification: AI Cover Letter Generation

**Feature Branch**: `008-ai-cover-letter-gen`  
**Created**: 2026-04-18  
**Status**: Draft (Clarifications Complete + Additional Clarities)  
**Input**: User description: "Build an AI-powered cover letter generation system that creates personalized, professional cover letters for job applications. Users can generate cover letters from job notifications or saved jobs, customize parameters (tone, length, focus, language), and regenerate with different settings. The system enforces daily quotas based on subscription tier (Free: 3/day, Basic: 15/day, Pro: 50/day) with Damascus timezone (Asia/Damascus) for daily reset at midnight. Generated cover letters are stored in the database with metadata for tracking and analytics."

## Clarifications

### Session 2026-04-19

- Q: How should user CV data (personal information) be handled when processing with external AI service (Gemini)? → A: Store CV with user consent
- Q: When a user attempts to generate a cover letter without having uploaded any CV, how should the system behave? → A: Block with redirect
- Q: If the Gemini API returns an empty or invalid response (network timeout, rate limit, malformed output), how should the system handle this failure scenario? → A: Retry without quota impact
- Q: For FR-038 (regeneration limit of 10 per job), should each regeneration attempt create a NEW cover_letter record (with incremented generation_count), or UPDATE the existing record in place? → A: In-place update
- Q: The spec mentions Sentry for prompt validation errors (FR-036), but does not fully specify the logging/metrics strategy. How detailed should operational logging be for cover letter generation operations? → A: Error-only logging (send errors to Sentry, basic operation counts to metrics)

### User Story 1 - Generate Cover Letter from Job Notification (Priority: P1)

A user receives a job notification and wants to generate a personalized cover letter. They click the [Cover Letter] button, select customization options (tone, length, focus, language), and receive an AI-generated cover letter within 10 seconds. The generation counts against their daily quota. If they have reached the limit, they see purchase/wait/upgrade options.

**Why this priority**: This is the primary user flow for cover letter generation. Job notifications are the main entry point for discovering new opportunities, and generating a cover letter immediately after seeing a match is the most natural user behavior.

**Independent Test**: Trigger job notification, click Cover Letter button, verify customization form, generate letter, verify quota increment. Delivers immediate value by providing a ready-to-use cover letter.

**Acceptance Scenarios**:

1. **Given** a user receives a job notification and has quota remaining, **When** they click [Cover Letter], **Then** a customization form is displayed with default values (Tone: Professional, Length: Medium, Focus: All, Language: Arabic)

2. **Given** a user submits customization form, **When** generation starts, **Then** a status message "Generating..." is displayed and the API is called with correct parameters

3. **Given** generation succeeds, **When** the cover letter is ready, **Then** it is displayed in chat with [Regenerate] and [Copy Text] buttons, and quota counter increments by 1

4. **Given** a user has exhausted daily quota (Free: 3/3), **When** they click [Cover Letter], **Then** they see three options: Wait (with countdown), Purchase extra ($0.50/5, $1/12, $3/40), Upgrade subscription

5. **Given** a user purchases extra generations, **When** purchase completes, **Then** purchased count is added to available quota and persists indefinitely

---

### User Story 2 - Generate Cover Letter from Saved Jobs (Priority: P1)

A user browses their saved jobs via /my_jobs and wants to generate a cover letter for a previously saved job. The flow is identical to generating from notifications, ensuring consistent UX across both entry points.

**Why this priority**: Users often save jobs to apply later. Providing cover letter generation from /my_jobs enables a complete "save - review - apply" workflow.

**Independent Test**: Save job, navigate to /my_jobs, click Cover Letter button, verify same customization flow as notifications.

**Acceptance Scenarios**:

1. **Given** a user views /my_jobs saved list, **When** they click [Cover Letter] on any job card, **Then** the same customization form as notifications is displayed

2. **Given** quota is available, **When** user generates from saved job, **Then** the generation flow matches notification flow exactly (same buttons, same quota increment)

---

### User Story 3 - Regenerate with Different Settings (Priority: P1)

A user generates a cover letter but wants to try different tone/length/focus. They click [Regenerate], modify settings in the customization form, and receive a new version. Each regeneration counts as a separate generation against daily quota.

**Why this priority**: Users often want to experiment with different styles. This is critical for user satisfaction and perceived value.

**Independent Test**: Generate cover letter, click Regenerate, change settings, verify new letter generated and quota incremented again.

**Acceptance Scenarios**:

1. **Given** a user has a generated cover letter displayed, **When** they click [Regenerate], **Then** the customization form reappears pre-filled with previous settings

2. **Given** user modifies settings and confirms, **When** regeneration completes, **Then** the NEW cover letter replaces the old one in chat, quota increments again, and generation_count field in database increments

3. **Given** user regenerates but has exhausted quota, **When** they try to regenerate, **Then** the same purchase/wait/upgrade options are shown

---

### User Story 4 - Daily Quota Reset at Midnight Damascus Time (Priority: P2)

The system automatically resets daily quota counters at midnight (00:00) Damascus timezone (Asia/Damascus). Users who exhausted quota can generate again after reset.

**Why this priority**: Daily quota is a core business rule. Correct timezone handling ensures fair quota allocation across users.

**Independent Test**: Set system time to 23:59 Damascus time, exhaust quota, wait 2 minutes, verify quota resets at 00:00.

**Acceptance Scenarios**:

1. **Given** a user exhausted quota on day N, **When** Damascus time reaches 00:00 on day N+1, **Then** their quota counter resets to 0 and they can generate again

2. **Given** multiple users in different timezones, **When** Damascus midnight occurs, **Then** ALL users quotas reset regardless of their local time

---

### User Story 5 - Purchase Extra Generations (Priority: P2)

A user who exhausted quota can purchase additional generations via in-app purchase. Purchased generations stack with daily quota and never expire. Payment integration is deferred to SPEC-009, but the UI and database schema are prepared.

**Why this priority**: Monetization opportunity and user satisfaction. Some users have urgent needs that cannot wait until tomorrow.

**Independent Test**: Exhaust quota, click Purchase, select pack, verify UI shows payment flow (deferred to SPEC-009).

**Acceptance Scenarios**:

1. **Given** user exhausted quota and clicks Purchase, **When** they select a pack ($0.50/5, $1/12, $3/40), **Then** a payment interface is shown (implementation deferred to SPEC-009)

2. **Given** payment succeeds (simulated), **When** purchase completes, **Then** purchased count is added to user available quota and stored in user_quota_tracking table

3. **Given** user has purchased extra generations, **When** daily quota resets, **Then** purchased count remains unchanged (only daily_used resets to 0)

---

### User Story 6 - Copy Generated Cover Letter (Priority: P3)

A user wants to copy the generated cover letter text to use in external applications (email, LinkedIn, job portals). They click [Copy Text] and the full text is displayed in a copyable format.

**Why this priority**: Users need to actually use the cover letter outside the bot. This enables the final step of the workflow.

**Independent Test**: Generate cover letter, click Copy Text, verify text is displayed in monospace/code block for easy copying.

**Acceptance Scenarios**:

1. **Given** a cover letter is displayed, **When** user clicks [Copy Text], **Then** the full text is sent in a new message formatted as monospace/code block for easy selection and copying

---

### User Story 7 - Handle Insufficient CV Data Gracefully (Priority: P3)

When a user CV lacks sufficient skills or experience data, the system warns them before generating and offers to continue anyway or improve CV first.

**Why this priority**: User education and quality control. Better to warn users upfront than surprise them with generic content.

**Independent Test**: Upload minimal CV, attempt generation, verify warning and choice prompt.

**Acceptance Scenarios**:

1. **Given** user CV has completeness score less than 50% or fewer than 3 skills, **When** they try to generate, **Then** warning is displayed with [Generate Anyway] and [Edit CV First] options

2. **Given** user chooses [Generate Anyway], **When** generation completes, **Then** cover letter includes disclaimer: "Generated with limited CV data"

---

### Edge Cases

- What happens when the user has no CV uploaded at all? → System blocks generation and redirects to /my_cvs to upload CV first
- How does the system handle a job with completely missing description?
- What if the Gemini API returns an empty response? → Display error with [Retry] button, do not count against quota
- How is the system affected during Damascus DST transitions? → Uses zoneinfo.ZoneInfo("Asia/Damascus") which handles DST automatically: Spring forward (last Friday in March at 3:00:01 AM UTC+3), Fall back (last Friday in October at 2:00:00 AM UTC+2). Reset check runs at 3:00:01 AM Damascus time to account for both transitions.
- What if the user has an active subscription but the tier changes mid-day?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow cover letter generation from job notifications via [Cover Letter] button
- **FR-002**: System MUST allow cover letter generation from /my_jobs saved jobs via [Cover Letter] button
- **FR-003**: System MUST enforce daily quota limits: Free=3, Basic=15, Pro=50 cover letters per day
- **FR-004**: System MUST track quota in Damascus timezone (Asia/Damascus) with midnight (00:00) reset
- **FR-005**: System MUST count each generation attempt (including regenerations) against daily quota
- **FR-006**: System MUST NOT increment quota on API failure or user cancellation
- **FR-007**: System MUST display customization form before generation with options: Tone, Length, Focus, Language
- **FR-008**: System MUST use default values: Tone=Professional, Length=Medium, Focus=All, Language=Arabic
- **FR-009**: System MUST validate user has available quota (daily_used less than daily_limit + purchased_extra) before generation
- **FR-010**: System MUST display purchase/wait/upgrade options when quota exhausted
- **FR-011**: System MUST use Gemini Flash for Free and Basic tiers
- **FR-012**: System MUST use Gemini Pro for Pro tier
- **FR-013**: System MUST construct prompt with job title, company, location, job description, CV content, user name, and customization parameters
- **FR-014**: System MUST generate cover letter within 10 seconds (p95 latency)
- **FR-015**: System MUST store prompt template in configurable location for easy editing without code changes
- **FR-016**: System MUST save all generated cover letters to cover_letters table with all required metadata
- **FR-017**: System MUST track quota usage in user_quota_tracking table
- **FR-018**: System MUST increment generation_count when user regenerates for same job
- **FR-019**: System MUST mark generated cover letters with counted_in_quota=true for normal generations
- **FR-020**: System MUST offer purchase packs: $0.50=5, $1.00=12, $3.00=40 extra generations
- **FR-021**: System MUST add purchased count to user purchased_extra field and persist indefinitely
- **FR-022**: System MUST NOT reset purchased_extra on daily quota reset (only daily_used resets)
- **FR-023**: System MUST reset quota counter to 0 and apply new tier limit when user upgrades subscription
- **FR-024**: Payment processing is DEFERRED to SPEC-009 - purchase buttons show "Coming soon" message
- **FR-025**: System MUST display generation status "Generating..." during API call
- **FR-026**: System MUST display generated cover letter in chat with [Regenerate] and [Copy Text] buttons
- **FR-027**: System MUST format Copy Text output as monospace/code block for easy selection
- **FR-028**: System MUST show countdown to midnight Damascus time when user exhausts quota
- **FR-029**: System MUST display "An error occurred. Please try again." with [Retry] button on API failure
- **FR-030**: System MUST warn users with CV completeness less than 50% or fewer than 3 skills before generating
- **FR-031**: System MUST offer [Generate Anyway] and [Edit CV First] options on CV quality warning
- **FR-032**: System MUST add disclaimer "Generated with limited CV data" when user chooses Generate Anyway
- **FR-033**: System MUST generate cover letter even if job description is fewer than 50 words, using job title and available info
- **FR-034**: System MUST require user to have uploaded CV before generating cover letter; if no CV exists, display message with redirect to /my_cvs
- **FR-035**: System MUST NOT count failed generation attempts against user quota; only successful completions count
- **FR-036**: System MUST validate prompt template on service startup for placeholders ({job_title}, {company}, {cv_content}); fallback to embedded default and log to Sentry if invalid.
- **FR-037**: System MUST prevent concurrent generation by locking user state; ignore subsequent [Generate] clicks with "Already generating..." message.
- **FR-038**: System MUST limit regeneration to 10 per job; regenerate updates existing CoverLetter in-place. Disable [Regenerate] button and show "Maximum reached" message after limit.
- **FR-039**: System MUST format bilingual letters with Arabic first, separator "━━━━━━━", then English.
- **FR-040**: System MUST log errors to Sentry and track basic operation counts (generation attempts, successes, failures) to metrics service; no PII in logs.

### Key Entities *(include if feature involves data)*

- **CoverLetter**: Represents a generated cover letter for a specific job application. Contains user_id, job_id, cv_id, content (full text), tone, length, focus_area, language, ai_model, generation_count, generated_at, and counted_in_quota flag.

- **UserQuotaTracking**: Tracks daily quota usage per user. Contains user_id, date (in Damascus timezone), daily_used count, purchased_extra count (never expires), and tier_at_generation for analytics.

- **SubscriptionTier**: Defines the tier limits. Contains tier_name (Free/Basic/Pro) and daily_limit (3/15/50).

- **PurchasePack**: Defines available purchase options. Contains pack_id, price, and generations_included.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cover letter generation completes within 10 seconds (p95 latency)
- **SC-002**: 95% of generations succeed on first attempt (excluding intentional API errors)
- **SC-003**: Daily quota resets within 60 seconds of midnight Damascus time
- **SC-004**: Generated cover letters are 200-600 words based on Length parameter
- **SC-005**: Quota tracking is accurate with zero double-counting or missed increments
- **SC-006**: Purchased extra generations persist correctly across daily resets
- **SC-007**: Timezone conversion to Damascus time is accurate year-round (including DST changes)
- **SC-008**: System achieves 90% success rate after Gemini API retry with exponential backoff (up to 3 attempts).

## Assumptions

- SPEC-007 (Bot Handlers) is complete and operational - provides the UI buttons and message handling
- SPEC-004 (CV Upload) provides user_cvs.parsed_text for CV content
- SPEC-005 (Job Matching) provides jobs.description for job details
- Gemini API key is configured in settings and accessible
- Prompt template will be stored in a configurable file location
- Payment processing will be added in a future spec (SPEC-009)
- All user-facing messages are bilingual (Arabic + English)
- Regeneration creates a NEW cover_letters record (not update existing)
- Admin/test generations can bypass quota by setting counted_in_quota=false
- CV data is processed with user consent; CV content sent to Gemini for generation but stored only as needed with user awareness in UI