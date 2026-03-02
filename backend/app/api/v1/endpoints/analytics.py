"""Analytics / dashboard endpoints."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.approval import ApprovalStatus, ApprovalTask
from app.models.exception import Exception_, ExceptionStatus, ExceptionType
from app.models.invoice import Invoice, InvoiceStatus
from app.models.matching import MatchResult, MatchStatus
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.analytics import (
    AgingBucket,
    AgingData,
    ApprovalTurnaround,
    DashboardKPI,
    ExceptionBreakdown,
    FunnelData,
    FunnelStage,
    MonthlyComparison,
    OptimizationProposal,
    RootCauseItem,
    TouchlessRate,
    TrendData,
    TrendPoint,
    VendorRiskDistribution,
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


@router.get("/aging", response_model=AgingData)
def invoice_aging(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bucket unpaid invoices by days to due date."""
    today = date.today()
    excluded = [InvoiceStatus.posted, InvoiceStatus.approved, InvoiceStatus.rejected]
    invoices = (
        db.query(Invoice.due_date, Invoice.total_amount)
        .filter(Invoice.status.notin_(excluded))
        .all()
    )

    buckets_map: dict[str, dict] = {
        "current": {"count": 0, "amount": 0.0},
        "1-30": {"count": 0, "amount": 0.0},
        "31-60": {"count": 0, "amount": 0.0},
        "61-90": {"count": 0, "amount": 0.0},
        "90+": {"count": 0, "amount": 0.0},
    }

    for inv in invoices:
        days_past = (today - inv.due_date).days
        if days_past <= 0:
            key = "current"
        elif days_past <= 30:
            key = "1-30"
        elif days_past <= 60:
            key = "31-60"
        elif days_past <= 90:
            key = "61-90"
        else:
            key = "90+"
        buckets_map[key]["count"] += 1
        buckets_map[key]["amount"] += float(inv.total_amount)

    buckets = [
        AgingBucket(bucket=k, count=v["count"], amount=round(v["amount"], 2))
        for k, v in buckets_map.items()
    ]
    return AgingData(buckets=buckets)


@router.get("/exceptions/breakdown", response_model=List[ExceptionBreakdown])
def exceptions_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Group exceptions by type with counts and percentages."""
    rows = (
        db.query(
            Exception_.exception_type,
            func.count(Exception_.id).label("cnt"),
        )
        .group_by(Exception_.exception_type)
        .all()
    )

    total = sum(r.cnt for r in rows) or 1
    return [
        ExceptionBreakdown(
            exception_type=r.exception_type.value if hasattr(r.exception_type, "value") else str(r.exception_type),
            count=r.cnt,
            percentage=round(r.cnt / total * 100, 1),
        )
        for r in rows
    ]


@router.get("/vendors/risk-distribution", response_model=List[VendorRiskDistribution])
def vendor_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Group vendors by risk level with counts and percentages."""
    rows = (
        db.query(
            Vendor.risk_level,
            func.count(Vendor.id).label("cnt"),
        )
        .group_by(Vendor.risk_level)
        .all()
    )

    total = sum(r.cnt for r in rows) or 1
    return [
        VendorRiskDistribution(
            risk_level=r.risk_level.value if hasattr(r.risk_level, "value") else str(r.risk_level),
            count=r.cnt,
            percentage=round(r.cnt / total * 100, 1),
        )
        for r in rows
    ]


@router.get("/monthly-comparison", response_model=List[MonthlyComparison])
def monthly_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare current vs previous month invoice counts and amounts."""
    today = date.today()
    current_month_start = today.replace(day=1)
    prev_month_end = current_month_start - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)

    results = []
    for label, start, end in [
        (prev_month_start.strftime("%Y-%m"), prev_month_start, prev_month_end),
        (current_month_start.strftime("%Y-%m"), current_month_start, today),
    ]:
        row = (
            db.query(
                func.count(Invoice.id).label("cnt"),
                func.coalesce(func.sum(Invoice.total_amount), 0).label("amt"),
            )
            .filter(
                func.date(Invoice.created_at) >= start,
                func.date(Invoice.created_at) <= end,
            )
            .one()
        )
        results.append(
            MonthlyComparison(
                month=label,
                invoice_count=row.cnt,
                total_amount=round(float(row.amt), 2),
            )
        )

    return results


@router.get("/approvals/turnaround", response_model=List[ApprovalTurnaround])
def approvals_turnaround(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate average approval turnaround hours grouped by level."""
    rows = (
        db.query(
            ApprovalTask.approval_level,
            func.avg(
                func.extract("epoch", ApprovalTask.decision_at)
                - func.extract("epoch", ApprovalTask.created_at)
            ).label("avg_seconds"),
            func.count(ApprovalTask.id).label("total"),
        )
        .filter(ApprovalTask.decision_at.isnot(None))
        .group_by(ApprovalTask.approval_level)
        .order_by(ApprovalTask.approval_level)
        .all()
    )

    return [
        ApprovalTurnaround(
            level=r.approval_level,
            avg_hours=round(float(r.avg_seconds or 0) / 3600, 2),
            total_tasks=r.total,
        )
        for r in rows
    ]


@router.get("/report/pdf")
def analytics_report_pdf(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return a PDF analytics report."""
    from app.services.pdf_report import generate_analytics_pdf

    if date_from is None:
        date_from = date.today() - timedelta(days=30)
    if date_to is None:
        date_to = date.today()

    pdf_bytes = generate_analytics_pdf(db, date_from, date_to)
    buffer = BytesIO(pdf_bytes)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=ap_analytics_{date_from}_{date_to}.pdf"
        },
    )


@router.get("/touchless-rate", response_model=TouchlessRate)
def touchless_rate(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate touchless processing rate and avg cycle time."""
    total = db.query(func.count(Invoice.id)).scalar() or 0

    # Touchless = invoices that reached approved/posted WITHOUT any exception
    from sqlalchemy import exists, and_
    exception_subq = db.query(Exception_.id).filter(
        Exception_.invoice_id == Invoice.id
    ).exists()

    touchless = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.status.in_([InvoiceStatus.approved, InvoiceStatus.posted]),
            ~exception_subq,
        )
        .scalar()
        or 0
    )

    rate = (touchless / total * 100) if total else 0.0

    # Avg cycle time: hours from created_at to updated_at for approved/posted
    from sqlalchemy import extract as sql_extract
    avg_hours_row = (
        db.query(
            func.avg(
                func.extract("epoch", Invoice.updated_at)
                - func.extract("epoch", Invoice.created_at)
            )
        )
        .filter(Invoice.status.in_([InvoiceStatus.approved, InvoiceStatus.posted]))
        .scalar()
    )
    avg_hours = round(float(avg_hours_row or 0) / 3600, 2)

    return TouchlessRate(
        rate=round(rate, 1),
        total_invoices=total,
        touchless_count=touchless,
        cycle_time_avg_hours=avg_hours,
    )


@router.get("/root-causes", response_model=List[RootCauseItem])
def root_causes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze exception patterns to identify root causes."""
    results = []

    # Group exceptions by type and vendor
    rows = (
        db.query(
            Exception_.exception_type,
            Vendor.name.label("vendor_name"),
            func.count(Exception_.id).label("cnt"),
            func.sum(Invoice.total_amount).label("total_amount"),
        )
        .join(Invoice, Invoice.id == Exception_.invoice_id)
        .join(Vendor, Vendor.id == Invoice.vendor_id)
        .group_by(Exception_.exception_type, Vendor.name)
        .order_by(func.count(Exception_.id).desc())
        .limit(15)
        .all()
    )

    fix_map = {
        "amount_variance": "Review tolerance thresholds or negotiate fixed pricing with vendor",
        "quantity_variance": "Align PO quantities with actual delivery schedules",
        "missing_po": "Enforce PO-required policy; train suppliers on PO reference requirements",
        "duplicate_invoice": "Enable real-time duplicate detection at email ingestion",
        "vendor_mismatch": "Cleanse vendor master data; standardize naming conventions",
        "tax_variance": "Update tax configuration for vendor jurisdiction",
        "expired_po": "Automate PO renewal reminders 30 days before expiry",
        "partial_delivery_overrun": "Require GRN confirmation before invoice acceptance",
        "contract_price_variance": "Auto-sync contract prices to PO catalog",
        "vendor_on_hold": "Block invoice submission for on-hold vendors at portal level",
    }

    for r in rows:
        exc_type = r.exception_type.value if hasattr(r.exception_type, "value") else str(r.exception_type)
        results.append(RootCauseItem(
            category=exc_type,
            issue=f"{exc_type.replace('_', ' ').title()} — {r.vendor_name}",
            occurrence_count=r.cnt,
            affected_invoices=r.cnt,
            impact_amount=round(float(r.total_amount or 0), 2),
            suggested_fix=fix_map.get(exc_type, "Investigate and update matching rules"),
        ))

    return results


@router.get("/optimization-proposals", response_model=List[OptimizationProposal])
def optimization_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate optimization proposals based on system performance data."""
    proposals = []

    # Analyze exception patterns to generate proposals
    total_invoices = db.query(func.count(Invoice.id)).scalar() or 1
    total_exceptions = db.query(func.count(Exception_.id)).scalar() or 0
    exception_rate = total_exceptions / total_invoices * 100

    # Check amount variance frequency
    amt_var_count = (
        db.query(func.count(Exception_.id))
        .filter(Exception_.exception_type == ExceptionType.amount_variance)
        .scalar() or 0
    )
    if amt_var_count > 0:
        proposals.append(OptimizationProposal(
            id="opt-1",
            title="Increase Amount Tolerance Threshold",
            description=f"{amt_var_count} amount variance exceptions detected. Increasing tolerance from 2% to 5% could auto-resolve ~{min(amt_var_count, int(amt_var_count*0.6))} of these.",
            category="tolerance",
            priority="high",
            projected_impact=f"+{round(amt_var_count*0.6/total_invoices*100, 1)}% touchless rate",
            effort="low",
            status="proposed",
        ))

    # Check missing PO frequency
    missing_po_count = (
        db.query(func.count(Exception_.id))
        .filter(Exception_.exception_type == ExceptionType.missing_po)
        .scalar() or 0
    )
    if missing_po_count > 0:
        proposals.append(OptimizationProposal(
            id="opt-2",
            title="Enable Fuzzy PO Matching",
            description=f"{missing_po_count} missing PO exceptions. Fuzzy matching on vendor + amount + date could resolve ~{min(missing_po_count, int(missing_po_count*0.7))} automatically.",
            category="matching_rule",
            priority="high",
            projected_impact=f"+{round(missing_po_count*0.7/total_invoices*100, 1)}% touchless rate",
            effort="medium",
            status="proposed",
        ))

    # Check quantity variance
    qty_var_count = (
        db.query(func.count(Exception_.id))
        .filter(Exception_.exception_type == ExceptionType.quantity_variance)
        .scalar() or 0
    )
    if qty_var_count > 0:
        proposals.append(OptimizationProposal(
            id="opt-3",
            title="Add Partial Delivery Tolerance",
            description=f"{qty_var_count} quantity variance exceptions. Allowing 10% partial delivery tolerance would reduce these by ~{min(qty_var_count, int(qty_var_count*0.5))}.",
            category="tolerance",
            priority="medium",
            projected_impact=f"-{qty_var_count} exceptions/month",
            effort="low",
            status="proposed",
        ))

    # Check vendor on-hold
    vendor_hold_count = (
        db.query(func.count(Exception_.id))
        .filter(Exception_.exception_type == ExceptionType.vendor_on_hold)
        .scalar() or 0
    )
    if vendor_hold_count > 0:
        proposals.append(OptimizationProposal(
            id="opt-4",
            title="Block Invoices from On-Hold Vendors at Ingestion",
            description=f"{vendor_hold_count} invoices from on-hold vendors reached processing. Pre-screening at email/portal would prevent wasted processing.",
            category="policy",
            priority="medium",
            projected_impact=f"-{vendor_hold_count} wasted processing cycles",
            effort="medium",
            status="proposed",
        ))

    # General: If exception rate is high, suggest supplier training
    if exception_rate > 20:
        proposals.append(OptimizationProposal(
            id="opt-5",
            title="Supplier Invoice Quality Training Program",
            description=f"Exception rate is {exception_rate:.0f}%. A supplier training program on proper PO referencing and invoice format could reduce exceptions by 30-40%.",
            category="supplier_config",
            priority="high",
            projected_impact="-30% exception rate",
            effort="high",
            status="proposed",
        ))

    return proposals
