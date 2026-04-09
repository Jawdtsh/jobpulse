# Feature Specification: CV Upload & Evaluation

**Feature Branch**: `004-cv-upload-evaluation`  
**Created**: 2026-04-08  
**Status**: Draft  
**Input**: User description: "CV Upload & Evaluation - Users upload CVs via Telegram, system parses multiple formats, evaluates quality using AI, calculates completeness score, generates vector embeddings, and stores them encrypted"

## Clarifications

### Session 2026-04-08

- Q: How is monthly quota reset handled? → A: Calendar month (reset on 1st of each month)
- Q: What are the possible states for a CV throughout its lifecycle? → A: pending, active, inactive, deleted
- Q: How should the system handle encryption key rotation? → A: Re-encrypt all CVs with new key on rotation
- Q: When a user deletes their CV, should it be soft delete or hard delete? → A: Soft delete (mark as deleted, retain data)
- Q: How should the system handle empty/near-empty extracted text (less than 100 chars)? → A: Reject with error asking user to provide complete CV

### Session 2026-04-09

- Q: Should the system trigger re-matching when a user uploads a new CV or updates an existing one? → A: Yes - when a CV becomes active (new upload or activation), trigger background job to re-run matching against recent jobs (last 7 days from jobs table). This ensures users don't miss opportunities posted while their CV was inactive.

- Q: What is the exact re-encryption strategy on encryption key rotation? → A: On ENCRYPTION_KEY change detection (compare hash of current key vs stored hash in Redis): (1) Acquire distributed lock `cv:reencryption:lock` with 1-hour TTL, (2) Iterate all user_cvs records in batches of 100, (3) For each: decrypt with old key → re-encrypt with new key → update database, (4) Log progress every 100 records, (5) Release lock on completion. Admin must trigger via CLI command `/admin reencrypt-cvs --old-key-file=/path/to/old.key`.

- Q: How should the system handle concurrent CV uploads from the same user? → A: Use database-level row locking: before creating new CV record, execute `SELECT FOR UPDATE` on user row to prevent race conditions. If upload is in progress (checked via Redis key `cv:upload:{user_id}` with 60s TTL), reject with "Upload already in progress, please wait." This prevents duplicate CVs and quota bypass.
## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload CV via Telegram (Priority: P1)

A user sends their CV file (PDF, DOCX, or TXT) as an attachment to the Telegram bot to enable job matching.

**Why this priority**: This is the core entry point for the entire CV system. Without CV upload, no job matching can occur.

**Independent Test**: Can be tested by sending various file formats through the bot and verifying text extraction and storage. Delivers value: User can now have their CV in the system for matching.

**Acceptance Scenarios**:

1. **Given** the user has a valid PDF file under 5MB, **When** they send it to the bot, **Then** the text is extracted and stored successfully
2. **Given** the user has a DOCX file under 5MB, **When** they send it to the bot, **Then** the text is extracted and stored successfully
3. **Given** the user has a TXT file under 5MB, **When** they send it to the bot, **Then** the content is stored successfully
4. **Given** the user sends a file larger than 5MB, **When** they attempt upload, **Then** they receive an error message indicating the size limit
5. **Given** the user sends an unsupported format (e.g., JPG, PNG), **When** they attempt upload, **Then** they receive an error message listing supported formats
6. **Given** the text extraction fails (corrupted file), **When** they upload, **Then** they receive a clear error message with guidance

---

### User Story 2 - AI-Powered CV Evaluation (Priority: P1)

After uploading their CV, the system analyzes it using AI to provide quality assessment and improvement suggestions.

**Why this priority**: Provides users with actionable feedback to improve their CV, increasing their chances of landing interviews.

**Independent Test**: Can be tested by uploading a CV and verifying AI evaluation returns structured results including skills, experience summary, and suggestions. Adds value: User understands CV quality and improvement areas.

**Acceptance Scenarios**:

1. **Given** a user uploads a valid CV, **When** the AI evaluates it, **Then** it returns skills list, experience summary, and improvement suggestions
2. **Given** the evaluation completes, **When** the user views the results, **Then** they see a readable format in their Telegram chat
3. **Given** the evaluation is complete, **When** the user views their results, **Then** the evaluation is persisted for future reference
4. **Given** a user has exceeded their evaluation quota, **When** they attempt to upload, **Then** they see a prompt to upgrade their subscription

---

### User Story 3 - CV Completeness Score (Priority: P1)

The system calculates and displays a completeness score showing what sections are missing from the user's CV.

**Why this priority**: Helps users understand what their CV lacks and provides motivation to improve. The 40% threshold affects referral eligibility.

**Independent Test**: Can be tested by uploading CVs with varying levels of detail and verifying the score calculation and breakdown. Delivers value: User knows exactly what to add to improve their CV.

**Acceptance Scenarios**:

1. **Given** a CV contains all required sections, **When** completeness is calculated, **Then** the score reflects the weighted presence of contact (20%), skills (25%), experience (30%), education (15%), summary (10%)
2. **Given** a CV is missing sections, **When** the user views completeness, **Then** they see a breakdown showing what is missing
3. **Given** a CV scores below 40%, **When** the user views results, **Then** they receive a warning about referral ineligibility

---

### User Story 4 - Generate CV Embeddings for Matching (Priority: P2)

The system generates 768-dimensional vector embeddings from CV text to enable semantic job matching.

**Why this priority**: Enables the core matching functionality - without embeddings, jobs cannot be matched semantically to CVs.

**Independent Test**: Can be tested by uploading a CV and verifying a 768-dimension vector is stored. Embedding failure should not block CV upload.

**Acceptance Scenarios**:

1. **Given** a user uploads a valid CV, **When** embedding is generated, **Then** a 768-dimension vector is stored in the database
2. **Given** embedding generation fails, **When** the user uploads, **Then** the upload succeeds with a null vector (no blocking)

---

### User Story 5 - Encrypted CV Storage (Priority: P1)

The system encrypts CV content before storage to protect user privacy.

**Why this priority**: CVs contain sensitive personal information. Encryption is required for data protection and compliance.

**Independent Test**: Can be tested by uploading a CV, retrieving it, and verifying the decrypted content matches the original. Ensures privacy: Only the user can read their CV.

**Acceptance Scenarios**:

1. **Given** a user uploads a CV, **When** it is stored, **Then** the content is encrypted using the system's encryption key
2. **Given** encrypted content exists, **When** it is retrieved, **Then** it decrypts correctly to match the original text

---

### User Story 6 - Subscription Tier CV Limits (Priority: P1)

The system enforces CV count limits based on subscription tier: Free/Basic = 1 CV, Pro = 2 CVs.

**Why this priority**: Enforces business model - CV limits are part of the subscription tier benefits.

**Independent Test**: Can be tested by creating users at different tiers and attempting to exceed their CV limit. Enforces business rules: Tier restrictions are respected.

**Acceptance Scenarios**:

1. **Given** a Free tier user has 1 active CV, **When** they attempt to upload another, **Then** they receive an error with upgrade prompt
2. **Given** a Basic tier user has 1 active CV, **When** they attempt to upload another, **Then** they receive an error with upgrade prompt
3. **Given** a Pro tier user has 2 active CVs, **When** they attempt to upload a third, **Then** they receive an error with upgrade prompt
4. **Given** a user at any tier has reached their limit, **When** they choose to replace, **Then** the old CV is marked inactive and new one becomes active

---

### User Story 7 - Manage Uploaded CVs (Priority: P2)

Users can list, activate, deactivate, and delete their uploaded CVs.

**Why this priority**: Gives users control over their CVs - they may have multiple versions and want to choose which is active for matching.

**Independent Test**: Can be tested by creating multiple CVs and exercising management commands. Delivers value: User has full control over their CV portfolio.

**Acceptance Scenarios**:

1. **Given** a user has multiple CVs, **When** they request a list, **Then** they see all their CVs with status indicators
2. **Given** a user has an inactive CV, **When** they activate it, **Then** it becomes the active CV for matching
3. **Given** a user has an active CV, **When** they deactivate it, **Then** it is excluded from matching
4. **Given** a user deletes a CV, **When** they request matching, **Then** the deleted CV is not used

---

### User Story 8 - CV Evaluation Quota Tracking (Priority: P2)

The system tracks monthly CV evaluation usage and enforces tier-based quotas.

**Why this priority**: Controls AI costs - evaluation quota is a tier benefit that must be enforced.

**Independent Test**: Can be tested by making multiple evaluations and verifying quota enforcement at each tier. Enforces business model: Quotas are respected.

**Acceptance Scenarios**:

1. **Given** a Free tier user makes an evaluation, **When** they check their quota, **Then** they have 1 remaining (at registration)
2. **Given** a Basic tier user makes evaluations, **When** they reach 5 in a month, **Then** further attempts show upgrade prompt
3. **Given** a Pro tier user makes evaluations, **When** they reach 10 in a month, **Then** further attempts show upgrade prompt

---

### Edge Cases

- What happens when the user sends a CV with no text content (blank file)?
- How does the system handle extremely long CVs (close to 5MB with extensive text)?
- What occurs when AI evaluation times out or returns malformed JSON?
- How is the monthly quota reset handled (calendar month vs rolling 30 days)?
- What happens if encryption key is changed - can old CVs still be decrypted? → Re-encrypt all CVs with new key on rotation

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept CV uploads via Telegram bot as file attachments
- **FR-002**: System MUST validate file size does not exceed 5MB
- **FR-003**: System MUST validate file format is PDF, DOCX, or TXT only
- **FR-004**: System MUST extract text from PDF files
- **FR-005**: System MUST extract text from DOCX files
- **FR-006**: System MUST store plain text files directly
- **FR-007**: System MUST provide clear error messages when text extraction fails
- **FR-007a**: System MUST reject CV uploads with empty or near-empty text (less than 100 characters) with clear guidance
- **FR-008**: System MUST evaluate uploaded CVs using AI to extract skills, experience summary, and provide improvement suggestions
- **FR-009**: System MUST display evaluation results in a readable format via Telegram
- **FR-010**: System MUST persist CV evaluations in the database
- **FR-011**: System MUST calculate completeness score as a percentage (0-100%)
- **FR-012**: System MUST calculate completeness using weighted scoring: contact (20%), skills (25%), experience (30%), education (15%), summary (10%)
- **FR-013**: System MUST display missing sections to users
- **FR-014**: System MUST warn users when completeness is below 40% (referral ineligibility)
- **FR-015**: System MUST generate 768-dimensional vector embeddings from CV text
- **FR-016**: System MUST store embeddings in the user_cvs table
- **FR-017**: System MUST NOT block CV upload when embedding generation fails (log error, store null)
- **FR-018**: System MUST encrypt CV content before database storage
- **FR-019**: System MUST use Fernet encryption with configured key
- **FR-020**: System MUST correctly decrypt CV content when retrieved
- **FR-021**: System MUST enforce CV count limits: Free=1, Basic=1, Pro=2 active CVs
- **FR-022**: System MUST display upgrade prompt when user exceeds CV limit
- **FR-023**: System MUST allow users to replace existing CV (mark old inactive, create new)
- **FR-024**: System MUST allow users to list all their CVs
- **FR-025**: System MUST allow users to activate/deactivate CVs
- **FR-026**: System MUST allow users to delete CVs (soft delete - mark as deleted, retain data)
- **FR-027**: System MUST use only active CVs for job matching
- **FR-028**: System MUST track CV evaluation usage per user monthly
- **FR-029**: System MUST enforce evaluation quotas: Free=1/month, Basic=5/month, Pro=10/month
- **FR-030**: System MUST display upgrade prompt when evaluation quota exceeded
- **FR-031**: System MUST define custom exceptions: CVFileSizeExceededError CVFormatNotSupportedError, CVTextExtractionError, CVQuotaExceededError, CVLimitExceededError
- **FR-032**: System MUST log all errors with context (user_id, cv_id, file_size, file_format) for debugging
- **FR-033**: System MUST support encryption key rotation by re-encrypting all existing CV content with new key when ENCRYPTION_KEY changes in settings

### Key Entities *(include if feature involves data)*

- **CV**: Represents a user's uploaded resume. States: pending → active/inactive → deleted. Contains: extracted text (encrypted), evaluation results, embedding vector, and metadata (created, is_active, etc.)
- **User**: Contains subscription tier information that determines CV and evaluation limits
- **CV Evaluation**: Contains AI-generated assessment (skills, experience, completeness score, suggestions)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can upload CVs in PDF, DOCX, or TXT format under 5MB in under 30 seconds
- **SC-002**: 95% of valid CV uploads result in successful text extraction
- **SC-003**: CV evaluations return structured results (skills, experience, suggestions) within 10 seconds
- **SC-004**: Users with CV completeness below 40% receive clear warning about referral ineligibility
- **SC-005**: Vector embeddings are generated at 768 dimensions for all successful extractions
- **SC-006**: Encrypted CVs decrypt correctly to match original content (100% accuracy)
- **SC-007**: Subscription tier limits are enforced 100% accurately (no bypass possible)
- **SC-008**: Users can manage (list, activate, deactivate, delete) their CVs through the bot

## Assumptions

- Users have Telegram installed and can send file attachments
- Text extraction libraries (PDF, DOCX) can handle common document formats
- AI evaluation service is available and responds within acceptable time
- Encryption key is properly configured and available at runtime
- Database schema from SPEC-001 includes user_cvs table with required columns
- Subscription tier information is available from existing user records
- Monthly quota resets at the beginning of each calendar month (1st day)
- Job matching system will use active CVs with valid embeddings
- Encryption key rotation involves re-encrypting all stored CV content