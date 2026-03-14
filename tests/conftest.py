import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.api.dependencies import get_db
from app.core.config import settings
from app.main import app
from app.models.base import Base

# Derive test database URL from settings
TEST_DATABASE_URL = settings.database_url + "_test"


async def create_test_db():
    """Create the test database if it doesn't exist."""
    url = make_url(settings.database_url)
    # Connect to the default 'postgres' database to issue CREATE DATABASE
    # Note: asyncpg connection string doesn't use the +asyncpg prefix
    conn_str = f"postgresql://{url.username}:{url.password}@{url.host}:{url.port}/postgres"

    conn = await asyncpg.connect(conn_str)
    try:
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", "marketplace_test"
        )
        if not db_exists:
            await conn.execute("CREATE DATABASE marketplace_test")
    finally:
        await conn.close()


@pytest.fixture(scope="session")
async def engine():
    await create_test_db()
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def setup_test_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(engine, setup_test_db):
    """Provides an AsyncSession for each test."""
    async with AsyncSession(bind=engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Provides an AsyncClient for tests with DB dependency override."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
