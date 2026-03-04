"""Demo Simulation Script — creates clean test data and runs the full pipeline.

Usage: cd backend && python demo_simulation.py

Creates 3 scenarios to demonstrate the full V2 flow:
  1. Amount Variance — invoice total differs from PO (triggers AI resolution plan)
  2. Quantity Variance — invoice qty exceeds PO ordered qty
  3. Missing PO — invoice from known vendor but no matching PO
"""

from __future__ import annotations

import sys
import os
import uuid
from datetime import date, timedelta
from decimal import Decimal

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.invoice import (
    DocumentType,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    SourceChannel,
)
from app.models.purchase_order import POLineItem, POStatus, PurchaseOrder
from app.models.goods_receipt import GoodsReceipt, GRNLineItem
from app.models.vendor import Vendor, VendorRiskLevel, VendorStatus
from app.models.config import ToleranceConfig


def clean_demo_data(db):
    """Remove previous demo simulation data (identified by 'DEMO-SIM' prefix)."""
    from app.models.exception import Exception_
    from app.models.resolution import ResolutionPlan, AutomationAction
    from app.models.matching import MatchResult
    from app.models.approval import ApprovalTask
    from app.models.audit import AuditLog

    # Step 1: Unlink invoice line items from PO lines (prevents FK violation)
    demo_invoices = db.query(Invoice).filter(Invoice.invoice_number.like("DEMO-SIM-%")).all()
    for inv in demo_invoices:
        for li in inv.line_items:
            li.po_line_id = None
    db.flush()

    # Step 2: Delete exceptions, plans, actions, audit logs
    for inv in demo_invoices:
        exceptions = db.query(Exception_).filter(Exception_.invoice_id == inv.id).all()
        for exc in exceptions:
            plans = db.query(ResolutionPlan).filter(ResolutionPlan.exception_id == exc.id).all()
            for plan in plans:
                # Delete audit logs for actions
                for action in plan.actions:
                    db.query(AuditLog).filter(
                        AuditLog.entity_type == "automation_action",
                        AuditLog.entity_id == action.id,
                    ).delete()
                db.query(AutomationAction).filter(AutomationAction.plan_id == plan.id).delete()
                # Delete audit logs for plan
                db.query(AuditLog).filter(
                    AuditLog.entity_type == "resolution_plan",
                    AuditLog.entity_id == plan.id,
                ).delete()
                db.delete(plan)
            # Delete audit logs for exception
            db.query(AuditLog).filter(
                AuditLog.entity_type == "exception",
                AuditLog.entity_id == exc.id,
            ).delete()
            db.delete(exc)

        db.query(MatchResult).filter(MatchResult.invoice_id == inv.id).delete()
        db.query(ApprovalTask).filter(ApprovalTask.invoice_id == inv.id).delete()
        db.delete(inv)

    # Step 3: Delete demo POs (safe now — invoice line items already unlinked)
    demo_pos = db.query(PurchaseOrder).filter(PurchaseOrder.po_number.like("DEMO-PO-%")).all()
    for po in demo_pos:
        grns = db.query(GoodsReceipt).filter(GoodsReceipt.po_id == po.id).all()
        for grn in grns:
            db.query(GRNLineItem).filter(GRNLineItem.grn_id == grn.id).delete()
            db.delete(grn)
        db.query(POLineItem).filter(POLineItem.po_id == po.id).delete()
        db.delete(po)

    # Also delete demo vendors (only DEMO-V02, keep DEMO-V01 for reuse)
    db.query(Vendor).filter(Vendor.vendor_code == "DEMO-V02").delete()

    db.commit()
    print("[CLEAN] Removed previous demo simulation data")


def ensure_tolerance(db):
    """Ensure a global tolerance config exists."""
    existing = (
        db.query(ToleranceConfig)
        .filter(ToleranceConfig.is_active == True, ToleranceConfig.scope == "global")
        .first()
    )
    if existing:
        print(f"[SETUP] Global tolerance exists: amount={existing.amount_tolerance_pct}%, qty={existing.quantity_tolerance_pct}%")
        return existing

    tol = ToleranceConfig(
        scope="global",
        scope_value="*",
        amount_tolerance_pct=5.0,
        amount_tolerance_abs=100.0,
        quantity_tolerance_pct=2.0,
        is_active=True,
    )
    db.add(tol)
    db.commit()
    print("[SETUP] Created global tolerance: amount=5%, qty=2%")
    return tol


def create_demo_vendor(db) -> Vendor:
    """Create or reuse a demo vendor."""
    existing = db.query(Vendor).filter(Vendor.vendor_code == "DEMO-V01").first()
    if existing:
        return existing

    vendor = Vendor(
        vendor_code="DEMO-V01",
        name="Delta Industrial Supply",
        tax_id="92-1234567",
        address="123 Industrial Pkwy",
        city="Houston",
        state="TX",
        country="US",
        payment_terms_code="Net30",
        status=VendorStatus.active,
        risk_level=VendorRiskLevel.medium,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    print(f"[VENDOR] Created: {vendor.name} ({vendor.vendor_code}) - ID: {vendor.id}")
    return vendor


def create_scenario_1(db, vendor: Vendor):
    """Scenario 1: Amount Variance.

    PO: 100 x Hydraulic Cylinders @ $250 each = $25,000
    Invoice: 100 x Hydraulic Cylinders @ $265 each = $26,500 (6% over — outside 5% tolerance)
    Expected: amount_variance exception → AI plan with diagnosis
    """
    print("\n--- Scenario 1: Amount Variance (6% price overcharge) ---")

    # Create PO
    po = PurchaseOrder(
        po_number="DEMO-PO-001",
        vendor_id=vendor.id,
        order_date=date.today() - timedelta(days=30),
        delivery_date=date.today() - timedelta(days=5),
        currency="USD",
        total_amount=Decimal("25000.00"),
        status=POStatus.fully_received,
    )
    db.add(po)
    db.flush()

    po_line = POLineItem(
        po_id=po.id,
        line_number=1,
        description="Hydraulic Cylinder HC-500",
        quantity_ordered=Decimal("100"),
        unit_price=Decimal("250.00"),
        line_total=Decimal("25000.00"),
        quantity_received=Decimal("100"),
        quantity_invoiced=Decimal("0"),
    )
    db.add(po_line)
    db.flush()

    # Create GRN (fully received)
    grn = GoodsReceipt(
        grn_number="DEMO-GRN-001",
        po_id=po.id,
        vendor_id=vendor.id,
        receipt_date=date.today() - timedelta(days=5),
        warehouse="Warehouse A",
    )
    db.add(grn)
    db.flush()

    grn_line = GRNLineItem(
        grn_id=grn.id,
        po_line_id=po_line.id,
        quantity_received=Decimal("100"),
        condition_notes="All items in good condition",
    )
    db.add(grn_line)
    db.flush()

    # Create Invoice with 6% price overcharge
    invoice = Invoice(
        invoice_number="DEMO-SIM-001",
        vendor_id=vendor.id,
        invoice_date=date.today() - timedelta(days=2),
        due_date=date.today() + timedelta(days=28),
        received_date=date.today() - timedelta(days=2),
        currency="USD",
        total_amount=Decimal("26500.00"),
        tax_amount=Decimal("0.00"),
        status=InvoiceStatus.extracted,
        document_type=DocumentType.invoice,
        source_channel=SourceChannel.manual,
        ocr_confidence_score=0.95,
    )
    db.add(invoice)
    db.flush()

    inv_line = InvoiceLineItem(
        invoice_id=invoice.id,
        line_number=1,
        description="Hydraulic Cylinder HC-500",
        quantity=Decimal("100"),
        unit_price=Decimal("265.00"),
        line_total=Decimal("26500.00"),
        po_line_id=po_line.id,  # pre-link to PO line
    )
    db.add(inv_line)
    db.commit()

    print(f"  PO: {po.po_number} — 100 x $250 = $25,000")
    print(f"  INV: {invoice.invoice_number} — 100 x $265 = $26,500 (+6%)")
    print(f"  Invoice ID: {invoice.id}")
    return invoice


def create_scenario_2(db, vendor: Vendor):
    """Scenario 2: Quantity Variance.

    PO: 200 x Steel Bearings @ $45 each = $9,000
    GRN: Received 200
    Invoice: 230 x Steel Bearings @ $45 each = $10,350 (15% over-qty — outside 2% tolerance)
    Expected: quantity_variance exception → AI plan with diagnosis
    """
    print("\n--- Scenario 2: Quantity Variance (15% over-delivery invoiced) ---")

    po = PurchaseOrder(
        po_number="DEMO-PO-002",
        vendor_id=vendor.id,
        order_date=date.today() - timedelta(days=45),
        delivery_date=date.today() - timedelta(days=10),
        currency="USD",
        total_amount=Decimal("9000.00"),
        status=POStatus.fully_received,
    )
    db.add(po)
    db.flush()

    po_line = POLineItem(
        po_id=po.id,
        line_number=1,
        description="Steel Bearing SB-200",
        quantity_ordered=Decimal("200"),
        unit_price=Decimal("45.00"),
        line_total=Decimal("9000.00"),
        quantity_received=Decimal("200"),
        quantity_invoiced=Decimal("0"),
    )
    db.add(po_line)
    db.flush()

    # GRN: received 200 (matches PO)
    grn = GoodsReceipt(
        grn_number="DEMO-GRN-002",
        po_id=po.id,
        vendor_id=vendor.id,
        receipt_date=date.today() - timedelta(days=10),
        warehouse="Warehouse B",
    )
    db.add(grn)
    db.flush()

    grn_line = GRNLineItem(
        grn_id=grn.id,
        po_line_id=po_line.id,
        quantity_received=Decimal("200"),
        condition_notes="Received per spec",
    )
    db.add(grn_line)
    db.flush()

    # Invoice: 230 qty (15% over what was ordered and received)
    invoice = Invoice(
        invoice_number="DEMO-SIM-002",
        vendor_id=vendor.id,
        invoice_date=date.today() - timedelta(days=1),
        due_date=date.today() + timedelta(days=44),
        received_date=date.today() - timedelta(days=1),
        currency="USD",
        total_amount=Decimal("10350.00"),
        tax_amount=Decimal("0.00"),
        status=InvoiceStatus.extracted,
        document_type=DocumentType.invoice,
        source_channel=SourceChannel.email,
        ocr_confidence_score=0.92,
    )
    db.add(invoice)
    db.flush()

    inv_line = InvoiceLineItem(
        invoice_id=invoice.id,
        line_number=1,
        description="Steel Bearing SB-200",
        quantity=Decimal("230"),
        unit_price=Decimal("45.00"),
        line_total=Decimal("10350.00"),
        po_line_id=po_line.id,
    )
    db.add(inv_line)
    db.commit()

    print(f"  PO: {po.po_number} — 200 x $45 = $9,000")
    print(f"  GRN: 200 received")
    print(f"  INV: {invoice.invoice_number} — 230 x $45 = $10,350 (+15% qty)")
    print(f"  Invoice ID: {invoice.id}")
    return invoice


def create_scenario_3(db, vendor: Vendor):
    """Scenario 3: Missing PO.

    Invoice from known vendor with no matching PO number.
    Expected: missing_po exception → AI plan to search PO candidates + draft vendor email
    """
    print("\n--- Scenario 3: Missing PO (no matching PO for vendor) ---")

    # Use a different vendor that has NO POs
    other_vendor = db.query(Vendor).filter(
        Vendor.vendor_code != "DEMO-V01",
        Vendor.status == VendorStatus.active,
    ).first()

    if not other_vendor:
        # Create a standalone vendor
        other_vendor = Vendor(
            vendor_code="DEMO-V02",
            name="Apex Chemical Corp",
            city="Newark",
            state="NJ",
            country="US",
            status=VendorStatus.active,
            risk_level=VendorRiskLevel.low,
        )
        db.add(other_vendor)
        db.commit()
        db.refresh(other_vendor)

    # Check if this vendor has any POs — if so, find one without
    has_pos = db.query(PurchaseOrder).filter(PurchaseOrder.vendor_id == other_vendor.id).count()
    if has_pos > 0:
        # Use the demo vendor but make an invoice that won't match any PO
        # (We'll just not link any PO lines)
        pass

    invoice = Invoice(
        invoice_number="DEMO-SIM-003",
        vendor_id=other_vendor.id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        received_date=date.today(),
        currency="USD",
        total_amount=Decimal("15750.00"),
        tax_amount=Decimal("1260.00"),
        status=InvoiceStatus.extracted,
        document_type=DocumentType.invoice,
        source_channel=SourceChannel.email,
        ocr_confidence_score=0.88,
    )
    db.add(invoice)
    db.flush()

    # Line items without PO links
    lines = [
        InvoiceLineItem(
            invoice_id=invoice.id,
            line_number=1,
            description="Industrial Solvent XR-100 (50L drum)",
            quantity=Decimal("10"),
            unit_price=Decimal("875.00"),
            line_total=Decimal("8750.00"),
        ),
        InvoiceLineItem(
            invoice_id=invoice.id,
            line_number=2,
            description="Cleaning Agent CA-50 (25L container)",
            quantity=Decimal("20"),
            unit_price=Decimal("350.00"),
            line_total=Decimal("7000.00"),
        ),
    ]
    db.add_all(lines)
    db.commit()

    vendor_name = other_vendor.name
    print(f"  Vendor: {vendor_name} (no POs in system)")
    print(f"  INV: {invoice.invoice_number} — $15,750 + $1,260 tax = $17,010")
    print(f"  Invoice ID: {invoice.id}")
    return invoice


def create_scenario_4(db, vendor: Vendor):
    """Scenario 4: Duplicate Invoice.

    Two invoices with the same invoice number from the same vendor.
    Expected: duplicate_invoice exception → AI plan to find duplicates + lock payment
    """
    print("\n--- Scenario 4: Duplicate Invoice (same number, same vendor) ---")

    # Create a PO for context
    po = PurchaseOrder(
        po_number="DEMO-PO-004",
        vendor_id=vendor.id,
        order_date=date.today() - timedelta(days=20),
        delivery_date=date.today() - timedelta(days=3),
        currency="USD",
        total_amount=Decimal("4500.00"),
        status=POStatus.fully_received,
    )
    db.add(po)
    db.flush()

    po_line = POLineItem(
        po_id=po.id,
        line_number=1,
        description="Precision Gauge PG-100",
        quantity_ordered=Decimal("50"),
        unit_price=Decimal("90.00"),
        line_total=Decimal("4500.00"),
        quantity_received=Decimal("50"),
        quantity_invoiced=Decimal("50"),  # already invoiced once
    )
    db.add(po_line)
    db.flush()

    # GRN
    grn = GoodsReceipt(
        grn_number="DEMO-GRN-004",
        po_id=po.id,
        vendor_id=vendor.id,
        receipt_date=date.today() - timedelta(days=3),
        warehouse="Warehouse A",
    )
    db.add(grn)
    db.flush()
    db.add(GRNLineItem(
        grn_id=grn.id,
        po_line_id=po_line.id,
        quantity_received=Decimal("50"),
    ))
    db.flush()

    # First invoice (already paid/approved — simulated by creating it in approved status)
    inv_original = Invoice(
        invoice_number="DEMO-SIM-004",
        vendor_id=vendor.id,
        invoice_date=date.today() - timedelta(days=10),
        due_date=date.today() + timedelta(days=20),
        received_date=date.today() - timedelta(days=10),
        currency="USD",
        total_amount=Decimal("4500.00"),
        tax_amount=Decimal("0.00"),
        status=InvoiceStatus.approved,
        document_type=DocumentType.invoice,
        source_channel=SourceChannel.email,
        ocr_confidence_score=0.97,
    )
    db.add(inv_original)
    db.flush()
    db.add(InvoiceLineItem(
        invoice_id=inv_original.id,
        line_number=1,
        description="Precision Gauge PG-100",
        quantity=Decimal("50"),
        unit_price=Decimal("90.00"),
        line_total=Decimal("4500.00"),
        po_line_id=po_line.id,
    ))
    db.flush()

    # Duplicate invoice (same number, arrives again)
    inv_duplicate = Invoice(
        invoice_number="DEMO-SIM-004",  # same number!
        vendor_id=vendor.id,
        invoice_date=date.today() - timedelta(days=1),
        due_date=date.today() + timedelta(days=29),
        received_date=date.today() - timedelta(days=1),
        currency="USD",
        total_amount=Decimal("4500.00"),
        tax_amount=Decimal("0.00"),
        status=InvoiceStatus.extracted,
        document_type=DocumentType.invoice,
        source_channel=SourceChannel.manual,
        ocr_confidence_score=0.94,
    )
    db.add(inv_duplicate)
    db.flush()
    db.add(InvoiceLineItem(
        invoice_id=inv_duplicate.id,
        line_number=1,
        description="Precision Gauge PG-100",
        quantity=Decimal("50"),
        unit_price=Decimal("90.00"),
        line_total=Decimal("4500.00"),
        po_line_id=po_line.id,
    ))
    db.commit()

    print(f"  Original INV: {inv_original.invoice_number} — $4,500 (approved)")
    print(f"  Duplicate INV: {inv_duplicate.invoice_number} — $4,500 (extracted)")
    print(f"  Invoice ID (dup): {inv_duplicate.id}")
    return inv_duplicate


def create_scenario_5(db, vendor: Vendor):
    """Scenario 5: Tax Variance.

    PO: 75 x Pump Assembly @ $320 = $24,000 (no tax on PO)
    Invoice: 75 x Pump Assembly @ $320 = $24,000 + $2,400 tax = $26,400
    But computed tax (8.25%) should be $1,980 — vendor overcharged $420 in tax
    Expected: tax_variance exception → AI plan with tax recalc + explanation
    """
    print("\n--- Scenario 5: Tax Variance (vendor overcharged tax) ---")

    po = PurchaseOrder(
        po_number="DEMO-PO-005",
        vendor_id=vendor.id,
        order_date=date.today() - timedelta(days=15),
        delivery_date=date.today() - timedelta(days=2),
        currency="USD",
        total_amount=Decimal("24000.00"),
        status=POStatus.fully_received,
    )
    db.add(po)
    db.flush()

    po_line = POLineItem(
        po_id=po.id,
        line_number=1,
        description="Pump Assembly PA-750",
        quantity_ordered=Decimal("75"),
        unit_price=Decimal("320.00"),
        line_total=Decimal("24000.00"),
        quantity_received=Decimal("75"),
        quantity_invoiced=Decimal("0"),
    )
    db.add(po_line)
    db.flush()

    # GRN
    grn = GoodsReceipt(
        grn_number="DEMO-GRN-005",
        po_id=po.id,
        vendor_id=vendor.id,
        receipt_date=date.today() - timedelta(days=2),
        warehouse="Warehouse A",
    )
    db.add(grn)
    db.flush()
    db.add(GRNLineItem(
        grn_id=grn.id,
        po_line_id=po_line.id,
        quantity_received=Decimal("75"),
    ))
    db.flush()

    # Invoice with overcharged tax
    invoice = Invoice(
        invoice_number="DEMO-SIM-005",
        vendor_id=vendor.id,
        invoice_date=date.today() - timedelta(days=1),
        due_date=date.today() + timedelta(days=29),
        received_date=date.today() - timedelta(days=1),
        currency="USD",
        total_amount=Decimal("26400.00"),  # $24,000 + $2,400 tax
        tax_amount=Decimal("2400.00"),     # should be $1,980 (8.25%)
        status=InvoiceStatus.extracted,
        document_type=DocumentType.invoice,
        source_channel=SourceChannel.email,
        ocr_confidence_score=0.91,
    )
    db.add(invoice)
    db.flush()

    inv_line = InvoiceLineItem(
        invoice_id=invoice.id,
        line_number=1,
        description="Pump Assembly PA-750",
        quantity=Decimal("75"),
        unit_price=Decimal("320.00"),
        line_total=Decimal("24000.00"),
        po_line_id=po_line.id,
    )
    db.add(inv_line)
    db.commit()

    print(f"  PO: {po.po_number} — 75 x $320 = $24,000 (no tax)")
    print(f"  INV: {invoice.invoice_number} — $24,000 + $2,400 tax = $26,400")
    print(f"  Expected tax (8.25%): $1,980 — Overcharged: $420")
    print(f"  Invoice ID: {invoice.id}")
    return invoice


def run_matching(db, invoice: Invoice):
    """Run the matching pipeline on an invoice."""
    from app.services.match_service import auto_link_po_lines, run_two_way_match, run_three_way_match
    from app.models.goods_receipt import GRNLineItem
    from sqlalchemy import func

    print(f"\n  [MATCH] Running pipeline for {invoice.invoice_number}...")

    # Step 1: Auto-link PO lines
    link_result = auto_link_po_lines(db, invoice.id)
    print(f"    Auto-link: {link_result}")

    # Refresh
    db.refresh(invoice)
    for li in invoice.line_items:
        db.refresh(li)

    # Step 2: Determine match type
    po_line_ids = [li.po_line_id for li in invoice.line_items if li.po_line_id]
    use_three_way = False
    if po_line_ids:
        grn_count = (
            db.query(func.count(GRNLineItem.id))
            .filter(GRNLineItem.po_line_id.in_(po_line_ids))
            .scalar()
        ) or 0
        use_three_way = grn_count > 0

    # Step 3: Run match
    if use_three_way:
        print(f"    Running 3-way match...")
        result = run_three_way_match(db, invoice.id)
    else:
        print(f"    Running 2-way match...")
        result = run_two_way_match(db, invoice.id)

    print(f"    Match result: {result.match_status.value} (score: {result.overall_score}%)")

    # Step 4: Check if exceptions were created
    from app.models.exception import Exception_
    exceptions = db.query(Exception_).filter(Exception_.invoice_id == invoice.id).all()
    if exceptions:
        for exc in exceptions:
            print(f"    Exception: {exc.exception_type.value} ({exc.severity.value}) — ID: {exc.id}")
    else:
        print(f"    No exceptions (clean match!)")

    return result, exceptions


def generate_ai_plans(db, exceptions):
    """Generate AI resolution plans, auto-approve, and auto-execute until human-approval step."""
    from app.services.ai_exception_resolver import generate_resolution_plan
    from app.services.ai_service import ai_service
    from app.services import resolution_orchestrator
    from app.models.resolution import PlanStatus

    if not ai_service.available:
        print("\n  [AI] WARNING: AI service not available (no API key). Skipping plan generation.")
        return []

    plans = []
    for exc in exceptions:
        try:
            print(f"\n  [AI] Generating resolution plan for {exc.exception_type.value} (exc: {exc.id})...")
            plan = generate_resolution_plan(db, exc.id)
            print(f"    Plan created: {plan.id}")
            print(f"    Diagnosis: {plan.diagnosis}")
            print(f"    Automation: {plan.automation_level.value} | Confidence: {plan.confidence}")
            print(f"    Steps: {len(plan.actions)}")
            for action in plan.actions:
                approval = " [REQUIRES APPROVAL]" if action.requires_human_approval else ""
                print(f"      {action.step_id}: {action.action_type} ({action.risk or 'n/a'}){approval}")

            # Auto-approve and execute (matching V2 flow)
            plan.status = PlanStatus.approved
            db.commit()
            print(f"    [AUTO] Plan approved")

            result = resolution_orchestrator.execute(db, plan.id)
            done = sum(1 for s in result["steps_executed"] if s["status"] == "done")
            total = len(result["steps_executed"])
            print(f"    [AUTO] Execution: status={result['plan_status']}, {done}/{total} steps done")

            plans.append(plan)
        except Exception as e:
            print(f"    ERROR generating plan: {e}")
            import traceback
            traceback.print_exc()
    return plans


def main():
    print("=" * 70)
    print("  AP Operations Manager — Demo Simulation")
    print("  Full Pipeline: Upload → OCR → Match → Exception → AI Plan")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Clean up previous demo data
        clean_demo_data(db)

        # Setup
        ensure_tolerance(db)
        vendor = create_demo_vendor(db)

        # Create scenarios
        inv1 = create_scenario_1(db, vendor)
        inv2 = create_scenario_2(db, vendor)
        inv3 = create_scenario_3(db, vendor)
        inv4 = create_scenario_4(db, vendor)
        inv5 = create_scenario_5(db, vendor)

        print("\n" + "=" * 70)
        print("  PHASE 2: Running Matching Engine")
        print("=" * 70)

        all_exceptions = []
        for inv in [inv1, inv2, inv3, inv5]:
            result, exceptions = run_matching(db, inv)
            all_exceptions.extend(exceptions)

        # Scenario 4: Duplicate invoice — create exception manually
        # (matching engine doesn't detect duplicates)
        from app.models.exception import Exception_, ExceptionSeverity, ExceptionStatus, ExceptionType
        dup_exc = Exception_(
            invoice_id=inv4.id,
            exception_type=ExceptionType.duplicate_invoice,
            severity=ExceptionSeverity.high,
            status=ExceptionStatus.open,
            ai_suggested_resolution=(
                "Invoice DEMO-SIM-004 appears to be a duplicate submission. "
                "An identical invoice number from the same vendor was already approved. "
                "Recommend checking for duplicates, locking invoice for payment, and "
                "contacting the vendor for confirmation."
            ),
        )
        db.add(dup_exc)
        inv4.status = InvoiceStatus.exception
        db.commit()
        db.refresh(dup_exc)
        all_exceptions.append(dup_exc)
        print(f"\n  [MANUAL] Created duplicate_invoice exception for {inv4.invoice_number}: {dup_exc.id}")

        # Scenario 5: Tax variance — create exception manually if not caught by matching
        tax_excs = [e for e in all_exceptions if str(e.invoice_id) == str(inv5.id) and e.exception_type.value == "tax_variance"]
        if not tax_excs:
            tax_exc = Exception_(
                invoice_id=inv5.id,
                exception_type=ExceptionType.tax_variance,
                severity=ExceptionSeverity.medium,
                status=ExceptionStatus.open,
                ai_suggested_resolution=(
                    "Tax on invoice ($2,400) exceeds expected rate. "
                    "Computed tax at 8.25% on $24,000 subtotal = $1,980. "
                    "Vendor may have applied incorrect tax rate. "
                    "Recommend recalculating tax and contacting vendor."
                ),
            )
            db.add(tax_exc)
            inv5.status = InvoiceStatus.exception
            db.commit()
            db.refresh(tax_exc)
            all_exceptions.append(tax_exc)
            print(f"  [MANUAL] Created tax_variance exception for {inv5.invoice_number}: {tax_exc.id}")

        print("\n" + "=" * 70)
        print(f"  PHASE 3: AI Resolution Plans ({len(all_exceptions)} exceptions)")
        print("=" * 70)

        plans = generate_ai_plans(db, all_exceptions)

        print("\n" + "=" * 70)
        print("  SIMULATION COMPLETE")
        print("=" * 70)
        print(f"\n  Created:")
        print(f"    - 1 vendor (Delta Industrial Supply)")
        print(f"    - 5 invoices (5 scenarios)")
        print(f"    - 4 POs with GRNs")
        print(f"    - {len(all_exceptions)} exceptions")
        print(f"    - {len(plans)} AI resolution plans")
        print(f"\n  Scenarios:")
        print(f"    1. Amount Variance — price overcharge (6%)")
        print(f"    2. Quantity Variance — over-qty invoiced (15%)")
        print(f"    3. Missing PO — no matching PO")
        print(f"    4. Duplicate Invoice — same number resubmitted")
        print(f"    5. Tax Variance — vendor overcharged tax")

        if all_exceptions:
            print(f"\n  Exception IDs for direct access:")
            for exc in all_exceptions:
                print(f"    http://localhost:3000/exceptions/{exc.id}")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
