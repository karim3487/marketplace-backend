from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.repositories.user import user_repository

# Using HTTPBearer for parsing the token out of the Authorization header
security = HTTPBearer()

# Password hashing context
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.PyJWTError as e:
        raise UnauthorizedError(message="Could not validate credentials") from e


async def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Dependency to validate the JWT token and return the admin payload.
    Verifies that the user exists and is an active superuser.
    """
    try:
        # We handle token stripping manually because HTTPBearer might return complex responses
        # if auto_error is True, but we want our own error format.
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str | None = payload.get("sub")
        if username is None:
            raise UnauthorizedError(message="Could not validate credentials")
    except jwt.PyJWTError as e:
        raise UnauthorizedError(message="Could not validate credentials") from e

    user = await user_repository.get_by_username(db, username=username)
    if not user:
        raise UnauthorizedError(message="User not found")
    if not user.is_active:
        raise ForbiddenError(message="Inactive user")
    if not user.is_superuser:
        raise ForbiddenError(message="Not enough privileges")

    return payload
