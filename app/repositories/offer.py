from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Offer
from app.repositories.base import BaseRepository
from app.schemas.models import OfferCreate, OfferUpdate


class OfferRepository(BaseRepository[Offer, OfferCreate, OfferUpdate]):
    def __init__(self) -> None:
        super().__init__(Offer)

    async def get_by_product(self, db: AsyncSession, product_id: str) -> list[Offer]:
        stmt = select(self.model).where(self.model.product_id == product_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())


offer_repository = OfferRepository()
