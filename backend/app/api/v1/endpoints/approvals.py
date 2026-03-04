"""Approval workflow endpoints."""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.approval import ApprovalStatus, ApprovalTask
from app.models.audit import ActorType
from app.models.user import User
from app.schemas.approval import ApprovalAction, ApprovalTaskResponse, BatchApprovalAction
from app.services import approval_service, audit_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/pending", response_model=List[ApprovalTaskResponse])
def list_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending approval tasks. Admins see all; others see only their own."""
    from app.models.user import UserRole

    query = db.query(ApprovalTask).filter(
        ApprovalTask.status == ApprovalStatus.pending,
    )
    # Admins and approvers see all pending tasks; others only their own
    if current_user.role not in (UserRole.admin, UserRole.approver):
        query = query.filter(ApprovalTask.approver_id == current_user.id)

    tasks = query.order_by(ApprovalTask.created_at.asc()).all()
    return tasks


@router.post("/{task_id}/approve", response_model=ApprovalTaskResponse)
def approve_task(
    task_id: uuid.UUID,
    payload: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve an approval task."""
    try:
        task = approval_service.process_approval(
            db, task_id, approved=True, comments=payload.comments
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    audit_service.log_action(
        db,
        entity_type="approval_task",
        entity_id=task.id,
        action="approved",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
    )
    db.commit()
    return task


@router.post("/{task_id}/reject", response_model=ApprovalTaskResponse)
def reject_task(
    task_id: uuid.UUID,
    payload: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject an approval task."""
    try:
        task = approval_service.process_approval(
            db, task_id, approved=False, comments=payload.comments
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    audit_service.log_action(
        db,
        entity_type="approval_task",
        entity_id=task.id,
        action="rejected",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
    )
    db.commit()
    return task


@router.post("/batch-approve")
def batch_approve(
    payload: BatchApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch-approve multiple approval tasks."""
    approved = 0
    errors: list[str] = []
    for tid in payload.task_ids:
        try:
            approval_service.process_approval(
                db, tid, approved=True, comments=payload.comments
            )
            approved += 1
        except ValueError as e:
            errors.append(str(e))

    db.commit()
    return {"approved": approved, "errors": errors}


@router.get("/history", response_model=List[ApprovalTaskResponse])
def approval_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List historical approval decisions for the current user."""
    tasks = (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.approver_id == current_user.id,
            ApprovalTask.status != ApprovalStatus.pending,
        )
        .order_by(ApprovalTask.decision_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return tasks
