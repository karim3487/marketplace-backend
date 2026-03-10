from app.models.models import Seller
from app.repositories.base import BaseRepository
from app.schemas.models import SellerBase, SellerCreate


class SellerRepository(BaseRepository[Seller, SellerCreate, SellerBase]):
    def __init__(self) -> None:
        super().__init__(Seller)


seller_repository = SellerRepository()
