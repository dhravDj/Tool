"""Standard API response envelopes and common models."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class APIErrorDetail(BaseModel):
    """Detailed error structure embedded in API error responses."""

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class APIResponse(BaseModel, Generic[DataT]):
    """Standard unified response wrapper for all DocuMind AI endpoints."""

    success: bool = True
    data: DataT | None = None
    message: str | None = None
    error: APIErrorDetail | None = None
    meta: dict[str, Any] | None = None

    @classmethod
    def ok(
        cls,
        data: DataT | None = None,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> "APIResponse[DataT]":
        return cls(success=True, data=data, message=message, meta=meta)

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> "APIResponse[Any]":
        return cls(
            success=False,
            data=None,
            error=APIErrorDetail(
                code=code,
                message=message,
                details=details,
                request_id=request_id,
            ),
        )
