# Research: CV Upload & Evaluation

**Date**: 2026-04-08  
**Feature**: SPEC-004 - CV Upload & Evaluation

## Decisions

### 1. CV File Parsing Libraries

**Decision**: Use PyPDF2 for PDF with pdfplumber fallback; use python-docx for DOCX; direct text for TXT.

**Rationale**: 
- PyPDF2 is lightweight and widely used for basic PDF text extraction
- pdfplumber provides more robust extraction for complex PDFs
- python-docx is the standard for DOCX parsing in Python

**Alternatives considered**:
- pdfminer.six - More powerful but slower, not needed for typical CVs
- docx2txt - Simpler but less flexible than python-docx

### 2. AI Evaluation Model

**Decision**: Use Gemini 2.5 Pro (gemini-2.5-pro) via existing AIProviderService.

**Rationale**:
- Per specification: "Gemini Pro only (no fallback for deep analysis)"
- Existing AIProviderService already configured with Google provider
- Structured JSON response support via response_format parameter

**Alternatives considered**:
- OpenAI GPT models - Not used per spec requirement
- Local models - Not viable for quality evaluation

### 3. Embedding Model

**Decision**: Use Text Embedding 004 via existing AIProviderService.

**Rationale**:
- Generates exactly 768-dimension vectors (matches job embeddings)
- Already integrated into AIProviderService
- Daily limits configurable in config/ai_models.py

### 4. Encryption Approach

**Decision**: Use existing Fernet encryption from src/utils/encryption.py.

**Rationale**:
- Already implemented and tested
- Uses AES-128-CBC with HMAC for authentication
- Key rotation requires re-encrypting all stored CVs (per clarification)

### 5. Subscription Quota Storage

**Decision**: Use Redis for monthly evaluation quota tracking (like daily limits).

**Rationale**:
- Redis already used for daily limit tracking in AIProviderService
- Monthly reset can be implemented with first-of-month key suffix
- Fast, in-memory, suitable for counter operations

### 6. CV Storage Schema

**Decision**: Extend existing user_cvs table with new columns for evaluation data.

**Rationale**:
- Table already exists with: id, user_id, title, content (encrypted), embedding_vector, is_active
- Need to add: skills (JSON), experience_summary (text), completeness_score (numeric), improvement_suggestions (JSON), evaluated_at (timestamp)
- Use Alembic migration for schema changes

**Alternatives considered**:
- Separate table for evaluations - Adds complexity for 1:1 relationship
- Store as JSON in single column - Less queryable, but acceptable for structured data

## Research Complete

All technical decisions aligned with existing codebase patterns and specification requirements. No further research needed.