from typing import Any
import hashlib
import json


VECTOR_DIMENSIONS = 768


def generate_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_content_hash_from_dict(data: dict[str, Any]) -> str:
    json_string = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_string.encode("utf-8")).hexdigest()


def validate_vector_dimensions(vector: list[float]) -> bool:
    return len(vector) == VECTOR_DIMENSIONS


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same dimension")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    if norm1 == 0 or norm2 == 0:
        return 0.0

    EPSILON = 1e-10
    return dot_product / (norm1 * norm2) if abs(norm1 * norm2) > EPSILON else 0.0


def normalize_vector(vector: list[float]) -> list[float]:
    EPSILON = 1e-10
    norm = sum(x * x for x in vector) ** 0.5
    if norm <= EPSILON:
        return vector
    return [x / norm for x in vector]
