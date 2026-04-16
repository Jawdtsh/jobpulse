# Feature Specification: Bot Handlers & UX Flow

**Feature Branch**: `007-bot-handlers-ux`
**Created**: 2026-04-13
**Status**: Draft
**Input**: User description: "Build a complete Telegram bot user interface that enables users to register, upload CVs, receive job match notifications, manage saved jobs, configure preferences, view subscription plans, and handle errors gracefully."

## Clarifications

### Session 2026-04-13

- Q: Should CV deletion capability be in scope for this spec? → A: Yes — CV deletion is in scope; add CV deletion capability (e.g., /my_cvs command with delete button)
- Q: What is the BotSession inactivity timeout before expiry? → A: 10 minutes of inactivity — session expires, user returns to main menu
- Q: Should users be able to unsave/remove a previously saved job? → A: Yes — add Unsave/Remove button on saved job cards
- Q: What does Dismiss suppress — the exact match, the same job, or the same company? → A: Exact match only — dismiss hides only the specific job match record
- Q: What are the reliability and availability requirements for this bot system? → A: Standard — 99% uptime, 24hr recovery, basic error logging only
- Q: What observability requirements should be implemented for debugging and monitoring? → A: Standard — Error logs + structured request logging + basic metrics (response time, error rate) + Sentry for exceptions
- Q: How should the system handle concurrent user actions that could conflict (e.g., user deletes CV while job matching is processing that CV)? → A: Last-write-wins — Most recent action takes precedence silently; matching jobs check if CV still exists before sending notifications
- Q: What scaling approach should be planned for future growth beyond 10k users? → A: Horizontal-ready — Stateless design with sessions in Redis, prepared for multiple instances

## User Scenarios & Testing *(mandatory)*

### User Story 1 - User Registration & Onboarding (Priority: P1)

A new user sends the /start command to the bot for the first time. The system automatically creates their user record, detects their preferred language from their Telegram settings, generates a unique referral code, and displays a welcome message with four main menu buttons: Upload CV, My Jobs, Invite Friends, and Settings. If the user already exists, the welcome message is simply re-displayed without creating a duplicate record. The /help command shows a list of all available commands and their descriptions.

**Why this priority**: Registration is the gateway to all other features. Without it, no user can access any functionality. It must work flawlessly and immediately to prevent drop-off.

**Independent Test**: Can be fully tested by sending /start to the bot and verifying the welcome message, user record creation, language detection, and referral code generation. Delivers immediate value by onboarding the user.

**Acceptance Scenarios**:

1. **Given** a user has never interacted with the bot, **When** they send /start, **Then** a new user record is created with their Telegram ID, username, first name, last name, auto-detected language, Free subscription tier, and a unique 12-character referral code, and a welcome message with main menu buttons is displayed
2. **Given** a user already exists in the system, **When** they send /start again, **Then** the welcome message is re-displayed without creating a duplicate record (idempotent)
3. **Given** a user sends /start with a referral parameter (e.g., ref_ABC123XYZ), **When** the user record is created, **Then** the referral source is tracked for the referring user
4. **Given** any registered user, **When** they send /help, **Then** a list of all bot commands and their descriptions is displayed

---

### User Story 2 - CV Upload & Evaluation Display (Priority: P1)

A user wants to upload their CV to receive job matches. They trigger the upload flow via the /upload_cv command or the Upload CV button. The bot prompts them to send a file, validates it (PDF, DOCX, or TXT, max 5MB), shows a processing status, and then displays evaluation results including completeness score, extracted skills, and improvement suggestions. For Free/Basic tier users with an existing active CV, a replacement prompt is shown. Pro tier users can have up to 2 active CVs simultaneously.

**Why this priority**: CV upload is the core input that powers the entire job matching pipeline. Without a CV, no matches can be generated.

**Independent Test**: Can be fully tested by uploading a CV file and verifying validation, processing status, evaluation display, and tier-based behavior. Delivers value by showing the user their CV analysis.

**Acceptance Scenarios**:

1. **Given** a user triggers the upload flow, **When** they send a valid file (PDF/DOCX/TXT, ≤5MB), **Then** a processing status message is shown, followed by evaluation results with completeness score, skills list, and improvement suggestions
2. **Given** a user triggers the upload flow, **When** they send an unsupported file format, **Then** an error message "Format not supported. Please send PDF, DOCX, or TXT." is displayed
3. **Given** a user triggers the upload flow, **When** they send a file exceeding 5MB, **Then** an error message "File too large (max 5MB). Please compress or use a smaller file." is displayed
4. **Given** a Free/Basic tier user with an existing active CV, **When** they upload a new CV, **Then** a replacement prompt "Replace existing CV? [Yes] [No]" is displayed
5. **Given** a user with no active CV, **When** they upload a new CV, **Then** the CV is automatically activated
6. **Given** a Pro tier user with fewer than 2 active CVs, **When** they upload a new CV, **Then** the CV is added without a replacement prompt
7. **Given** a Pro tier user with 2 active CVs, **When** they attempt to upload a 3rd CV, **Then** an error message "Pro tier allows 2 CVs. Delete one first." is displayed
8. **Given** a user is in the CV upload flow, **When** they send a non-file message, **Then** the message is ignored and the upload prompt is repeated

---

### User Story 2.1 - CV Deletion & Management (Priority: P1)

A user wants to manage their uploaded CVs, including deleting ones they no longer need. The /my_cvs command displays a list of the user's CVs with status (active/inactive), upload date, and completeness score. Each CV has a Delete button. Deleting a CV removes it from active matching. If the deleted CV was active and another inactive CV exists, the system prompts the user to activate a replacement.

**Why this priority**: Without deletion, Pro users who hit the 2-CV limit are locked out (the error message promises deletion). This is a necessary lifecycle operation.

**Independent Test**: Can be tested by uploading CVs, then using /my_cvs to delete one, verifying it no longer appears and matching stops using it.

**Acceptance Scenarios**:

1. **Given** a user sends /my_cvs, **When** they have one or more CVs, **Then** a list of their CVs is displayed with status, upload date, completeness score, and a Delete button for each
2. **Given** a user clicks Delete on a CV, **When** a confirmation prompt appears and they confirm, **Then** the CV is removed and no longer used for job matching
3. **Given** a user deletes their only active CV, **When** they have another inactive CV, **Then** they are prompted to activate the inactive CV
4. **Given** a user deletes their only active CV, **When** they have no other CVs, **Then** they are informed that job matching will be paused until a new CV is uploaded

---

### User Story 3 - Job Match Notifications (Priority: P1)

When a job matches a user's CV above their similarity threshold, the user receives a rich notification containing job details (title, company, location, salary, match percentage, description preview up to 200 characters) along with action buttons: Save, Full Details, Cover Letter, and Dismiss. For Pro users with multiple active CVs, a single notification shows match scores for each CV.

**Why this priority**: Job notifications are the primary value delivery mechanism. Users signed up to receive relevant job matches — this is the core output of the system.

**Independent Test**: Can be tested by triggering a match notification and verifying content, buttons, and tier-specific behavior. Delivers immediate value by showing matched jobs.

**Acceptance Scenarios**:

1. **Given** a job matches a user's active CV above the similarity threshold, **When** the notification is sent, **Then** it includes job title, company, location, salary range, match percentage, and description preview (first 200 characters), with inline buttons: Save, Full Details, Cover Letter, Dismiss
2. **Given** a user receives a job notification, **When** they click Save, **Then** the job is added to their saved jobs list and a confirmation "Saved! View in /my_jobs" is shown
3. **Given** a user has already saved a job, **When** they click Save on the same job notification again, **Then** a message "Already saved" is displayed without creating a duplicate
4. **Given** a user receives a job notification, **When** they click Full Details, **Then** a new message with the full job description and a link to the source Telegram channel is sent
5. **Given** a user receives a job notification, **When** they click Dismiss, **Then** the match is marked as dismissed (does not block future similar job matches)
6. **Given** a Pro tier user with 2 active CVs both matching a job, **When** the notification is sent, **Then** a single notification shows match scores for both CVs (e.g., "Matches 2 CVs: Backend (87%), Frontend (72%)")
7. **Given** a user has deleted all their CVs, **When** a match would be sent, **Then** the notification is skipped (no active CV)

---

### User Story 4 - Saved Jobs Management (Priority: P2)

A user wants to browse and manage their job matches. The /my_jobs command presents three views: Saved Jobs (default), All Notified, and Dismissed. Each view shows job cards with title, company, match percentage, and relative date. Users can filter by similarity threshold (>80%, >70%, All) and date range (7 days, 14 days, 30 days). Results are paginated at 5 jobs per page with navigation buttons.

**Why this priority**: Once users receive notifications, they need a way to review and organize them. This is the post-notification management layer.

**Independent Test**: Can be tested by saving jobs via notifications, then browsing /my_jobs with different views, filters, and pagination. Delivers value by letting users organize their job search.

**Acceptance Scenarios**:

1. **Given** a user sends /my_jobs, **When** the command is processed, **Then** a view selector is displayed with three options: Saved, All Notified, Dismissed, defaulting to Saved
2. **Given** a user is viewing any job list, **When** jobs exist, **Then** each job card shows title, company, match percentage, relative date (e.g., "3 hours ago"), and inline buttons for View and Cover Letter; in the Saved view, an additional Unsave/Remove button is shown
3. **Given** a user is viewing a job list with more than 5 jobs, **When** the first page is displayed, **Then** a Next button appears; when on subsequent pages, both Prev and Next buttons appear as appropriate
4. **Given** a user is viewing a job list, **When** they apply similarity and date filters, **Then** only matching jobs are shown, and the filters persist across page navigation
5. **Given** a user is viewing a job list, **When** no jobs match the current filters, **Then** an appropriate empty state message is displayed ("No saved jobs yet" or "No jobs match filters")
6. **Given** a user is viewing the Saved view, **When** they click Unsave/Remove on a job card, **Then** the job is removed from their saved jobs list and the list is updated

---

### User Story 5 - Settings & Preferences (Priority: P2)

A user wants to configure their matching preferences and view their account details. The /settings command displays their current similarity threshold (default 80%), notification toggle, auto-detected language (read-only), current subscription tier, and referral code. Users can adjust their similarity threshold (60%-100%), toggle notifications on/off, and view their referral statistics.

**Why this priority**: Settings give users control over their experience. Without threshold control, users may receive too many or too few matches.

**Independent Test**: Can be tested by adjusting settings and verifying persistence. Delivers value by giving users control over match quality.

**Acceptance Scenarios**:

1. **Given** a user sends /settings, **When** the command is processed, **Then** their current similarity threshold, notification status, detected language (read-only), subscription tier, referral code with Copy and Share buttons, and referral statistics are displayed
2. **Given** a user opens threshold editing, **When** they input a value between 60 and 100, **Then** the threshold is saved and a confirmation is displayed
3. **Given** a user opens threshold editing, **When** they input a value outside 60-100, **Then** an error message rejects the input
4. **Given** a user toggles notifications, **When** they switch from enabled to disabled (or vice versa), **Then** the new state is saved and reflected in the settings display
5. **Given** a user views settings, **When** they click Upgrade Plan, **Then** the subscription tiers view is displayed

---

### User Story 6 - Referral System UI (Priority: P2)

A user wants to invite friends to the bot and track their referral rewards. The Invite Friends button from the main menu opens the referral interface with a pre-filled share message containing the user's unique referral link. The settings view shows referral statistics including total invites, successful registrations, rewards earned, and claimed rewards.

**Why this priority**: Referrals drive organic growth. Enabling easy sharing and transparent tracking incentivizes users to invite others.

**Independent Test**: Can be tested by clicking Invite Friends, sharing the link, and verifying referral statistics update. Delivers value through potential rewards.

**Acceptance Scenarios**:

1. **Given** a user clicks Invite Friends from the main menu, **When** the referral interface opens, **Then** a pre-filled message with their unique referral link and benefit description is displayed
2. **Given** a user views the referral interface, **When** they click Share Link, **Then** the platform's native share interface opens with the referral message pre-filled
3. **Given** a user views their referral stats in Settings, **When** the stats are displayed, **Then** total invites sent, successful registrations, rewards earned progress (e.g., "3/5 for free Basic month"), and claimed rewards history are shown
4. **Given** a new user sends /start with a referral parameter, **When** their account is created, **Then** the referral source is tracked and credited to the referring user

---

### User Story 7 - Subscription Plans Preview (Priority: P3)

A user wants to understand the available subscription tiers and their features. The /subscribe command displays three tiers (Free, Basic at $7/month, Pro at $12/month) with a feature comparison showing CV limits, notification delays, and cover letter quotas. The user's current plan is highlighted. Choose Plan buttons are present but payment processing is deferred to a future specification.

**Why this priority**: This is informational only and payment flow is deferred. Users need to see options, but no transaction happens in this spec.

**Independent Test**: Can be tested by viewing /subscribe and verifying all tier details and current plan highlighting. Delivers value by informing upgrade decisions.

**Acceptance Scenarios**:

1. **Given** a user sends /subscribe, **When** the command is processed, **Then** three tiers are displayed: Free, Basic ($7/month), and Pro ($12/month), each showing CV limit, notification delay, and cover letter quota
2. **Given** a user views subscription tiers, **When** their current plan is among the displayed tiers, **Then** it is highlighted with a checkmark badge
3. **Given** a user views subscription tiers, **When** they click Choose Plan, **Then** the button is present (payment flow is deferred)
4. **Given** a user has reached their CV limit or cover letter quota, **When** they attempt the restricted action, **Then** an upgrade prompt appears directing them to /subscribe

---

### User Story 8 - Error Handling & Recovery (Priority: P3)

When errors occur during bot interactions, users receive clear, actionable feedback. A /cancel command stops any in-progress operation and returns to the main menu. Specific validation errors have specific messages. Recoverable errors (like network failures) show a retry button. Unhandled exceptions show a generic error message.

**Why this priority**: Error handling is essential for a polished experience but can be iteratively improved. Core flows must work first.

**Independent Test**: Can be tested by triggering various error conditions and verifying appropriate messages and recovery options. Delivers value by preventing user frustration.

**Acceptance Scenarios**:

1. **Given** a user is in any multi-step flow, **When** they send /cancel, **Then** the current operation is cancelled and the main menu is displayed
2. **Given** an unhandled exception occurs, **When** the error is caught, **Then** a generic error message "حدث خطأ. حاول لاحقاً." is displayed
3. **Given** a recoverable error occurs (e.g., network failure during CV processing), **When** the error is caught, **Then** a retry button is displayed allowing the user to attempt the operation again
4. **Given** a user sends an invalid file format, **When** validation fails, **Then** a specific error message "Format not supported. Please send PDF, DOCX, or TXT." is displayed
5. **Given** a user sends a file exceeding 5MB, **When** validation fails, **Then** a specific error message "File too large (max 5MB). Please compress or use a smaller file." is displayed

---

### Edge Cases

- What happens when a user sends /start multiple times? The welcome message is re-displayed without creating a duplicate record (idempotent).
- What happens when a Pro user tries to upload a 3rd CV? An error message "Pro tier allows 2 CVs. Delete one first." is displayed.
- What happens when a user clicks Save on an already-saved job? A message "Already saved" is displayed without creating a duplicate.
- What happens when a user clicks Unsave on a saved job? The job is removed from the saved jobs list and the list updates immediately.
- What happens when a notification would be sent but the user has no active CV? The notification is skipped entirely.
- What happens when a user changes their similarity threshold while jobs are queued for notification? Only future matches are affected; queued notifications are delivered as originally computed.
- What happens when a user dismisses a job match? Only the exact match record is hidden; the same job posting from a different CV or a new match is not suppressed.
- What happens when the platform's message rate limit is hit? Messages are queued and retried with increasing delays between attempts.
- What happens when a user sends a non-file message during the CV upload flow? The message is ignored and the upload prompt is repeated.
- What happens when a user's language cannot be detected from their Telegram settings? A default language (Arabic) is used.
- What happens when a user starts a multi-step flow (e.g., CV upload) but is inactive for 10 minutes? The session expires automatically and the user is returned to the main menu.
- What happens when a user deletes their CV while a job matching job is processing that CV? The matching job checks if CV still exists before sending notification; if deleted, notification is skipped silently.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a user record upon first /start interaction with telegram ID, username, first name, last name, auto-detected language, Free subscription tier, and unique 12-character referral code
- **FR-002**: System MUST re-display the welcome message without creating duplicate records when an existing user sends /start (idempotent behavior)
- **FR-003**: System MUST auto-detect user language from the user's platform language setting, defaulting to Arabic when not available
- **FR-004**: System MUST display a main menu with four options: Upload CV, My Jobs, Invite Friends, and Settings
- **FR-005**: System MUST respond to /help with a list of all available commands and their descriptions
- **FR-006**: System MUST handle /upload_cv command and the Upload CV button identically, prompting the user to send a file
- **FR-007**: System MUST validate uploaded file type (PDF, DOCX, TXT only) and reject unsupported formats with a specific error message
- **FR-008**: System MUST validate uploaded file size (maximum 5MB) and reject oversized files with a specific error message
- **FR-009**: System MUST display a processing status message while the CV is being evaluated
- **FR-010**: System MUST display evaluation results including completeness percentage, extracted skills list, and improvement suggestions
- **FR-011**: System MUST prompt Free/Basic tier users with an existing active CV whether to replace it before saving a new one
- **FR-012**: System MUST automatically activate a newly uploaded CV when the user has no other active CV
- **FR-013**: System MUST allow Pro tier users to upload a second CV without a replacement prompt
- **FR-014**: System MUST manage CV lifecycle with the following capabilities:
  - a) Provide a `/my_cvs` command that lists all user CVs with status, upload date, completeness score, and a Delete button.
  - b) Allow users to delete a CV with a confirmation prompt.
  - c) Prompt the user to activate an inactive CV when they delete their only active CV and another inactive CV exists.
  - d) Inform the user that job matching is paused when they delete their only CV and no other CVs exist.
- **FR-015**: System MUST send job match notifications including job title, company, location, salary range, match percentage, and description preview (first 200 characters)
- **FR-016**: System MUST include four action buttons in each job notification: Save, Full Details, Cover Letter, and Dismiss
- **FR-017**: System MUST add a job to the user's saved jobs when Save is clicked and display a confirmation message
- **FR-018**: System MUST prevent duplicate saves by checking the saved jobs list before adding, and display "Already saved" if the job was previously saved
- **FR-019**: System MUST send the full job description with a link to the source channel when Full Details is clicked
- **FR-020**: System MUST mark a specific job match record as dismissed when Dismiss is clicked; dismissal only affects the exact match record and does not suppress future notifications for the same job posting from other CVs or new matches
- **FR-021**: System MUST send a single consolidated notification for Pro tier users when a job matches multiple active CVs, showing match scores for each
- **FR-022**: System MUST skip job notifications for users who have no active CVs
- **FR-023**: System MUST display a view selector in /my_jobs with three options: Saved, All Notified, and Dismissed, defaulting to Saved
- **FR-024**: System MUST display job cards showing title, company, match percentage, and relative date with View and Cover Letter action buttons; in the Saved view, an additional Unsave/Remove button must be shown; users MUST be allowed to remove a job from their saved jobs list by clicking Unsave/Remove, updating the list immediately
- **FR-025**: System MUST paginate job lists at 5 jobs per page with Prev and Next navigation buttons when multiple pages exist
- **FR-026**: System MUST provide similarity filters (>80%, >70%, All) and date range filters (7 days, 14 days, 30 days) in the job list view
- **FR-027**: System MUST persist filter selections across page navigation within the same viewing session
- **FR-028**: System MUST display an appropriate empty state message when no jobs match the current view or filter criteria
- **FR-029**: System MUST format dates as relative times with the following exact logic:
  - <60 seconds: "just now"
  - <60 minutes: "X minutes ago"
  - <24 hours: "X hours ago"
  - <7 days: "X days ago"
  - >=7 days: "MMM DD, YYYY" (e.g., "Apr 10, 2026")
- **FR-030**: System MUST display the user's current similarity threshold (default 80%) in settings
- **FR-031**: System MUST allow users to adjust their similarity threshold between 60% and 100% via inline buttons or numeric input
- **FR-032**: System MUST save threshold changes to the user's preferences immediately
- **FR-033**: System MUST display the user's current notification preference (enabled/disabled) in settings
- **FR-034**: System MUST allow users to toggle notifications on or off and persist the change immediately
- **FR-035**: System MUST display the user's auto-detected language as read-only in settings
- **FR-036**: System MUST display the user's current subscription tier in settings
- **FR-037**: System MUST display the user's referral code with Copy and Share buttons in settings
- **FR-038**: System MUST validate threshold input and reject values outside the 60%-100% range with an error message
- **FR-039**: System MUST generate a referral link in the format: https://t.me/{bot_name}?start=ref_{referral_code}
- **FR-040**: System MUST display referral statistics: total invites sent, successful registrations, rewards earned progress, and claimed rewards history
- **FR-041**: System MUST use the platform's native share interface when the user clicks Share Link
- **FR-042**: System MUST track referral source when a new user starts the bot via a referral parameter
- **FR-043**: System MUST display three subscription tiers in /subscribe: Free, Basic ($7/month), and Pro ($12/month), each with CV limit, notification delay, and cover letter quota details
- **FR-044**: System MUST highlight the user's current subscription tier with a visual indicator
- **FR-045**: System MUST show Choose Plan buttons for each subscription tier (payment processing is deferred)
- **FR-046**: System MUST display an upgrade prompt when a user reaches their tier's CV limit or cover letter quota
- **FR-047**: System MUST respond to /cancel by stopping the current operation and returning to the main menu
- **FR-047a**: System MUST automatically expire a BotSession after 10 minutes of user inactivity and return the user to the main menu
- **FR-048**: System MUST display a generic error message for unhandled exceptions
- **FR-049**: System MUST display a retry button for recoverable errors (e.g., network failures)
- **FR-050**: System MUST validate all user inputs including file uploads and text inputs before processing
- **FR-051**: System MUST queue and retry message delivery with increasing delays when the platform's rate limit is reached
- **FR-052**: System MUST validate that inline button callbacks originate from the same user who received the original message
- **FR-053**: System MUST store filter state (view, similarity, date range) in BotSession and persist it across pagination within the same viewing session.
- **FR-054**: System MUST clean up temporary uploaded files when BotSession expires or `/cancel` is triggered during the CV upload flow.

### Key Entities

- **User**: A registered bot user with telegram ID, username, `language_id` (FK -> `languages.id`), subscription tier, referral code, and notification settings. Relates to SavedJobs, UserPreferences, and UserCVs.
- **Language**: A system language dictionary (e.g., Arabic, English) containing `id`, `code`, and `name`. Linked to Users via `language_id`.
- **UserCV**: A CV belonging to a user, with status (active/inactive), upload date, completeness score, extracted skills, and file reference. Can be deleted by the user. Active CVs are used for job matching.
- **SavedJob**: A many-to-many relationship between a user and a job they bookmarked, with a saved timestamp. Uniquely constrained per user-job pair.
- **UserPreferences**: User-configurable settings including similarity threshold (60%-100%, default 80%) and notification toggle (stored as `notification_enabled` boolean column). Belongs to one user.
- **BotSession**: Temporary state tracking a user's position in a multi-step conversation flow (e.g., CV upload, threshold editing). Belongs to one user. Expires after 10 minutes of inactivity or when the flow completes or is cancelled, returning the user to the main menu.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users receive the welcome message and are registered within 2 seconds of sending /start
- **SC-002**: Users see CV evaluation results within 30 seconds of uploading their file
- **SC-003**: Job match notifications are delivered within 30 seconds of the match being identified (adjusted by tier-defined delays)
- **SC-004**: The /my_jobs list loads and displays a page of results within 1 second
- **SC-005**: Filters are applied and results update within 1 second
- **SC-006**: All inline button actions respond within 500ms
- **SC-007**: Error messages are displayed for 100% of validation failures (file format, file size, threshold range)
- **SC-008**: Referral links are generated successfully 100% of the time
- **SC-009**: 90% of new users complete the registration flow (send /start) and see the main menu on their first attempt
- **SC-010**: Saved jobs are persisted and retrievable across bot sessions with no data loss
- **SC-011**: Notification delivery success rate is >=99% (excluding cases where the user blocked the bot).
- **SC-012**: BotSession MUST expire and return the user to the main menu within 5 seconds of reaching the 10-minute inactivity threshold.
- **SC-013**: System MUST maintain 99% uptime with 24-hour recovery capability for critical failures.
- **SC-014**: System MUST log all requests with structured format and track basic metrics (response time, error rate); exceptions MUST be tracked via Sentry.

## Assumptions

- The bot token and configuration are already set up from a previous specification (SPEC-002)
- All database tables from the initial schema specification exist (users, user_cvs, jobs, job_matches)
- The job matching engine from a previous specification is operational and produces matches
- The CV evaluation service from a previous specification is operational and returns completeness, skills, and suggestions
- Cover letter generation buttons are present but the underlying functionality is deferred to a future specification
- Payment processing for subscription upgrades is deferred to a future specification — Choose Plan buttons are non-functional placeholders
- User language auto-detection relies on the user's platform language setting, which may not be available (defaults to Arabic)
- The platform enforces a rate limit of approximately 30 messages per second; the system handles this with queuing and retries
- The bot runs in webhook mode for production deployment
- All user-facing messages use bilingual format (Arabic primary, English secondary) with emoji for visual clarity
- Inline keyboard layouts use a maximum of 3 buttons per row for mobile usability
- A new "saved_jobs" data structure is needed to track user-job bookmark relationships with unique constraints per user-job pair
- Referral rewards follow a 5-invites-per-reward model (e.g., 5 successful referrals earns a free Basic month)
- Users can have a maximum of 1 active CV on Free/Basic tier and 2 active CVs on Pro tier
- The similarity threshold default is 80% and the adjustable range is 60%-100%
- Accepted CV file formats are PDF, DOCX, and TXT with a maximum size of 5MB
- BotSession is stored in Redis (key: `bot_session:{user_id}`, TTL: 600 seconds) with fields: current_state, last_activity, flow_data.
- System is designed for horizontal scaling with stateless application tier and Redis-backed sessions.
