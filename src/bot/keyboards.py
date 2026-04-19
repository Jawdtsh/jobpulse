from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 رفع سيرة ذاتية (Upload CV)", callback_data="menu:upload_cv")
    builder.button(text="💼 وظائفي (My Jobs)", callback_data="menu:my_jobs")
    builder.button(text="🎁 دعوة صديق (Invite Friends)", callback_data="menu:invite")
    builder.button(text="⚙️ الإعدادات (Settings)", callback_data="menu:settings")
    builder.adjust(2)
    return builder.as_markup()


def job_notification_keyboard(job_id: str, match_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💾 حفظ (Save)", callback_data=f"save_job:{job_id}")
    builder.button(text="📋 تفاصيل (Details)", callback_data=f"job_details:{job_id}")
    builder.button(text="🗑️ تجاهل (Dismiss)", callback_data=f"dismiss_match:{match_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def saved_jobs_view_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💾 المحفوظة (Saved)", callback_data="view:saved")
    builder.button(text="📋 كل الإشعارات (All)", callback_data="view:notified")
    builder.button(text="🗑️ المتجاهلة (Dismissed)", callback_data="view:dismissed")
    builder.adjust(3)
    return builder.as_markup()


def pagination_keyboard(
    view: str, current_page: int, total_pages: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_page > 1:
        builder.button(
            text="◀️ السابق (Prev)", callback_data=f"jobs_page:{view}:{current_page - 1}"
        )
    builder.button(
        text=f"{current_page}/{total_pages}",
        callback_data=f"jobs_page:{view}:{current_page}",
    )
    if current_page < total_pages:
        builder.button(
            text="التالي ▶️ (Next)", callback_data=f"jobs_page:{view}:{current_page + 1}"
        )
    builder.adjust(3)
    return builder.as_markup()


def similarity_filter_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=">80%", callback_data="filter_sim:80")
    builder.button(text=">70%", callback_data="filter_sim:70")
    builder.button(text="الكل (All)", callback_data="filter_sim:all")
    builder.adjust(3)
    return builder.as_markup()


def date_filter_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="7 أيام (7d)", callback_data="filter_date:7")
    builder.button(text="14 يوم (14d)", callback_data="filter_date:14")
    builder.button(text="30 يوم (30d)", callback_data="filter_date:30")
    builder.button(text="الكل (All)", callback_data="filter_date:all")
    builder.adjust(2, 2)
    return builder.as_markup()


def settings_keyboard(
    threshold: int, *, notifications_on: bool
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for val in [60, 70, 80, 90, 100]:
        marker = " ✅" if val == threshold else ""
        builder.button(text=f"{val}%{marker}", callback_data=f"threshold:{val}")
    builder.adjust(5)

    notif_text = (
        "🔕 إيقاف الإشعارات (Off)" if notifications_on else "🔔 تفعيل الإشعارات (On)"
    )
    builder.button(text=notif_text, callback_data="toggle_notifications")
    builder.button(text="💳 ترقية الخطة (Upgrade)", callback_data="upgrade_plan:basic")
    builder.button(text="📋 نسخ الرمز (Copy Code)", callback_data="copy_referral")
    builder.button(text="🔗 مشاركة (Share)", callback_data="share_referral")
    builder.button(text="🏠 القائمة (Menu)", callback_data="back_to_menu")
    builder.adjust(5, 2, 2, 1)
    return builder.as_markup()


def cv_list_keyboard(cvs: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cv in cvs:
        status = "✅" if cv.get("is_active") else "⏸️"
        builder.button(
            text=f"{status} {cv['title']}",
            callback_data=f"cv_details:{cv['id']}",
        )
    builder.button(text="📤 رفع جديد (Upload New)", callback_data="menu:upload_cv")
    builder.button(text="🏠 القائمة (Menu)", callback_data="back_to_menu")
    builder.adjust(1, 2)
    return builder.as_markup()


def cv_details_keyboard(cv_id: str, *, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_active:
        builder.button(text="✅ تفعيل (Activate)", callback_data=f"activate_cv:{cv_id}")
    builder.button(text="🗑️ حذف (Delete)", callback_data=f"delete_cv:{cv_id}")
    builder.button(text="🔙 رجوع (Back)", callback_data="back_to_cvs")
    builder.adjust(2, 1)
    return builder.as_markup()


def confirm_delete_keyboard(cv_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ نعم (Yes)", callback_data=f"confirm_delete:{cv_id}:yes")
    builder.button(text="❌ لا (No)", callback_data=f"confirm_delete:{cv_id}:no")
    builder.adjust(2)
    return builder.as_markup()


def confirm_replace_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ نعم استبدل (Yes Replace)", callback_data="confirm_replace:yes"
    )
    builder.button(text="❌ لا (No)", callback_data="confirm_replace:no")
    builder.adjust(2)
    return builder.as_markup()


def subscription_keyboard(current_tier: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if current_tier != "basic":
        builder.button(text="🥉 Basic - $7/شهر", callback_data="upgrade_plan:basic")
    else:
        builder.button(text="🥉 Basic ✅", callback_data="upgrade_plan:current")
    if current_tier != "pro":
        builder.button(text="🥇 Pro - $12/شهر", callback_data="upgrade_plan:pro")
    else:
        builder.button(text="🥇 Pro ✅", callback_data="upgrade_plan:current")
    builder.button(text="🏠 القائمة (Menu)", callback_data="back_to_menu")
    builder.adjust(2, 1)
    return builder.as_markup()


def referral_keyboard(referral_code: str, bot_username: str) -> InlineKeyboardMarkup:
    link = f"https://t.me/{bot_username}?start=ref_{referral_code}"
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔗 مشاركة الرابط (Share)", url=f"https://t.me/share/url?url={link}"
    )
    builder.button(text="📋 نسخ الرمز (Copy)", callback_data="copy_referral")
    builder.button(text="🏠 القائمة (Menu)", callback_data="back_to_menu")
    builder.adjust(1, 2)
    return builder.as_markup()


def error_retry_keyboard(action: str, params: str = "") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 إعادة المحاولة (Retry)", callback_data=f"retry:{action}:{params}"
    )
    builder.button(text="🏠 القائمة (Menu)", callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def job_card_keyboard(job_id: str, *, is_saved: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_saved:
        builder.button(
            text="💾 إلغاء الحفظ (Unsave)", callback_data=f"unsave_job:{job_id}"
        )
    else:
        builder.button(text="💾 حفظ (Save)", callback_data=f"save_job:{job_id}")
    builder.button(text="📋 تفاصيل (Details)", callback_data=f"job_details:{job_id}")
    builder.adjust(2)
    return builder.as_markup()


def cover_letter_keyboard(job_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📝 خطاب تغطية (Cover Letter)",
        callback_data=f"cover_letter:start:{job_id}",
    )
    return builder.as_markup()


def cover_letter_customization_keyboard(
    tone: str = "professional",
    length: str = "medium",
    focus: str = "all",
    language: str = "english",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    def _marker(current: str, value: str) -> str:
        return " ✅" if current == value else ""

    builder.button(
        text=f"Formal{_marker(tone, 'formal')}",
        callback_data="cl_tone:formal",
    )
    builder.button(
        text=f"Casual{_marker(tone, 'casual')}",
        callback_data="cl_tone:casual",
    )
    builder.button(
        text=f"Professional{_marker(tone, 'professional')}",
        callback_data="cl_tone:professional",
    )
    builder.adjust(3)

    builder.button(
        text=f"Short{_marker(length, 'short')}",
        callback_data="cl_length:short",
    )
    builder.button(
        text=f"Medium{_marker(length, 'medium')}",
        callback_data="cl_length:medium",
    )
    builder.button(
        text=f"Long{_marker(length, 'long')}",
        callback_data="cl_length:long",
    )
    builder.adjust(3)

    builder.button(
        text=f"Skills{_marker(focus, 'skills')}",
        callback_data="cl_focus:skills",
    )
    builder.button(
        text=f"Experience{_marker(focus, 'experience')}",
        callback_data="cl_focus:experience",
    )
    builder.button(
        text=f"Education{_marker(focus, 'education')}",
        callback_data="cl_focus:education",
    )
    builder.button(
        text=f"All{_marker(focus, 'all')}",
        callback_data="cl_focus:all",
    )
    builder.adjust(4)

    builder.button(
        text=f"🇬🇧 English{_marker(language, 'english')}",
        callback_data="cl_lang:english",
    )
    builder.button(
        text=f"🇸🇦 عربي{_marker(language, 'arabic')}",
        callback_data="cl_lang:arabic",
    )
    builder.button(
        text=f"🌍 Both{_marker(language, 'bilingual')}",
        callback_data="cl_lang:bilingual",
    )
    builder.adjust(3)

    builder.button(
        text="✨ Generate Cover Letter",
        callback_data="cl_generate",
    )
    builder.button(
        text="❌ Cancel",
        callback_data="cl_cancel",
    )
    builder.adjust(1, 2)

    return builder.as_markup()


def cover_letter_action_keyboard(cover_letter_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Regenerate",
        callback_data=f"cover_letter:regenerate:{cover_letter_id}",
    )
    builder.button(
        text="📋 Copy Text",
        callback_data=f"cover_letter:copy:{cover_letter_id}",
    )
    builder.button(
        text="🏠 Menu",
        callback_data="back_to_menu",
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def quota_exhausted_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏰ Wait for Reset",
        callback_data="cover_letter:wait",
    )
    builder.button(
        text="💰 Purchase Extra",
        callback_data="cover_letter:purchase:menu",
    )
    builder.button(
        text="⬆️ Upgrade Plan",
        callback_data="upgrade_plan:basic",
    )
    builder.button(
        text="🏠 Menu",
        callback_data="back_to_menu",
    )
    builder.adjust(2, 2)
    return builder.as_markup()


def purchase_packs_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="$0.50 - 5 generations",
        callback_data="cover_letter:purchase:small",
    )
    builder.button(
        text="$1.00 - 12 generations",
        callback_data="cover_letter:purchase:medium",
    )
    builder.button(
        text="$3.00 - 40 generations",
        callback_data="cover_letter:purchase:large",
    )
    builder.button(
        text="🔙 Back",
        callback_data="cover_letter:purchase:menu",
    )
    builder.adjust(1, 2)
    return builder.as_markup()


def cv_warning_keyboard(job_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Generate Anyway",
        callback_data=f"cl_generate_anyway:{job_id}",
    )
    builder.button(
        text="✏️ Edit CV First",
        callback_data="menu:upload_cv",
    )
    builder.button(
        text="❌ Cancel",
        callback_data="cl_cancel",
    )
    builder.adjust(2, 1)
    return builder.as_markup()
