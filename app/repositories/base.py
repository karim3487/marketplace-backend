from typing import Any

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[ModelType, CreateSchemaType: BaseModel, UpdateSchemaType: BaseModel]:
    """Base repository for CRUD operations."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """Get by ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Get multiple records."""
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    def _normalize_money_input(self, data: dict) -> dict:
        """Flattens nested 'price' object into 'price_amount' and 'price_currency'."""
        if "price" in data and isinstance(data["price"], dict):
            price_data = data.pop("price")
            data["price_amount"] = price_data.get("amount")
            data["price_currency"] = price_data.get("currency", "RUB")
        return data

    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """Create new record with flattened money fields."""
        data = self._normalize_money_input(obj_in.model_dump())
        # Handle attributes separately if they exist in schema
        attributes_data = data.pop("attributes", None)

        db_obj = self.model(**data)
        if attributes_data and hasattr(db_obj, "attributes"):
            from app.models.models import ProductAttribute

            db_obj.attributes = [ProductAttribute(**attr) for attr in attributes_data]

        db.add(db_obj)
        await db.flush()
        # Re-fetch to ensure all relationships (like attributes) are loaded
        # We use self.get() which can be overridden in subclasses for eager loading
        return await self.get(db, db_obj.id)

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """Update record with flattened money fields."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        update_data = self._normalize_money_input(update_data)

        for field, value in update_data.items():
            if field == "attributes" and hasattr(db_obj, "attributes"):
                # Check if attributes actually changed
                from app.models.models import ProductAttribute

                current_attrs = {attr.key: attr.value for attr in db_obj.attributes}
                new_attrs = {attr["key"]: attr["value"] for attr in value}

                if current_attrs != new_attrs:
                    # For prototype, we just replace all attributes if there is a change
                    db_obj.attributes = [ProductAttribute(**attr) for attr in value]
            else:
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        # Re-fetch to ensure all relationships (like attributes) are loaded
        return await self.get(db, db_obj.id)

    async def remove(self, db: AsyncSession, id: Any) -> bool:
        """Delete record."""
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.flush()
            return True
        return False
