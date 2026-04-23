# Quickstart: Manual Wallet and Credit Management System

## Test Scenarios

### Scenario 1: First-time User Checks Balance

1. Clear test database or use fresh user
2. User sends `/wallet` command to bot
3. **Expected**: Bot responds with $0.00 balance and buttons [Top Up Balance], [Back]
4. Verify: New wallet record created in database

### Scenario 2: Admin Adds Balance

1. Pre-condition: User exists with UUID `test-user-id`
2. Admin sends `/admin_add_balance test-user-id 50.00 "MTN Cash top-up"`
3. **Expected**: 
   - User balance becomes $50.00
   - Transaction logged with type `top_up`
   - Admin action logged in admin_action_log
   - User receives notification
4. Verify: Balance in database is 50.00

### Scenario 3: User Purchases Subscription (Success)

1. Pre-condition: User has $50.00 balance
2. User sends `/subscribe`
3. Bot displays tiers: Basic ($10), Pro ($25)
4. User clicks Basic
5. Bot shows confirmation: "Confirm: Basic $10/month. New balance: $40.00"
6. User clicks Confirm
7. **Expected**:
   - Balance deducted to $40.00
   - Subscription activated for 30 days
   - Transaction logged
   - Confirmation message sent

### Scenario 4: User Purchases Subscription (Insufficient Balance)

1. Pre-condition: User has $5.00 balance
2. User sends `/subscribe`
3. User selects Basic
4. **Expected**: Bot shows "Insufficient balance" with [Top Up Balance] button

### Scenario 5: Idempotency - Duplicate Purchase Prevention

1. Pre-condition: User has $20.00 balance
2. Simulate concurrent requests:
   - Click [Confirm Purchase] within 1 second
3. **Expected**: 
   - First request completes successfully
   - Second request shows "Transaction in progress" error
   - Balance deducted only once ($20.00 → $10.00)
   - Only one transaction record in database
4. **Manual Testing**: 
   - use Postman to send two identical requests at same time
6. **Expected**: Second purchase rejected with "Transaction in progress" message

### Scenario 6: Subscription Expiry and Downgrade

1. Pre-condition: User has active Basic subscription nearing expiry
2. Wait for subscription to expire OR admin runs `/admin_force_expire user-id`
3. **Expected**:
   - User tier changed to Free
   - Notification sent to user
   - SubscriptionHistory status updated to `expired`

### Scenario 7: Admin Views Statistics

1. Admin sends `/admin_panel`
2. **Expected**: Dashboard displays:
   - Total users
   - Active subscriptions (by tier)
   - Total revenue
   - Recent transactions

### Scenario 8: Extra Generations Purchase

1. Pre-condition: User has exhausted daily quota AND has $2.00 balance
2. User sees "Quota exhausted" with [Purchase Extra] button
3. User clicks [Purchase Extra]
4. Bot displays packs: Small ($0.50/5), Medium ($1.00/12), Large ($3.00/40)
5. User selects Medium
6. User confirms
7. **Expected**:
   - Balance deducted
   - purchased_extra updated with 12 generations
   - Generations never expire

### Scenario 9: Admin Permission Denied

1. Pre-condition: User Telegram ID NOT in ADMIN_USER_IDS list
2. User sends `/admin_panel`
3. **Expected**: 
   - Bot shows "Permission Denied" message
   - OR bot ignores command silently
   - No admin action logged
4. Verify: admin_action_log table has no records for this user

---

## Verification Queries

### Check User Balance
```sql
SELECT * FROM user_wallet WHERE user_id = 'test-user-id';
```

### Check Transactions
```sql
SELECT * FROM wallet_transaction 
WHERE user_id = 'test-user-id' 
ORDER BY created_at DESC;
```

### Check Active Subscription
```sql
SELECT * FROM subscription_history 
WHERE user_id = 'test-user-id' AND status = 'active';
```

### Check Admin Actions
```sql
SELECT * FROM admin_action_log 
ORDER BY created_at DESC;
```

---

## Expected API Responses

### /wallet Response Format
```
💰 محفظتي | My Wallet

الرصيد الحالي: $10.00
المودع_total: $50.00
المُنفق: $40.00

[شحن الرصيد | Top Up] [ سحب الرصيد | Withdraw] [العودة | Back]
```

### /subscribe Response Format
```
الاشتراكات | Subscriptions

��� Free - مجاني (3 رسائل/يوم)
📋 Basic - $10/شهر (15 رسالة/يوم) [اشترك | Subscribe]
📋 Pro - $25/شهر (50 رسالة/اليوم) [اشترك | Subscribe]

[العودة | Back]
```

### Admin Panel Response
```
📊 Admin Panel

المستخدمين: 150
الاشتراكات النشطة:
- Free: 100
- Basic: 30
- Pro: 20

الإيرادات: $850.00
آخر المعاملات: 5
```