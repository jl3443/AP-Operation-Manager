"""Exception-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.models.exception import (
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    ResolutionType,
)


class ExceptionCommentCreate(BaseModel):
    comment_text: str
    mentions: Optional[List[str]] = None


class ExceptionCommentResponse(BaseModel):
    id: uuid.UUID
    exception_id: uuid.UUID
    user_id: uuid.UUID
    comment_text: str
    mentions: Optional[List[str]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExceptionUpdate(BaseModel):
    status: Optional[ExceptionStatus] = None
    assigned_to: Optional[uuid.UUID] = None
    severity: Optional[ExceptionSeverity] = None
    resolution_type: Optional[ResolutionType] = None
    resolution_notes: Optional[str] = None


class ExceptionResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    exception_type: ExceptionType
    severity: ExceptionSeverity
    status: ExceptionStatus
    assigned_to: Optional[uuid.UUID] = None
    resolution_type: Optional[ResolutionType] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None
    comments: List[ExceptionCommentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchAssignRequest(BaseModel):
    exception_ids: List[uuid.UUID]
    assigned_to: uuid.UUID
