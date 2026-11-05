"""Centralized custom exceptions and HTTP exception handlers for DocuMind AI."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import logger, request_id_ctx


class DocuMindError(Exception):
    """Base exception for all DocuMind AI domain errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"

    def __init__(
        self,
        message: str = "An unexpected internal server error occurred.",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(DocuMindError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "RESOURCE_NOT_FOUND"


class FileValidationError(DocuMindError):
    """Raised when an uploaded file violates size, MIME, or safety constraints."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "FILE_VALIDATION_ERROR"


class StorageError(DocuMindError):
    """Raised when a storage read/write operation fails."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "STORAGE_ERROR"


class PluginError(DocuMindError):
    """Raised when a plugin fails registration, capability check, or execution."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "PLUGIN_ERROR"


class AuthenticationError(DocuMindError):
    """Raised when authentication credentials are invalid or missing."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_FAILED"


class PermissionDeniedError(DocuMindError):
    """Raised when a client attempts an action beyond their permitted scope."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = "PERMISSION_DENIED"


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with the FastAPI application."""

    @app.exception_handler(DocuMindError)
    async def documind_error_handler(request: Request, exc: DocuMindError) -> JSONResponse:
        req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "")
        logger.warning(
            f"Handled application error: [{exc.error_code}] {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": req_id,
                },
                "data": None,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "")
        error_code = "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": error_code,
                    "message": str(exc.detail),
                    "details": {},
                    "request_id": req_id,
                },
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "")
        formatted_errors = []
        for error in exc.errors():
            loc = " -> ".join(str(part) for part in error.get("loc", []))
            formatted_errors.append(
                {
                    "field": loc,
                    "message": error.get("msg", "Invalid value"),
                    "type": error.get("type", "value_error"),
                }
            )

        logger.info(f"Validation failure on {request.url.path}: {formatted_errors}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request body or parameters failed validation.",
                    "details": {"validation_errors": formatted_errors},
                    "request_id": req_id,
                },
                "data": None,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", "")
        # Log the full exception internally
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {exc}",
            exc_info=True,
            extra={"path": str(request.url.path)},
        )
        # Never leak internal stack trace to client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please contact the administrator with the request ID.",
                    "details": {},
                    "request_id": req_id,
                },
                "data": None,
            },
        )
