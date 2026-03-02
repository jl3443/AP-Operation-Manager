"""Exception management service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.exception import (
    Exception_,
    ExceptionComment,
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
)
from app.models.invoice import Invoice
from app.schemas.exception import ExceptionUpdate


def create_exception(
    db: Session,
    *,
    invoice_id: uuid.UUID,
    exception_type: ExceptionType,
    severity: ExceptionSeverity = ExceptionSeverity.medium,
) -> Exception_:
    """Create a new exception record."""
    exc = Exception_(
        invoice_id=invoice_id,
        exception_type=exception_type,
        severity=severity,
        status=ExceptionStatus.open,
    )
    db.add(exc)
    db.flush()
    return exc


def update_exception(
    db: Session,
    exception_id: uuid.UUID,
    payload: ExceptionUpdate,
    resolved_by: Optional[uuid.UUID] = None,
) -> Optional[Exception_]:
    """Update an exception (assign, resolve, escalate, etc.)."""
    exc = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not exc:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exc, field, value)

    # If resolving, stamp the timestamp
    if payload.status == ExceptionStatus.resolved:
        exc.resolved_at = datetime.now(timezone.utc)
        exc.resolved_by = resolved_by

    db.commit()
    db.refresh(exc)
    return exc


def detect_duplicate_invoice(
    db: Session, invoice_number: str, vendor_id: uuid.UUID
) -> bool:
    """Return True if an invoice with the same number + vendor already exists."""
    existing = (
        db.query(Invoice)
        .filter(
            Invoice.invoice_number == invoice_number,
            Invoice.vendor_id == vendor_id,
        )
        .first()
    )
    return existing is not None


def add_comment(
    db: Session,
    exception_id: uuid.UUID,
    user_id: uuid.UUID,
    comment_text: str,
    mentions: Optional[list[str]] = None,
) -> ExceptionComment:
    """Add a comment to an exception."""
    comment = ExceptionComment(
        exception_id=exception_id,
        user_id=user_id,
        comment_text=comment_text,
        mentions=mentions,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
