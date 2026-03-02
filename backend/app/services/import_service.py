"""CSV import services for POs, GRNs, and Vendors.

Resolves human-readable codes (vendor_code, po_number, po_line_number) to
database UUIDs so the test CSV files work directly.
"""

from __future__ import annotations

import io
from datetime import date, datetime
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.goods_receipt import GoodsReceipt, GRNLineItem
from app.models.purchase_order import POLineItem, POStatus, PurchaseOrder
from app.models.vendor import Vendor, VendorRiskLevel, VendorStatus


def _parse_date(val: Any) -> date | None:
    """Try to coerce a value to a date."""
    if pd.isna(val):
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        return pd.to_datetime(str(val)).date()
    except Exception:
        return None


def _resolve_vendor(db: Session, vendor_code: str) -> Vendor | None:
    """Look up a vendor by vendor_code."""
    return db.query(Vendor).filter(Vendor.vendor_code == vendor_code).first()


# ── Purchase Orders ──────────────────────────────────────────────────────


def import_csv_purchase_orders(db: Session, file_content: bytes) -> dict[str, Any]:
    """Import purchase orders from CSV.

    Expected columns (matching test-data/purchase_orders.csv):
        po_number, vendor_code, order_date, delivery_date, currency, status,
        line_number, description, quantity_ordered, unit_price,
        quantity_received, quantity_invoiced
    """
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = [c.strip().lower() for c in df.columns]

    created = 0
    skipped = 0
    errors: list[str] = []

    grouped = df.groupby("po_number")
    for po_number, group in grouped:
        try:
            first = group.iloc[0]

            # Skip if PO already exists
            existing = db.query(PurchaseOrder).filter(
                PurchaseOrder.po_number == str(po_number)
            ).first()
            if existing:
                skipped += 1
                continue

            # Resolve vendor_code → vendor UUID
            vendor_code = str(first.get("vendor_code", "")).strip()
            vendor = _resolve_vendor(db, vendor_code)
            if not vendor:
                errors.append(f"PO {po_number}: vendor '{vendor_code}' not found")
                continue

            # Calculate total_amount from line items
            total_amount = 0.0
            line_data = []
            for _, row in group.iterrows():
                qty = float(row.get("quantity_ordered", 0))
                price = float(row.get("unit_price", 0))
                line_total = qty * price
                total_amount += line_total
                line_data.append({
                    "line_number": int(row.get("line_number", 1)),
                    "description": str(row.get("description", "")),
                    "quantity_ordered": qty,
                    "unit_price": price,
                    "line_total": line_total,
                    "quantity_received": float(row.get("quantity_received", 0)),
                    "quantity_invoiced": float(row.get("quantity_invoiced", 0)),
                })

            status_str = str(first.get("status", "open")).strip()
            po = PurchaseOrder(
                po_number=str(po_number),
                vendor_id=vendor.id,
                order_date=_parse_date(first["order_date"]) or date.today(),
                delivery_date=_parse_date(first.get("delivery_date")),
                currency=str(first.get("currency", "USD")),
                total_amount=total_amount,
                status=POStatus(status_str),
            )
            db.add(po)
            db.flush()

            for ld in line_data:
                li = POLineItem(
                    po_id=po.id,
                    line_number=ld["line_number"],
                    description=ld["description"],
                    quantity_ordered=ld["quantity_ordered"],
                    unit_price=ld["unit_price"],
                    line_total=ld["line_total"],
                    quantity_received=ld["quantity_received"],
                    quantity_invoiced=ld["quantity_invoiced"],
                )
                db.add(li)

            created += 1
        except Exception as e:
            errors.append(f"PO {po_number}: {e}")

    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}


# ── Goods Receipts ───────────────────────────────────────────────────────


def import_csv_goods_receipts(db: Session, file_content: bytes) -> dict[str, Any]:
    """Import goods receipts from CSV.

    Expected columns (matching test-data/goods_receipts.csv):
        grn_number, po_number, vendor_code, receipt_date, warehouse,
        po_line_number, quantity_received, condition_notes
    """
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = [c.strip().lower() for c in df.columns]

    created = 0
    skipped = 0
    errors: list[str] = []

    grouped = df.groupby("grn_number")
    for grn_number, group in grouped:
        try:
            first = group.iloc[0]

            # Skip if GRN already exists
            existing = db.query(GoodsReceipt).filter(
                GoodsReceipt.grn_number == str(grn_number)
            ).first()
            if existing:
                skipped += 1
                continue

            # Resolve po_number → PO UUID
            po_number = str(first.get("po_number", "")).strip()
            po = db.query(PurchaseOrder).filter(
                PurchaseOrder.po_number == po_number
            ).first()
            if not po:
                errors.append(f"GRN {grn_number}: PO '{po_number}' not found")
                continue

            # Resolve vendor_code → vendor UUID
            vendor_code = str(first.get("vendor_code", "")).strip()
            vendor = _resolve_vendor(db, vendor_code)
            if not vendor:
                errors.append(f"GRN {grn_number}: vendor '{vendor_code}' not found")
                continue

            grn = GoodsReceipt(
                grn_number=str(grn_number),
                po_id=po.id,
                vendor_id=vendor.id,
                receipt_date=_parse_date(first["receipt_date"]) or date.today(),
                warehouse=str(first.get("warehouse", "")) or None,
            )
            db.add(grn)
            db.flush()

            for _, row in group.iterrows():
                # Resolve po_line_number → POLineItem UUID
                po_line_number = int(row.get("po_line_number", 0))
                po_line = db.query(POLineItem).filter(
                    POLineItem.po_id == po.id,
                    POLineItem.line_number == po_line_number,
                ).first()
                if not po_line:
                    errors.append(
                        f"GRN {grn_number}: PO line {po_line_number} not found in {po_number}"
                    )
                    continue

                li = GRNLineItem(
                    grn_id=grn.id,
                    po_line_id=po_line.id,
                    quantity_received=float(row["quantity_received"]),
                    condition_notes=str(row.get("condition_notes", "")) or None,
                )
                db.add(li)

            created += 1
        except Exception as e:
            errors.append(f"GRN {grn_number}: {e}")

    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}


# ── Vendors ──────────────────────────────────────────────────────────────


def import_csv_vendors(db: Session, file_content: bytes) -> dict[str, Any]:
    """Import vendors from CSV.

    Expected columns (matching test-data/vendors.csv):
        vendor_code, name, tax_id, address, city, state, country,
        payment_terms_code, status, risk_level
    """
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = [c.strip().lower() for c in df.columns]

    created = 0
    skipped = 0
    errors: list[str] = []

    for _, row in df.iterrows():
        vendor_code = str(row.get("vendor_code", "")).strip()
        try:
            existing = db.query(Vendor).filter(Vendor.vendor_code == vendor_code).first()
            if existing:
                skipped += 1
                continue

            # Handle NaN values from pandas
            def safe_str(val: Any) -> str | None:
                if pd.isna(val):
                    return None
                s = str(val).strip()
                return s if s else None

            vendor = Vendor(
                vendor_code=vendor_code,
                name=str(row["name"]),
                tax_id=safe_str(row.get("tax_id")),
                address=safe_str(row.get("address")),
                city=safe_str(row.get("city")),
                state=safe_str(row.get("state")),
                country=str(row.get("country", "US")),
                payment_terms_code=safe_str(row.get("payment_terms_code")),
                status=VendorStatus(str(row.get("status", "active"))),
                risk_level=VendorRiskLevel(str(row.get("risk_level", "low"))),
            )
            db.add(vendor)
            created += 1
        except Exception as e:
            errors.append(f"Vendor {vendor_code}: {e}")

    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
