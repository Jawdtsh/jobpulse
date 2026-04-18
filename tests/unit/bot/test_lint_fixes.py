import inspect

import pytest

from src.bot.handlers.subscription import cmd_subscribe


def test_subscription_no_dead_if_else():
    source = inspect.getsource(cmd_subscribe)
    assert 'if tier == "free" else "subscribe_free"' not in source


def test_subscription_uses_loop():
    source = inspect.getsource(cmd_subscribe)
    assert "tiers_info" in source
    assert "for tier_key, msg_key in tiers_info:" in source


def test_keyboards_keyword_only_bools():
    import inspect as insp
    from src.bot.keyboards import (
        settings_keyboard,
        cv_details_keyboard,
        job_card_keyboard,
    )

    sig_settings = insp.signature(settings_keyboard)
    assert (
        insp.Parameter.KEYWORD_ONLY == sig_settings.parameters["notifications_on"].kind
    )

    sig_cv = insp.signature(cv_details_keyboard)
    assert insp.Parameter.KEYWORD_ONLY == sig_cv.parameters["is_active"].kind

    sig_job = insp.signature(job_card_keyboard)
    assert insp.Parameter.KEYWORD_ONLY == sig_job.parameters["is_saved"].kind


@pytest.mark.asyncio
async def test_error_handler_detects_locale():
    from src.bot.handlers.errors import on_error

    source = inspect.getsource(on_error)
    assert "get_locale" in source
    assert 'locale = "ar"' not in source


def test_referral_no_hardcoded_bot_username():
    source = inspect.getsource(
        __import__("src.bot.handlers.referral", fromlist=["src.bot.handlers"])
    )
    assert "jobpulse_bot" not in source
    assert "get_settings" in source
