# Telegram Bot Interface Contracts

## User Commands

### /wallet Command

**Trigger**: User sends `/wallet` or clicks [My Wallet] button

**Response** (Inline Keyboard):
```
Message: "💰 محفظتي | My Wallet"

Balance Display:
-_current_balance: $X.XX
- Deposited_total: $X.XX
- Spent_total: $X.XX (if > 0)

Buttons:
[شحن الرصيد | Top Up Balance] [سحب الرصيد | Withdraw] [العودة | Back]
```

**State Flow**: `wallet:main` → `wallet:top_up` OR `wallet:withdraw`

---

### Top Up Flow

**Trigger**: User clicks [Top Up Balance]

**Response**:
```
Message: "اختر طريقة الدفع | Choose Payment Method"

Payment Methods (from config/payment_methods.json):
- MTN Cash
- Sham Cash
- USDT
- الهرم
- الفؤاد

Message: "للشحن، يرجى التواصل مع {admin_contact} عبر رسالة خاصة"
"To top up, please contact {admin_contact} via private message"
```

---

### /subscribe Command

**Trigger**: User sends `/subscribe` or clicks [Upgrade] button

**Response**:
```
Message: "الاشتراكات | Subscriptions"

Tiers:
├─ Free - $0/month (3/day)
├─ Basic - $10/month (15/day) [اشتراك | Subscribe]
└─ Pro - $25/month (50/day) [اشتراك | Subscribe]

[العودة | Back]
```

**State Flow**: `subscribe:select_tier` → `subscribe:confirm`

---

### Confirmation Dialog (Purchase)

**Trigger**: User selects tier

**Response**:
```
Message: "تأكيد | Confirm"

"Confirm purchase: {tier} for ${price}/month"
"Your new balance will be ${current_balance - price}"

Buttons: [تأكيد | Confirm Purchase] [إلغاء | Cancel]
```

---

### Success Response (Purchase)

**Trigger**: User confirms purchase

**Response**:
```
Message: "✅ تم | Done"

"🎉 تم تفعيل اشتراك {tier}!"
"Subscription activated: {tier}"
"Expires: {expiry_date}"

[العودة | Back]
```

---

## Admin Commands

### /admin_panel

**Trigger**: Admin sends `/admin_panel`

**Response**:
```
Message: "📊 لوحة الإدارة | Admin Panel"

Stats:
- Total Users: {count}
- Active Subscriptions:
  • Free: {free_count}
  • Basic: {basic_count}
  • Pro: {pro_count}
- Total Revenue: ${total_revenue}
- Recent Transactions: {recent_count}

Buttons:
[بحث | Search] [المستخدمين | Users] [الإحصائيات | Stats]
[المعاملات | Transactions] [العودة | Back]
```

---

### /admin_add_balance

**Trigger**: Admin sends `/admin_add_balance {user_id} {amount} {reason}`

**Format**: `/admin_add_balance 123456789 50.00 "Top-up via MTN"`

**Response (Success)**:
```
✅ Added ${amount} to user {user_id}
New balance: ${new_balance}
```

**Response (Error)**:
```
❌ Error: User not found / Invalid amount / Insufficient reason
```

---

### /admin_deduct_balance

**Trigger**: Admin sends `/admin_deduct_balance {user_id} {amount} {reason}`

**Format**: `/admin_deduct_balance 123456789 30.00 "Withdrawal to USDT"`

**Response (Success)**:
```
✅ Deducted ${amount} from user {user_id}
New balance: ${new_balance}
```

---

### /admin_search

**Trigger**: Admin sends `/admin_search {user_id}`

**Response**:
```
Message: "👤 المستخدم | User: {user_id}"

Telegram ID: {telegram_id}
Balance: ${balance}
Tier: {tier}
Subscription: {expiry_date or "N/A"}
Deposited_total: ${deposited}
Spent_total: ${spent}
Withdrawn_total: ${withdrawn}

[Transaction History] [Add Balance] [Deduct Balance]
```

---

### /admin_stats

**Trigger**: Admin sends `/admin_stats`

**Response**:
```
Message: "📈 الإحصائيات | Statistics"

Revenue:
- Total Top-ups: ${top_ups}
- Total Spent: ${spent}
- Total Withdrawals: ${withdrawn}

Subscriptions:
- Active: {active_count}
- Basic: {basic_count}
- Pro: {pro_count}

Users:
- Total: {total_users}
- With Balance: {with_balance}
```

---

### /admin_force_expire

**Trigger**: Admin sends `/admin_force_expire {user_id}`

**Response**:
```
✅ Subscription expired for user {user_id}
User downgraded to Free tier
```

---
## Error Response Formats

### Insufficient Balance Error
❌ رصيد غير كافٍ | Insufficient Balance
You need $X.XX more to purchase {item}.
Current balance: $Y.YY
[شحن الرصيد | Top Up Balance]

### Permission Denied (Non-Admin)
❌ غير مصرّح | Permission Denied
This command is for admins only.

### Transaction In Progress Error
⏳ معاملة قيد التنفيذ | Transaction In Progress
Please wait 5 seconds before trying again.

---
## Extra Generations Purchase Flow

**Trigger**: User exhausts quota, SPEC-008 displays [Purchase Extra] button

**Callback Data**: `gen_pack:start`

**Response**:
Message: "📦 حزم التوليد | Generation Packs"
Packs:

Small: $0.50 for 5 letters [شراء | Buy]
Medium: $1.00 for 12 letters [شراء | Buy]
Large: $3.00 for 40 letters [شراء | Buy]

[العودة | Back]

**Callback Patterns**:
| Callback Data | Action |
|--------------|--------|
| `gen_pack:small` | Select Small pack ($0.50/5) |
| `gen_pack:medium` | Select Medium pack ($1.00/12) |
| `gen_pack:large` | Select Large pack ($3.00/40) |

---

## Callback Query Patterns

| Callback Data | Action |
|--------------|--------|
| `wallet:top_up` | Show top-up flow |
| `wallet:withdraw` | Show withdraw flow |
| `subscribe:basic` | Select Basic tier |
| `subscribe:pro` | Select Pro tier |
| `confirm:yes` | Confirm purchase |
| `confirm:no` | Cancel purchase |
| `gen_pack:small` | Select Small pack |
| `gen_pack:medium` | Select Medium pack |
| `gen_pack:large` | Select Large pack |