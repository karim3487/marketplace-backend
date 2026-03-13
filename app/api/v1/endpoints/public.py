import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.models import PaginatedResponse, ProductDetailResponse, ProductListItem
from app.services.catalog_service import catalog_service
from app.services.storage import storage_service

router = APIRouter()


@router.get("/products", response_model=PaginatedResponse[ProductListItem])
async def get_products(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[ProductListItem]:
    """
    Retrieve a paginated list of products for infinite scroll.
    Computes 'nearest_delivery_date' locally from early relation load.
    """
    return await catalog_service.get_products(
        db, limit=limit, offset=offset, storage=storage_service
    )


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product_details(
    product_id: uuid.UUID,
    offers_sort: Literal["price", "delivery_date"] = Query(
        "price", description="Sort offers criteria"
    ),
    db: AsyncSession = Depends(get_db),
) -> ProductDetailResponse:
    """
    Get detailed product layout, incorporating explicitly sorted embedded offers.
    """
    return await catalog_service.get_product_details(
        db, product_id=product_id, offers_sort=offers_sort, storage=storage_service
    )
