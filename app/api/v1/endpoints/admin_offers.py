import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_admin
from app.models.models import ProductAuditLog
from app.repositories.offer import offer_repository
from app.schemas.models import AdminOfferResponse, OfferCreate, OfferUpdate

router = APIRouter()


@router.post("/", response_model=AdminOfferResponse, status_code=status.HTTP_201_CREATED)
async def create_offer(
    offer: OfferCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
) -> AdminOfferResponse:
    db_obj = await offer_repository.create(db, obj_in=offer)

    audit_log = ProductAuditLog(
        product_id=db_obj.product_id,
        action="OFFER_ADD",
        admin_username=current_admin.get("sub"),
        changes=offer.model_dump(mode="json"),
    )
    db.add(audit_log)
    await db.commit()

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
    current_admin: dict = Depends(get_current_admin),
) -> AdminOfferResponse:
    offer = await offer_repository.get(db, id=offer_id)
    if not offer:
        raise NotFoundError(message="Offer not found")

    # Capture changes for audit log
    old_data = AdminOfferResponse.model_validate(offer).model_dump(mode="json")
    updated_offer = await offer_repository.update(db, db_obj=offer, obj_in=offer_in)
    new_data = AdminOfferResponse.model_validate(updated_offer).model_dump(mode="json")

    # Simple diff
    diff = {}
    update_dict = offer_in.model_dump(exclude_unset=True)
    for key in update_dict:
        if old_data.get(key) != new_data.get(key):
            diff[key] = {"old": old_data.get(key), "new": new_data.get(key)}

    if diff:
        audit_log = ProductAuditLog(
            product_id=updated_offer.product_id,
            action="OFFER_UPDATE",
            admin_username=current_admin.get("sub"),
            changes={"offer_id": str(offer_id), "diff": diff},
        )
        db.add(audit_log)
        await db.commit()

    return AdminOfferResponse.model_validate(updated_offer)


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(
    offer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
) -> None:
    offer = await offer_repository.get(db, id=offer_id)
    if not offer:
        raise NotFoundError(message="Offer not found")

    audit_log = ProductAuditLog(
        product_id=offer.product_id,
        action="OFFER_REMOVE",
        admin_username=current_admin.get("sub"),
        changes={"offer_id": str(offer.id), "seller_id": str(offer.seller_id)},
    )
    db.add(audit_log)

    await offer_repository.remove(db, id=offer_id)
    await db.commit()
