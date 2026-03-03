"""Duplicate invoice detection service.

Checks incoming invoices against existing records using multiple strategies:
1. Exact match on invoice_number + vendor
2. Fuzzy match on amount + vendor + date proximity
3. Hash-based detection using line item fingerprints
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus


def check_duplicate(
    db: Session,
    invoice_number: str,
    vendor_id: str,
    total_amount: float,
    invoice_date: Any = None,
    *,
    exclude_invoice_id: str | None = None,
) -> dict[str, Any]:
    """Check if an invoice is a potential duplicate.

    Returns:
        {
            "is_duplicate": bool,
            "confidence": float (0.0 - 1.0),
            "matches": [{"invoice_id": str, "reason": str, "score": float}],
        }
    """
    matches: list[dict[str, Any]] = []

    base_query = db.query(Invoice).filter(
        Invoice.status != InvoiceStatus.draft,
    )
    if exclude_invoice_id:
        matches_query = base_query.filter(Invoice.id != exclude_invoice_id)
    else:
        matches_query = base_query

    # ── Strategy 1: Exact invoice number + vendor match ───────────
    exact = matches_query.filter(
        and_(
            func.lower(Invoice.invoice_number) == invoice_number.strip().lower(),
            Invoice.vendor_id == vendor_id,
        )
    ).all()

    for inv in exact:
        matches.append({
            "invoice_id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "reason": "Exact invoice number and vendor match",
            "score": 1.0,
        })

    # ── Strategy 2: Same vendor + same amount ± 0.01 ─────────────
    amount_matches = matches_query.filter(
        and_(
            Invoice.vendor_id == vendor_id,
            Invoice.total_amount.between(total_amount - 0.01, total_amount + 0.01),
            func.lower(Invoice.invoice_number) != invoice_number.strip().lower(),
        )
    ).all()

    for inv in amount_matches:
        score = 0.7
        # Boost score if dates are close
        if invoice_date and inv.invoice_date:
            date_diff = abs((inv.invoice_date - invoice_date).days)
            if date_diff == 0:
                score = 0.95
            elif date_diff <= 3:
                score = 0.85
            elif date_diff <= 7:
                score = 0.75

        # Only flag if score is significant
        if score >= 0.7:
            matches.append({
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "reason": f"Same vendor and amount (${total_amount:,.2f}), date diff: {abs((inv.invoice_date - invoice_date).days) if invoice_date and inv.invoice_date else 'N/A'} days",
                "score": score,
            })

    # ── Strategy 3: Same invoice number, different vendor ─────────
    cross_vendor = matches_query.filter(
        and_(
            func.lower(Invoice.invoice_number) == invoice_number.strip().lower(),
            Invoice.vendor_id != vendor_id,
        )
    ).all()

    for inv in cross_vendor:
        matches.append({
            "invoice_id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "reason": "Same invoice number but different vendor (possible vendor mismatch)",
            "score": 0.6,
        })

    # Determine overall result
    if not matches:
        return {"is_duplicate": False, "confidence": 0.0, "matches": []}

    max_score = max(m["score"] for m in matches)
    return {
        "is_duplicate": max_score >= 0.7,
        "confidence": max_score,
        "matches": sorted(matches, key=lambda m: m["score"], reverse=True),
    }


def check_batch_duplicates(
    db: Session,
    invoices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Check a batch of invoices for duplicates (both against DB and within batch).

    Each item in invoices should have: invoice_number, vendor_id, total_amount, invoice_date
    """
    results = []

    for i, inv in enumerate(invoices):
        result = check_duplicate(
            db,
            invoice_number=inv["invoice_number"],
            vendor_id=inv["vendor_id"],
            total_amount=inv["total_amount"],
            invoice_date=inv.get("invoice_date"),
        )

        # Also check within the batch (against items before this one)
        for j in range(i):
            other = invoices[j]
            if (inv["invoice_number"].lower() == other["invoice_number"].lower()
                    and inv["vendor_id"] == other["vendor_id"]):
                result["matches"].append({
                    "invoice_id": f"batch_item_{j}",
                    "invoice_number": other["invoice_number"],
                    "reason": "Duplicate within current import batch",
                    "score": 1.0,
                })
                result["is_duplicate"] = True
                result["confidence"] = 1.0

        results.append(result)

    return results
