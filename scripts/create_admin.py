import asyncio
import sys
from pathlib import Path

# Add the project root to sys.path to allow imports from 'app'
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import async_session_maker
from app.repositories.user import UserCreate, user_repository


async def create_admin():
    username = settings.first_admin_username
    password = settings.first_admin_password

    async with async_session_maker() as db:
        user = await user_repository.get_by_username(db, username=username)
        if user:
            print(f"User '{username}' already exists.")
            return

        user_in = UserCreate(username=username, password=password, is_superuser=True)
        await user_repository.create(db, obj_in=user_in)
        await db.commit()
        print(f"Superuser '{username}' created successfully.")


if __name__ == "__main__":
    asyncio.run(create_admin())
