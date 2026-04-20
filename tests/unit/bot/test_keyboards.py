import uuid

from src.bot.keyboards import (
    cv_warning_keyboard,
    cover_letter_customization_keyboard,
    quota_exhausted_keyboard,
)


def test_cv_warning_keyboard_generates_anyway_callback_has_job_prefix():
    job_id = str(uuid.uuid4())
    kb = cv_warning_keyboard(job_id)

    generate_btn = None
    for row in kb.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("cl_generate_anyway"):
                generate_btn = btn
                break

    assert generate_btn is not None
    parts = generate_btn.callback_data.split(":")
    assert parts[0] == "cl_generate_anyway"
    assert parts[1] == "job"
    assert parts[2] == job_id


def test_customization_keyboard_default_language_is_arabic():
    kb = cover_letter_customization_keyboard()
    all_callbacks = []
    for row in kb.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                all_callbacks.append(btn.callback_data)

    found_arabic = False
    for row in kb.inline_keyboard:
        for btn in row:
            if btn.callback_data == "cl_lang:arabic" and "✅" in btn.text:
                found_arabic = True
    assert found_arabic


def test_quota_exhausted_keyboard_pro_has_no_upgrade():
    kb = quota_exhausted_keyboard(current_tier="pro")
    all_callbacks = []
    for row in kb.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                all_callbacks.append(btn.callback_data)
    assert "upgrade_plan:basic" not in all_callbacks


def test_quota_exhausted_keyboard_free_has_upgrade():
    kb = quota_exhausted_keyboard(current_tier="free")
    all_callbacks = []
    for row in kb.inline_keyboard:
        for btn in row:
            if btn.callback_data:
                all_callbacks.append(btn.callback_data)
    assert "upgrade_plan:basic" in all_callbacks


def test_customization_keyboard_single_adjust_layout():
    kb = cover_letter_customization_keyboard()
    rows = kb.inline_keyboard
    assert len(rows) == 6
    assert len(rows[0]) == 3
    assert len(rows[1]) == 3
    assert len(rows[2]) == 4
    assert len(rows[3]) == 3
    assert len(rows[4]) == 1
    assert len(rows[5]) == 1
