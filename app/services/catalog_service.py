import uuid
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.product import product_repository
from app.schemas.models import PaginatedResponse, ProductDetailResponse, ProductListItem


class CatalogService:
    async def get_products(
        self, db: AsyncSession, limit: int, offset: int
    ) -> PaginatedResponse[ProductListItem]:
        products = await product_repository.get_many_paginated(db, limit=limit, offset=offset)

        results = []
        for product in products:
            d_dates = [offer.delivery_date for offer in product.offers]
            nearest_date = min(d_dates) if d_dates else None

            prod_data = ProductListItem.model_validate(product)
            prod_data.nearest_delivery_date = nearest_date
            results.append(prod_data)

        next_cursor = str(offset + limit) if len(products) == limit else None
        return PaginatedResponse(items=results, next_cursor=next_cursor)

    async def get_product_details(
        self,
        db: AsyncSession,
        product_id: uuid.UUID,
        offers_sort: Literal["price", "delivery_date"],
    ) -> ProductDetailResponse:
        product = await product_repository.get_product_with_sorted_offers(
            db, product_id=product_id, offers_sort=offers_sort
        )
        if not product:
            raise NotFoundError(message="Product not found")

        return ProductDetailResponse.model_validate(product)


catalog_service = CatalogService()
