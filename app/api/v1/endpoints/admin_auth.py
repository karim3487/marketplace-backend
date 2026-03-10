from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.schemas.models import LoginRequest, Token
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    responses={
        401: {"description": "Incorrect username or password"},
    },
)
async def login_for_access_token(
    login_data: Annotated[LoginRequest, Body(description="Admin credentials for authentication")],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    """
    Authenticate an admin user and return a JWT token.

    Verifies credentials against the database using bcrypt hashing.
    """
    return await auth_service.authenticate_admin(
        db, username=login_data.username, password=login_data.password
    )
