import asyncio
import uuid
from concurrent.futures import ProcessPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.product import product_repository
from app.schemas.models import (
    ImageUploadResponse,
    PaginatedResponse,
    ProductCreate,
    ProductDetailResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.storage import StorageService
from app.utils.image import process_image_variants

executor = ProcessPoolExecutor()


class ProductService:
    async def _create_audit_log(
        self,
        db: AsyncSession,
        product_id: uuid.UUID,
        action: str,
        admin_username: str | None = None,
        changes: dict | None = None,
    ) -> None:
        """
        Helper to create an audit log entry.
        """
        from app.models.models import ProductAuditLog

        audit_log = ProductAuditLog(
            product_id=product_id,
            action=action,
            admin_username=admin_username,
            changes=changes,
        )
        db.add(audit_log)

    async def list_products(
        self, db: AsyncSession, limit: int, offset: int
    ) -> PaginatedResponse[ProductResponse]:
        products = await product_repository.get_many_paginated(db, limit=limit, offset=offset)
        results = [ProductResponse.model_validate(p) for p in products]
        next_cursor = str(offset + limit) if len(products) == limit else None
        return PaginatedResponse(items=results, next_cursor=next_cursor)

    async def create_product(
        self, db: AsyncSession, product_in: ProductCreate, admin_username: str | None = None
    ) -> ProductResponse:
        db_obj = await product_repository.create(db, obj_in=product_in)

        await self._create_audit_log(
            db,
            product_id=db_obj.id,
            action="CREATE",
            admin_username=admin_username,
            changes=product_in.model_dump(mode="json"),
        )
        await db.commit()

        return ProductResponse.model_validate(db_obj)

    async def get_product(self, db: AsyncSession, product_id: uuid.UUID) -> ProductResponse:
        product = await product_repository.get(db, id=product_id)
        if not product:
            raise NotFoundError(message="Product not found")
        return ProductResponse.model_validate(product)

    async def get_product_detail(
        self, db: AsyncSession, product_id: uuid.UUID
    ) -> ProductDetailResponse:
        product = await product_repository.get_product_with_sorted_offers(
            db, product_id=product_id, offers_sort="price"
        )
        if not product:
            raise NotFoundError(message="Product not found")
        return ProductDetailResponse.model_validate(product)

    async def update_product(
        self,
        db: AsyncSession,
        product_id: uuid.UUID,
        product_in: ProductUpdate,
        admin_username: str | None = None,
    ) -> ProductResponse:
        product = await product_repository.get(db, id=product_id)
        if not product:
            raise NotFoundError(message="Product not found")

        # Audit Diff Calculation
        old_data = ProductResponse.model_validate(product).model_dump(
            mode="json", exclude={"created_at", "updated_at", "image_url", "thumbnail_url"}
        )
        updated_product = await product_repository.update(db, db_obj=product, obj_in=product_in)
        new_data = ProductResponse.model_validate(updated_product).model_dump(
            mode="json", exclude={"created_at", "updated_at", "image_url", "thumbnail_url"}
        )

        diff = {}
        for k in product_in.model_dump(exclude_unset=True):
            if old_data.get(k) != new_data.get(k):
                diff[k] = {"old": old_data.get(k), "new": new_data.get(k)}

        if diff:
            await self._create_audit_log(
                db,
                product_id=product_id,
                action="UPDATE",
                admin_username=admin_username,
                changes=diff,
            )
            await db.commit()

        return ProductResponse.model_validate(updated_product)

    async def delete_product(
        self, db: AsyncSession, product_id: uuid.UUID, admin_username: str | None = None
    ) -> None:
        product = await product_repository.get(db, id=product_id)
        if not product:
            raise NotFoundError(message="Product not found")

        await self._create_audit_log(
            db, product_id=product_id, action="DELETE", admin_username=admin_username, changes=None
        )
        await product_repository.remove(db, id=product_id)
        await db.commit()

    async def get_product_audit_logs(self, db: AsyncSession, product_id: uuid.UUID) -> list[dict]:
        from sqlalchemy import select

        from app.models.models import ProductAuditLog

        stmt = (
            select(ProductAuditLog)
            .where(ProductAuditLog.product_id == product_id)
            .order_by(ProductAuditLog.created_at.desc())
        )

        result = await db.execute(stmt)
        logs = result.scalars().all()
        return logs

    async def upload_image(
        self,
        db: AsyncSession,
        product_id: uuid.UUID,
        file_name: str,
        file_content: bytes,
        content_type: str | None,
        storage: StorageService,
        admin_username: str | None = None,
    ) -> ImageUploadResponse:
        product = await product_repository.get(db, id=product_id)
        if not product:
            raise NotFoundError(message="Product not found")

        # Process image variants in ProcessPool (non-blocking)
        loop = asyncio.get_running_loop()
        variants = await loop.run_in_executor(
            executor, process_image_variants, file_content, file_name
        )

        # Upload variants in parallel using asyncio.gather
        full = variants["full"]
        thumb = variants["thumb"]

        upload_tasks = [
            storage.upload_file(
                file_name=full["name"],
                file_content=full["content"],
                content_type=full["content_type"],
            ),
            storage.upload_file(
                file_name=thumb["name"],
                file_content=thumb["content"],
                content_type=thumb["content_type"],
            ),
        ]

        # obj_key_url = (object_key, url)
        (obj_key, url), (thumb_key, thumb_url) = await asyncio.gather(*upload_tasks)

        # Persist both keys
        await product_repository.update(
            db,
            db_obj=product,
            obj_in={"image_object_key": obj_key, "thumbnail_object_key": thumb_key},
        )

        await self._create_audit_log(
            db,
            product_id=product_id,
            action="IMAGE_UPLOAD",
            admin_username=admin_username,
            changes={"image_object_key": obj_key, "thumbnail_object_key": thumb_key},
        )

        await db.commit()

        return ImageUploadResponse(
            image_url=url,
            thumbnail_url=thumb_url,
            object_key=obj_key,
        )


product_service = ProductService()
