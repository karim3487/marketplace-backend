import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.api.dependencies import get_db
from app.core.config import settings
from app.main import app
from app.models.base import Base

# Derive test database URL from settings
TEST_DATABASE_URL = settings.database_url + "_test"


async def create_test_db() -> str:
    """Create the test database if it doesn't exist."""
    base_url = make_url(settings.database_url)

    test_db_name = f"{base_url.database}_test"

    host = "localhost" if base_url.host in ("db", "postgres", "marketplace_db") else base_url.host

    admin_url = base_url.set(host=host, database="postgres")

    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"), {"db_name": test_db_name}
        )
        exists = result.scalar()

        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))

    await engine.dispose()

    return base_url.set(host=host, database=test_db_name).render_as_string(hide_password=False)


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
