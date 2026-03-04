"""Approval-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.approval import AIRecommendation, ApprovalStatus


class ApprovalAction(BaseModel):
    comments: str | None = None


class BatchApprovalAction(BaseModel):
    task_ids: list[uuid.UUID]
    comments: str | None = None


class ApprovalTaskResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    approver_id: uuid.UUID
    approval_level: int
    approval_order: int
    status: ApprovalStatus
    ai_recommendation: AIRecommendation | None = None
    ai_recommendation_reason: str | None = None
    decision_at: datetime | None = None
    comments: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
