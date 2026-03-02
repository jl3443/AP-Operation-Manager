"""Shared / generic Pydantic schemas used across the API."""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Wrapper for paginated list endpoints."""

    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class FilterParams(BaseModel):
    """Common query-parameter filter bag."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Column to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort direction")
    search: Optional[str] = Field(None, description="Free-text search term")
    status: Optional[str] = Field(None, description="Status filter")
    vendor_id: Optional[str] = Field(None, description="Vendor UUID filter")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class MessageResponse(BaseModel):
    """Simple message-only response."""

    message: str
