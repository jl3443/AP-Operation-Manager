"""Pydantic schemas for the Resolution Plan and AutomationAction endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.resolution import ActionStatus, AutomationLevel, PlanStatus


class AutomationActionResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    step_id: str
    action_type: str
    params_json: dict[str, Any] | None = None
    status: ActionStatus
    requires_human_approval: bool
    risk: str | None = None
    expected_result: str | None = None
    result_json: dict[str, Any] | None = None
    error_message: str | None = None
    executed_at: datetime | None = None
    approved_by: uuid.UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResolutionPlanResponse(BaseModel):
    id: uuid.UUID
    exception_id: uuid.UUID
    plan_json: dict[str, Any]
    status: PlanStatus
    automation_level: AutomationLevel
    confidence: float | None = None
    diagnosis: str | None = None
    recheck_strategy: dict[str, Any] | None = None
    audit_evidence: list[dict[str, Any]] | None = None
    approved_by: uuid.UUID | None = None
    approved_at: datetime | None = None
    actions: list[AutomationActionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanApproveRequest(BaseModel):
    comments: str | None = None


class ActionApproveRequest(BaseModel):
    comments: str | None = None


class ActionRedirectRequest(BaseModel):
    """User tells Claude what to do instead for a blocked action."""

    instructions: str
