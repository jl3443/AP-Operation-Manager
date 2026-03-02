"""Approval-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.approval import AIRecommendation, ApprovalStatus


class ApprovalAction(BaseModel):
    comments: Optional[str] = None


class BatchApprovalAction(BaseModel):
    task_ids: List[uuid.UUID]
    comments: Optional[str] = None


class ApprovalTaskResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    approver_id: uuid.UUID
    approval_level: int
    approval_order: int
    status: ApprovalStatus
    ai_recommendation: Optional[AIRecommendation] = None
    ai_recommendation_reason: Optional[str] = None
    decision_at: Optional[datetime] = None
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
