"""Global audit trail endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: str | None = Query(None),
    action: str | None = Query(None),
    actor_name: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all audit log entries with optional filtering and pagination."""
    query = db.query(AuditLog)

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if actor_name:
        query = query.filter(AuditLog.actor_name.ilike(f"%{actor_name}%"))
    if date_from:
        query = query.filter(func.date(AuditLog.timestamp) >= date_from)
    if date_to:
        query = query.filter(func.date(AuditLog.timestamp) <= date_to)

    total = query.count()
    items = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": [AuditLogResponse.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
