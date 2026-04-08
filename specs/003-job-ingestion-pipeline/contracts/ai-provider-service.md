# Contract: AI Provider Service Interface

## Purpose

Defines the abstract interface for the AI provider service that handles model calls with fallback chain, retry logic, and daily limit tracking.

## Interface: AIProviderService

### Method: `call_model`

Calls an AI model with automatic fallback through the provider chain.

**Signature**:
```python
async def call_model(
    model_type: str,
    prompt: str,
    system_prompt: str | None = None,
    response_format: dict | None = None,
    timeout: int = 30,
) -> str
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_type | str | Yes | One of: `classifier`, `extractor`, `embedder`, `evaluator` |
| prompt | str | Yes | User prompt/message content |
| system_prompt | str | No | System instruction for the model |
| response_format | dict | No | JSON schema for structured output (extractor only) |
| timeout | int | No | Request timeout in seconds (default: 30) |

**Returns**: Raw response text from the first successful provider.

**Raises**:
- `AIServiceUnavailableError`: All providers in the fallback chain failed
- `DailyLimitReachedError`: Model has reached its daily request limit
- `InvalidModelTypeError`: model_type not in ACTIVE_MODELS

**Behavior**:
1. Look up `model_type` in `ACTIVE_MODELS` from `config/ai_models.py`
2. Check daily limit in Redis cache; raise `DailyLimitReachedError` if exceeded
3. Iterate through `FALLBACK_CHAIN[model_type]` providers in order
4. For each provider: attempt call with exponential backoff (1s, 2s, 4s), max 3 retries
5. On success: increment daily usage counter in Redis, return response
6. On all failures: log error with provider names, raise `AIServiceUnavailableError`

---

### Method: `generate_embedding`

Generates a vector embedding for the given text.

**Signature**:
```python
async def generate_embedding(
    text: str,
    expected_dimensions: int = 768,
) -> list[float] | None
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | str | Yes | Input text to embed |
| expected_dimensions | int | No | Expected vector length for validation (default: 768) |

**Returns**: List of floats (embedding vector), or `None` if all providers fail.

**Raises**:
- `InvalidEmbeddingDimensionsError`: Vector length does not match expected_dimensions

**Behavior**:
1. Call embedder model via `call_model` with embedding-specific logic
2. Validate returned vector length matches `expected_dimensions`
3. On mismatch: retry up to 3 times
4. If all retries fail: return `None` (caller decides whether to proceed)

---

### Method: `check_daily_limit`

Checks if a model has remaining daily quota.

**Signature**:
```python
async def check_daily_limit(self, model_name: str) -> bool
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_name | str | Yes | Exact model name from ACTIVE_MODELS |

**Returns**: `True` if requests remain under daily limit, `False` if limit reached.

---

### Method: `increment_usage`

Increments the daily usage counter for a model.

**Signature**:
```python
async def increment_usage(self, model_name: str) -> int
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model_name | str | Yes | Exact model name from ACTIVE_MODELS |

**Returns**: Updated daily request count.

**Behavior**:
- Increments Redis counter with key `ai_daily_usage:{model_name}:{YYYY-MM-DD}`
- Counter expires at end of day (86400s TTL)
