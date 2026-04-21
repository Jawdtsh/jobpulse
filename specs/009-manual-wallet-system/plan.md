# Implementation Plan: Manual Wallet and Credit Management System

**Branch**: `009-manual-wallet-system` | **Date**: 2026-04-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-manual-wallet-system/spec.md`

## Summary

Manual wallet and credit management system for a Telegram bot with admin control panel. Supports user balance management (USD only), manual credit top-up confirmation via admin private chat, automated subscription purchases using wallet balance, extra generation pack purchases, manual withdrawal requests, and comprehensive admin operations. All fund additions are manual and admin-confirmed - NO automated payment gateways.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: aiogram 3.x (Telegram bot), SQLAlchemy 2.0 async (database), asyncpg (PostgreSQL driver)  
**Storage**: PostgreSQL 16 with pgvector (existing), Redis for rate limiting  
**Testing**: pytest (existing project standard)  
**Target Platform**: Linux server (Telegram bot)  
**Project Type**: Telegram bot with FastAPI backend  
**Performance Goals**: Subscription purchase < 3 seconds, balance updates atomic, idempotency enforcement  
**Constraints**: Atomic transactions required, duplicate prevention via idempotency keys, max top-up $1000, min transaction $1.00  
**Scale/Scope**: User wallet per Telegram user, estimated 10k users based on existing user base

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| Clean Architecture (layer separation) | ✓ PASS | Routes → Services → Repositories pattern maintained |
| SOLID Principles | ✓ PASS | Single responsibility, DI for services |
| Clean Code (20 lines/function) | ✓ PASS | Will enforce in implementation |
| Security First | ✓ PASS | No secrets in code, input validation required |
| Config Management | ✓ PASS | Uses config/settings.py and JSON config files |
| Language Policy | ✓ PASS | English code, bilingual user-facing messages |
| Database Changes | ✓ PASS | Uses Alembic for migrations |
| Async Best Practices | ✓ PASS | Uses async/await consistently |

**Constitution Compliance**: All gates pass - no violations.

## Project Structure

### Documentation (this feature)

```
specs/009-manual-wallet-system/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Telegram commands)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```
src/
├── models/
│   ├── user_wallet.py          # NEW: User wallet entity
│   ├── wallet_transaction.py   # NEW: Transaction audit log
│   ├── subscription_history.py  # NEW: Subscription tracking
│   └── admin_action_log.py      # NEW: Admin audit trail
├── services/
│   ├── wallet_service.py        # NEW: Balance operations
│   ├── subscription_service.py  # NEW: Subscription management
│   └── notification_service.py # MODIFY: Add wallet notifications
├── repositories/
│   ├── wallet_repository.py           # NEW
│   ├── transaction_repository.py       # NEW
│   ├── subscription_history_repository.py  # NEW
│   └── admin_action_log_repository.py  # NEW
└── bot/
    ├── handlers/
    │   ├── wallet.py           # NEW: /wallet command
    │   ├── admin.py            # NEW: Admin commands
    │   └── cron.py             # MODIFY: Expiry notifications
    ├── keyboards.py             # MODIFY: Add wallet buttons
    └── states.py               # MODIFY: Add wallet FSM states

config/
├── payment_methods.json     # NEW: Payment method config
└── subscription_tiers.json # NEW: Subscription tiers + generation packs

tests/
├── unit/
│   ├── test_wallet_service.py     # NEW
│   └── test_subscription_service.py # NEW
└── integration/
    └── test_wallet_flows.py       # NEW
```

**Structure Decision**: Single project following existing codebase patterns. Models in src/models/, services in src/services/, repositories in src/repositories/, bot handlers in src/bot/handlers/, configs in config/.

---

# Phase 0: Research

## Research Findings

### Decision 1: Idempotency Implementation
- **Chosen**: Idempotency key format: `{user_id}:{type}:{unix_timestamp_ms}`
- **Rationale**: Timestamp-based keys allow 5-second window check: reject if key exists with timestamp within 5 seconds
- **Implementation**: 
  - Generate key on purchase attempt
  - Check database for existing key with timestamp in range `[now-5s, now]`
  - If exists, treat as duplicate (return original transaction)
  - If not, insert new transaction with key
- **Cleanup**: Cron job deletes keys older than 24 hours
- **Alternatives**: Database unique constraint (more complex), Redis-based locking (external dependency)

### Decision 2: Admin Authentication
- **Chosen**: Telegram user ID verification only (ADMIN_USER_IDS in config)
- **Rationale**: Telegram already provides user identity, no additional auth needed for admin commands
- **Alternatives**: PIN/password (adds friction, unnecessary for this use case)

### Decision 3: Wallet Creation
- **Chosen**: Lazy initialization on first /wallet or purchase
- **Rationale**: Saves storage for users who never use wallet feature
- **Alternatives**: Create on registration (wasteful), manual only (more admin work)

### Decision 4: Atomic Transactions
- **Chosen**: Database-level row locking (SELECT FOR UPDATE) + check-then-act pattern
- **Rationale**: PostgreSQL supports this natively, prevents race conditions
- **Alternatives**: Distributed locks (overkill for single-instance deployment)

---

# Phase 1: Design

## Entities

### UserWallet
- user_id: UUID (FK to users, unique)
- balance_usd: DECIMAL(10,2), default 0.00
- total_deposited_usd: DECIMAL(10,2), default 0.00
- total_spent_usd: DECIMAL(10,2), default 0.00
- total_withdrawn_usd: DECIMAL(10,2), default 0.00
- updated_at: TIMESTAMP
- created_at: TIMESTAMP

### Transaction
- id: UUID (PK)
- user_id: UUID (FK to users)
- type: ENUM (top_up, subscription_purchase, generation_purchase, withdrawal, admin_adjustment, refund)
- amount_usd: DECIMAL(10,2)
- balance_before: DECIMAL(10,2)
- balance_after: DECIMAL(10,2)
- status: ENUM (completed, failed, reversed)
- description: VARCHAR(500)
- admin_id: UUID (nullable)
- metadata: JSONB
- created_at: TIMESTAMP
- idempotency_key: VARCHAR(100) (unique, nullable)

### SubscriptionHistory
- id: UUID (PK)
- user_id: UUID (FK to users)
- tier: ENUM (free, basic, pro)
- start_date: DATE
- end_date: DATE
- status: ENUM (active, expired, cancelled)
- purchase_transaction_id: UUID (FK to transactions, nullable)
- created_at: TIMESTAMP

### AdminActionLog
- id: UUID (PK)
- admin_user_id: BIGINT (Telegram user ID)
- action_type: ENUM (add_balance, deduct_balance, force_expire, view_user, view_transactions)
- target_user_id: UUID (nullable)
- amount_usd: DECIMAL(10,2) (nullable)
- reason: TEXT (nullable)
- details: JSONB
- created_at: TIMESTAMP

## Interface Contracts (Telegram Commands)

### User Commands
- `/wallet` - Display wallet balance, top-up, withdraw buttons
- `/subscribe` - Display subscription tier options
- Callback queries for tier/pack selection and purchase confirmation

### Admin Commands
- `/admin_panel` - Dashboard with quick stats
- `/admin_search {user_id}` - Search user by ID
- `/admin_users {filter}` - List users with filters
- `/admin_add_balance {user_id} {amount} {reason}` - Add balance
- `/admin_deduct_balance {user_id} {amount} {reason}` - Deduct balance
- `/admin_transactions {filter}` - View transactions
- `/admin_stats` - Revenue statistics
- `/admin_force_expire {user_id}` - Force subscription expiry

## Quickstart Scenarios

### Scenario 1: First-time User Checks Balance
1. User sends /wallet
2. System auto-creates wallet with $0.00
3. System displays balance with options: [Top Up], [Back]

### Scenario 2: User Purchases Subscription
1. User sends /subscribe
2. System displays tiers: Basic ($10), Pro ($25)
3. User clicks Basic
4. System checks balance - if insufficient, show [Top Up] button
5. If sufficient, show confirmation: "Confirm: Basic $10/month. New balance: $X"
6. User clicks Confirm
7. System generates idempotency key, checks duplicates
8. System deducts balance, activates 30-day subscription
9. System sends confirmation with expiry date

### Scenario 3: Admin Adds Balance
1. Admin sends /admin_add_balance 123456789 50.00 "Top-up via MTN"
2. System validates admin ID
3. System credits user wallet
4. System logs transaction and admin action
5. System notifies user of credit

---

## Integration Points

| Dependency | Spec | Integration | Usage |
|------------|------|-------------|-------|
| SPEC-008 (Cover Letter) | user_quota_tracking.purchased_extra | src/services/quota_service.py | Update purchased_extra when generation pack purchased |
| SPEC-007 (Bot Handlers) | i18n system | src/bot/utils/i18n.py | Bilingual messages for wallet commands |
| SPEC-007 (Bot Handlers) | BotSession | src/bot/session.py | FSM state tracking for wallet flows |
| User Table | Existing | src/models/user.py | UserWallet links to users via user_id |

---

**Plan Complete**: Ready for Phase 2 (Tasks Generation)
