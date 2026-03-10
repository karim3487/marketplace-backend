from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin_auth,
    admin_offers,
    admin_products,
    admin_sellers,
    public,
)

api_router = APIRouter()
api_router.include_router(public.router, prefix="/public", tags=["Public"])
api_router.include_router(admin_auth.router, prefix="/admin/auth", tags=["AdminAuth"])
api_router.include_router(admin_products.router, prefix="/admin/products", tags=["AdminProducts"])
api_router.include_router(admin_sellers.router, prefix="/admin/sellers", tags=["AdminSellers"])
api_router.include_router(admin_offers.router, prefix="/admin/offers", tags=["AdminOffers"])
