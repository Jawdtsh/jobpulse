import uuid
from abc import ABC
from typing import Generic, TypeVar, Type, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class AbstractRepository(ABC, Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self._session = session
        self._model = model

    async def get(self, id: uuid.UUID) -> Optional[ModelType]:
        stmt = select(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        stmt = select(self._model).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        instance = self._model(**kwargs)
        self._session.add(instance)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, **kwargs) -> Optional[ModelType]:
        instance = await self.get(id)
        if instance is None:
            return None

        # Fail-fast: Validate that all kwargs correspond to actual model attributes
        invalid_keys = [key for key in kwargs.keys() if not hasattr(instance, key)]
        if invalid_keys:
            raise ValueError(
                f"Invalid fields for {self._model.__name__}: {invalid_keys}"
            )

        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self._session.flush()
        await self._session.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        instance = await self.get(id)
        if instance is None:
            return False
        await self._session.delete(instance)
        await self._session.flush()
        return True
