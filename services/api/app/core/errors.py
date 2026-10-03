from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorEnvelope(BaseModel):
    error_code: str
    message: str
    details: dict[str, Any] | None = None


class VaspTraceException(HTTPException):
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.message = message
        self.details = details


class InvalidAddressException(VaspTraceException):
    def __init__(self, message: str = "Invalid wallet address for specified blockchain"):
        super().__init__(
            error_code="INVALID_ADDRESS",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class UnsupportedChainException(VaspTraceException):
    def __init__(self, message: str = "Chain not supported in this deployment"):
        super().__init__(
            error_code="UNSUPPORTED_CHAIN",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class DuplicateResourceException(VaspTraceException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            error_code="DUPLICATE_RESOURCE",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class NotFoundException(VaspTraceException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            error_code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PermissionDeniedException(VaspTraceException):
    def __init__(self, message: str = "Permission denied", details: dict[str, Any] | None = None):
        super().__init__(
            error_code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class AdapterNotConfiguredException(VaspTraceException):
    def __init__(self, message: str = "Intelligence adapter not configured"):
        super().__init__(
            error_code="ADAPTER_NOT_CONFIGURED",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# Provider Exception Hierarchy (PRD §9.2)
class ProviderError(VaspTraceException):
    def __init__(
        self,
        message: str = "Blockchain provider error",
        error_code: str = "PROVIDER_ERROR",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            error_code=error_code,
            message=message,
            status_code=status_code,
            details=details,
        )


class ProviderInvalidAddress(ProviderError):
    def __init__(self, message: str = "Invalid address for chain", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_INVALID_ADDRESS",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ProviderUnsupportedChain(ProviderError):
    def __init__(self, message: str = "Unsupported chain", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_UNSUPPORTED_CHAIN",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class ProviderRateLimited(ProviderError):
    def __init__(
        self,
        retry_after: float = 1.0,
        message: str = "Provider rate limit reached",
        details: dict[str, Any] | None = None,
    ):
        d = dict(details or {})
        d["retry_after"] = retry_after
        self.retry_after = retry_after
        super().__init__(
            message=message,
            error_code="PROVIDER_RATE_LIMITED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=d,
        )


class ProviderTimeout(ProviderError):
    def __init__(self, message: str = "Provider request timed out", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_TIMEOUT",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details=details,
        )


class ProviderUnavailable(ProviderError):
    def __init__(self, message: str = "Provider service unavailable", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class ProviderMalformedResponse(ProviderError):
    def __init__(self, message: str = "Malformed provider response payload", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_MALFORMED_RESPONSE",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class ProviderAuthError(ProviderError):
    def __init__(self, message: str = "Provider authentication failed", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_AUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ProviderNotFound(ProviderError):
    def __init__(self, message: str = "Resource not found on provider", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            error_code="PROVIDER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )



async def vasp_trace_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, VaspTraceException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorEnvelope(
            error_code="BAD_REQUEST",
            message=str(exc),
        ).model_dump(),
    )


async def generic_http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorEnvelope(
                error_code="HTTP_ERROR",
                message=str(exc.detail),
            ).model_dump(),
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorEnvelope(
            error_code="INTERNAL_ERROR",
            message="An unexpected server error occurred",
        ).model_dump(),
    )

