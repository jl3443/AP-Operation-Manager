"""Auto-resolution engine for minor invoice discrepancies.

Automatically resolves exceptions that fall within configurable tolerance
thresholds, reducing manual intervention for low-risk variances.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.config import ToleranceConfig
from app.models.exception import (
    Exception_,
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
    ResolutionType,
)
from app.models.invoice import Invoice, InvoiceStatus
from app.models.matching import MatchResult
from app.models.purchase_order import POLineItem


def get_active_tolerance(db: Session, vendor_id: str | None = None) -> ToleranceConfig | None:
    """Get the applicable tolerance config (vendor-specific or global)."""
    if vendor_id:
        vendor_tol = db.query(ToleranceConfig).filter(
            ToleranceConfig.scope == "vendor",
            ToleranceConfig.scope_value == str(vendor_id),
            ToleranceConfig.is_active == True,
        ).first()
        if vendor_tol:
            return vendor_tol

    return db.query(ToleranceConfig).filter(
        ToleranceConfig.scope == "global",
        ToleranceConfig.is_active == True,
    ).first()


def evaluate_exception(
    db: Session,
    exception: Exception_,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Evaluate whether an exception can be auto-resolved.

    Args:
        db: Database session
        exception: The exception to evaluate
        dry_run: If True, don't actually resolve — just return the evaluation

    Returns:
        {
            "can_auto_resolve": bool,
            "reason": str,
            "resolution_type": str | None,
            "details": dict,
        }
    """
    invoice = db.query(Invoice).filter(Invoice.id == exception.invoice_id).first()
    if not invoice:
        return {"can_auto_resolve": False, "reason": "Invoice not found", "details": {}}

    tolerance = get_active_tolerance(db, str(invoice.vendor_id))
    if not tolerance:
        return {"can_auto_resolve": False, "reason": "No active tolerance config", "details": {}}

    result: dict[str, Any] = {
        "can_auto_resolve": False,
        "reason": "",
        "resolution_type": None,
        "details": {},
    }

    if exception.exception_type == ExceptionType.amount_variance:
        result = _evaluate_amount_variance(db, exception, invoice, tolerance)
    elif exception.exception_type == ExceptionType.quantity_variance:
        result = _evaluate_quantity_variance(db, exception, invoice, tolerance)
    elif exception.exception_type == ExceptionType.tax_variance:
        result = _evaluate_tax_variance(db, exception, invoice, tolerance)
    else:
        result = {
            "can_auto_resolve": False,
            "reason": f"Exception type '{exception.exception_type.value}' requires manual review",
            "resolution_type": None,
            "details": {"exception_type": exception.exception_type.value},
        }

    # Apply auto-resolution if applicable and not dry run
    if result["can_auto_resolve"] and not dry_run:
        _apply_auto_resolution(db, exception, invoice, result)

    return result


def _evaluate_amount_variance(
    db: Session,
    exception: Exception_,
    invoice: Invoice,
    tolerance: ToleranceConfig,
) -> dict[str, Any]:
    """Check if an amount variance is within tolerance."""
    match_result = db.query(MatchResult).filter(
        MatchResult.invoice_id == invoice.id
    ).first()

    if not match_result or not match_result.matched_po_id:
        return {
            "can_auto_resolve": False,
            "reason": "No matched PO to compare against",
            "resolution_type": None,
            "details": {},
        }

    # Get PO line items for comparison
    po_lines = db.query(POLineItem).filter(
        POLineItem.po_id == match_result.matched_po_id
    ).all()
    po_total = sum(float(pl.line_total) for pl in po_lines)
    inv_total = float(invoice.total_amount)

    if po_total == 0:
        return {
            "can_auto_resolve": False,
            "reason": "PO total is zero",
            "resolution_type": None,
            "details": {},
        }

    variance_abs = abs(inv_total - po_total)
    variance_pct = (variance_abs / po_total) * 100

    within_pct = variance_pct <= float(tolerance.amount_tolerance_pct)
    within_abs = variance_abs <= float(tolerance.amount_tolerance_abs)

    if within_pct or within_abs:
        return {
            "can_auto_resolve": True,
            "reason": f"Amount variance (${variance_abs:,.2f} / {variance_pct:.1f}%) is within tolerance (${float(tolerance.amount_tolerance_abs):,.2f} / {float(tolerance.amount_tolerance_pct):.1f}%)",
            "resolution_type": ResolutionType.tolerance_applied.value,
            "details": {
                "po_total": po_total,
                "invoice_total": inv_total,
                "variance_abs": variance_abs,
                "variance_pct": variance_pct,
                "tolerance_abs": float(tolerance.amount_tolerance_abs),
                "tolerance_pct": float(tolerance.amount_tolerance_pct),
            },
        }

    return {
        "can_auto_resolve": False,
        "reason": f"Amount variance (${variance_abs:,.2f} / {variance_pct:.1f}%) exceeds tolerance (${float(tolerance.amount_tolerance_abs):,.2f} / {float(tolerance.amount_tolerance_pct):.1f}%)",
        "resolution_type": None,
        "details": {
            "po_total": po_total,
            "invoice_total": inv_total,
            "variance_abs": variance_abs,
            "variance_pct": variance_pct,
        },
    }


def _evaluate_quantity_variance(
    db: Session,
    exception: Exception_,
    invoice: Invoice,
    tolerance: ToleranceConfig,
) -> dict[str, Any]:
    """Check if a quantity variance is within tolerance."""
    match_result = db.query(MatchResult).filter(
        MatchResult.invoice_id == invoice.id
    ).first()

    if not match_result or not match_result.matched_po_id:
        return {
            "can_auto_resolve": False,
            "reason": "No matched PO to compare quantities against",
            "resolution_type": None,
            "details": {},
        }

    po_lines = db.query(POLineItem).filter(
        POLineItem.po_id == match_result.matched_po_id
    ).all()

    max_variance_pct = 0.0
    line_details = []

    for po_line in po_lines:
        ordered = float(po_line.quantity_ordered)
        received = float(po_line.quantity_received)
        if ordered == 0:
            continue

        variance_pct = abs(ordered - received) / ordered * 100
        max_variance_pct = max(max_variance_pct, variance_pct)
        line_details.append({
            "line": po_line.line_number,
            "ordered": ordered,
            "received": received,
            "variance_pct": variance_pct,
        })

    qty_tol = float(tolerance.quantity_tolerance_pct)
    if max_variance_pct <= qty_tol:
        return {
            "can_auto_resolve": True,
            "reason": f"Max quantity variance ({max_variance_pct:.1f}%) within tolerance ({qty_tol:.1f}%)",
            "resolution_type": ResolutionType.tolerance_applied.value,
            "details": {"lines": line_details, "tolerance_pct": qty_tol},
        }

    return {
        "can_auto_resolve": False,
        "reason": f"Quantity variance ({max_variance_pct:.1f}%) exceeds tolerance ({qty_tol:.1f}%)",
        "resolution_type": None,
        "details": {"lines": line_details, "tolerance_pct": qty_tol},
    }


def _evaluate_tax_variance(
    db: Session,
    exception: Exception_,
    invoice: Invoice,
    tolerance: ToleranceConfig,
) -> dict[str, Any]:
    """Check if a tax variance is within a small absolute threshold."""
    # Tax variances within $10 are auto-resolvable (rounding differences)
    TAX_TOLERANCE_ABS = 10.0

    details = exception.comments  # may contain tax diff info
    return {
        "can_auto_resolve": False,  # Conservative: require manual review for tax
        "reason": "Tax variances require manual review per policy",
        "resolution_type": None,
        "details": {"tax_tolerance_abs": TAX_TOLERANCE_ABS},
    }


def _apply_auto_resolution(
    db: Session,
    exception: Exception_,
    invoice: Invoice,
    evaluation: dict[str, Any],
) -> None:
    """Apply auto-resolution to an exception."""
    exception.status = ExceptionStatus.resolved
    exception.resolution_type = ResolutionType(evaluation["resolution_type"])
    exception.resolution_notes = f"AUTO-RESOLVED: {evaluation['reason']}"
    exception.resolved_at = datetime.now(timezone.utc)

    # If all exceptions for this invoice are resolved, advance the invoice status
    open_exceptions = db.query(Exception_).filter(
        Exception_.invoice_id == invoice.id,
        Exception_.status.in_([ExceptionStatus.open, ExceptionStatus.assigned, ExceptionStatus.in_progress]),
        Exception_.id != exception.id,
    ).count()

    if open_exceptions == 0:
        invoice.status = InvoiceStatus.pending_approval


def auto_resolve_all(db: Session, *, dry_run: bool = False) -> dict[str, Any]:
    """Scan all open exceptions and auto-resolve where possible.

    Returns summary of actions taken.
    """
    open_exceptions = db.query(Exception_).filter(
        Exception_.status.in_([ExceptionStatus.open, ExceptionStatus.assigned]),
        Exception_.exception_type.in_([
            ExceptionType.amount_variance,
            ExceptionType.quantity_variance,
            ExceptionType.tax_variance,
        ]),
    ).all()

    resolved = []
    skipped = []

    for exc in open_exceptions:
        result = evaluate_exception(db, exc, dry_run=dry_run)
        entry = {
            "exception_id": str(exc.id),
            "invoice_id": str(exc.invoice_id),
            "type": exc.exception_type.value,
            "evaluation": result,
        }
        if result["can_auto_resolve"]:
            resolved.append(entry)
        else:
            skipped.append(entry)

    if not dry_run:
        db.commit()

    return {
        "total_evaluated": len(open_exceptions),
        "auto_resolved": len(resolved),
        "requires_manual": len(skipped),
        "resolved": resolved,
        "skipped": skipped,
    }
