"""Invoice-to-PO / GRN matching service."""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.goods_receipt import GoodsReceipt, GRNLineItem
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
            line_details.append({"line": li.line_number, "status": "no_po_ref", "description": li.description or ""})
            continue

        po_line = po_line_map.get(li.po_line_id)
        if not po_line:
            line_details.append({"line": li.line_number, "status": "po_line_not_found", "description": li.description or ""})
            continue

        matched_po_ids.add(po_line.po_id)
        inv_qty = float(li.quantity)
        inv_price = float(li.unit_price) if li.unit_price else 0
        inv_total = float(li.line_total)
        po_qty = float(po_line.quantity_ordered)
        po_price = float(po_line.unit_price) if po_line.unit_price else 0
        po_total = float(po_line.line_total)

        amount_ok = _within_tolerance(inv_total, po_total, tol_pct, tol_abs)
        qty_ok = _within_tolerance(inv_qty, po_qty, qty_tol_pct, tol_abs)

        amt_variance_pct = ((inv_total - po_total) / po_total * 100) if po_total else 0
        qty_variance_pct = ((inv_qty - po_qty) / po_qty * 100) if po_qty else 0

        line_matched = amount_ok and qty_ok
        status_parts = []
        exceptions_for_line = []
        if not amount_ok:
            status_parts.append("amount_variance")
            exceptions_for_line.append({"type": "amount_variance", "variance": f"${abs(inv_total - po_total):.2f} ({abs(amt_variance_pct):.1f}%)"})
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
            exceptions_for_line.append({"type": "quantity_variance", "variance": f"{abs(inv_qty - po_qty):.0f} units ({abs(qty_variance_pct):.1f}%)"})
            exc = Exception_(
                invoice_id=invoice.id,
                exception_type=ExceptionType.quantity_variance,
                severity=ExceptionSeverity.medium,
                status=ExceptionStatus.open,
            )
            db.add(exc)
            exceptions_created.append(exc)

        if line_matched:
            matched_count += 1

        line_details.append({
            "line": li.line_number,
            "description": li.description or "",
            "status": "matched" if line_matched else ", ".join(status_parts),
            "invoice": {"quantity": inv_qty, "unit_price": inv_price, "line_total": inv_total},
            "po": {"quantity": po_qty, "unit_price": po_price, "line_total": po_total},
            "checks": {
                "amount": {"match": amount_ok, "variance_pct": round(amt_variance_pct, 1)},
                "quantity": {"match": qty_ok, "variance_pct": round(qty_variance_pct, 1)},
            },
            "exceptions": exceptions_for_line,
        })

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


def run_three_way_match(db: Session, invoice_id: uuid.UUID) -> MatchResult:
    """Compare invoice lines to PO lines AND GRN lines (three-way match).

    For each invoice line:
    1. Find the linked PO line (via po_line_id)
    2. Find GRN lines for that PO line (via GRNLineItem.po_line_id)
    3. Sum quantity_received across GRN lines
    4. Compare invoice qty/amount vs PO and invoice qty vs GRN received qty
    5. Create exceptions for variances
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

    po_line_ids = [li.po_line_id for li in invoice.line_items if li.po_line_id]
    if not po_line_ids:
        result = MatchResult(
            invoice_id=invoice.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.unmatched,
            overall_score=0.0,
            details={"reason": "No PO references on invoice line items"},
            tolerance_applied=False,
        )
        db.add(result)
        db.add(Exception_(
            invoice_id=invoice.id,
            exception_type=ExceptionType.missing_po,
            severity=ExceptionSeverity.high,
            status=ExceptionStatus.open,
        ))
        invoice.status = InvoiceStatus.exception
        db.commit()
        db.refresh(result)
        return result

    # Load PO lines with their GRN line items
    po_lines = (
        db.query(POLineItem)
        .options(joinedload(POLineItem.grn_line_items))
        .filter(POLineItem.id.in_(po_line_ids))
        .all()
    )
    po_line_map = {pl.id: pl for pl in po_lines}

    tolerance = _get_active_tolerance(db, vendor_id=invoice.vendor_id)
    tol_pct = tolerance.amount_tolerance_pct if tolerance else 0.0
    tol_abs = float(tolerance.amount_tolerance_abs) if tolerance else 0.0
    qty_tol_pct = tolerance.quantity_tolerance_pct if tolerance else 0.0

    matched_count = 0
    line_details: list[dict] = []
    matched_po_ids: set[uuid.UUID] = set()
    matched_grn_id_set: set[uuid.UUID] = set()

    for li in invoice.line_items:
        if not li.po_line_id:
            line_details.append({"line": li.line_number, "status": "no_po_ref", "description": li.description or ""})
            continue

        po_line = po_line_map.get(li.po_line_id)
        if not po_line:
            line_details.append({"line": li.line_number, "status": "po_line_not_found", "description": li.description or ""})
            continue

        matched_po_ids.add(po_line.po_id)

        inv_qty = float(li.quantity)
        inv_price = float(li.unit_price) if li.unit_price else 0
        inv_total = float(li.line_total)
        po_qty = float(po_line.quantity_ordered)
        po_price = float(po_line.unit_price) if po_line.unit_price else 0
        po_total = float(po_line.line_total)

        # 2-way checks: invoice vs PO
        amount_ok = _within_tolerance(inv_total, po_total, tol_pct, tol_abs)
        qty_ok = _within_tolerance(inv_qty, po_qty, qty_tol_pct, tol_abs)

        # 3-way check: invoice qty vs GRN received qty
        grn_lines = po_line.grn_line_items or []
        total_received = sum(float(gl.quantity_received) for gl in grn_lines)
        for gl in grn_lines:
            matched_grn_id_set.add(gl.grn_id)

        grn_ok = True
        if total_received > 0:
            grn_ok = _within_tolerance(inv_qty, total_received, qty_tol_pct, tol_abs)

        # Compute variances for rich comparison data
        amt_variance_pct = ((inv_total - po_total) / po_total * 100) if po_total else 0
        qty_variance_pct = ((inv_qty - po_qty) / po_qty * 100) if po_qty else 0
        grn_variance_pct = ((inv_qty - total_received) / total_received * 100) if total_received else 0

        status_parts = []
        exceptions_for_line = []
        if not amount_ok:
            status_parts.append("amount_variance")
            exceptions_for_line.append({"type": "amount_variance", "variance": f"${abs(inv_total - po_total):.2f} ({abs(amt_variance_pct):.1f}%)"})
            db.add(Exception_(
                invoice_id=invoice.id,
                exception_type=ExceptionType.amount_variance,
                severity=ExceptionSeverity.medium,
                status=ExceptionStatus.open,
            ))
        if not qty_ok:
            status_parts.append("quantity_variance")
            exceptions_for_line.append({"type": "quantity_variance", "variance": f"{abs(inv_qty - po_qty):.0f} units ({abs(qty_variance_pct):.1f}%)"})
            db.add(Exception_(
                invoice_id=invoice.id,
                exception_type=ExceptionType.quantity_variance,
                severity=ExceptionSeverity.medium,
                status=ExceptionStatus.open,
            ))
        if not grn_ok:
            status_parts.append("partial_delivery_overrun")
            exceptions_for_line.append({"type": "partial_delivery_overrun", "variance": f"{abs(inv_qty - total_received):.0f} units ({abs(grn_variance_pct):.1f}%)"})
            db.add(Exception_(
                invoice_id=invoice.id,
                exception_type=ExceptionType.partial_delivery_overrun,
                severity=ExceptionSeverity.medium,
                status=ExceptionStatus.open,
            ))

        line_matched = amount_ok and qty_ok and grn_ok
        if line_matched:
            matched_count += 1

        line_details.append({
            "line": li.line_number,
            "description": li.description or "",
            "status": "matched" if line_matched else ", ".join(status_parts),
            "invoice": {"quantity": inv_qty, "unit_price": inv_price, "line_total": inv_total},
            "po": {"quantity": po_qty, "unit_price": po_price, "line_total": po_total},
            "grn": {"quantity_received": total_received, "grn_count": len(grn_lines)},
            "checks": {
                "amount": {"match": amount_ok, "variance_pct": round(amt_variance_pct, 1)},
                "quantity": {"match": qty_ok, "variance_pct": round(qty_variance_pct, 1)},
                "grn_receipt": {"match": grn_ok, "variance_pct": round(grn_variance_pct, 1)},
            },
            "exceptions": exceptions_for_line,
        })

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

    if tolerance and match_status == MatchStatus.matched:
        match_status = MatchStatus.tolerance_passed

    first_po_id = next(iter(matched_po_ids), None)

    result = MatchResult(
        invoice_id=invoice.id,
        match_type=MatchType.three_way,
        match_status=match_status,
        overall_score=score,
        details={"lines": line_details},
        matched_po_id=first_po_id,
        matched_grn_ids=[str(gid) for gid in matched_grn_id_set],
        tolerance_applied=tolerance is not None,
        tolerance_config_id=tolerance.id if tolerance else None,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
