import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MESSAGES: dict[str, dict[str, str]] | None = None
_DEFAULT_LOCALE = "ar"


def _load_messages() -> dict[str, dict[str, str]]:
    global _MESSAGES
    if _MESSAGES is not None:
        return _MESSAGES

    messages_path = Path(__file__).parent.parent / "locales" / "messages.json"
    try:
        with open(messages_path, encoding="utf-8") as f:
            _MESSAGES = json.load(f)
    except FileNotFoundError:
        logger.warning("Messages file not found at %s", messages_path)
        _MESSAGES = {}
    except json.JSONDecodeError:
        logger.error("Invalid JSON in messages file %s", messages_path)
        _MESSAGES = {}
    return _MESSAGES


def t(key: str, locale: str = _DEFAULT_LOCALE, **kwargs) -> str:
    messages = _load_messages()
    entry = messages.get(key, {})
    text = entry.get(locale) or entry.get(_DEFAULT_LOCALE) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def bilingual(key: str, **kwargs) -> str:
    ar = t(key, "ar", **kwargs)
    en = t(key, "en", **kwargs)
    if ar == en:
        return ar
    return f"{ar}\n({en})"


def get_locale(user_lang_code: str | None) -> str:
    if user_lang_code and user_lang_code.lower().startswith("ar"):
        return "ar"
    return "en"
