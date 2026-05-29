"""
repository.py — Generic async CRUD repository pattern.
"""

import uuid
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.database.base_model import WealthBase

ModelT = TypeVar("ModelT", bound=WealthBase)


class BaseRepository(Generic[ModelT]):
    def __init__(self, model: Type[ModelT], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID, raise_not_found: bool = True) -> Optional[ModelT]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        instance = result.scalar_one_or_none()
        if instance is None and raise_not_found:
            raise NotFoundException(resource=self.model.__name__, identifier=str(id))
        return instance

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[ModelT]:
        result = await self.db.execute(
            select(self.model).order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    async def create(self, data: dict) -> ModelT:
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, data: dict) -> ModelT:
        instance = await self.get_by_id(id)
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        instance = await self.get_by_id(id, raise_not_found=False)
        if instance is None:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def exists(self, id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return result.scalar_one() > 0
