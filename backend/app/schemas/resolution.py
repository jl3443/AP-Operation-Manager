"""Pydantic schemas for the Resolution Plan and AutomationAction endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel

from app.models.resolution import ActionStatus, AutomationLevel, PlanStatus


class AutomationActionResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    step_id: str
    action_type: str
    params_json: Optional[dict[str, Any]] = None
    status: ActionStatus
    requires_human_approval: bool
    risk: Optional[str] = None
    expected_result: Optional[str] = None
    result_json: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    executed_at: Optional[datetime] = None
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResolutionPlanResponse(BaseModel):
    id: uuid.UUID
    exception_id: uuid.UUID
    plan_json: dict[str, Any]
    status: PlanStatus
    automation_level: AutomationLevel
    confidence: Optional[float] = None
    diagnosis: Optional[str] = None
    recheck_strategy: Optional[dict[str, Any]] = None
    audit_evidence: Optional[list[dict[str, Any]]] = None
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    actions: List[AutomationActionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanApproveRequest(BaseModel):
    comments: Optional[str] = None


class ActionApproveRequest(BaseModel):
    comments: Optional[str] = None


class ActionRedirectRequest(BaseModel):
    """User tells Claude what to do instead for a blocked action."""
    instructions: str
