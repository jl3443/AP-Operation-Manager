"""Invoice-to-PO / GRN matching service."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.goods_receipt import GoodsReceipt
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.matching import MatchResult, MatchStatus, MatchType
from app.models.purchase_order import POLineItem, PurchaseOrder
from app.models.config import ToleranceConfig
from app.models.exception import (
    Exception_,
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
)


def _get_active_tolerance(db: Session, vendor_id: uuid.UUID | None = None) -> ToleranceConfig | None:
    """Return the most specific active tolerance config."""
    if vendor_id:
        vendor_tol = (
            db.query(ToleranceConfig)
            .filter(
                ToleranceConfig.is_active == True,
                ToleranceConfig.scope == "vendor",
                ToleranceConfig.scope_value == str(vendor_id),
            )
            .first()
        )
        if vendor_tol:
            return vendor_tol

    return (
        db.query(ToleranceConfig)
        .filter(
            ToleranceConfig.is_active == True,
            ToleranceConfig.scope == "global",
        )
        .first()
    )


def _within_tolerance(
    invoice_val: float,
    po_val: float,
    tol_pct: float,
    tol_abs: float,
) -> bool:
    """Check whether the variance falls within tolerance."""
    if po_val == 0:
        return invoice_val == 0
    variance = abs(invoice_val - po_val)
    pct_variance = (variance / po_val) * 100
    return pct_variance <= tol_pct or variance <= tol_abs


def run_two_way_match(db: Session, invoice_id: uuid.UUID) -> MatchResult:
    """Compare invoice line items to PO line items (two-way match).

    Detects exceptions for amount variance, quantity variance, missing PO, etc.
    """
    invoice = (
        db.query(Invoice)
        .options(joinedload(Invoice.line_items))
        .filter(Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    invoice.status = InvoiceStatus.matching

    # Gather PO IDs referenced by invoice line items
    po_line_ids = [li.po_line_id for li in invoice.line_items if li.po_line_id]
    if not po_line_ids:
        # No PO references at all => missing_po exception
        result = MatchResult(
            invoice_id=invoice.id,
            match_type=MatchType.two_way,
            match_status=MatchStatus.unmatched,
            overall_score=0.0,
            details={"reason": "No PO references on invoice line items"},
            tolerance_applied=False,
        )
        db.add(result)

        exc = Exception_(
            invoice_id=invoice.id,
            exception_type=ExceptionType.missing_po,
            severity=ExceptionSeverity.high,
            status=ExceptionStatus.open,
        )
        db.add(exc)
        invoice.status = InvoiceStatus.exception
        db.commit()
        db.refresh(result)
        return result

    # Load the PO lines
    po_lines = db.query(POLineItem).filter(POLineItem.id.in_(po_line_ids)).all()
    po_line_map = {pl.id: pl for pl in po_lines}

    tolerance = _get_active_tolerance(db, vendor_id=invoice.vendor_id)
    tol_pct = tolerance.amount_tolerance_pct if tolerance else 0.0
    tol_abs = float(tolerance.amount_tolerance_abs) if tolerance else 0.0
    qty_tol_pct = tolerance.quantity_tolerance_pct if tolerance else 0.0

    matched_count = 0
    exceptions_created: list[Exception_] = []
    line_details: list[dict] = []
    matched_po_ids: set[uuid.UUID] = set()

    for li in invoice.line_items:
        if not li.po_line_id:
            line_details.append({"line": li.line_number, "status": "no_po_ref"})
            continue

        po_line = po_line_map.get(li.po_line_id)
        if not po_line:
            line_details.append({"line": li.line_number, "status": "po_line_not_found"})
            continue

        matched_po_ids.add(po_line.po_id)
        amount_ok = _within_tolerance(float(li.line_total), float(po_line.line_total), tol_pct, tol_abs)
        qty_ok = _within_tolerance(float(li.quantity), float(po_line.quantity_ordered), qty_tol_pct, tol_abs)

        if amount_ok and qty_ok:
            matched_count += 1
            line_details.append({"line": li.line_number, "status": "matched"})
        else:
            status_parts = []
            if not amount_ok:
                status_parts.append("amount_variance")
                exc = Exception_(
                    invoice_id=invoice.id,
                    exception_type=ExceptionType.amount_variance,
                    severity=ExceptionSeverity.medium,
                    status=ExceptionStatus.open,
                )
                db.add(exc)
                exceptions_created.append(exc)
            if not qty_ok:
                status_parts.append("quantity_variance")
                exc = Exception_(
                    invoice_id=invoice.id,
                    exception_type=ExceptionType.quantity_variance,
                    severity=ExceptionSeverity.medium,
                    status=ExceptionStatus.open,
                )
                db.add(exc)
                exceptions_created.append(exc)
            line_details.append({"line": li.line_number, "status": ", ".join(status_parts)})

    total_lines = len(invoice.line_items)
    score = (matched_count / total_lines * 100) if total_lines else 0.0

    if matched_count == total_lines:
        match_status = MatchStatus.matched
        invoice.status = InvoiceStatus.pending_approval
    elif matched_count > 0:
        match_status = MatchStatus.partial
        invoice.status = InvoiceStatus.exception
    else:
        match_status = MatchStatus.unmatched
        invoice.status = InvoiceStatus.exception

    # If tolerance was applied and everything passed, mark accordingly
    if tolerance and match_status == MatchStatus.matched:
        match_status = MatchStatus.tolerance_passed

    first_po_id = next(iter(matched_po_ids), None)

    result = MatchResult(
        invoice_id=invoice.id,
        match_type=MatchType.two_way,
        match_status=match_status,
        overall_score=score,
        details={"lines": line_details},
        matched_po_id=first_po_id,
        tolerance_applied=tolerance is not None,
        tolerance_config_id=tolerance.id if tolerance else None,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
