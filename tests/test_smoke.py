import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_list_products_public(client: AsyncClient):
    # Mocking the repository to return an empty list for stability
    with patch(
        "app.repositories.product.product_repository.get_many_paginated", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = []
        response = await client.get("/api/v1/public/products")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "next_cursor" in data


@pytest.mark.asyncio
async def test_admin_login_wrong_credentials(client: AsyncClient):
    # Mock user not found
    with patch(
        "app.repositories.user.user_repository.get_by_username", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None
        response = await client.post(
            "/api/v1/admin/auth/login",
            json={"username": "wrong_user", "password": "wrong_password"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "unauthorized"


@pytest.mark.asyncio
async def test_admin_login_validation_error(client: AsyncClient):
    # Missing password - should trigger FastAPI validation error before repo call
    response = await client.post("/api/v1/admin/auth/login", json={"username": "admin"})
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "validation_error"


@pytest.mark.asyncio
async def test_get_non_existent_product(client: AsyncClient):
    # Mock product not found
    random_id = str(uuid.uuid4())
    with patch(
        "app.repositories.product.product_repository.get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None
        response = await client.get(f"/api/v1/public/products/{random_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "not_found"
