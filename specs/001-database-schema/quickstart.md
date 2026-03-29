# Quickstart: Database Schema & Migrations

## Prerequisites

- PostgreSQL 16 with pgvector extension
- Python 3.12+
- Environment variables configured in `.env`

## Setup Steps

### 1. Configure Database Connection

Edit `.env` with your database credentials:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/jobpulse
FERNET_KEY=your-fernet-key-here
```

Generate a Fernet key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Initialize pgvector Extension

The migration will create the extension automatically, but you can verify:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Run Migrations

```bash
# Run all migrations
alembic upgrade head

# Verify migration status
alembic current
alembic history --verbose
```

### 4. Verify Schema

```bash
# Check tables exist
psql $DATABASE_URL -c "\dt"

# Check indexes (including HNSW)
psql $DATABASE_URL -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'public';"
```

## Project Structure

```
migrations/
├── env.py              # Alembic environment (async)
├── script.py.mako     # Migration template
└── versions/
    ├── 001_initial_schema.py      # 12 tables
    ├── 002_hnsw_indexes.py       # Vector indexes
    └── 003_performance_indexes.py  # B-tree indexes

src/
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── user_cv.py
│   ├── job.py
│   └── ...
├── repositories/
│   ├── __init__.py
│   ├── base.py
│   ├── user_repository.py
│   └── ...
└── database.py         # Async engine setup

tests/
├── integration/
│   ├── test_user_repository.py
│   └── ...
└── unit/
    └── ...
```

## Usage Examples

### Creating a User

```python
from src.database import get_async_session
from src.repositories.user_repository import UserRepository

async def create_user(telegram_id: int, first_name: str):
    async with get_async_session() as session:
        repo = UserRepository(session)
        user = await repo.create(
            telegram_id=telegram_id,
            first_name=first_name
        )
        return user
```

### Storing an Encrypted CV

```python
from src.repositories.cv_repository import CVRepository

async def save_cv(user_id: UUID, title: str, content: str):
    async with get_async_session() as session:
        repo = CVRepository(session)
        cv = await repo.create_with_embedding(
            user_id=user_id,
            title=title,
            content=content  # Automatically encrypted
        )
        return cv
```

### Vector Similarity Search

```python
from src.repositories.job_repository import JobRepository

async def find_similar_jobs(embedding: list[float], threshold: float = 0.8):
    async with get_async_session() as session:
        repo = JobRepository(session)
        jobs = await repo.find_similar(embedding, threshold)
        return jobs
```

## Testing

```bash
# Run integration tests
pytest tests/integration/ -v

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest --cov=src --cov-report=html
```

## Rollback

```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001

# Rollback all
alembic downgrade base
```

## Troubleshooting

### pgvector Extension Missing

```bash
# Install pgvector
# On Ubuntu:
apt-get install postgresql-16-pgvector

# Or build from source
```

### Connection Pool Exhausted

Check connection pool settings in config/settings.py:

```python
DATABASE_POOL_SIZE = 5
DATABASE_MAX_OVERFLOW = 10
```

### Encryption Key Rotation

1. Update FERNET_KEY in .env
2. Re-encrypt all sensitive data (CVs, sessions)
3. Verify data integrity
