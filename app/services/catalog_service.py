import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.product import product_repository
from app.schemas.models import PaginatedResponse, ProductDetailResponse, ProductListItem


class CatalogService:
    def _map_product_to_list_item(self, product: Any) -> ProductListItem:
        """
        Helper to map a Product model to a ProductListItem schema and inject presigned URLs.
        """
        from app.services.storage import storage_service

        data = ProductListItem.model_validate(product)
        if product.thumbnail_object_key:
            data.thumbnail_url = storage_service.get_presigned_url_sync(
                product.thumbnail_object_key
            )

        # Calculate nearest delivery date
        d_dates = [offer.delivery_date for offer in product.offers]
        data.nearest_delivery_date = min(d_dates) if d_dates else None

        return data

    def _map_product_to_detail_response(self, product: Any) -> ProductDetailResponse:
        """
        Helper to map a Product model to a ProductDetailResponse schema and inject presigned URLs.
        """
        from app.services.storage import storage_service

        data = ProductDetailResponse.model_validate(product)
        if product.image_object_key:
            data.image_url = storage_service.get_presigned_url_sync(product.image_object_key)
        if product.thumbnail_object_key:
            data.thumbnail_url = storage_service.get_presigned_url_sync(
                product.thumbnail_object_key
            )

        return data

    async def get_products(
        self, db: AsyncSession, limit: int, offset: int
    ) -> PaginatedResponse[ProductListItem]:
        products = await product_repository.get_many_paginated(db, limit=limit, offset=offset)

        results = [self._map_product_to_list_item(p) for p in products]

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

        return self._map_product_to_detail_response(product)


catalog_service = CatalogService()
