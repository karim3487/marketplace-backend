import uuid
from datetime import date, datetime
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict | None = None


class CurrencyCode(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    KGS = "KGS"


class Money(BaseModel):
    amount: float = Field(..., ge=0)
    currency: CurrencyCode = CurrencyCode.RUB


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


#
# Product Schemas
#
class ProductAttributeBase(BaseModel):
    key: str
    value: str


class ProductAttributeCreate(ProductAttributeBase):
    pass


class ProductAttributeResponse(ProductAttributeBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    price: Money
    stock: int = Field(0, ge=0)


class ProductCreate(ProductBase):
    attributes: list[ProductAttributeCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    price: Money | None = None
    stock: int | None = Field(None, ge=0)
    attributes: list[ProductAttributeCreate] | None = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    image_url: str | None = None
    thumbnail_url: str | None = None
    created_at: datetime
    updated_at: datetime
    attributes: list[ProductAttributeResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProductListItem(BaseModel):
    id: uuid.UUID
    name: str
    thumbnail_url: str | None = None
    price: Money
    stock: int
    nearest_delivery_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


#
# Seller Schemas
#
class SellerBase(BaseModel):
    name: str
    rating: float = Field(..., ge=1, le=5)


class SellerCreate(SellerBase):
    pass


class SellerUpdate(BaseModel):
    name: str | None = None
    rating: float | None = Field(None, ge=1, le=5)


class SellerResponse(SellerBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


#
# Offer Schemas
#
class OfferBase(BaseModel):
    seller_id: uuid.UUID
    price: Money
    delivery_date: date


class OfferCreate(OfferBase):
    product_id: uuid.UUID


class OfferUpdate(BaseModel):
    seller_id: uuid.UUID | None = None
    price: Money | None = None
    delivery_date: date | None = None


class OfferResponse(BaseModel):
    id: uuid.UUID
    seller: SellerResponse
    price: Money
    delivery_date: date

    model_config = ConfigDict(from_attributes=True)


class AdminOfferResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    seller_id: uuid.UUID
    price: Money
    delivery_date: date

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    offers: list[OfferResponse] = Field(default_factory=list)


#
# Audit Log Schemas
#
class ProductAuditLogResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    action: str
    admin_username: str | None
    changes: dict | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


#
# Pagination Wrapper
#
class PaginatedResponse[T](BaseModel):
    items: list[T]
    next_cursor: str | None = None


# Image Upload Schema
#
class ImageUploadResponse(BaseModel):
    image_url: str
    thumbnail_url: str | None = None
    object_key: str
