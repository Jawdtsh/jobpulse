# Data Model: Manual Wallet and Credit Management System

## Entities

### UserWallet

Represents user's wallet with balance in USD, tracks lifetime deposited/spent/withdrawn amounts.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| user_id | UUID | FK to users, UNIQUE, NOT NULL | Reference to user |
| balance_usd | DECIMAL(10,2) | DEFAULT 0.00, NOT NULL | Current balance |
| total_deposited_usd | DECIMAL(10,2) | DEFAULT 0.00, NOT NULL | Lifetime deposits |
| total_spent_usd | DECIMAL(10,2) | DEFAULT 0.00, NOT NULL | Lifetime spending |
| total_withdrawn_usd | DECIMAL(10,2) | DEFAULT 0.00, NOT NULL | Lifetime withdrawals |
| updated_at | TIMESTAMP | NOT NULL | Last update time |
| created_at | TIMESTAMP | NOT NULL | Creation time |

**Relationships**:
- One-to-One with User (via user_id)
- One-to-Many with Transaction (via user_id)
- One-to-Many with SubscriptionHistory (via user_id)

### Transaction

Represents a single balance movement with full audit trail.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | UUID | PK | Unique transaction ID |
| user_id | UUID | FK to users, NOT NULL | User reference |
| type | ENUM | NOT NULL | top_up, subscription_purchase, generation_purchase, withdrawal, admin_adjustment, refund |
| amount_usd | DECIMAL(10,2) | NOT NULL | Transaction amount |
| balance_before | DECIMAL(10,2) | NOT NULL | Balance before transaction |
| balance_after | DECIMAL(10,2) | NOT NULL | Balance after transaction |
| status | ENUM | NOT NULL | completed, failed, reversed |
| description | VARCHAR(500) | NULLABLE | Human-readable description |
| admin_id | UUID | NULLABLE | Admin who performed action (if admin) |
| metadata | JSONB | NULLABLE | Flexible field for tier, pack_id, payment_method |
| created_at | TIMESTAMP | NOT NULL | Transaction time |
| idempotency_key | VARCHAR(100) | UNIQUE, NULLABLE | Prevents duplicate purchases |

**Relationships**:
- Many-to-One with User (via user_id)
- One-to-One with SubscriptionHistory (via purchase_transaction_id)

### SubscriptionHistory

Represents subscription periods with tier, dates, status.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | UUID | PK | Unique subscription ID |
| user_id | UUID | FK to users, NOT NULL | User reference |
| tier | ENUM | NOT NULL | free, basic, pro |
| start_date | DATE | NOT NULL | Subscription start |
| end_date | DATE | NOT NULL | Subscription end |
| status | ENUM | NOT NULL | active, expired, cancelled |
| purchase_transaction_id | UUID | FK to transactions, NULLABLE | Transaction that created this subscription |
| created_at | TIMESTAMP | NOT NULL | Record creation time |

**Relationships**:
- Many-to-One with User (via user_id)
- Many-to-One with Transaction (via purchase_transaction_id)

### AdminActionLog

Represents admin operations for audit trail.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | UUID | PK | Unique log ID |
| admin_user_id | BIGINT | NOT NULL | Telegram user ID of admin |
| action_type | ENUM | NOT NULL | add_balance, deduct_balance, force_expire, view_user, view_transactions |
| target_user_id | UUID | NULLABLE | User affected by action |
| amount_usd | DECIMAL(10,2) | NULLABLE | Amount if applicable |
| reason | TEXT | NULLABLE | Reason provided by admin |
| details | JSONB | NULLABLE | Additional context |
| created_at | TIMESTAMP | NOT NULL | Action time |


## Foreign Key Constraints

| Table | Column | References | On Delete | Description |
|-------|--------|-----------|-----------|-------------|
| user_wallet | user_id | users.id | CASCADE | Delete wallet when user deleted |
| wallet_transaction | user_id | users.id | CASCADE | Delete transactions when user deleted |
| subscription_history | user_id | users.id | CASCADE | Delete history when user deleted |
| subscription_history | purchase_transaction_id | wallet_transaction.id | SET NULL | Preserve history if transaction deleted |

**Relationships**:
- No foreign keys (stores Telegram IDs)

## Indexes

### UserWallet
- UNIQUE INDEX idx_user_wallet_user_id ON user_wallet(user_id)

### Transaction
- INDEX idx_transaction_user_id ON wallet_transaction(user_id)
- INDEX idx_transaction_created_at ON wallet_transaction(created_at DESC)
- UNIQUE INDEX idx_transaction_idempotency ON wallet_transaction(idempotency_key) WHERE idempotency_key IS NOT NULL

### SubscriptionHistory
- INDEX idx_subscription_user_status ON subscription_history(user_id, status)
- INDEX idx_subscription_end_date ON subscription_history(end_date) WHERE status = 'active'

### AdminActionLog
- INDEX idx_admin_log_admin_id ON admin_action_log(admin_user_id)
- INDEX idx_admin_log_created_at ON admin_action_log(created_at DESC)

---
## Migrations Required

### Migration 017: Create user_wallet table
**File**: `migrations/versions/017_create_user_wallet.py`

### Migration 018: Create wallet_transaction table
**File**: `migrations/versions/018_create_wallet_transaction.py`

### Migration 019: Create subscription_history table
**File**: `migrations/versions/019_create_subscription_history.py`

### Migration 020: Create admin_action_log table
**File**: `migrations/versions/020_create_admin_action_log.py`

---

## Validation Rules

1. **balance_usd** >= 0 (CHECK constraint)
2. **amount_usd** >= 0.10 for transactions
3. **amount_usd** <= 1000 for top-ups
4. **idempotency_key** unique within 24 hours
5. **SubscriptionHistory** max 1 active per user
6. **end_date** = start_date + 30 days for purchased subscriptions
7. **Transaction type** must be one of predefined ENUM values; new types require migration
8. Alternative: Consider VARCHAR(50) with application-level validation for easier extensibility

---

## State Transitions

### Transaction Status
- `pending` → `completed` (successful)
- `pending` → `failed` (error)
- `completed` → `reversed` (admin reversal)

### Subscription History Status
- `active` → `expired` (on end_date)
- `active` → `cancelled` (admin force_expire)