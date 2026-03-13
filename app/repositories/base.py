from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[ModelType, CreateSchemaType: BaseModel, UpdateSchemaType: BaseModel]:
    """Base repository for CRUD operations."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def _preprocess_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Hook for preprocessing data before database operations.
        Useful for flattening nested Pydantic models (e.g. Money).
        """
        processed = data.copy()

        # Generic Money flattening: if a field 'foo' is a dict with 'amount'/'currency',
        # flatten it into 'foo_amount' and 'foo_currency'.
        fields_to_process = list(processed.keys())
        for field in fields_to_process:
            value = processed[field]
            if isinstance(value, dict) and "amount" in value and "currency" in value:
                processed[f"{field}_amount"] = value["amount"]
                processed[f"{field}_currency"] = value.get("currency", "RUB")
                del processed[field]

        return processed

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Get by ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get multiple records."""
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(
        self, db: AsyncSession, obj_in: CreateSchemaType | dict[str, Any]
    ) -> ModelType:
        """Create new record."""
        obj_in_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        obj_in_data = self._preprocess_data(obj_in_data)

        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """Update record."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        update_data = self._preprocess_data(update_data)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        return db_obj

    async def remove(self, db: AsyncSession, id: Any) -> bool:
        """Delete record."""
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.flush()
            return True
        return False
