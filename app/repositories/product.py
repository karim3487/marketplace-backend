import uuid
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Offer, Product, ProductAttribute
from app.repositories.base import BaseRepository
from app.schemas.models import ProductCreate, ProductUpdate


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    def __init__(self) -> None:
        super().__init__(Product)

    def _normalize_input(self, data: dict) -> dict:
        """Flatten nested 'price' object into 'price_amount' and 'price_currency'."""
        if "price" in data and isinstance(data["price"], dict):
            price_data = data.pop("price")
            data["price_amount"] = price_data.get("amount")
            data["price_currency"] = price_data.get("currency", "RUB")
        return data

    async def create(self, db: AsyncSession, obj_in: ProductCreate | dict[str, Any]) -> Product:
        """Create new record with flattened money and attributes."""
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        data = self._normalize_input(data)

        attributes_data = data.pop("attributes", None)

        db_obj = self.model(**data)
        if attributes_data:
            db_obj.attributes = [ProductAttribute(**attr) for attr in attributes_data]

        db.add(db_obj)
        await db.flush()
        return await self.get(db, db_obj.id)

    async def update(
        self, db: AsyncSession, db_obj: Product, obj_in: ProductUpdate | dict[str, Any]
    ) -> Product:
        """Update record with flattened money and attributes."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        update_data = self._normalize_input(update_data)

        for field, value in update_data.items():
            if field == "attributes":
                current_attrs = {attr.key: attr.value for attr in db_obj.attributes}
                new_attrs = {attr["key"]: attr["value"] for attr in value}

                if current_attrs != new_attrs:
                    db_obj.attributes = [ProductAttribute(**attr) for attr in value]
            else:
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.flush()
        return await self.get(db, db_obj.id)

    async def get(self, db: AsyncSession, id: uuid.UUID) -> Product | None:
        """Fetch product with attributes."""
        stmt = select(self.model).options(selectinload(Product.attributes)).where(Product.id == id)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_many_paginated(
        self, db: AsyncSession, limit: int = 10, offset: int = 0
    ) -> list[Product]:
        """
        Fetch products with attributes and related offers to calculate `nearest_delivery_date`
        via pure Python logic in the response mapping.
        """
        stmt = (
            select(self.model)
            .options(selectinload(Product.attributes), selectinload(Product.offers))
            .limit(limit)
            .offset(offset)
            .order_by(Product.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_product_with_sorted_offers(
        self,
        db: AsyncSession,
        product_id: uuid.UUID,
        offers_sort: Literal["price", "delivery_date"],
    ) -> Product | None:
        """Fetch a single product formatting its offers specifically sorted."""
        from sqlalchemy.orm.attributes import set_committed_value

        stmt = (
            select(self.model)
            .options(selectinload(Product.attributes))
            .where(Product.id == product_id)
        )
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()

        if product:
            offer_stmt = (
                select(Offer)
                .options(selectinload(Offer.seller))
                .where(Offer.product_id == product_id)
            )
            if offers_sort == "price":
                offer_stmt = offer_stmt.order_by(Offer.price_amount.asc())
            else:
                offer_stmt = offer_stmt.order_by(Offer.delivery_date.asc())

            offer_res = await db.execute(offer_stmt)
            offers = list(offer_res.scalars().all())

            # Use set_committed_value to manually populate the relationship
            # without triggering lazy load or greenlet errors.
            set_committed_value(product, "offers", offers)

        return product


product_repository = ProductRepository()
