# Data Model: Bot Handlers & UX Flow

**Feature Branch**: `007-bot-handlers-ux`  
**Phase**: 1 - Design  
**Date**: 2026-04-16

## Entities

### Language (NEW TABLE)

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | INT | PK | Primary key (1=Arabic, 2=English) |
| code | VARCHAR(2) | NOT NULL, UNIQUE | Language code ('ar', 'en') |
| name | VARCHAR(50) | NOT NULL | Language name ('Arabic', 'English') |

**Seed Data**: (1, 'ar', 'Arabic'), (2, 'en', 'English')

---

### UserPreferences (UPDATE EXISTING)

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK → users.id, NOT NULL, UNIQUE | Owner user |
| similarity_threshold | FLOAT | 60%-100%, default 80% | Match threshold |
| notification_enabled | BOOLEAN | NOT NULL, DEFAULT TRUE | Notification toggle |

---

### SavedJob (NEW TABLE)

| Column | Type | Constraints | Description |
|--------|------|--------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK → users.id, NOT NULL, ON DELETE CASCADE | Owner user |
| job_id | UUID | FK → jobs.id, NOT NULL, ON DELETE SET NULL | Saved job |
| saved_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | When saved |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Record creation |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update |

**Unique Constraint**: (user_id, job_id) - one save per user-job pair

**Indexes**: idx_saved_jobs_user_id, idx_saved_jobs_job_id

---

### BotSession (Redis-backed, NEW)

| Field | Type | Description |
|-------|------|-------------|
| user_id | int | Telegram user ID |
| current_state | str | Current FSM state name |
| last_activity | datetime | Last interaction timestamp |
| flow_data | dict | State-specific data (e.g., upload step) |
| created_at | datetime | Session start |
| expires_at | datetime | Session expiry (last_activity + 10 min) |

**Key Format**: `bot_session:{user_id}`  
**TTL**: 600 seconds (10 minutes)

**Error Handling**: If Redis is unavailable, the system should gracefully degrade to stateless mode (re-prompt user, log error to Sentry) and MUST NOT block core bot functionality.

---

### JobMatch (UPDATE EXISTING)

| Column | Type | Changes |
|--------|------|---------|
| is_dismissed | BOOLEAN | NEW - Default FALSE, NOT NULL |

---

## Migrations Required

### Migration 008: Add is_dismissed to job_matches

- **File**: `migrations/versions/008_add_is_dismissed_to_job_matches.py`
- **Operation**: `ALTER TABLE job_matches ADD COLUMN is_dismissed BOOLEAN NOT NULL DEFAULT FALSE`
- **Purpose**: Track dismissed job matches for US3 and US4 functionality

### Migration 009: Create saved_jobs table

- **File**: `migrations/versions/009_create_saved_jobs_table.py`
- **Operation**: `CREATE TABLE saved_jobs (...)`
- **Purpose**: Track user-saved jobs for US3 and US4 functionality

---

## FSM States

### CVUploadState

```
CVUploadState:
  - waiting_for_file: User triggered /upload_cv, awaiting file
  - processing_file: File received, validating and processing
  - confirming_replace: Free/Basic user with existing CV, awaiting Yes/No
```

### SettingsState

```
SettingsState:
  - threshold_editing: User adjusting similarity threshold
```

### MyJobsState

```
MyJobsState:
  - browsing: User viewing job list with filters
```

### FSM State Transitions

```
CVUploadState:
  None -> waiting_for_file (user triggers /upload_cv)
  waiting_for_file -> processing_file (file received, validating)
  processing_file -> confirming_replace (Free/Basic with existing active CV)
  processing_file -> success (no replacement needed)
  confirming_replace -> processing_file (user confirms Yes)
  confirming_replace -> waiting_for_file (user confirms No)
  Any state -> None (/cancel, session expires, flow completes)

SettingsState:
  None -> threshold_editing (user edits threshold)
  threshold_editing -> None (saved, cancelled, session expires)
```

---

## Message Templates (Bilingual Arabic + English)

### Welcome Message
```
مرحباً بك في JobPulse! 👋
(Welcome to JobPulse!)

اسمك: {first_name}
خطتك: {tier}

ابدأ الآن! /start
```

### Main Menu
```
🔘 الرئيسية (Main Menu)
```

Buttons: Upload CV | My Jobs | Invite Friends | Settings

### Job Notification
```
🎯 {job_title}
🏢 {company}
📍 {location}
💰 {salary}
📊 نسبة التطابق: {match_percent}% (Match: {match_percent}%)

{description_preview}

[Save] [Full Details] [Cover Letter] [Dismiss]
```

### Settings Display
```
⚙️ الإعدادات (Settings)

• نسبة التطابق: {threshold}% (Threshold: {threshold}%)
• الإشعارات: {on/off} (Notifications: {on/off})
• اللغة: {language} (Language)
• الخطة: {tier} (Plan)
• رمز الإحالة: {referral_code} (Referral Code)

[Edit Threshold] [Toggle Notifications] [Upgrade Plan]
```

### Error Messages
- Format not supported: "التنسيق غير مدعوم. أرسل PDF، DOCX، أو TXT. (Format not supported. Send PDF, DOCX, or TXT.)"
- File too large: "الملف كبير جداً (الأقصى 5MB). (File too large, max 5MB.)"
- Generic error: "حدث خطأ. حاول لاحقاً. (An error occurred. Please try again.)"
- Already saved: "تم حفظه بالفعل (Already saved)"

---

## Callback Data Patterns

| Action | Format | Example |
|--------|--------|---------|
| Save job | `save_job:{job_id}` | `save_job:abc123` |
| Unsave job | `unsave_job:{job_id}` | `unsave_job:abc123` |
| View full details | `job_details:{job_id}` | `job_details:abc123` |
| Dismiss match | `dismiss_match:{match_id}` | `dismiss_match:xyz789` |
| Cover letter | `cover_letter:{job_id}` | `cover_letter:abc123` |
| Pagination next | `jobs_page:{view}:{page}` | `jobs_page:saved:2` |
| Pagination prev | `jobs_page:{view}:{page}` | `jobs_page:saved:1` |
| Filter similarity | `filter_sim:{value}` | `filter_sim:80` |
| Filter date | `filter_date:{value}` | `filter_date:7` |
| Edit threshold | `edit_threshold:start` | `edit_threshold:start` |
| Toggle notifications | `toggle_notifications` | `toggle_notifications` |
| View CV details | `cv_details:{cv_id}` | `cv_details:cv123` |
| Delete CV | `delete_cv:{cv_id}` | `delete_cv:cv123` |
| Confirm replace | `confirm_replace:{yes/no}` | `confirm_replace:yes` |

---

## API Contracts (Summary)

### Bot Commands
- `/start` - Register or welcome user
- `/help` - Show all commands
- `/upload_cv` - Start CV upload flow
- `/my_cvs` - List user CVs with delete option
- `/my_jobs` - Browse saved/notified/dismissed jobs
- `/settings` - View and edit preferences
- `/invite` - Open referral interface
- `/subscribe` - View subscription tiers
- `/cancel` - Cancel current operation

### Callback Queries
- All callback actions defined in table above
- All callbacks must verify `callback.from_user.id == message.from_user.id`

### Inline Keyboards
- Max 3 buttons per row
- Use `InlineKeyboardBuilder` for complex layouts
- Pagination: Prev | Page X/Y | Next
- View selector: Saved | All Notified | Dismissed