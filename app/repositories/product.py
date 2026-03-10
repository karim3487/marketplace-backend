import uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Offer, Product
from app.repositories.base import BaseRepository
from app.schemas.models import ProductCreate, ProductUpdate


class ProductRepository(BaseRepository[Product, ProductCreate, ProductUpdate]):
    def __init__(self) -> None:
        super().__init__(Product)

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
