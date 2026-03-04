"""CSV import services for POs, GRNs, and Vendors.

Supports two CSV formats:
1. Internal format (test-data/*.csv) with lowercase column names
2. AP_Inputs format (PO_Data.csv, GRN_Data.csv) with different column names

Auto-detects the format based on column names present.
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


def _safe_str(val: Any) -> str | None:
    """Convert to string, returning None for NaN/empty."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s else None


def _resolve_vendor(db: Session, vendor_code: str) -> Vendor | None:
    """Look up a vendor by vendor_code."""
    return db.query(Vendor).filter(Vendor.vendor_code == vendor_code).first()


def _resolve_or_create_vendor(
    db: Session,
    vendor_code: str,
    vendor_name: str | None = None,
) -> Vendor | None:
    """Look up a vendor by code, or auto-create if name is provided."""
    vendor = _resolve_vendor(db, vendor_code)
    if vendor:
        return vendor

    # Auto-create vendor from PO/GRN data if we have a name
    if vendor_name and vendor_code:
        vendor = Vendor(
            vendor_code=vendor_code,
            name=vendor_name,
            country="US",
            status=VendorStatus.active,
            risk_level=VendorRiskLevel.low,
        )
        db.add(vendor)
        db.flush()
        return vendor

    return None


def _is_ap_inputs_po_format(columns: list[str]) -> bool:
    """Detect if the CSV uses AP_Inputs format for POs."""
    return "supplier_id" in columns or "created_date" in columns


def _is_ap_inputs_grn_format(columns: list[str]) -> bool:
    """Detect if the CSV uses AP_Inputs format for GRNs."""
    return "supplier_id" in columns or "qty_received" in columns


# ── Purchase Orders ──────────────────────────────────────────────────────


def import_csv_purchase_orders(db: Session, file_content: bytes) -> dict[str, Any]:
    """Import purchase orders from CSV.

    Supports two formats:
    1. Internal: po_number, vendor_code, order_date, delivery_date, currency,
       status, line_number, description, quantity_ordered, unit_price
    2. AP_Inputs: PO_Number, Supplier_ID, Supplier_Name, Created_Date,
       Expected_Delivery, Status, Line_Number, Description, Quantity,
       Unit_Price, Line_Total, Currency
    """
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = [c.strip().lower() for c in df.columns]

    is_ap_format = _is_ap_inputs_po_format(list(df.columns))

    created = 0
    skipped = 0
    errors: list[str] = []

    # Normalize column names for AP_Inputs format
    po_number_col = "po_number"
    vendor_col = "supplier_id" if is_ap_format else "vendor_code"
    vendor_name_col = "supplier_name" if is_ap_format else None
    order_date_col = "created_date" if is_ap_format else "order_date"
    delivery_date_col = "expected_delivery" if is_ap_format else "delivery_date"
    qty_col = "quantity" if is_ap_format else "quantity_ordered"
    line_total_col = "line_total" if "line_total" in df.columns else None

    grouped = df.groupby(po_number_col)
    for po_number, group in grouped:
        try:
            first = group.iloc[0]

            # Skip if PO already exists
            existing = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == str(po_number)).first()
            if existing:
                skipped += 1
                continue

            # Resolve vendor
            vendor_code = str(first.get(vendor_col, "")).strip()
            vendor_name = (
                str(first.get(vendor_name_col, "")).strip()
                if vendor_name_col and vendor_name_col in first.index
                else None
            )

            if is_ap_format:
                vendor = _resolve_or_create_vendor(db, vendor_code, vendor_name)
            else:
                vendor = _resolve_vendor(db, vendor_code)

            if not vendor:
                errors.append(f"PO {po_number}: vendor '{vendor_code}' not found")
                continue

            # Build line items
            total_amount = 0.0
            line_data = []
            for _, row in group.iterrows():
                qty = float(row.get(qty_col, 0))
                price = float(row.get("unit_price", 0))

                if line_total_col and line_total_col in row.index and not pd.isna(row.get(line_total_col)):
                    lt = float(row[line_total_col])
                else:
                    lt = qty * price

                total_amount += lt
                line_data.append(
                    {
                        "line_number": int(row.get("line_number", 1)),
                        "description": str(row.get("description", "")),
                        "quantity_ordered": qty,
                        "unit_price": price,
                        "line_total": lt,
                        "quantity_received": float(row.get("quantity_received", 0)),
                        "quantity_invoiced": float(row.get("quantity_invoiced", 0)),
                    }
                )

            # Use PO_Total if available (AP_Inputs format)
            if is_ap_format and "po_total" in first.index and not pd.isna(first.get("po_total")):
                total_amount = float(first["po_total"])

            status_str = str(first.get("status", "open")).strip()
            # Map AP_Inputs statuses
            status_map = {
                "service_completed": "service_completed",
                "fully_received": "fully_received",
                "partially_received": "partially_received",
            }
            try:
                po_status = POStatus(status_map.get(status_str, status_str))
            except ValueError:
                po_status = POStatus.open

            po = PurchaseOrder(
                po_number=str(po_number),
                vendor_id=vendor.id,
                order_date=_parse_date(first.get(order_date_col)) or date.today(),
                delivery_date=_parse_date(first.get(delivery_date_col)),
                currency=str(first.get("currency", "USD")),
                total_amount=total_amount,
                status=po_status,
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

    Supports two formats:
    1. Internal: grn_number, po_number, vendor_code, receipt_date, warehouse,
       po_line_number, quantity_received, condition_notes
    2. AP_Inputs: GRN_Number, PO_Number, Supplier_ID, Received_Date, Warehouse,
       Line_Number, Qty_Received, Condition, Notes
    """
    df = pd.read_csv(io.BytesIO(file_content))
    df.columns = [c.strip().lower() for c in df.columns]

    is_ap_format = _is_ap_inputs_grn_format(list(df.columns))

    created = 0
    skipped = 0
    errors: list[str] = []

    vendor_col = "supplier_id" if is_ap_format else "vendor_code"
    receipt_date_col = "received_date" if is_ap_format else "receipt_date"
    line_number_col = "line_number" if is_ap_format else "po_line_number"
    qty_received_col = "qty_received" if is_ap_format else "quantity_received"
    notes_col = "notes" if is_ap_format else "condition_notes"

    grouped = df.groupby("grn_number")
    for grn_number, group in grouped:
        try:
            first = group.iloc[0]

            # Skip if GRN already exists
            existing = db.query(GoodsReceipt).filter(GoodsReceipt.grn_number == str(grn_number)).first()
            if existing:
                skipped += 1
                continue

            # Resolve po_number → PO UUID
            po_number = str(first.get("po_number", "")).strip()
            po = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
            if not po:
                errors.append(f"GRN {grn_number}: PO '{po_number}' not found")
                continue

            # Resolve vendor
            vendor_code = str(first.get(vendor_col, "")).strip()
            vendor = _resolve_vendor(db, vendor_code)
            if not vendor:
                # Try the vendor from the PO
                vendor = db.query(Vendor).filter(Vendor.id == po.vendor_id).first()
            if not vendor:
                errors.append(f"GRN {grn_number}: vendor '{vendor_code}' not found")
                continue

            warehouse_val = first.get("warehouse")
            warehouse = (
                str(warehouse_val).strip() if not pd.isna(warehouse_val) and str(warehouse_val).strip() else None
            )

            grn = GoodsReceipt(
                grn_number=str(grn_number),
                po_id=po.id,
                vendor_id=vendor.id,
                receipt_date=_parse_date(first.get(receipt_date_col)) or date.today(),
                warehouse=warehouse,
            )
            db.add(grn)
            db.flush()

            for _, row in group.iterrows():
                # Resolve line number → POLineItem UUID
                line_num = int(row.get(line_number_col, 0))
                po_line = (
                    db.query(POLineItem)
                    .filter(
                        POLineItem.po_id == po.id,
                        POLineItem.line_number == line_num,
                    )
                    .first()
                )
                if not po_line:
                    errors.append(f"GRN {grn_number}: PO line {line_num} not found in {po_number}")
                    continue

                qty = float(row.get(qty_received_col, 0))
                notes_val = row.get(notes_col, "")
                notes = str(notes_val).strip() if not pd.isna(notes_val) else None

                li = GRNLineItem(
                    grn_id=grn.id,
                    po_line_id=po_line.id,
                    quantity_received=qty,
                    condition_notes=notes or None,
                )
                db.add(li)

                # Update the PO line item's quantity_received
                po_line.quantity_received = max(float(po_line.quantity_received), qty)

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

    # Detect column name variants
    code_col = "vendor_code" if "vendor_code" in df.columns else "supplier_id"
    name_col = "name" if "name" in df.columns else "supplier_name"

    for _, row in df.iterrows():
        vendor_code = str(row.get(code_col, "")).strip()
        try:
            existing = db.query(Vendor).filter(Vendor.vendor_code == vendor_code).first()
            if existing:
                skipped += 1
                continue

            vendor = Vendor(
                vendor_code=vendor_code,
                name=str(row.get(name_col, vendor_code)),
                tax_id=_safe_str(row.get("tax_id")),
                address=_safe_str(row.get("address")),
                city=_safe_str(row.get("city")),
                state=_safe_str(row.get("state")),
                country=str(row.get("country", "US")),
                payment_terms_code=_safe_str(row.get("payment_terms_code")),
                status=VendorStatus(str(row.get("status", "active")))
                if _safe_str(row.get("status"))
                else VendorStatus.active,
                risk_level=VendorRiskLevel(str(row.get("risk_level", "low")))
                if _safe_str(row.get("risk_level"))
                else VendorRiskLevel.low,
            )
            db.add(vendor)
            created += 1
        except Exception as e:
            errors.append(f"Vendor {vendor_code}: {e}")

    db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}
