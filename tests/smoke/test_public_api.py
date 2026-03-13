import uuid
from datetime import date

import pytest
from sqlalchemy import insert

from app.models.models import Offer, Product, Seller


@pytest.fixture
async def seed_data(db_session):
    # Create a seller
    seller_id = uuid.uuid4()
    await db_session.execute(insert(Seller).values(id=seller_id, name="Test Seller", rating=4.5))

    # Create a product
    product_id = uuid.uuid4()
    await db_session.execute(
        insert(Product).values(
            id=product_id,
            name="Test Product",
            price_amount=100.0,
            price_currency="RUB",
            stock=10,
        )
    )

    # Create an offer
    await db_session.execute(
        insert(Offer).values(
            id=uuid.uuid4(),
            product_id=product_id,
            seller_id=seller_id,
            price_amount=95.0,
            price_currency="RUB",
            delivery_date=date(2026, 3, 20),
        )
    )
    await db_session.commit()
    return {"product_id": product_id, "seller_id": seller_id}


@pytest.mark.asyncio
async def test_get_products_list(client, seed_data):
    response = await client.get("/api/v1/public/products")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert any(item["name"] == "Test Product" for item in data["items"])


@pytest.mark.asyncio
async def test_get_product_details(client, seed_data):
    product_id = seed_data["product_id"]
    response = await client.get(f"/api/v1/public/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(product_id)
    assert data["name"] == "Test Product"
    assert "offers" in data
    assert len(data["offers"]) >= 1
    assert data["offers"][0]["seller"]["name"] == "Test Seller"
