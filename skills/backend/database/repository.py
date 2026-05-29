"""
repository.py — Generic async CRUD repository pattern.

All database access goes through a repository. Routes never use the session directly.
Extend BaseRepository for each model to add domain-specific queries.

Dependencies: base_model.py, exceptions.py (Tier 3)
Consumed by: All route handlers, AI tools, compliance engine

Example usage:
    class ClientRepository(BaseRepository[Client]):
        async def get_by_email(self, email: str) -> Optional[Client]:
            result = await self.db.execute(
                select(Client).where(Client.email == email)
            )
            return result.scalar_one_or_none()

    # In route handler:
    client_repo = ClientRepository(Client, db_session)
    client = await client_repo.get_by_id(client_id)
"""

import uuid
from typing import Generic, Optional, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from skills.backend.core.exceptions import NotFoundException
from skills.backend.database.base_model import WealthBase

ModelT = TypeVar("ModelT", bound=WealthBase)


class BaseRepository(Generic[ModelT]):
    """
    Generic async CRUD repository.

    Type parameter ModelT is the SQLAlchemy ORM model class.
    """

    def __init__(self, model: Type[ModelT], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: uuid.UUID, raise_not_found: bool = True) -> Optional[ModelT]:
        """
        Fetch a single record by primary key.

        Args:
            id: UUID primary key
            raise_not_found: If True and record missing, raise NotFoundException

        Returns:
            Model instance or None (if raise_not_found=False)
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        instance = result.scalar_one_or_none()
        if instance is None and raise_not_found:
            raise NotFoundException(
                resource=self.model.__name__,
                identifier=str(id),
            )
        return instance

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelT]:
        """
        Fetch all records with pagination.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum records to return
        """
        result = await self.db.execute(
            select(self.model)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return total record count."""
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def create(self, data: dict) -> ModelT:
        """
        Create a new record.

        Args:
            data: Dict of field values (must match model columns)

        Returns:
            Created model instance (with id and timestamps populated)
        """
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()  # Get ID without committing transaction
        await self.db.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, data: dict) -> ModelT:
        """
        Update an existing record.

        Args:
            id: UUID of record to update
            data: Dict of fields to update (partial update supported)

        Returns:
            Updated model instance
        """
        instance = await self.get_by_id(id)
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        """
        Hard delete a record.

        Returns:
            True if deleted, False if not found
        """
        instance = await self.get_by_id(id, raise_not_found=False)
        if instance is None:
            return False
        await self.db.delete(instance)
        await self.db.flush()
        return True

    async def exists(self, id: uuid.UUID) -> bool:
        """Check if a record exists without fetching it."""
        result = await self.db.execute(
            select(func.count())
            .select_from(self.model)
            .where(self.model.id == id)
        )
        return result.scalar_one() > 0
