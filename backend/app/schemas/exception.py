"""Exception-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.exception import (
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    ResolutionType,
)


class ExceptionCommentCreate(BaseModel):
    comment_text: str
    mentions: list[str] | None = None


class ExceptionCommentResponse(BaseModel):
    id: uuid.UUID
    exception_id: uuid.UUID
    user_id: uuid.UUID
    comment_text: str
    mentions: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExceptionUpdate(BaseModel):
    status: ExceptionStatus | None = None
    assigned_to: uuid.UUID | None = None
    severity: ExceptionSeverity | None = None
    resolution_type: ResolutionType | None = None
    resolution_notes: str | None = None


class ExceptionResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    exception_type: ExceptionType
    severity: ExceptionSeverity
    status: ExceptionStatus
    assigned_to: uuid.UUID | None = None
    resolution_type: ResolutionType | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None
    resolved_by: uuid.UUID | None = None
    ai_suggested_resolution: str | None = None
    ai_severity_reasoning: str | None = None
    comments: list[ExceptionCommentResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchAssignRequest(BaseModel):
    exception_ids: list[uuid.UUID]
    assigned_to: uuid.UUID
