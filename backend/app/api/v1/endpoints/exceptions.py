"""Exception management endpoints."""

from __future__ import annotations

import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit import ActorType
from app.models.exception import Exception_, ExceptionStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.exception import (
    BatchAssignRequest,
    ExceptionCommentCreate,
    ExceptionCommentResponse,
    ExceptionResponse,
    ExceptionUpdate,
)
from app.services import audit_service, exception_service

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
