import asyncio
import os
import random
import sys
import uuid
from datetime import date

# Ensure the parent directory is in sys.path to find 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.models import Offer, Product, ProductAttribute, Seller

PRODUCT_PREFIXES = ["Super", "Mega", "Ultra", "Hyper", "Pro", "Basic", "Smart"]
PRODUCT_NOUNS = ["Phone", "Laptop", "Watch", "TV", "Headphones", "Tablet", "Monitor"]

ATTRIBUTES = {
    "Color": ["Red", "Blue", "Black", "White", "Silver", "Gold"],
    "Material": ["Plastic", "Metal", "Glass", "Wood", "Leather"],
    "Brand": ["Apple", "Samsung", "Sony", "LG", "Xiaomi", "Huawei"],
    "Condition": ["New", "Used - Like New", "Used - Good", "Refurbished"],
}


async def clear_data(session: AsyncSession):
    """Clear existing seed data tables to avoid conflicts or duplication."""
    await session.execute(Offer.__table__.delete())
    await session.execute(ProductAttribute.__table__.delete())
    await session.execute(Seller.__table__.delete())
    await session.execute(Product.__table__.delete())
    await session.commit()


async def seed():
    async with async_session_maker() as session:
        print("Clearing old data...")
        await clear_data(session)

        print("Seeding sellers...")
        sellers = []
        for i in range(10):
            seller = Seller(
                id=uuid.uuid4(),
                name=f"Seller Store {i + 1}",
                rating=round(random.uniform(3.5, 5.0), 1),
            )
            session.add(seller)
            sellers.append(seller)

        await session.flush()

        print("Seeding products, attributes, and offers...")
        for i in range(100):
            # 1. Product
            product = Product(
                id=uuid.uuid4(),
                name=f"{random.choice(PRODUCT_PREFIXES)} {random.choice(PRODUCT_NOUNS)} {i + 1}",
                price_amount=round(random.uniform(10.0, 5000.0), 2),
                price_currency="RUB",
                stock=random.randint(0, 1000),
            )
            session.add(product)
            await session.flush()

            # 2. Attributes (2-6 per product)
            num_attrs = random.randint(2, 6)
            attr_keys = random.sample(list(ATTRIBUTES.keys()), min(num_attrs, len(ATTRIBUTES)))
            for key in attr_keys:
                attr = ProductAttribute(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    key=key,
                    value=random.choice(ATTRIBUTES[key]),
                )
                session.add(attr)

            # 3. Offers (2-10 per product)
            num_offers = random.randint(2, 10)
            offer_sellers = random.choices(sellers, k=num_offers)
            for seller in offer_sellers:
                # Target dates: March 2 to 8, 2026
                delivery_day = random.randint(2, 8)
                offer = Offer(
                    id=uuid.uuid4(),
                    product_id=product.id,
                    seller_id=seller.id,
                    price_amount=round(product.price_amount * random.uniform(0.8, 1.2), 2),
                    price_currency="RUB",
                    delivery_date=date(2026, 3, delivery_day),
                )
                session.add(offer)

        await session.commit()
        print("Seeding complete! 100 products added.")


if __name__ == "__main__":
    asyncio.run(seed())
