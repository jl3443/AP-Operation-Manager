#!/usr/bin/env python3
"""Generate demo invoice PDFs on Desktop + seed matching PO/GRN data in DB.

Usage:
  cd backend
  python generate_demo_invoices.py           # Clean old data + generate PDFs + seed DB
  python generate_demo_invoices.py --clean   # Only clean all demo/showcase data

Creates 5 invoice PDF files on ~/Desktop/Demo_Invoices/
Seeds corresponding PO and GRN records so the pipeline produces specific outcomes.

Scenarios:
  1. Clean Match      — SteelCore: perfect 3-way match → auto-approve
  2. Missing PO       — TechParts: no PO exists → exception → AI drafts email
  3. Data Mismatch    — SafeGuard: line totals don't add up → needs calculation
  4. Amount Variance   — MachPrecision: 10% price overcharge
  5. Quantity Overrun  — LogiTrans: invoiced 580, PO/GRN only 500
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

# ── ReportLab PDF generation ──────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ── SQLAlchemy (seed data) ────────────────────────────────────────────────
from app.core.database import SessionLocal
from app.models.vendor import Vendor
from app.models.purchase_order import PurchaseOrder, POLineItem, POStatus
from app.models.goods_receipt import GoodsReceipt, GRNLineItem
from app.models.invoice import Invoice, InvoiceLineItem
from app.models.matching import MatchResult
from app.models.exception import Exception_
from app.models.resolution import ResolutionPlan, AutomationAction
from app.models.approval import ApprovalTask
from app.models.audit import AuditLog

OUTPUT_DIR = Path.home() / "Desktop" / "Demo_Invoices"

# ── Vendor lookup ─────────────────────────────────────────────────────────
VENDORS = {
    "SUP001": {"name": "SteelCore Industries Ltd.", "addr": "100 Steel Way, Pittsburgh PA 15201", "tax_id": "91-1234567"},
    "SUP002": {"name": "TechParts Global Inc.", "addr": "200 Tech Blvd, San Jose CA 95131", "tax_id": "91-2345678"},
    "SUP003": {"name": "LogiTrans Freight Solutions", "addr": "300 Freight Rd, Memphis TN 38118", "tax_id": "91-3456789"},
    "SUP004": {"name": "SafeGuard PPE & Safety", "addr": "400 Safety Lane, Houston TX 77001", "tax_id": "91-4567890"},
    "SUP005": {"name": "MachPrecision Tools Corp.", "addr": "500 Precision Dr, Detroit MI 48201", "tax_id": "91-5678901"},
}

# ── Demo invoice numbers (used for cleanup identification) ───────────────
DEMO_INVOICE_NUMBERS = [
    "SC-INV-2025-0201",
    "TP-INV-2025-0415",
    "SG-INV-2025-0330",
    "MP-INV-2025-0298",
    "LT-INV-2025-0612",
]

DEMO_PO_NUMBERS = ["PO-DEMO-201", "PO-DEMO-203", "PO-DEMO-204", "PO-DEMO-205"]
DEMO_GRN_NUMBERS = ["GRN-DEMO-201", "GRN-DEMO-203", "GRN-DEMO-204", "GRN-DEMO-205"]

# Also clean old DEMO-SIM data from previous demo_simulation.py
OLD_DEMO_PREFIXES = ["DEMO-SIM-", "DEMO-PO-"]
OLD_DEMO_GRN_PREFIXES = ["DEMO-GRN-"]
OLD_DEMO_VENDOR_CODES = ["DEMO-V01", "DEMO-V02"]

# ── Invoice data definitions ──────────────────────────────────────────────

SCENARIOS = [
    # 1) Clean 3-way match — everything aligns perfectly
    {
        "filename": "INV-SC-2025-0201.pdf",
        "invoice_number": "SC-INV-2025-0201",
        "vendor_code": "SUP001",
        "po_number": "PO-DEMO-201",
        "invoice_date": date(2025, 3, 1),
        "due_date": date(2025, 4, 1),
        "lines": [
            {"desc": "Hot-Rolled Steel Sheet 4x8ft 11 Gauge", "qty": 150, "price": 142.50},
            {"desc": "Cold-Rolled Steel Coil 48in Wide", "qty": 80, "price": 195.00},
        ],
        "tax_rate": 0.0825,
        "freight": 450.00,
        "notes": "PO Reference: PO-DEMO-201\nShipment received in full — GRN-DEMO-201",
        "po_lines": [
            {"line": 1, "desc": "Hot-Rolled Steel Sheet 4x8ft 11 Gauge", "qty": 150, "price": 142.50},
            {"line": 2, "desc": "Cold-Rolled Steel Coil 48in Wide", "qty": 80, "price": 195.00},
        ],
        "grn_qty": [150, 80],
    },
    # 2) Missing PO — vendor known, no PO in system
    {
        "filename": "INV-TP-2025-0415.pdf",
        "invoice_number": "TP-INV-2025-0415",
        "vendor_code": "SUP002",
        "po_number": None,
        "invoice_date": date(2025, 2, 28),
        "due_date": date(2025, 3, 30),
        "lines": [
            {"desc": "PCB Circuit Board Assembly Rev.C", "qty": 200, "price": 45.75},
            {"desc": "SMD Capacitor Kit 0402 (1000pc)", "qty": 50, "price": 28.00},
            {"desc": "IC Chip AT328P-AU (reel/500)", "qty": 10, "price": 185.00},
        ],
        "tax_rate": 0.0725,
        "freight": 125.00,
        "notes": "Urgent order — please process ASAP\nNo PO was issued prior to shipment",
        "po_lines": None,
        "grn_qty": None,
    },
    # 3) Data mismatch — line totals intentionally wrong (needs calculation)
    {
        "filename": "INV-SG-2025-0330.pdf",
        "invoice_number": "SG-INV-2025-0330",
        "vendor_code": "SUP004",
        "po_number": "PO-DEMO-203",
        "invoice_date": date(2025, 3, 3),
        "due_date": date(2025, 4, 3),
        "lines": [
            {"desc": "Safety Helmet Class E (White)", "qty": 200, "price": 45.00, "force_total": 8800.00},
            {"desc": "Hi-Vis Safety Vest ANSI Class 3", "qty": 300, "price": 18.50, "force_total": 5550.00},
            {"desc": "Steel-Toe Boot Size Assorted", "qty": 50, "price": 89.00, "force_total": 4450.00},
        ],
        "tax_rate": 0.0825,
        "freight": 275.00,
        "force_subtotal": 18800.00,
        "force_total": 20592.00,
        "notes": "PO Reference: PO-DEMO-203\nPlease verify line item totals",
        "po_lines": [
            {"line": 1, "desc": "Safety Helmet Class E (White)", "qty": 200, "price": 45.00},
            {"line": 2, "desc": "Hi-Vis Safety Vest ANSI Class 3", "qty": 300, "price": 18.50},
            {"line": 3, "desc": "Steel-Toe Boot Size Assorted", "qty": 50, "price": 89.00},
        ],
        "grn_qty": [200, 300, 50],
    },
    # 4) Amount variance — 10% price overcharge on drill bits
    {
        "filename": "INV-MP-2025-0298.pdf",
        "invoice_number": "MP-INV-2025-0298",
        "vendor_code": "SUP005",
        "po_number": "PO-DEMO-204",
        "invoice_date": date(2025, 2, 25),
        "due_date": date(2025, 3, 25),
        "lines": [
            {"desc": "Precision Drill Bit Set HSS 1-13mm", "qty": 75, "price": 352.00},
            {"desc": "Carbide End Mill 4-Flute 8mm", "qty": 40, "price": 89.50},
        ],
        "tax_rate": 0.06,
        "freight": 180.00,
        "notes": "PO Reference: PO-DEMO-204\nPrice adjustment per vendor quote QT-2025-118",
        "po_lines": [
            {"line": 1, "desc": "Precision Drill Bit Set HSS 1-13mm", "qty": 75, "price": 320.00},
            {"line": 2, "desc": "Carbide End Mill 4-Flute 8mm", "qty": 40, "price": 89.50},
        ],
        "grn_qty": [75, 40],
    },
    # 5) Quantity overrun — invoiced 580 but PO/GRN = 500
    {
        "filename": "INV-LT-2025-0612.pdf",
        "invoice_number": "LT-INV-2025-0612",
        "vendor_code": "SUP003",
        "po_number": "PO-DEMO-205",
        "invoice_date": date(2025, 3, 2),
        "due_date": date(2025, 4, 2),
        "lines": [
            {"desc": "Corrugated Shipping Box 24x18x12", "qty": 580, "price": 4.75},
            {"desc": "Packing Foam Insert Custom-Cut", "qty": 580, "price": 2.25},
        ],
        "tax_rate": 0.0,
        "freight": 350.00,
        "notes": "PO Reference: PO-DEMO-205\n80 additional units shipped per verbal approval",
        "po_lines": [
            {"line": 1, "desc": "Corrugated Shipping Box 24x18x12", "qty": 500, "price": 4.75},
            {"line": 2, "desc": "Packing Foam Insert Custom-Cut", "qty": 500, "price": 2.25},
        ],
        "grn_qty": [500, 500],
    },
]

# ══════════════════════════════════════════════════════════════════════════
# PDF Generation
# ══════════════════════════════════════════════════════════════════════════

styles = getSampleStyleSheet()
title_style = ParagraphStyle("InvTitle", parent=styles["Title"], fontSize=22, spaceAfter=4)
heading_style = ParagraphStyle("InvHeading", parent=styles["Heading2"], fontSize=11, spaceAfter=2)
normal_style = ParagraphStyle("InvNormal", parent=styles["Normal"], fontSize=9, leading=12)
small_style = ParagraphStyle("InvSmall", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.grey)


def _money(val: float) -> str:
    return f"${val:,.2f}"


def generate_invoice_pdf(scenario: dict, path: Path):
    """Generate a professional-looking invoice PDF."""
    doc = SimpleDocTemplate(str(path), pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)

    vendor = VENDORS[scenario["vendor_code"]]
    elements = []

    # ── Header
    header_data = [
        [Paragraph(f"<b>{vendor['name']}</b>", title_style),
         Paragraph("<b>INVOICE</b>", ParagraphStyle("Right", parent=title_style, alignment=2))],
        [Paragraph(vendor["addr"], small_style),
         Paragraph(f"Invoice #: <b>{scenario['invoice_number']}</b>", normal_style)],
        [Paragraph(f"Tax ID: {vendor['tax_id']}", small_style),
         Paragraph(f"Date: {scenario['invoice_date'].strftime('%B %d, %Y')}", normal_style)],
        ["", Paragraph(f"Due: {scenario['due_date'].strftime('%B %d, %Y')}", normal_style)],
    ]
    if scenario.get("po_number"):
        header_data.append(["", Paragraph(f"PO #: <b>{scenario['po_number']}</b>", normal_style)])

    header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))

    # ── Bill To
    elements.append(Paragraph("<b>Bill To:</b>", heading_style))
    elements.append(Paragraph("Apex Manufacturing Corp.", normal_style))
    elements.append(Paragraph("1000 Industrial Parkway, Suite 200", normal_style))
    elements.append(Paragraph("Chicago, IL 60607", normal_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.Color(0.8, 0.8, 0.8)))
    elements.append(Spacer(1, 8))

    # ── Line Items
    table_data = [["#", "Description", "Qty", "Unit Price", "Line Total"]]
    subtotal = 0
    for i, line in enumerate(scenario["lines"], 1):
        line_total = line.get("force_total", line["qty"] * line["price"])
        subtotal += line_total
        table_data.append([
            str(i), line["desc"], str(line["qty"]),
            _money(line["price"]), _money(line_total),
        ])

    if "force_subtotal" in scenario:
        subtotal = scenario["force_subtotal"]

    line_table = Table(table_data, colWidths=[0.4 * inch, 3.4 * inch, 0.7 * inch, 1 * inch, 1.2 * inch])
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.35)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ALIGN", (3, 0), (4, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 12))

    # ── Totals
    tax = subtotal * scenario["tax_rate"]
    freight = scenario.get("freight", 0)
    total = scenario.get("force_total", subtotal + tax + freight)

    totals_data = [["", "Subtotal:", _money(subtotal)]]
    if scenario["tax_rate"] > 0:
        totals_data.append(["", f"Tax ({scenario['tax_rate']*100:.2f}%):", _money(tax)])
    if freight > 0:
        totals_data.append(["", "Freight:", _money(freight)])
    totals_data.append(["", "TOTAL DUE:", _money(total)])

    totals_table = Table(totals_data, colWidths=[4.5 * inch, 1.2 * inch, 1.2 * inch])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (2, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (1, -1), (2, -1), "Helvetica-Bold"),
        ("LINEABOVE", (1, -1), (2, -1), 1.5, colors.Color(0.2, 0.2, 0.35)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 20))

    # ── Notes
    if scenario.get("notes"):
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(0.85, 0.85, 0.85)))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("<b>Notes:</b>", heading_style))
        for line in scenario["notes"].split("\n"):
            elements.append(Paragraph(line, small_style))
        elements.append(Spacer(1, 10))

    # ── Footer
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.Color(0.85, 0.85, 0.85)))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "Payment Terms: Net 30 | Bank: First National | Account: ****4821 | Routing: ****6712",
        ParagraphStyle("Footer", parent=small_style, alignment=1),
    ))
    elements.append(Paragraph(
        "Thank you for your business!",
        ParagraphStyle("Footer2", parent=small_style, alignment=1, textColor=colors.Color(0.4, 0.4, 0.4)),
    ))

    doc.build(elements)


# ══════════════════════════════════════════════════════════════════════════
# Database Cleanup — removes ALL demo/showcase data
# ══════════════════════════════════════════════════════════════════════════

def cleanup_all_demo_data(db):
    """Remove ALL demo and showcase data from the database.

    Deletes in correct FK order:
      AuditLog → AutomationAction → ResolutionPlan → Exception
      → ApprovalTask → MatchResult → Invoice (cascades InvoiceLineItems)
      → GRNLineItem → GoodsReceipt → POLineItem → PurchaseOrder
      → Demo Vendors
    """
    counts = {}

    # ── 1. Find demo invoice IDs ──────────────────────────────────────
    demo_invoices = db.query(Invoice).filter(
        Invoice.invoice_number.in_(DEMO_INVOICE_NUMBERS) |
        Invoice.invoice_number.like("DEMO-SIM-%") |
        Invoice.invoice_number.like("DRAFT-%")  # leftover drafts from uploads
    ).all()
    demo_inv_ids = [inv.id for inv in demo_invoices]

    # Also find any invoices uploaded from our demo PDFs (matched by DRAFT- prefix that got extracted)
    # These would have been uploaded and renamed during OCR extraction
    for inv_num in DEMO_INVOICE_NUMBERS:
        found = db.query(Invoice).filter(Invoice.invoice_number == inv_num).all()
        for f in found:
            if f.id not in demo_inv_ids:
                demo_inv_ids.append(f.id)
                demo_invoices.append(f)

    if demo_inv_ids:
        # ── 2. Delete exceptions and their children ───────────────────
        demo_exceptions = db.query(Exception_).filter(
            Exception_.invoice_id.in_(demo_inv_ids)
        ).all()
        demo_exc_ids = [exc.id for exc in demo_exceptions]

        if demo_exc_ids:
            # Delete automation actions (via resolution plans)
            demo_plans = db.query(ResolutionPlan).filter(
                ResolutionPlan.exception_id.in_(demo_exc_ids)
            ).all()
            demo_plan_ids = [p.id for p in demo_plans]

            if demo_plan_ids:
                n = db.query(AutomationAction).filter(
                    AutomationAction.plan_id.in_(demo_plan_ids)
                ).delete(synchronize_session=False)
                counts["automation_actions"] = n

                n = db.query(ResolutionPlan).filter(
                    ResolutionPlan.id.in_(demo_plan_ids)
                ).delete(synchronize_session=False)
                counts["resolution_plans"] = n

            # Delete audit logs for these exceptions
            for exc_id in demo_exc_ids:
                db.query(AuditLog).filter(
                    AuditLog.entity_id == exc_id
                ).delete(synchronize_session=False)

            n = db.query(Exception_).filter(
                Exception_.id.in_(demo_exc_ids)
            ).delete(synchronize_session=False)
            counts["exceptions"] = n

        # ── 3. Delete match results ───────────────────────────────────
        n = db.query(MatchResult).filter(
            MatchResult.invoice_id.in_(demo_inv_ids)
        ).delete(synchronize_session=False)
        counts["match_results"] = n

        # ── 4. Delete approval tasks ──────────────────────────────────
        n = db.query(ApprovalTask).filter(
            ApprovalTask.invoice_id.in_(demo_inv_ids)
        ).delete(synchronize_session=False)
        counts["approval_tasks"] = n

        # ── 5. Delete audit logs for invoices ─────────────────────────
        for inv_id in demo_inv_ids:
            db.query(AuditLog).filter(
                AuditLog.entity_id == inv_id
            ).delete(synchronize_session=False)

        # ── 6. Delete invoices (cascades InvoiceLineItems) ────────────
        n = db.query(Invoice).filter(
            Invoice.id.in_(demo_inv_ids)
        ).delete(synchronize_session=False)
        counts["invoices"] = n

    # ── 7. Delete demo POs and related GRN/line data ──────────────────
    all_demo_po_numbers = DEMO_PO_NUMBERS.copy()
    # Also find old DEMO-PO-* from demo_simulation.py
    old_pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.like("DEMO-PO-%")
    ).all()
    for op in old_pos:
        if op.po_number not in all_demo_po_numbers:
            all_demo_po_numbers.append(op.po_number)

    demo_pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.po_number.in_(all_demo_po_numbers)
    ).all()
    demo_po_ids = [po.id for po in demo_pos]

    if demo_po_ids:
        # Get PO line IDs for GRN cleanup
        demo_po_line_ids = [
            pl.id for po_id in demo_po_ids
            for pl in db.query(POLineItem).filter(POLineItem.po_id == po_id).all()
        ]

        if demo_po_line_ids:
            n = db.query(GRNLineItem).filter(
                GRNLineItem.po_line_id.in_(demo_po_line_ids)
            ).delete(synchronize_session=False)
            counts["grn_line_items"] = n

        # Delete GRNs
        n = db.query(GoodsReceipt).filter(
            GoodsReceipt.po_id.in_(demo_po_ids)
        ).delete(synchronize_session=False)
        counts["goods_receipts"] = n

        # Delete PO line items
        n = db.query(POLineItem).filter(
            POLineItem.po_id.in_(demo_po_ids)
        ).delete(synchronize_session=False)
        counts["po_line_items"] = n

        # Delete POs
        n = db.query(PurchaseOrder).filter(
            PurchaseOrder.id.in_(demo_po_ids)
        ).delete(synchronize_session=False)
        counts["purchase_orders"] = n

    # ── 8. Delete old demo vendors ────────────────────────────────────
    n = db.query(Vendor).filter(
        Vendor.vendor_code.in_(OLD_DEMO_VENDOR_CODES)
    ).delete(synchronize_session=False)
    if n:
        counts["vendors"] = n

    db.commit()

    # Report
    total = sum(counts.values())
    if total:
        print(f"  Cleaned up {total} records:")
        for entity, count in counts.items():
            if count:
                print(f"    {entity}: {count}")
    else:
        print("  No demo data found — database is clean")


# ══════════════════════════════════════════════════════════════════════════
# Database Seeding
# ══════════════════════════════════════════════════════════════════════════

def seed_po_and_grn(db, scenario: dict):
    """Create PO + GRN records for a scenario."""
    if not scenario.get("po_lines"):
        print("  (no PO — Missing PO scenario)")
        return

    po_number = scenario["po_number"]
    vendor = db.query(Vendor).filter(Vendor.vendor_code == scenario["vendor_code"]).first()
    if not vendor:
        print(f"  WARNING: Vendor {scenario['vendor_code']} not found — skipping")
        return

    # Create PO
    po_total = sum(Decimal(str(l["qty"])) * Decimal(str(l["price"])) for l in scenario["po_lines"])
    po = PurchaseOrder(
        id=uuid.uuid4(),
        po_number=po_number,
        vendor_id=vendor.id,
        order_date=scenario["invoice_date"] - timedelta(days=30),
        delivery_date=scenario["invoice_date"] - timedelta(days=5),
        currency="USD",
        total_amount=po_total,
        status=POStatus.fully_received,
    )
    db.add(po)
    db.flush()
    print(f"  Created PO {po_number} (${po_total:,.2f})")

    # Create PO Line Items
    po_line_ids = []
    for pl in scenario["po_lines"]:
        po_line = POLineItem(
            id=uuid.uuid4(),
            po_id=po.id,
            line_number=pl["line"],
            description=pl["desc"],
            quantity_ordered=Decimal(str(pl["qty"])),
            unit_price=Decimal(str(pl["price"])),
            line_total=Decimal(str(pl["qty"])) * Decimal(str(pl["price"])),
            quantity_received=Decimal(str(scenario["grn_qty"][pl["line"] - 1])) if scenario.get("grn_qty") else Decimal("0"),
            quantity_invoiced=Decimal("0"),
        )
        db.add(po_line)
        db.flush()
        po_line_ids.append(po_line.id)

    # Create GRN
    if scenario.get("grn_qty"):
        grn_number = po_number.replace("PO-DEMO", "GRN-DEMO")
        grn = GoodsReceipt(
            id=uuid.uuid4(),
            grn_number=grn_number,
            po_id=po.id,
            vendor_id=vendor.id,
            receipt_date=scenario["invoice_date"] - timedelta(days=3),
            warehouse="WH-CHI-01",
        )
        db.add(grn)
        db.flush()

        for i, qty in enumerate(scenario["grn_qty"]):
            grn_line = GRNLineItem(
                id=uuid.uuid4(),
                grn_id=grn.id,
                po_line_id=po_line_ids[i],
                quantity_received=Decimal(str(qty)),
                condition_notes="Received in good condition",
            )
            db.add(grn_line)

        print(f"  Created GRN {grn_number} (received: {scenario['grn_qty']})")

    db.commit()


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Demo Invoice Generator")
    parser.add_argument("--clean", action="store_true", help="Only clean demo data (no PDF generation)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  AP Ops Manager — Demo Invoice Generator")
    print(f"{'='*60}\n")

    # ── Step 1: Clean all previous demo data ──────────────────────────
    print("[CLEAN] Removing all demo/showcase data...")
    db = SessionLocal()
    try:
        cleanup_all_demo_data(db)
    finally:
        db.close()

    # Also remove demo PDF folder
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        print(f"  Removed {OUTPUT_DIR}")

    if args.clean:
        print(f"\n{'='*60}")
        print(f"  Clean complete — database and desktop are clean")
        print(f"{'='*60}\n")
        return

    # ── Step 2: Generate PDFs ─────────────────────────────────────────
    print(f"\n[PDF] Generating invoice PDFs → {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for sc in SCENARIOS:
        path = OUTPUT_DIR / sc["filename"]
        generate_invoice_pdf(sc, path)
        print(f"  {sc['filename']}")

    # ── Step 3: Seed PO/GRN data ──────────────────────────────────────
    print(f"\n[DB] Seeding PO and GRN records...")
    db = SessionLocal()
    try:
        for sc in SCENARIOS:
            print(f"\n  Scenario: {sc['invoice_number']}")
            seed_po_and_grn(db, sc)
        db.commit()
    finally:
        db.close()

    # ── Summary ───────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Ready! 5 invoices at ~/Desktop/Demo_Invoices/")
    print(f"")
    print(f"  1. INV-SC-2025-0201.pdf  → Clean match (auto-approve)")
    print(f"  2. INV-TP-2025-0415.pdf  → Missing PO (AI drafts email)")
    print(f"  3. INV-SG-2025-0330.pdf  → Data mismatch (needs calc)")
    print(f"  4. INV-MP-2025-0298.pdf  → Amount variance (10% over)")
    print(f"  5. INV-LT-2025-0612.pdf  → Qty overrun (580 vs 500)")
    print(f"")
    print(f"  To clean up after showcase:")
    print(f"    python generate_demo_invoices.py --clean")
    print(f"")
    print(f"  To reset and regenerate:")
    print(f"    python generate_demo_invoices.py")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
