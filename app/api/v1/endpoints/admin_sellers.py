import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_admin
from app.repositories.seller import seller_repository
from app.schemas.models import SellerCreate, SellerResponse, SellerUpdate

router = APIRouter()


@router.get("/", response_model=list[SellerResponse])
async def list_sellers(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> list[SellerResponse]:
    """List all sellers for administrative purposes."""
    sellers = await seller_repository.get_multi(db)
    return [SellerResponse.model_validate(s) for s in sellers]


@router.post("/", response_model=SellerResponse, status_code=status.HTTP_201_CREATED)
async def create_seller(
    seller_in: SellerCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> SellerResponse:
    """Create a new seller."""
    db_obj = await seller_repository.create(db, obj_in=seller_in)
    return SellerResponse.model_validate(db_obj)


@router.get("/{seller_id}", response_model=SellerResponse)
async def get_seller(
    seller_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> SellerResponse:
    """Get details of a specific seller."""
    seller = await seller_repository.get(db, id=seller_id)
    if not seller:
        raise NotFoundError(message="Seller find failed")
    return SellerResponse.model_validate(seller)


@router.put("/{seller_id}", response_model=SellerResponse)
async def update_seller(
    seller_id: uuid.UUID,
    seller_in: SellerUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> SellerResponse:
    seller = await seller_repository.get(db, id=seller_id)
    if not seller:
        raise NotFoundError(message="Seller not found")
    seller = await seller_repository.update(db, db_obj=seller, obj_in=seller_in)
    return SellerResponse.model_validate(seller)


@router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(
    seller_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> None:
    """Delete a specific seller."""
    await seller_repository.remove(db, id=seller_id)
