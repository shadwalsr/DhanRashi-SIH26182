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

