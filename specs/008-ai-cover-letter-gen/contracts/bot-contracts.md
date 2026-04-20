# Contracts: AI Cover Letter Generation

**Feature**: 008-ai-cover-letter-gen  
**Date**: 2026-04-19

## Telegram Bot Contracts

### Callback Data Patterns

All callback data follows aiogram 3.x conventions with data serialization.

#### Cover Letter Generation Trigger

```
cover_letter:start:{job_id}
```

**Parameters**:
- `job_id`: UUID of the job to generate cover letter for

#### Cover Letter Actions

```
cover_letter:regenerate:{cover_letter_id}
cover_letter:copy:{cover_letter_id}
cover_letter:retry:{job_id}
```

**Parameters**:
- `cover_letter_id`: UUID of existing cover letter
- `job_id`: UUID of job for retry

#### Quota Exhaustion Options

```
cover_letter:purchase:{pack_id}
cover_letter:wait
cover_letter:upgrade
```

**Parameters**:
- `pack_id`: small | medium | large

---

### Keyboard Layouts

#### Customization Form Keyboard

| Row | Buttons |
|-----|---------|
| 1 | Tone: [Formal] [Casual] [Professional] |
| 2 | Length: [Short] [Medium] [Long] |
| 3 | Focus: [Skills] [Experience] [Education] [All] |
| 4 | Language: [Arabic] [English] [Bilingual] |
| 5 | [Generate Cover Letter] |

#### Cover Letter Action Keyboard

| Row | Buttons |
|-----|---------|
| 1 | [Regenerate] [Copy Text] |

#### Quota Exhausted Keyboard

| Row | Buttons |
|-----|---------|
| 1 | [Wait for Reset] [Purchase Extra] |
| 2 | [Upgrade Subscription] (if not Pro) |

---

### State Machine (FSM)

#### CoverLetterGeneration

```
states:
  - cover_letter_job_selected    # Job selected, ready to check quota
  - cover_letter_customizing     # User selecting options
  - cover_letter_generating      # API call in progress
  - cover_letter_displayed      # Cover letter shown
  - cover_letter_quota_exhausted # Quota limit reached

transitions:
  cover_letter_job_selected -> cover_letter_customizing:
    - Check quota available
    - Check CV exists
  cover_letter_customizing -> cover_letter_generating:
    - User confirms options
  cover_letter_generating -> cover_letter_displayed:
    - API returns success
  cover_letter_generating -> cover_letter_quota_exhausted:
    - Quota check fails
  cover_letter_displayed -> cover_letter_customizing:
    - User clicks regenerate
```

---

### Message Templates

#### Generation Status
```
⏳ جارٍ التوليد...
Generating your cover letter...
```

#### Success Message
```
📝 Your Cover Letter

{cover_letter_content}

━━━━━━━━━━━━━━━━━━━━━━━━
[Regenerate]  [Copy Text]
```

#### Error Message
```
❌ An error occurred. Please try again.

[Retry]
```

#### Quota Exhausted Message
```
🚫 Daily Limit Reached

You have used all your cover letter generations today.

⏰ Next reset: {countdown_to_midnight_damascus}

[Wait for Tomorrow] [Purchase Extra] [Upgrade]
```

#### CV Warning Message
```
⚠️ Your CV contains limited information.
The cover letter may be generic.

[Generate Anyway] [Edit CV First]
```

---

### AI Prompt Contract

Prompt template stored at: `config/prompts/cover_letter_prompt.txt`

Required placeholders:
- `{job_title}` - Job position
- `{company}` - Company name
- `{location}` - Job location
- `{job_description}` - Full job description text
- `{cv_content}` - User's CV parsed text
- `{user_name}` - User's name from profile
- `{tone}` - Selected tone (formal/casual/professional)
- `{length}` - Selected length (short/medium/long)
- `{focus}` - Selected focus (skills/experience/education/all)
- `{language}` - Selected language (arabic/english/bilingual)

Output: Plain text cover letter, {length} words (200/400/600)