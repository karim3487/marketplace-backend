import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_admin
from app.repositories.offer import offer_repository
from app.schemas.models import AdminOfferResponse, OfferCreate, OfferUpdate

router = APIRouter()


@router.post("/", response_model=AdminOfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    offer: OfferCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> AdminOfferResponse:
    db_obj = await offer_repository.create(db, obj_in=offer)
    return AdminOfferResponse.model_validate(db_obj)


@router.get("/{offer_id}", response_model=AdminOfferResponse)
async def read_offer(
    offer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> AdminOfferResponse:
    offer = await offer_repository.get(db, id=offer_id)
    if not offer:
        raise NotFoundError(message="Offer not found")
    return AdminOfferResponse.model_validate(offer)


@router.put("/{offer_id}", response_model=AdminOfferResponse)
async def update_offer(
    offer_id: uuid.UUID,
    offer_in: OfferUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> AdminOfferResponse:
    offer = await offer_repository.get(db, id=offer_id)
    if not offer:
        raise NotFoundError(message="Offer not found")

    updated_offer = await offer_repository.update(db, db_obj=offer, obj_in=offer_in)
    return AdminOfferResponse.model_validate(updated_offer)


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(
    offer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_admin),
) -> None:
    offer = await offer_repository.get(db, id=offer_id)
    if not offer:
        raise NotFoundError(message="Offer not found")

    await offer_repository.remove(db, id=offer_id)
