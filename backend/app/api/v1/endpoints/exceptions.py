"""Exception management endpoints."""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit import ActorType
from app.models.exception import Exception_, ExceptionStatus
from app.models.resolution import (
    ActionStatus,
    AutomationAction,
    PlanStatus,
    ResolutionPlan,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.exception import (
    BatchAssignRequest,
    ExceptionCommentCreate,
    ExceptionCommentResponse,
    ExceptionResponse,
    ExceptionUpdate,
)
from app.schemas.resolution import (
    ActionApproveRequest,
    ActionRedirectRequest,
    PlanApproveRequest,
    ResolutionPlanResponse,
)
from app.services import audit_service, exception_service
from app.services import resolution_orchestrator as orchestrator

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


@router.get("", response_model=PaginatedResponse[ExceptionResponse])
def list_exceptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    exception_type: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List exceptions with pagination and filtering."""
    query = db.query(Exception_).options(joinedload(Exception_.comments))

    if status_filter:
        query = query.filter(Exception_.status == status_filter)
    if severity:
        query = query.filter(Exception_.severity == severity)
    if exception_type:
        query = query.filter(Exception_.exception_type == exception_type)
    if assigned_to:
        query = query.filter(Exception_.assigned_to == uuid.UUID(assigned_to))

    total = query.count()
    items = (
        query.order_by(Exception_.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Deduplicate from joinedload
    seen: set[uuid.UUID] = set()
    unique: list[Exception_] = []
    for item in items:
        if item.id not in seen:
            seen.add(item.id)
            unique.append(item)

    return PaginatedResponse[ExceptionResponse](
        items=unique,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{exception_id}", response_model=ExceptionResponse)
def get_exception(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single exception by ID."""
    exc = (
        db.query(Exception_)
        .options(joinedload(Exception_.comments))
        .filter(Exception_.id == exception_id)
        .first()
    )
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    return exc


@router.patch("/{exception_id}", response_model=ExceptionResponse)
def update_exception(
    exception_id: uuid.UUID,
    payload: ExceptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an exception (assign, resolve, escalate, etc.)."""
    exc = exception_service.update_exception(
        db, exception_id, payload, resolved_by=current_user.id
    )
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    audit_service.log_action(
        db,
        entity_type="exception",
        entity_id=exc.id,
        action="updated",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        changes=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    return exc


@router.post("/{exception_id}/comments", response_model=ExceptionCommentResponse, status_code=201)
def add_comment(
    exception_id: uuid.UUID,
    payload: ExceptionCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a comment to an exception."""
    exc = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    comment = exception_service.add_comment(
        db,
        exception_id=exception_id,
        user_id=current_user.id,
        comment_text=payload.comment_text,
        mentions=payload.mentions,
    )
    return comment


@router.post("/batch-assign")
def batch_assign(
    payload: BatchAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch-assign exceptions to a user."""
    updated = 0
    for exc_id in payload.exception_ids:
        exc = db.query(Exception_).filter(Exception_.id == exc_id).first()
        if exc:
            exc.assigned_to = payload.assigned_to
            if exc.status == ExceptionStatus.open:
                exc.status = ExceptionStatus.assigned
            updated += 1

    db.commit()
    return {"message": f"{updated} exceptions assigned", "updated": updated}


# ---------------------------------------------------------------------------
# V2: Resolution Plan endpoints
# ---------------------------------------------------------------------------


@router.post("/{exception_id}/generate-plan", response_model=ResolutionPlanResponse)
def generate_plan(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an AI resolution plan for an exception."""
    exc = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    try:
        plan = orchestrator.plan(db, exception_id)
        # Auto-approve and execute so actions run immediately
        plan.status = PlanStatus.approved
        db.commit()
        orchestrator.execute(db, plan.id)
        # Refresh to get updated action statuses
        db.refresh(plan)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    return plan


@router.get("/{exception_id}/plan", response_model=ResolutionPlanResponse)
def get_resolution_plan(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the latest resolution plan for an exception."""
    plan = (
        db.query(ResolutionPlan)
        .options(joinedload(ResolutionPlan.actions))
        .filter(ResolutionPlan.exception_id == exception_id)
        .order_by(ResolutionPlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No resolution plan found for this exception")
    return plan


@router.post("/{exception_id}/plan/approve", response_model=ResolutionPlanResponse)
def approve_plan(
    exception_id: uuid.UUID,
    payload: PlanApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a resolution plan so it can be executed."""
    plan = (
        db.query(ResolutionPlan)
        .options(joinedload(ResolutionPlan.actions))
        .filter(
            ResolutionPlan.exception_id == exception_id,
            ResolutionPlan.status == PlanStatus.draft,
        )
        .order_by(ResolutionPlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No draft plan found for this exception")

    plan.status = PlanStatus.approved
    plan.approved_by = current_user.id
    plan.approved_at = datetime.now(timezone.utc)
    db.commit()

    audit_service.log_action(
        db,
        entity_type="resolution_plan",
        entity_id=plan.id,
        action="plan_approved",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        evidence={"comments": payload.comments} if payload.comments else None,
    )
    db.commit()

    return plan


@router.post("/{exception_id}/plan/execute")
def execute_plan(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute an approved resolution plan."""
    plan = (
        db.query(ResolutionPlan)
        .filter(
            ResolutionPlan.exception_id == exception_id,
            ResolutionPlan.status.in_([PlanStatus.approved, PlanStatus.executing]),
        )
        .order_by(ResolutionPlan.created_at.desc())
        .first()
    )
    if not plan:
        raise HTTPException(
            status_code=404,
            detail="No approved/executing plan found for this exception",
        )

    try:
        result = orchestrator.execute(db, plan.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.post("/{exception_id}/plan/actions/{action_id}/approve")
def approve_action(
    exception_id: uuid.UUID,
    action_id: uuid.UUID,
    payload: ActionApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a single action step that requires human approval."""
    action = (
        db.query(AutomationAction)
        .join(ResolutionPlan)
        .filter(
            ResolutionPlan.exception_id == exception_id,
            AutomationAction.id == action_id,
        )
        .first()
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.status != ActionStatus.awaiting_approval:
        raise HTTPException(
            status_code=400,
            detail=f"Action is not awaiting approval (current: {action.status.value})",
        )

    action.approved_by = current_user.id
    action.approved_at = datetime.now(timezone.utc)
    action.status = ActionStatus.pending  # Reset to pending so execute picks it up
    db.commit()

    audit_service.log_action(
        db,
        entity_type="automation_action",
        entity_id=action.id,
        action="action_approved",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        evidence={"comments": payload.comments} if payload.comments else None,
    )
    db.commit()

    return {"message": "Action approved", "action_id": str(action_id), "status": "pending"}


@router.post("/{exception_id}/plan/actions/{action_id}/approve-and-continue")
def approve_action_and_continue(
    exception_id: uuid.UUID,
    action_id: uuid.UUID,
    payload: ActionApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a single action AND immediately continue execution.

    This is the one-click approve flow: approve the blocking step,
    then resume execution until the next approval step or completion.
    """
    action = (
        db.query(AutomationAction)
        .join(ResolutionPlan)
        .filter(
            ResolutionPlan.exception_id == exception_id,
            AutomationAction.id == action_id,
        )
        .first()
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.status != ActionStatus.awaiting_approval:
        raise HTTPException(
            status_code=400,
            detail=f"Action is not awaiting approval (current: {action.status.value})",
        )

    # Approve the action
    action.approved_by = current_user.id
    action.approved_at = datetime.now(timezone.utc)
    action.status = ActionStatus.pending
    db.commit()

    audit_service.log_action(
        db,
        entity_type="automation_action",
        entity_id=action.id,
        action="action_approved",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        evidence={"comments": payload.comments} if payload.comments else None,
    )
    db.commit()

    # Continue execution
    result = orchestrator.execute(db, action.plan_id)
    return result


@router.post("/{exception_id}/plan/actions/{action_id}/redirect")
def redirect_action(
    exception_id: uuid.UUID,
    action_id: uuid.UUID,
    payload: ActionRedirectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tell Claude what to do instead for a blocked action.

    Re-generates the action's parameters/approach using the user's instructions,
    then resumes execution.
    """
    action = (
        db.query(AutomationAction)
        .join(ResolutionPlan)
        .filter(
            ResolutionPlan.exception_id == exception_id,
            AutomationAction.id == action_id,
        )
        .first()
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Use AI to regenerate this step with user's instructions
    from app.services.ai_service import ai_service

    if not ai_service.available:
        raise HTTPException(status_code=503, detail="AI service not available")

    prompt = (
        f"The user wants to change the approach for this action step.\n\n"
        f"Original action type: {action.action_type}\n"
        f"Original parameters: {action.params_json}\n"
        f"Original expected result: {action.expected_result}\n\n"
        f"User's instructions: {payload.instructions}\n\n"
        f"Generate updated params_json and expected_result based on the user's "
        f"instructions. Return ONLY a JSON object with keys: "
        f'"params" (dict) and "expected_result" (string).'
    )

    raw = ai_service.call_claude(
        system_prompt="You update action step parameters based on user instructions. Return ONLY JSON.",
        user_message=prompt,
        max_tokens=1024,
    )
    parsed = ai_service.extract_json(raw) if raw else None

    if parsed:
        action.params_json = parsed.get("params", action.params_json)
        action.expected_result = parsed.get("expected_result", action.expected_result)

    # Mark as approved (user has reviewed and redirected)
    action.approved_by = current_user.id
    action.approved_at = datetime.now(timezone.utc)
    action.status = ActionStatus.pending
    db.commit()

    audit_service.log_action(
        db,
        entity_type="automation_action",
        entity_id=action.id,
        action="action_redirected",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        evidence={"instructions": payload.instructions},
    )
    db.commit()

    # Continue execution
    result = orchestrator.execute(db, action.plan_id)
    return result


@router.post("/{exception_id}/rerun-match")
def rerun_match(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-run matching for an exception's invoice."""
    exc = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    try:
        result = orchestrator.recheck(db, exception_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result
