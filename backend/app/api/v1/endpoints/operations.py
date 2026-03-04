"""Operations endpoints: duplicate detection, auto-resolution, batch tasks."""

from __future__ import annotations

import contextlib

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.auto_resolution import auto_resolve_all
from app.services.duplicate_detection import check_duplicate

router = APIRouter(prefix="/operations", tags=["operations"])


class DuplicateCheckRequest(BaseModel):
    invoice_number: str = Field(..., min_length=1)
    vendor_id: str = Field(...)
    total_amount: float = Field(...)
    invoice_date: str | None = None


@router.post("/check-duplicate")
def check_invoice_duplicate(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if an invoice is a potential duplicate before processing."""
    from datetime import date

    invoice_date = None
    if payload.invoice_date:
        with contextlib.suppress(ValueError):
            invoice_date = date.fromisoformat(payload.invoice_date)

    result = check_duplicate(
        db,
        invoice_number=payload.invoice_number,
        vendor_id=payload.vendor_id,
        total_amount=payload.total_amount,
        invoice_date=invoice_date,
    )
    return result


@router.post("/auto-resolve")
def run_auto_resolution(
    dry_run: bool = Query(False, description="If true, only evaluate without applying resolutions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan open exceptions and auto-resolve those within tolerance."""
    result = auto_resolve_all(db, dry_run=dry_run)
    return result


@router.post("/batch-match")
def run_batch_matching(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run matching on all extracted invoices."""
    from app.tasks.invoice_tasks import run_batch_matching

    result = run_batch_matching()
    return result


@router.post("/duplicate-scan")
def run_duplicate_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan recent invoices for potential duplicates."""
    from app.tasks.invoice_tasks import run_duplicate_scan

    result = run_duplicate_scan()
    return result


@router.get("/daily-report")
def get_daily_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a daily AP operations summary."""
    from app.tasks.invoice_tasks import generate_daily_report

    result = generate_daily_report()
    return result
