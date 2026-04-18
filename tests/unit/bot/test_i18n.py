from unittest.mock import patch
from src.bot.utils.i18n import get_locale, t


def test_get_locale_arabic():
    assert get_locale("ar") == "ar"
    assert get_locale("ar-SA") == "ar"
    assert get_locale("ar-EG") == "ar"


def test_get_locale_non_arabic_returns_arabic_default():
    assert get_locale("en") == "ar"
    assert get_locale("fr") == "ar"
    assert get_locale("es") == "ar"


def test_get_locale_none_returns_arabic_default():
    assert get_locale(None) == "ar"


def test_t_returns_arabic_by_default():
    messages = {"hello": {"ar": "مرحبا", "en": "Hello"}}
    with patch("src.bot.utils.i18n._MESSAGES", messages):
        assert t("hello") == "مرحبا"


def test_t_returns_key_when_missing():
    with patch("src.bot.utils.i18n._MESSAGES", {}):
        assert t("nonexistent") == "nonexistent"
