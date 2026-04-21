---

description: "Task list for Manual Wallet and Credit Management System implementation"
---

# Tasks: Manual Wallet and Credit Management System

**Input**: Design documents from `/specs/009-manual-wallet-system/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/telegram-commands.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create configuration files and database models

- [x] T001 [P] Create payment methods config in config/payment_methods.json
- [x] T002 [P] Create subscription tiers config in config/subscription_tiers.json
- [x] T002b [P] Add ADMIN_USER_IDS list to config/settings.py (not JSON - Python config file)
- [x] T003 Create UserWallet model in src/models/user_wallet.py
- [x] T004 Create WalletTransaction model in src/models/wallet_transaction.py
- [x] T005 Create SubscriptionHistory model in src/models/subscription_history.py
- [x] T006 Create AdminActionLog model in src/models/admin_action_log.py
- [x] T006b Create Alembic migration 017 for user_wallet table
- [x] T006c Create Alembic migration 018 for wallet_transaction table
- [x] T006d Create Alembic migration 019 for subscription_history table
- [x] T006e Create Alembic migration 020 for admin_action_log table
---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Repositories and core services that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 [P] Create wallet repository in src/repositories/wallet_repository.py
- [x] T008 [P] Create transaction repository in src/repositories/transaction_repository.py
- [x] T009 [P] Create subscription history repository in src/repositories/subscription_history_repository.py
- [x] T010 [P] Create admin action log repository in src/repositories/admin_action_log_repository.py
- [x] T011 Create wallet service with balance operations in src/services/wallet_service.py
- [x] T012 Create subscription service in src/services/subscription_service.py
- [x] T013 Create admin service in src/services/wallet_admin_service.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Wallet Balance (Priority: P1) 🎯 MVP

**Goal**: Users can view their wallet balance with 2 decimal places, auto-create wallet if not exists

**Independent Test**: User sends /wallet command and receives balance displayed in USD format ($X.XX)

### Implementation for User Story 1

- [x] T014 [P] [US1] Create wallet command handler in src/bot/handlers/wallet.py
- [x] T015 [P] [US1] Add wallet keyboard in src/bot/keyboards.py
- [x] T016 [US1] Add wallet states in src/bot/states.py (depends on T014)
- [x] T016b [US1] Display lifetime deposited/spent/withdrawn totals in balance view (depends on T014)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Manual Credit Top-Up (Priority: P1)

**Goal**: Users can initiate top-up flow, contact admin privately for payment confirmation

**Independent Test**: User goes through top-up flow and admin successfully adds balance via admin command

### Implementation for User Story 2

- [x] T017 [P] [US2] Add top-up button handler in src/bot/handlers/wallet.py
- [x] T018 [P] [US2] Implement payment methods display in wallet handler
- [x] T019 [US2] Create admin add balance command in src/bot/handlers/admin.py (depends on T013)
- [x] T020 [US2] Add balance notification in src/services/notification_service.py

---

## Phase 5: User Story 3 - Automated Subscription Purchase (Priority: P1)

**Goal**: Users can purchase subscription tiers (Basic $10, Pro $25) with wallet balance using atomic transactions

**Independent Test**: User with sufficient balance purchases tier and receives immediate 30-day access

### Implementation for User Story 3

- [x] T021 [P] [US3] Create /subscribe command handler in src/bot/handlers/subscription.py
- [x] T022 [P] [US3] Add subscription tier keyboard in src/bot/keyboards.py
- [x] T023 [P] [US3] Implement tier selection in subscription handler
- [x] T024 [US3] Add atomic balance deduction in wallet_service.py (depends on T011)
- [x] T025 [US3] Add subscription activation logic in subscription_service.py (depends on T012)
- [x] T026 [US3] Add idempotency check in wallet_service.py

---

## Phase 6: User Story 4 - Extra Generations Purchase (Priority: P2)

**Goal**: Users can purchase extra cover letter generations when quota exhausted

**Independent Test**: User with exhausted quota purchases generation pack and receives additional generations

### Implementation for User Story 4

- [x] T027 [P] [US4] Add extra packs to subscription_tiers.json
- [x] T028 [P] [US4] Create generation pack purchase flow in subscription.py
- [x] T029 [US4] Add purchased_extra update in src/services/quota_service.py

---

## Phase 7: User Story 5 - Manual Withdrawal Request (Priority: P2)

**Goal**: Users can request withdrawal, admin processes manually outside bot

**Independent Test**: User requests withdrawal and admin deducts balance

### Implementation for User Story 5

- [x] T030 [P] [US5] Add withdraw button handler in src/bot/handlers/wallet.py
- [x] T031 [P] [US5] Implement withdrawal methods display
- [x] T032 [US5] Create admin deduct balance command in src/bot/handlers/admin.py

---

## Phase 8: User Story 6 - Admin Dashboard (Priority: P1)

**Goal**: Admin can view stats, search users, manage balances through commands

**Independent Test**: Admin executes commands and receives accurate information

### Implementation for User Story 6

- [x] T033 [P] [US6] Create /admin_panel command in src/bot/handlers/admin.py
- [x] T034 [P] [US6] Create /admin_search command in admin handler
- [x] T035 [P] [US6] Create /admin_users command in admin handler
- [x] T036 [P] [US6] Create /admin_stats command in admin handler
- [x] T037 [P] [US6] Create /admin_transactions command in admin handler
- [x] T038 [US6] Create /admin_force_expire command in admin handler
- [x] T038b [US6] Add admin permission check in admin handler to reject non-admin commands with permission denied message

---

## Phase 9: User Story 7 - Subscription Expiry Notifications (Priority: P2)

**Goal**: System notifies users 3 days before expiry and on downgrade

**Independent Test**: User receives notification 3 days before expiry and when subscription expires

### Implementation for User Story 7

- [x] T039 [P] [US7] Add expiry cron job in workers/tasks/wallet_tasks.py
- [x] T040 [P] [US7] Add downgrade to Free logic in subscription_service.py
- [x] T041 [US7] Add expiry notification in notification_service.py

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T042 [P] Add comprehensive logging for wallet operations
- [x] T043 [P] Add rate limiting (5-second purchase window)
- [x] T044 Validate all transactions with audit trail
- [x] T045 Run quickstart.md validation scenarios

---

## Phase 11: Tests (Constitution VIII)

### Unit Tests

- [x] UT001 [US1] Unit test WalletService.get_or_create_wallet() in tests/unit/services/test_wallet_service.py
- [x] UT002 [US2] Unit test WalletService.add_balance() atomic transaction in tests/unit/services/test_wallet_service.py
- [x] UT003 [US3] Unit test SubscriptionService.purchase_tier() idempotency in tests/unit/services/test_subscription_service.py
- [x] UT004 [US3] Unit test WalletService.deduct_balance() insufficient balance error in tests/unit/services/test_wallet_service.py
- [x] UT005 [US6] Unit test AdminService.verify_admin() permission check in tests/unit/services/test_wallet_admin_service.py

### Integration Tests

- [x] IT001 End-to-end: User checks balance → Wallet auto-created → Balance displayed in tests/integration/test_wallet_flows.py
- [x] IT002 End-to-end: Admin adds balance → User notified → Balance updated in tests/integration/test_wallet_flows.py
- [x] IT003 End-to-end: User purchases Basic → Subscription activated → Quota updated in tests/integration/test_subscription_flows.py
- [x] IT004 End-to-end: Concurrent purchases → Idempotency enforced → Single charge in tests/integration/test_subscription_flows.py
- [x] IT005 End-to-end: Subscription expires → Auto-downgrade → User notified in tests/integration/test_subscription_flows.py

### Edge Case Tests

- [x] ET001 Test negative balance prevention (database constraint + application logic)
- [x] ET002 Test duplicate purchase prevention (idempotency key enforcement)
- [x] ET003 Test admin deduct more than balance (error handling)
- [x] ET004 Test subscription purchase with exact balance (balance becomes $0.00)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Uses wallet service from Phase 2 - depends on T011
- **User Story 3 (P3)**: Uses wallet service, subscription service - depends on T011, T012
- **User Story 4 (P2)**: Uses quota service integration - depends on T011
- **User Story 5 (P2)**: Uses wallet service - depends on T011
- **User Story 6 (P1)**: Uses all repositories - depends on T007-T010
- **User Story 7 (P2)**: Uses subscription service - depends on T012

### Within Each User Story

- Models before services
- Services before handlers
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- All user story tasks marked [P] within same phase can run in parallel

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3, 6 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Complete Phase 4: User Story 2
5. Complete Phase 5: User Story 3
6. Complete Phase 8: User Story 6
7. **STOP and VALIDATE**: Test core functionality
8. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4-7 → Test independently → Deploy/Demo

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 6
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Verify tests fail before implementing
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence