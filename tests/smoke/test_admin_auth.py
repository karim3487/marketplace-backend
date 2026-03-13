import pytest
from sqlalchemy import insert

from app.core.security import get_password_hash
from app.models.models import User


@pytest.fixture
async def test_user(db_session):
    username = "admin_smoke"
    password = "password123"
    await db_session.execute(
        insert(User).values(
            username=username, hashed_password=get_password_hash(password), is_superuser=True
        )
    )
    await db_session.commit()  # Added commit to ensure data is persisted
    # The original code had db_session.flush(), which is not needed if we commit.
    # If refresh is needed, it would be on the specific object, not the session directly.
    # For this fixture, committing the data is sufficient.
    return {"username": username, "password": password}


@pytest.mark.asyncio
async def test_admin_login_success(client, test_user):
    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_admin_login_failure(client):
    response = await client.post(
        "/api/v1/admin/auth/login", json={"username": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401
