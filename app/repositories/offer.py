from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Offer
from app.repositories.base import BaseRepository
from app.schemas.models import OfferCreate, OfferUpdate


class OfferRepository(BaseRepository[Offer, OfferCreate, OfferUpdate]):
    def __init__(self) -> None:
        super().__init__(Offer)

    def _normalize_input(self, data: dict) -> dict:
        """Flatten nested 'price' object into 'price_amount' and 'price_currency'."""
        if "price" in data and isinstance(data["price"], dict):
            price_data = data.pop("price")
            data["price_amount"] = price_data.get("amount")
            data["price_currency"] = price_data.get("currency", "RUB")
        return data

    async def create(self, db: AsyncSession, obj_in: OfferCreate | dict[str, Any]) -> Offer:
        """Create new record with flattened money."""
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        data = self._normalize_input(data)

        db_obj = self.model(**data)
        db.add(db_obj)
        await db.flush()
        return db_obj

    async def update(
        self, db: AsyncSession, db_obj: Offer, obj_in: OfferUpdate | dict[str, Any]
    ) -> Offer:
        """Update record with flattened money."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        update_data = self._normalize_input(update_data)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        return db_obj

    async def get_by_product(self, db: AsyncSession, product_id: str) -> list[Offer]:
        stmt = select(self.model).where(self.model.product_id == product_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())


offer_repository = OfferRepository()
