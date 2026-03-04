"""Auto-match vendor from OCR-extracted fields (name, tax ID)."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from app.models.vendor import Vendor

FUZZY_THRESHOLD = 0.85


def auto_match_vendor(
    db: Session,
    vendor_name: Optional[str] = None,
    vendor_tax_id: Optional[str] = None,
) -> Optional[Vendor]:
    """Find the best matching vendor by tax_id (exact) or name (fuzzy).

    Returns the matched Vendor or None.
    """
    if not vendor_name and not vendor_tax_id:
        return None

    # 1) Exact match on tax_id (most reliable)
    if vendor_tax_id:
        vendor = (
            db.query(Vendor)
            .filter(Vendor.tax_id == vendor_tax_id.strip())
            .first()
        )
        if vendor:
            return vendor

    # 2) Fuzzy match on name
    if not vendor_name:
        return None

    target = vendor_name.strip().lower()
    vendors = db.query(Vendor).all()

    best_vendor: Optional[Vendor] = None
    best_ratio = 0.0

    for v in vendors:
        candidate = (v.name or "").strip().lower()
        if not candidate:
            continue
        ratio = SequenceMatcher(None, target, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_vendor = v

    if best_vendor and best_ratio >= FUZZY_THRESHOLD:
        return best_vendor

    return None
