import hashlib

from src.utils.text_normalizer import normalize_text


def compute_content_hash(raw_text: str) -> str:
    normalized = normalize_text(raw_text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
