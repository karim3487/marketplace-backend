import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.product import product_repository
from app.schemas.models import PaginatedResponse, ProductDetailResponse, ProductListItem
from app.services.storage import StorageService


class CatalogService:
    async def _map_product_to_list_item(
        self, product: Any, storage: StorageService
    ) -> ProductListItem:
        """
        Helper to map a Product model to a ProductListItem schema and inject presigned URLs.
        """
        data = ProductListItem.model_validate(product)
        if product.thumbnail_object_key:
            data.thumbnail_url = await storage.get_presigned_url(product.thumbnail_object_key)

        # Calculate nearest delivery date
        d_dates = [offer.delivery_date for offer in product.offers]
        data.nearest_delivery_date = min(d_dates) if d_dates else None

        return data

    async def _map_product_to_detail_response(
        self, product: Any, storage: StorageService
    ) -> ProductDetailResponse:
        """
        Helper to map a Product model to a ProductDetailResponse schema and inject presigned URLs.
        """
        data = ProductDetailResponse.model_validate(product)
        if product.image_object_key:
            data.image_url = await storage.get_presigned_url(product.image_object_key)
        if product.thumbnail_object_key:
            data.thumbnail_url = await storage.get_presigned_url(product.thumbnail_object_key)

        return data

    async def get_products(
        self, db: AsyncSession, limit: int, offset: int, storage: StorageService
    ) -> PaginatedResponse[ProductListItem]:
        products = await product_repository.get_many_paginated(db, limit=limit, offset=offset)

        results = [await self._map_product_to_list_item(p, storage) for p in products]

        next_cursor = str(offset + limit) if len(products) == limit else None
        return PaginatedResponse(items=results, next_cursor=next_cursor)

    async def get_product_details(
        self,
        db: AsyncSession,
        product_id: uuid.UUID,
        offers_sort: Literal["price", "delivery_date"],
        storage: StorageService,
    ) -> ProductDetailResponse:
        product = await product_repository.get_product_with_sorted_offers(
            db, product_id=product_id, offers_sort=offers_sort
        )
        if not product:
            raise NotFoundError(message="Product not found")

        return await self._map_product_to_detail_response(product, storage)


catalog_service = CatalogService()
