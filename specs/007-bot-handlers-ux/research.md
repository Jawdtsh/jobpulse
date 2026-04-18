# Research: Bot Handlers & UX Flow

**Feature Branch**: `007-bot-handlers-ux`  
**Phase**: 0 - Research  
**Date**: 2026-04-16

## Research Summary

### Aiogram 3.x FSM Patterns

The project uses aiogram 3.x. Key patterns identified:
- **FSM**: Use `aiogram.fsm.context.FSMContext` for multi-step flows (CV upload, threshold editing)
- **States**: Define states as classes inheriting from `FSM` with state attributes
- **Transitions**: Use `@router.message()` and `@router.callback_query()` with `state=...` filter

### Redis-Backed Session

- BotSession needs Redis-backed session state with 10-minute expiry
- Key format: `bot_session:{user_id}`
- Store: current state, last activity timestamp, flow-specific data (e.g., upload progress)

### Rate Limiting

- Telegram rate limit: ~30 msg/s
- Middleware approach: check last message timestamp per user
- If limit exceeded, queue message and retry with exponential backoff

### Bilingual Messages (Arabic + English)

- i18n resolver needed: `src/utils/i18n.py`
- Message format: Arabic text first, English in parentheses
- Example: "مرحباً بك (Welcome)" or "حدث خطأ. حاول لاحقاً. (An error occurred. Please try again.)"

### Existing Patterns to Follow

From existing `src/bot/handlers.py`:
- Use `filters.ChatTypeFilter(chat_type=types.ChatType.PRIVATE)` for private chats
- Keyboard buttons use `InlineKeyboardButton(text=..., callback_data=...)`
- Callback data format: `action:entity_id:value`
- Error handling wraps handlers with try/except and logs to Sentry

## Questions Resolved

1. **File formats**: PDF, DOCX, TXT only - need validation in upload handler
2. **Max file size**: 5MB - need check before processing
3. **Tier-based CV limits**: Free/Basic = 1 active, Pro = 2 active
4. **Pagination**: 5 jobs per page, use offset/limit in queries
5. **Dismiss behavior**: Exact match only - `is_dismissed` column on JobMatch table

## Key Entities to Create

1. **SavedJob** (new table): user_id, job_id, saved_at - unique constraint on (user_id, job_id)
2. **BotSession** (Redis): user_id, current_state, last_activity, flow_data
3. Update **JobMatch**: add `is_dismissed` boolean column

## Implementation Approach

- Create router structure under `src/bot/handlers/`
- Use middleware for auth, rate limiting, session expiry
- Service layer for business logic (BotSessionService, SavedJobService)
- Repository for SavedJob data access

## Notes

- Webhook mode deployment
- Test with pytest-asyncio using existing conftest pattern