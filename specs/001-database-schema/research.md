# Research: Database Schema & Migrations

## Decision: Async SQLAlchemy 2.0 with PostgreSQL and pgvector

**Rationale**: Project requires async operations for performance. SQLAlchemy 2.0 provides native async support with asyncpg driver. pgvector extension enables vector similarity search essential for job matching.

**Alternatives evaluated**:
- SQLAlchemy 1.4 with asyncio compatibility layer: More mature but 2.0 is the future
- Raw asyncpg: Loses ORM benefits, more verbose code
- ORM alternatives (Django ORM, Peewee): Less flexible for complex queries

---

## Decision: Alembic with async SQLAlchemy engine

**Rationale**: Constitution requires Alembic for all migrations. Need to configure Alembic to work with async SQLAlchemy engines.

**Alternatives evaluated**:
- Using `alembic.ini` with async URL: Supported in recent Alembic versions
- Custom async migration runners: Unnecessary complexity
- Manual migration scripts: Violates Constitution VII

**Implementation pattern**:
```python
# alembic/env.py uses run_migrations_offline/online with async engine
from sqlalchemy.ext.asyncio import create_async_engine
```

---

## Decision: Fernet encryption for sensitive fields

**Rationale**: Constitution IV requires Fernet encryption for CV data at rest. Will implement custom SQLAlchemy type for transparent encryption/decryption.

**Alternatives evaluated**:
- Database-level encryption (pgcrypto): Less flexible, tied to PostgreSQL
- Application-level encryption with hashing: CVs need to be readable
- Column-level encryption (TDE): Requires database configuration changes

**Implementation pattern**:
```python
class FernetColumn(TypeDecorator):
    impl = LargeBinary
    # Encrypt on bind, decrypt on result processing
```

---

## Decision: Repository pattern with async CRUD operations

**Rationale**: Constitution I requires Repository pattern for all database access. Async support requires careful design to maintain clean architecture.

**Alternatives evaluated**:
- DAO pattern: Similar but less explicit about abstraction
- Active Record: Mixes business logic with data access
- Direct service-layer queries: Violates Clean Architecture

**Implementation pattern**:
```python
class AbstractRepository(ABC):
    @abstractmethod
    async def get(self, id: UUID) -> Optional[Model]: ...
    
class UserRepository(AbstractRepository):
    def __init__(self, session: AsyncSession): ...
```

---

## Decision: HNSW vector indexes with m=16, ef_construction=64

**Rationale**: pgvector recommends HNSW for production workloads with large datasets. Parameters m=16 and ef_construction=64 balance speed and accuracy.

**Alternatives evaluated**:
- IVFFlat: Good for smaller datasets, slower for exact k-NN
- Brute force: Too slow for production scale

---

## Decision: SQLAlchemy ORM models with declarative base

**Rationale**: Standard SQLAlchemy 2.0 approach. Declarative base provides clean model definition.

**Alternatives evaluated**:
- Imperative/functional mapping: More verbose, less readable
- SQLModel: Good but adds another dependency layer

---

## Decision: Environment-based configuration for all database settings

**Rationale**: Constitution V requires all settings from config/settings.py. Database connection details must be configurable without code changes.

**Environment variables required**:
- DATABASE_URL (async format: postgresql+asyncpg://...)
- FERNET_KEY (for encryption)
- Connection pool settings from config

---

## Summary of Technical Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| ORM | SQLAlchemy 2.0 async | Constitution compliance, performance |
| Migration | Alembic | Constitution VII |
| Encryption | Fernet | Constitution IV |
| Architecture | Repository pattern | Constitution I |
| Indexes | HNSW (m=16, ef_construction=64) | Performance for vector search |
| Config | Environment variables | Constitution V |
