from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import create_access_token, verify_password
from app.repositories.user import user_repository
from app.schemas.models import Token


class AuthService:
    async def authenticate_admin(self, db: AsyncSession, username: str, password: str) -> Token:
        user = await user_repository.get_by_username(db, username=username)

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError(message="Incorrect username or password")

        if not user.is_active:
            raise ForbiddenError(message="User is inactive")

        if not user.is_superuser:
            raise ForbiddenError(message="User does not have administrative privileges")

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token)


auth_service = AuthService()
