from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Project settings loaded from environment variables or .env file.
    """

    project_name: str = "Marketplace API"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/marketplace"

    # MinIO
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "changeme"
    minio_bucket_name: str = "products"
    minio_public_url: str = "http://localhost:9000/products"

    # Security
    secret_key: str = "marketplace-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Initial Admin (Seed)
    first_admin_username: str = "admin"
    first_admin_password: str = "admin_password"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
