# Feature Specification: Manual Wallet and Credit Management System

**Feature Branch**: `009-manual-wallet-system`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: User description: "Build a manual wallet and credit management system for a Telegram bot with admin control panel. The system supports user balance management (USD only), manual credit top-up confirmation, automated subscription purchases using wallet balance, and admin operations through Telegram admin interface. NO automated payment gateways - all fund additions are manual and admin-confirmed."

## User Scenarios & Testing

### User Story 1 - View Wallet Balance (Priority: P1)

User can view their current wallet balance through the /wallet command or My Wallet button in the bot interface.

**Why this priority**: Core functionality - users must be able to see their balance to make informed decisions about purchases and top-ups.

**Independent Test**: User sends /wallet command or clicks [My Wallet] button and receives their current balance displayed in USD format ($X.XX).

**Acceptance Scenarios**:
1. **Given** user has a wallet, **When** user requests balance, **Then** system displays current balance with 2 decimal places
2. **Given** user has no wallet, **When** user requests balance OR attempts purchase, **Then** system auto-creates wallet and displays $0.00 balance
3. **Given** user has wallet with funds, **When** user requests balance, **Then** system shows total deposited, total spent, and current balance

---

### User Story 2 - Manual Credit Top-Up (Priority: P1)

User initiates top-up process and contacts admin privately to confirm payment, then admin credits their wallet.

**Why this priority**: Core payment mechanism - all fund additions require manual admin confirmation, no automated gateways.

**Independent Test**: User goes through top-up flow and admin successfully adds balance via admin command.

**Acceptance Scenarios**:
1. **Given** user clicks /wallet → [Top Up Balance], **When** system responds, **Then** displays available payment methods and admin contact instructions
2. **Given** user receives top-up instructions, **When** user contacts admin privately, **Then** system shows message directing user NOT to send payment proof in bot
3. **Given** admin receives payment proof, **When** admin uses /admin_add_balance command, **Then** system credits user wallet and sends confirmation notification
4. **Given** wallet credited, **When** user checks balance, **Then** new balance reflects the credited amount

---

### User Story 3 - Automated Subscription Purchase (Priority: P1)

User purchases subscription tier using wallet balance with instant, atomic transaction and idempotency protection.

**Why this priority**: Primary revenue mechanism - users can upgrade to paid tiers instantly without admin intervention.

**Independent Test**: User with sufficient balance purchases Basic or Pro tier and receives immediate access.

**Acceptance Scenarios**:
1. **Given** user clicks /subscribe or [Upgrade], **When** system responds, **Then** displays tier options with prices in USD
2. **Given** user selects tier with insufficient balance, **Then** system shows "Insufficient balance" message with [Top Up Balance] button
3. **Given** user selects tier with sufficient balance, **Then** system shows confirmation with new balance preview
4. **Given** user confirms purchase, **Then** system atomically deducts balance, activates 30-day subscription, logs transaction
5. **Given** concurrent purchase attempt within 5 seconds, **Then** system treats as single purchase request
6. **Given** existing active subscription of same tier, **When** user attempts purchase, **Then** system prevents purchase until current expires
7. **Given** subscription expires, **Then** system auto-downgrades to Free tier and notifies user

---

### User Story 4 - Extra Generations Purchase (Priority: P2)

User purchases extra cover letter generation packs when daily quota is exhausted.

**Why this priority**: Secondary revenue mechanism - users can buy additional generations beyond their tier limit.

**Independent Test**: User with exhausted quota purchases generation pack and receives additional generations.

**Acceptance Scenarios**:
1. **Given** user exhausts daily quota, **When** user sees [Purchase Extra] button, **Then** system displays available generation packs with prices
2. **Given** user selects pack with insufficient balance, **Then** system shows "Insufficient balance" with [Top Up Balance] button
3. **Given** user confirms pack purchase, **Then** system atomically deducts balance, adds generations to purchased_extra, logs transaction
4. **Given** generations purchased, **Then** generations persist across daily resets and never expire

---

### User Story 5 - Manual Withdrawal Request (Priority: P2)

User requests withdrawal and admin processes it manually outside the bot.

**Why this priority**: Allows users to retrieve funds from their wallet - required for complete wallet functionality.

**Independent Test**: User requests withdrawal and admin successfully deducts balance and processes refund externally.

**Acceptance Scenarios**:
1. **Given** user clicks /wallet → [Withdraw Balance], **Then** system displays available balance and withdrawal methods with admin contact
2. **Given** user contacts admin with withdrawal request, **When** admin uses /admin_deduct_balance, **Then** system deducts balance and notifies user
3. **Given** user has zero balance, **Then** system shows message that no balance is available for withdrawal

---

### User Story 6 - Admin Dashboard and User Management (Priority: P1)

Admin can view statistics, search users, and manage balances through Telegram commands.

**Why this priority**: Core admin functionality - required for manual balance management and user support.

**Independent Test**: Admin executes admin commands and receives accurate information or performs balance operations.

**Acceptance Scenarios**:
1. **Given** admin sends /admin_panel, **Then** system shows dashboard with quick stats
2. **Given** admin sends /admin_search with user_id, **Then** system displays full user profile including balance, tier, transactions
3. **Given** admin sends /admin_add_balance with valid parameters, **Then** system credits user and logs action
4. **Given** admin sends /admin_deduct_balance with valid parameters, **Then** system debits user and logs action
5. **Given** non-admin sends admin command, **Then** system ignores or shows permission denied message

---

### User Story 7 - Subscription Expiry Notifications (Priority: P2)

System notifies users before subscription expires and after downgrade to Free tier.

**Why this priority**: Retention mechanism - reminds users to renew before losing premium features.

**Independent Test**: User receives notification 3 days before expiry and when subscription expires.

**Acceptance Scenarios**:
1. **Given** user has active subscription 3 days from expiry, **Then** system sends renewal reminder
2. **Given** subscription expires, **Then** system downgrades to Free tier and sends expiry notification

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST allow users to view wallet balance via /wallet command or [My Wallet] button
- **FR-002**: System MUST display ALL monetary amounts (balance, deposited, spent, withdrawn) with exactly 2 decimal places in USD format ($X.XX); amounts stored in database as DECIMAL(10,2)
- **FR-003**: System MUST provide top-up flow showing payment methods and admin contact
- **FR-004**: System MUST NOT accept payment proof in bot - all payment confirmation via private admin chat
- **FR-005**: System MUST allow admin to add balance via /admin_add_balance command with user_id, amount, and reason
- **FR-006**: System MUST allow admin to deduct balance via /admin_deduct_balance command with user_id, amount, and reason
- **FR-007**: System MUST implement idempotency protection using random code per request with 5-second duplicate detection window
- **FR-008**: System MUST use atomic database transactions for balance updates to prevent race conditions
- **FR-024**: Subscription expiry reminders sent within 1 hour of scheduled time (3 days before expiry at 12:00 UTC); expiry notifications sent within 1 hour of downgrade (at 00:00 UTC on expiry+1 day)
- **FR-010**: System MUST activate subscriptions for exactly 30 days from purchase date
- **FR-011**: System MUST auto-downgrade to Free tier at 00:00 UTC on the day after subscription end_date (no grace period); subscription remains active until end_date at 23:59:59 UTC
- **FR-012**: System MUST send renewal reminder 3 days before subscription expiry
- **FR-013**: System MUST support generation packs: Small ($0.50/5), Medium ($1.00/12), Large ($3.00/40)
- **FR-014**: System MUST update user_quota_tracking.purchased_extra when generation pack purchased
- **FR-015**: System MUST allow withdrawal requests via admin contact (no automated withdrawal)
- **FR-016**: System MUST log all transactions with type, amount, balance_before, balance_after, description, metadata
- **FR-017**: System MUST log all admin actions with admin_id, action_type, target_user_id, amount, reason
- **FR-018**: System MUST notify users when balance is added or deducted by admin
- **FR-019**: System MUST validate amounts: minimum $1.00, maximum top-up $1000 and display error messages: "Minimum amount is $1.00", "Maximum top-up is $1000"
- **FR-020**: System MUST prevent negative balances through database constraints and application logic
- **FR-021**: System MUST verify admin identity via Telegram user ID matching ADMIN_USER_IDS in config
- **FR-022**: System MUST auto-create wallet with $0.00 balance on first /wallet command or purchase attempt; if creation fails, display error message "Unable to initialize wallet, please try again"
- **FR-023**: System MUST prevent users from purchasing a subscription tier if they already have an active subscription of ANY tier; users can only purchase a new tier after their current subscription expires


### Edge Cases
- User attempts purchase with exactly balance equal to price: Allowed (balance would become $0.00)
- Concurrent subscription purchase attempts: Treated as single request if within 5-second window
- Idempotency key collision: First request succeeds; duplicates within 5-second window rejected
- Timezone for subscription expiry: Use UTC for storage; display in user's local timezone (from i18n settings)
- Admin attempts to deduct more than available balance: Rejected with error showing "Insufficient balance: user has ${available}, cannot deduct ${requested}"
- User has $9.99 but Basic costs $10.00: System shows "Insufficient balance" with exact shortfall: "You need $0.01 more to purchase Basic tier"
- Concurrent balance operations (admin adds while user purchases): Atomic transactions prevent conflicts; operations execute sequentially
- User attempts withdrawal for amount greater than balance: Rejected with error showing available balance
- User already has active subscription of ANY tier: Cannot purchase new tier until current expires (FR-023)

### Key Entities

- **UserWallet**: Represents user's wallet with balance in USD, tracks lifetime deposited/spent/withdrawn amounts
- **Transaction**: Represents a single balance movement with type, amount, before/after balance, status, idempotency key
- **SubscriptionHistory**: Represents subscription periods with tier, start/end dates, status, linked transaction
- **AdminActionLog**: Represents admin operations for audit trail with admin user ID, action type, target user, amount, reason

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can purchase subscription within 3 seconds when balance is sufficient (measured via manual timing test, no automated metrics required)
- **SC-002**: Balance updates are atomic with 100% accuracy - zero rounding errors, zero race conditions
- **SC-003**: Zero duplicate charges even under concurrent purchase attempts due to idempotency enforcement
- **SC-004**: Admin can add/deduct balance within 10 seconds of command execution
- **SC-005**: Users receive balance confirmation notification within 2 seconds of admin action
- **SC-006**: Subscription activation is immediate (0 delay) after purchase confirmation
- **SC-007**: All transactions logged with complete audit trail - zero missing records
- **SC-008**: Configuration changes (payment methods, prices) take effect without code changes or restart

## Clarifications

### Session 2026-04-20

- Q: Admin authentication method → A: Telegram ID only - Admin identified by Telegram user ID matching ADMIN_USER_IDS in config settings
- Q: User wallet creation timing → A: On first /wallet or purchase - Lazy initialization saves storage when user first checks balance or attempts purchase
- Q: Concurrent purchase idempotency behavior → A: Random code per purchase request, 5-second window for duplicates - First attempt completes; concurrent attempts within 5 seconds treated as single request
- Q: Withdrawal limit → A: Full balance available - User can withdraw entire balance in one transaction (no per-transaction cap)

## Assumptions

- Payment confirmation is fully manual via private admin chat - no bot automation for payment verification
- All amounts stored and displayed in USD only - single currency system
- Payment can be received in any currency (SYP, USDT, etc.) but admin converts to USD when adding balance
- No exchange rate handling in bot - admin handles conversion manually outside the system
- All user-facing messages are bilingual (Arabic + English) - user preference determined by existing i18n system
- Admins use same Telegram bot interface - no separate web dashboard
- Payment methods can be enabled/disabled via config without code changes
- Subscription durations are fixed at 30 days - no custom durations
- No promo codes or discounts in this implementation
- Existing user table exists in database - wallet links to users via user_id
- SPEC-008 quota tracking system exists - integration point for generation packs
- SPEC-007 bot handlers and i18n system exist - integration points for commands and messages