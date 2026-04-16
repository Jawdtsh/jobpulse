# Bot Commands Contract

**Feature Branch**: `007-bot-handlers-ux`  
**Date**: 2026-04-16

## Commands

### /start

**Description**: Register new user or welcome existing user  
**Parameters**: Optional `ref_{code}` parameter for referral tracking  
**Response**: Welcome message with main menu buttons  

**Flow**:
1. Check if user exists by telegram_id
2. If new: create user record with auto-detected language, Free tier, unique referral code
3. If referral param provided: credit referring user
4. Display welcome message with main menu

**Response Format**:
```
مرحباً بك في JobPulse! 👋
اسمك: {first_name}
خطتك: {tier}

[Upload CV] [My Jobs] [Invite Friends] [Settings]
```

---

### /help

**Description**: Show all available commands with descriptions  
**Response**: List of commands and descriptions  

**Response Format**:
```
📋 المساعدة (Help)

/start - ابدأ الآن (Start)
/upload_cv - ارفع سيرتك الذاتية (Upload CV)
/my_cvs - سيرتي الذاتية (My CVs)
/my_jobs - الوظائف المحفوظة (Saved Jobs)
/settings - الإعدادات (Settings)
/invite - دعوة صديق (Invite Friend)
/subscribe - الخطط والاشتراكات (Plans)
/cancel - إلغاء (Cancel)
```

---

### /upload_cv

**Description**: Start CV upload flow  
**Parameters**: None  
**Response**: Prompt to send a file  

**Flow**:
1. Enter FSM state `CVUploadState.waiting_for_file`
2. Display upload prompt
3. Wait for file upload

**Response Format**:
```
📄 ارفع سيرتك الذاتية (Upload your CV)

• التنسيقات المدعومة: PDF, DOCX, TXT
• الحجم الأقصى: 5MB

أرسل الملف الآن (Send the file now)
```

---

### /my_cvs

**Description**: List all user CVs with status and actions  
**Parameters**: None  
**Response**: List of CV cards with delete buttons  

**Response Format**:
```
📁 سيرتي الذاتية (My CVs)

1. CV1.pdf - نشط (Active) - 85% - 2026-04-10
[Delete]

2. CV2.docx - غير نشط (Inactive) - 60% - 2026-04-05
[Delete]

[Upload New CV]
```

---

### /my_jobs

**Description**: Browse saved jobs, all notified, or dismissed  
**Parameters**: Optional view filter  
**Response**: Job list with pagination and filters  

**Flow**:
1. Display view selector: Saved | All Notified | Dismissed
2. Default to Saved view
3. Show filters: Similarity (>80%, >70%, All), Date (7d, 14d, 30d)
4. Paginate at 5 jobs per page

**Response Format**:
```
💼 وظائف محفوظة (Saved Jobs) - صفحة 1/3

[View: Saved | All | Dismissed]

1. Senior Developer @ TechCorp - 92% - منذ 3 ساعات (3h ago)
[View] [Cover Letter] [Unsave]

2. Backend Engineer @ StartupXYZ - 87% - منذ يوم (1d ago)
[View] [Cover Letter] [Unsave]

[Prev] 1/3 [Next]

[Filter: >80%] [Filter: 7 days]
```

---

### /settings

**Description**: View and edit user preferences  
**Parameters**: None  
**Response**: Settings display with edit options  

**Response Format**:
```
⚙️ الإعدادات (Settings)

• نسبة التطابق: 80% (Match Threshold)
  [60%] [70%] [80%] [90%] [100%]

• الإشعارات: ✅ مفعل (Enabled)

• اللغة: العربية (Arabic)

• الخطة: Free (Current Plan)
  [Upgrade to Basic] [Upgrade to Pro]

• رمز الإحالة: ABC123XYZ (Referral Code)
  [Copy] [Share]

📊 الإحصائيات: 5 مدعوون، 2 مسجلون (Stats: 5 invited, 2 registered)
```

---

### /invite

**Description**: Open referral interface with shareable link  
**Parameters**: None  
**Response**: Referral link with share options  

**Response Format**:
```
🎁 دعوة صديق (Invite a Friend)

مشاركة الرابط (Share Link):
https://t.me/jobpulse_bot?start=ref_{user_code}

كل 5 تسجيلات ناجحة = شهر مجاني من Basic!
(5 successful registrations = 1 free Basic month!)

[Share Link]
```

---

### /subscribe

**Description**: Display subscription tier comparison  
**Parameters**: None  
**Response**: Three-tier comparison with current tier highlighted  

**Response Format**:
```
💳 الخطط والاشتراكات (Subscription Plans)

📌 خطتك الحالية: Free (Current: Free)

┌─────────────────────────────────┐
│ 🆓 Free                         │
│ • سيرات CV: 1                   │
│ • تأخير الإشعارات: 24 ساعة      │
│ • خطابات الغلاف: 0             │
│ [Current Plan]                  │
├─────────────────────────────────┤
│ 🥉 Basic - $7/月               │
│ • سيرات CV: 1                   │
│ • تأخير الإشعارات: 12 ساعة      │
│ • خطابات الغلاف: 5             │
│ [Choose Plan]                   │
├─────────────────────────────────┤
│ 🥇 Pro - $12/月                 │
│ • سيرات CV: 2                   │
• • تأخير الإشعارات: فوري        │
• • خطابات الغلاف: غير محدود    │
│ [Choose Plan]                   │
└─────────────────────────────────┘

[Back to Menu]
```

---

### /cancel

**Description**: Cancel current operation and return to main menu  
**Parameters**: None  
**Response**: Main menu display  

**Flow**:
1. Clear current FSM state
2. Clear BotSession
3. Display main menu

---

## Rate Limits

- All commands subject to Telegram's 30 msg/s limit
- Implement message queuing with exponential backoff on limit hit

## Error Responses

- Invalid command: "الأمر غير معروف. /help (Unknown command. Use /help)"
- Session expired: "انتهت الجلسة. /start (Session expired. /start)"
- Rate limited: Retry with backoff, display "يرجى الانتظار... (Please wait...)"