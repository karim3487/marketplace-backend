from typing import Any


class MarketplaceException(Exception):
    """
    Base exception for marketplace application.
    """

    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(MarketplaceException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(status_code=404, error="not_found", message=message, details=details)


class UnauthorizedError(MarketplaceException):
    def __init__(self, message: str = "Unauthorized", details: dict[str, Any] | None = None):
        super().__init__(status_code=401, error="unauthorized", message=message, details=details)


class ForbiddenError(MarketplaceException):
    def __init__(self, message: str = "Forbidden", details: dict[str, Any] | None = None):
        super().__init__(status_code=403, error="forbidden", message=message, details=details)


class BadRequestError(MarketplaceException):
    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None):
        super().__init__(status_code=400, error="bad_request", message=message, details=details)
