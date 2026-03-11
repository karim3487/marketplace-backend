import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.security import get_current_admin
from app.schemas.models import (
    ImageUploadResponse,
    PaginatedResponse,
    ProductAuditLogResponse,
    ProductCreate,
    ProductDetailResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import product_service
from app.services.storage import StorageService, get_storage_service

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> PaginatedResponse[ProductResponse]:
    """Retrieve list of products for administration."""
    return await product_service.list_products(db, limit=limit, offset=offset)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
) -> ProductResponse:
    # Here we would strictly handle complex relationships insertion explicitly.
    # In base SQLALchemy context we just utilize naive dict packing for simplicity.
    return await product_service.create_product(
        db, product_in=product, admin_username=current_admin.get("sub")
    )


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def read_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> ProductDetailResponse:
    return await product_service.get_product_detail(db, product_id=product_id)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
) -> ProductResponse:
    return await product_service.update_product(
        db, product_id=product_id, product_in=product_in, admin_username=current_admin.get("sub")
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
) -> None:
    await product_service.delete_product(
        db, product_id=product_id, admin_username=current_admin.get("sub")
    )


@router.post("/{product_id}/image", response_model=ImageUploadResponse)
async def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
    current_admin: dict = Depends(get_current_admin),
) -> ImageUploadResponse:
    return await product_service.upload_image(
        db,
        product_id=product_id,
        file_name=file.filename or "image.jpg",
        file_content=await file.read(),
        content_type=file.content_type,
        storage=storage,
        admin_username=current_admin.get("sub"),
    )


@router.get("/{product_id}/audit", response_model=list[ProductAuditLogResponse])
async def get_product_audit_logs(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> list[ProductAuditLogResponse]:
    return await product_service.get_product_audit_logs(db, product_id=product_id)
