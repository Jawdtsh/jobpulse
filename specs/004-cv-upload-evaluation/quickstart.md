# Quickstart: CV Upload & Evaluation

**Feature**: SPEC-004 - CV Upload & Evaluation  
**Date**: 2026-04-08

## Prerequisites

1. **Dependencies** (add to requirements.txt):
   ```
   PyPDF2>=3.0.0
   pdfplumber>=0.10.0
   python-docx>=1.0.0
   ```

2. **Configuration** (config/ai_models.py):
   - Add CV evaluation model: `gemini-2.5-pro` to `ACTIVE_MODELS` and `MODEL_TYPES`
   - Verify embedding model: `text-embedding-004` (768-dim)

3. **Database**:
   - Run Alembic migration to add evaluation columns to user_cvs table

## Implementation Order

### Phase 1: Core Services
1. **CV Parser** (`src/services/cv_parser.py`):
   - `extract_text_from_pdf(file_path) -> str`
   - `extract_text_from_docx(file_path) -> str`
   - `extract_text(file_path, format) -> str`

2. **CV Evaluator** (`src/services/cv_evaluator.py`):
   - `evaluate_cv(text) -> CVEvaluationResult`
   - Uses AIProviderService.call_model with gemini-2.5-pro
   - Returns: skills, experience_summary, completeness_score, improvement_suggestions

3. **CV Service** (`src/services/cv_service.py`):
   - `upload_cv(user_id, file) -> UserCV`
   - `evaluate_cv(cv_id) -> CVEvaluationResult`
   - `list_user_cvs(user_id) -> list[UserCV]`
   - `activate_cv(cv_id, user_id) -> UserCV`
   - `deactivate_cv(cv_id, user_id) -> UserCV`
   - `delete_cv(cv_id, user_id) -> bool`
   - `check_quota(user_id) -> (allowed, remaining)`

### Phase 2: Bot Integration
4. **Bot Handlers** (`src/bot/handlers/cv_handlers.py`):
   - Handle document messages (PDF/DOCX/TXT)
   - Process file upload, validation, parsing
   - Display evaluation results to user
   - CV management commands (/mycvs, /activatecv, /deletecv)

### Phase 3: Testing
5. **Unit Tests**:
   - Test CV parser with sample files
   - Test evaluator with mock AI responses
   - Test service business logic

## Key Interfaces

### CVParser Interface
```python
class CVParserProtocol:
    async def extract_text(self, file_path: Path, format: str) -> str: ...
```

### CVEvaluator Interface
```python
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class CVEvaluationResult:
    skills: list[str]
    experience_summary: str
    completeness_score: Decimal
    improvement_suggestions: list[str]

class CVEvaluatorProtocol:
    async def evaluate(self, text: str) -> CVEvaluationResult: ...
```

### CVService Interface
```python
class CVServiceProtocol:
    async def upload(self, user_id: UUID, file: UploadFile) -> UserCV: ...
    async def evaluate(self, cv_id: UUID) -> CVEvaluationResult: ...
    async def list(self, user_id: UUID) -> list[UserCV]: ...
    async def activate(self, cv_id: UUID, user_id: UUID) -> UserCV: ...
    async def deactivate(self, cv_id: UUID, user_id: UUID) -> UserCV: ...
    async def delete(self, cv_id: UUID, user_id: UUID) -> bool: ...
```

## Common Issues

| Issue | Solution |
|-------|----------|
| PyPDF2 fails on scanned PDF | Try pdfplumber fallback |
| Empty text extraction | Reject with error (FR-007a) |
| AI returns malformed JSON | Retry with timeout, log error |
| Quota exceeded | Show upgrade prompt |
| CV limit reached | Show upgrade prompt, offer replace |

## Success Metrics

- CV upload: <30 seconds
- Text extraction: 95% success rate
- Evaluation: <10 seconds
- Encryption: 100% correct decryption