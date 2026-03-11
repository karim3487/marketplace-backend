import mimetypes
import uuid

import boto3
from aiobotocore.session import get_session
from fastapi import HTTPException, status

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.session = get_session()
        self.endpoint_url = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.bucket_name = settings.minio_bucket_name
        self.public_url = settings.minio_public_url
        self.browser_endpoint = settings.minio_browser_endpoint

        # Sync client for generating presigned URLs in synchronous contexts (e.g. model properties)
        self.sync_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    def get_presigned_url_sync(self, object_key: str, expires_in: int = 3600) -> str:
        """
        Generates a presigned URL synchronously.
        """
        try:
            url = self.sync_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expires_in,
            )
        except Exception:
            url = f"{self.public_url}/{object_key}"

        if self.browser_endpoint:
            url = url.replace(self.endpoint_url, self.browser_endpoint)
        return url

    async def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """
        Generates a presigned URL for an object.
        """
        try:
            async with self.session.create_client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as client:
                url = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_key},
                    ExpiresIn=expires_in,
                )
        except Exception:
            # Fallback to public URL if presigning fails (though in prod we should log/error)
            url = f"{self.public_url}/{object_key}"

        if self.browser_endpoint:
            url = url.replace(self.endpoint_url, self.browser_endpoint)
        return url

    async def upload_file(
        self, file_name: str, file_content: bytes, content_type: str | None = None
    ) -> tuple[str, str]:
        """
        Uploads file content to MinIO asynchronously using aiobotocore.
        Returns: tuple of (object_key, file_url)
        """
        if not content_type:
            content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"

        ext = file_name.split(".")[-1] if "." in file_name else ""
        object_key = f"{uuid.uuid4()}.{ext}" if ext else str(uuid.uuid4())

        try:
            async with self.session.create_client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_key,
                    Body=file_content,
                    ContentType=content_type,
                )

                # Return the key and a presigned URL (valid for 1 hour by default)
                url = await self.get_presigned_url(object_key)
                return object_key, url
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to storage: {str(e)}",
            ) from e


def get_storage_service() -> StorageService:
    return storage_service


storage_service = StorageService()
