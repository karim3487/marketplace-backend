from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import User
from app.repositories.base import BaseRepository


class UserCreate(BaseModel):
    username: str
    password: str
    is_superuser: bool = False


class UserUpdate(BaseModel):
    is_active: bool | None = None


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        from app.core.security import get_password_hash

        db_obj = User(
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


user_repository = UserRepository()
