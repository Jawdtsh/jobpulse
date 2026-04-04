# Research: Settings & Config Layer

## Decision: Pydantic v2 BaseSettings with python-dotenv

**Rationale**: 
- Pydantic v2 BaseSettings provides built-in environment variable loading with type validation
- python-dotenv handles .env file loading for local development
- Field validators allow custom validation logic (Fernet key format, bot token format, etc.)
- SecretStr type provides built-in masking for sensitive values
- Environment variables take precedence over .env file by default

**Alternatives considered**:
- Pydantic v1 BaseSettings - Rejected: v2 is current standard with better performance and validation
- Custom config class with os.environ - Rejected: No type safety, manual validation required
- Dynaconf - Rejected: Overkill for this use case; adds unnecessary complexity

## Decision: Settings class structure with nested models

**Rationale**:
- Single Settings class with nested category models (DatabaseSettings, RedisSettings, etc.) provides clean organization
- Each category model can have its own validators
- Easy to import specific settings groups in tests
- Follows Pydantic best practices for complex configurations

**Alternatives considered**:
- Flat Settings class with all fields - Rejected: Hard to maintain, no logical grouping
- Multiple separate settings modules - Rejected: Violates single import principle from spec

## Decision: Secret masking via custom __repr__ and __str__

**Rationale**:
- Override __repr__ and __str__ methods on Settings class to mask secrets
- Show first 8 characters only for API keys and tokens
- Use Pydantic's SecretStr type where appropriate for automatic masking
- Custom validator for Fernet key format validation (44-char base64)

**Alternatives considered**:
- Logging filter to mask secrets - Rejected: Doesn't prevent accidental exposure in error messages
- Separate masked/unmasked settings instances - Rejected: Confusing, error-prone

## Decision: Integration with existing ai_models.py

**Rationale**:
- Import AI model definitions from config/ai_models.py into settings
- Settings class references AI model config rather than duplicating
- Maintains Constitution V compliance: "ALL AI model names MUST come from config/ai_models.py only"
- AI model API keys loaded from environment, model definitions from ai_models.py

**Alternatives considered**:
- Merge ai_models.py into settings.py - Rejected: Violates Constitution V principle about AI model names source
- Keep AI models completely separate - Rejected: Settings should be single source of truth for all config

## Decision: Validation at import time (fail-fast)

**Rationale**:
- Pydantic BaseSettings validates on instantiation
- Module-level singleton instantiation ensures validation happens at import
- Clear error messages with field names and expected formats
- Application fails before any business logic executes if config is invalid

**Alternatives considered**:
- Lazy validation on first access - Rejected: Errors surface too late, harder to debug
- Validation endpoint for runtime checking - Rejected: Unnecessary complexity for startup config
