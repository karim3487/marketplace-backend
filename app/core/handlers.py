from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import MarketplaceException


async def marketplace_exception_handler(
    request: Request, exc: MarketplaceException
) -> JSONResponse:
    content = {"error": exc.error, "message": exc.message}
    if exc.details:
        content["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Fallback for standard HTTP exceptions (e.g. from FastAPI internal like 405 Method Not Allowed)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": str(exc.detail).lower().replace(" ", "_"),
            "message": str(exc.detail),
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Input validation failed",
            "details": {"errors": exc.errors()},
        },
    )
