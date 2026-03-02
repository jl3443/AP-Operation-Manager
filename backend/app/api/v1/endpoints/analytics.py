"""Analytics / dashboard endpoints."""

from __future__ import annotations

from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.approval import ApprovalStatus, ApprovalTask
from app.models.exception import Exception_, ExceptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.matching import MatchResult, MatchStatus
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.analytics import (
    DashboardKPI,
    FunnelData,
    FunnelStage,
    TrendData,
    TrendPoint,
    VendorSummary,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardKPI)
def dashboard_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return high-level KPIs for the dashboard."""
    total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
    pending_approval = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.status == InvoiceStatus.pending_approval)
        .scalar()
        or 0
    )
    open_exceptions = (
        db.query(func.count(Exception_.id))
        .filter(Exception_.status.in_([ExceptionStatus.open, ExceptionStatus.assigned, ExceptionStatus.in_progress]))
        .scalar()
        or 0
    )
    total_amount_pending = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
        .filter(Invoice.status.in_([InvoiceStatus.pending_approval, InvoiceStatus.matching]))
        .scalar()
    )

    # Match rate
    total_matched = db.query(func.count(MatchResult.id)).scalar() or 0
    fully_matched = (
        db.query(func.count(MatchResult.id))
        .filter(MatchResult.match_status.in_([MatchStatus.matched, MatchStatus.tolerance_passed]))
        .scalar()
        or 0
    )
    match_rate = (fully_matched / total_matched * 100) if total_matched else 0.0

    # Straight-through rate: invoices that went from draft -> approved without exception
    approved = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.status == InvoiceStatus.approved)
        .scalar()
        or 0
    )
    stp_rate = (approved / total_invoices * 100) if total_invoices else 0.0

    # Overdue
    today = date.today()
    overdue = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.due_date < today, Invoice.status.notin_([InvoiceStatus.posted, InvoiceStatus.approved, InvoiceStatus.rejected]))
        .scalar()
        or 0
    )

    return DashboardKPI(
        total_invoices=total_invoices,
        pending_approval=pending_approval,
        open_exceptions=open_exceptions,
        total_amount_pending=float(total_amount_pending),
        avg_processing_time_hours=0.0,  # would require timestamps delta calculation
        match_rate_pct=round(match_rate, 1),
        straight_through_rate_pct=round(stp_rate, 1),
        overdue_invoices=overdue,
    )


@router.get("/funnel", response_model=FunnelData)
def invoice_funnel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return invoice processing funnel data."""
    stages = []
    for s in InvoiceStatus:
        count = db.query(func.count(Invoice.id)).filter(Invoice.status == s).scalar() or 0
        amount = (
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(Invoice.status == s)
            .scalar()
        )
        stages.append(FunnelStage(stage=s.value, count=count, amount=float(amount)))
    return FunnelData(stages=stages)


@router.get("/trends", response_model=List[TrendData])
def invoice_trends(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return daily invoice volume trends for the past N days."""
    today = date.today()
    start = today - timedelta(days=days)

    rows = (
        db.query(
            func.date(Invoice.created_at).label("day"),
            func.count(Invoice.id).label("cnt"),
        )
        .filter(func.date(Invoice.created_at) >= start)
        .group_by(func.date(Invoice.created_at))
        .order_by(func.date(Invoice.created_at))
        .all()
    )

    data_points = [TrendPoint(date=str(r.day), value=r.cnt) for r in rows]
    return [TrendData(series_name="invoices_received", data_points=data_points)]


@router.get("/vendors/top", response_model=List[VendorSummary])
def top_vendors(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return top vendors by invoice volume."""
    rows = (
        db.query(
            Vendor.id,
            Vendor.name,
            func.count(Invoice.id).label("invoice_count"),
            func.coalesce(func.sum(Invoice.total_amount), 0).label("total_amount"),
        )
        .join(Invoice, Invoice.vendor_id == Vendor.id)
        .group_by(Vendor.id, Vendor.name)
        .order_by(func.count(Invoice.id).desc())
        .limit(limit)
        .all()
    )

    results = []
    for r in rows:
        exc_count = (
            db.query(func.count(Exception_.id))
            .join(Invoice, Invoice.id == Exception_.invoice_id)
            .filter(Invoice.vendor_id == r.id)
            .scalar()
            or 0
        )
        results.append(
            VendorSummary(
                vendor_id=str(r.id),
                vendor_name=r.name,
                invoice_count=r.invoice_count,
                total_amount=float(r.total_amount),
                exception_count=exc_count,
            )
        )
    return results
