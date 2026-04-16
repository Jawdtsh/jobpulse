# Callback Actions Contract

**Feature Branch**: `007-bot-handlers-ux`  
**Date**: 2026-04-16

## Callback Data Format

All callback data follows pattern: `action:entity_id:value`

---

## Job Actions

### save_job

**Callback Data**: `save_job:{job_id}`  
**Description**: Save a job from notification to saved list  
**Verification**: Must verify callback.from_user.id == original message.from_user.id  

**Response**: "تم الحفظ! Jobs in /my_jobs" (Saved! View in /my_jobs)  
**Duplicate**: Display "تم حفظه بالفعل (Already saved)"

---

### unsave_job

**Callback Data**: `unsave_job:{job_id}`  
**Description**: Remove a job from saved list (in /my_jobs view)  
**Verification**: Must verify user owns the saved job  

**Response**: Update the job list, remove the card

---

### job_details

**Callback Data**: `job_details:{job_id}`  
**Description**: Show full job description and source link  
**Response**: Full job details with link to Telegram channel  

**Response Format**:
```
🏢 {company}
📍 {location}
💰 {salary}
📊 {match_percent}%

{description_full}

🔗 المصدر (Source): [View Channel](channel_link)
```

---

### cover_letter

**Callback Data**: `cover_letter:{job_id}`  
**Description**: Generate cover letter for job (placeholder, deferred)  
**Response**: Placeholder message "قيد التطوير (Coming soon)"

---

### dismiss_match

**Callback Data**: `dismiss_match:{match_id}`  
**Description**: Dismiss exact job match (set is_dismissed=true)  
**Note**: Only affects exact match record, not same job from different CV  

**Response**: "تم التجاهل (Dismissed)" - remove notification message

---

## Pagination

### jobs_page_next

**Callback Data**: `jobs_page:{view}:{next_page}`  
**Description**: Navigate to next page of job list  

### jobs_page_prev

**Callback Data**: `jobs_page:{view}:{prev_page}`  
**Description**: Navigate to previous page of job list  

### jobs_page_num

**Callback Data**: `jobs_page:{view}:{page}`  
**Description**: Jump to specific page  

---

## View Selection

### view_saved

**Callback Data**: `view:saved`  
**Description**: Switch to Saved Jobs view  

### view_notified

**Callback Data**: `view:notified`  
**Description**: Switch to All Notified view  

### view_dismissed

**Callback Data**: `view:dismissed`  
**Description**: Switch to Dismissed view  

---

## Filters

### filter_similarity

**Callback Data**: `filter_sim:{value}`  
**Values**: `80`, `70`, `all`  
**Description**: Filter jobs by minimum similarity percentage  

### filter_date

**Callback Data**: `filter_date:{value}`  
**Values**: `7`, `14`, `30`, `all`  
**Description**: Filter jobs by date range  

---

## Settings Actions

### edit_threshold

**Callback Data**: `edit_threshold:start`  
**Description**: Enter threshold editing mode  

### threshold_set

**Callback Data**: `threshold:{value}`  
**Values**: `60`, `70`, `80`, `90`, `100`  
**Description**: Set similarity threshold  

### toggle_notifications

**Callback Data**: `toggle_notifications`  
**Description**: Toggle notification preference on/off  

### copy_referral

**Callback Data**: `copy_referral`  
**Description**: Copy referral code to clipboard (show in message)  

### share_referral

**Callback Data**: `share_referral`  
**Description**: Open share interface with referral link  

### upgrade_plan

**Callback Data**: `upgrade_plan:{tier}`  
**Values**: `basic`, `pro`  
**Description**: Show upgrade prompt (payment deferred)  

---

## CV Management

### cv_details

**Callback Data**: `cv_details:{cv_id}`  
**Description**: Show CV details (score, skills, suggestions)  

### delete_cv

**Callback Data**: `delete_cv:{cv_id}`  
**Description**: Initiate CV deletion with confirmation  

### confirm_delete

**Callback Data**: `confirm_delete:{cv_id}:{yes|no}`  
**Description**: Confirm or cancel CV deletion  

### activate_cv

**Callback Data**: `activate_cv:{cv_id}`  
**Description**: Activate an inactive CV  

### confirm_replace

**Callback Data**: `confirm_replace:{yes|no}`  
**Description**: Confirm/reject CV replacement (Free/Basic tier)  

---

## Navigation

### back_to_menu

**Callback Data**: `back_to_menu`  
**Description**: Return to main menu  

### back_to_settings

**Callback Data**: `back_to_settings`  
**Description**: Return to settings view  

### back_to_jobs

**Callback Data**: `back_to_jobs`  
**Description**: Return to job list  

---

## Error Handling

### retry_action

**Callback Data**: `retry:{action}:{params}`  
**Description**: Retry failed action (network error recovery)  

---

## Security: Callback Verification

Every callback query MUST verify:
```python
if callback.from_user.id != message.from_user.id:
    await callback.answer("Unauthorized", show_alert=True)
    return
```

This prevents users from clicking buttons on other users' messages.

---

## Response Patterns

### Success
- Edit original message with updated state
- Or send new message for confirmations
- Use ✅ reaction or checkmark in text

### Error
- Answer callback with alert: `await callback.answer("Error message", show_alert=True)`
- Or edit message to show error state

### Processing
- Answer callback with loading: `await callback.answer("Processing...", show_alert=False)`
- Or edit message to show spinner