"""Seed the database with realistic demo data from AP_Inputs.

Uses real PO, GRN, and supplier data from the AP_Inputs business context.

Run from the ``backend/`` directory::

    python -m app.seed
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.approval import AIRecommendation, ApprovalStatus, ApprovalTask
from app.models.audit import ActorType, AuditLog
from app.models.config import Notification, NotificationType, ToleranceConfig
from app.models.exception import (
    Exception_,
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
)
from app.models.goods_receipt import GoodsReceipt, GRNLineItem
from app.models.invoice import (
    DocumentType,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    SourceChannel,
)
from app.models.matching import MatchResult, MatchStatus, MatchType
from app.models.purchase_order import POLineItem, POStatus, PurchaseOrder
from app.models.user import User, UserRole
from app.models.vendor import Vendor, VendorRiskLevel, VendorStatus


def _today() -> date:
    return date.today()


def _days_ago(n: int) -> date:
    return _today() - timedelta(days=n)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hours_ago(n: int) -> datetime:
    return _now() - timedelta(hours=n)


def seed() -> None:
    db = SessionLocal()
    try:
        # Idempotency check
        if db.query(User).filter(User.email == "admin@apops.dev").first():
            print("Seed data already exists — skipping.")
            return

        # ── Users ──────────────────────────────────────────────────────
        users = {
            "admin": User(
                email="admin@apops.dev",
                name="Kyle Stevens",
                hashed_password=hash_password("admin123"),
                role=UserRole.admin,
                department="Finance",
            ),
            "clerk": User(
                email="clerk@apops.dev",
                name="Maria Garcia",
                hashed_password=hash_password("clerk123"),
                role=UserRole.ap_clerk,
                department="Accounts Payable",
            ),
            "analyst": User(
                email="analyst@apops.dev",
                name="John Davis",
                hashed_password=hash_password("analyst123"),
                role=UserRole.ap_analyst,
                department="Accounts Payable",
            ),
            "approver": User(
                email="approver@apops.dev",
                name="Sarah Kim",
                hashed_password=hash_password("approver123"),
                role=UserRole.approver,
                department="Finance",
            ),
            "auditor": User(
                email="auditor@apops.dev",
                name="David Park",
                hashed_password=hash_password("auditor123"),
                role=UserRole.auditor,
                department="Internal Audit",
            ),
        }
        for u in users.values():
            db.add(u)
        db.flush()
        print(f"  Created {len(users)} users")

        # ── Tolerance Config ───────────────────────────────────────────
        tol = ToleranceConfig(
            name="Global Default",
            scope="global",
            scope_value=None,
            amount_tolerance_pct=5.0,
            amount_tolerance_abs=Decimal("100.00"),
            quantity_tolerance_pct=2.0,
            is_active=True,
            version=1,
        )
        db.add(tol)
        db.flush()
        print("  Created global tolerance config")

        # ── Vendors (from AP_Inputs suppliers) ────────────────────────
        vendor_defs = [
            ("SUP001", "SteelCore Industries Ltd.", "Chicago", "IL", "Net30", VendorStatus.active, VendorRiskLevel.low),
            ("SUP002", "TechParts Global Inc.", "San Jose", "CA", "Net45", VendorStatus.active, VendorRiskLevel.low),
            ("SUP003", "LogiTrans Freight Solutions", "Chicago", "IL", "Net30", VendorStatus.active, VendorRiskLevel.medium),
            ("SUP004", "SafeGuard PPE & Safety", "Milwaukee", "WI", "Net30", VendorStatus.active, VendorRiskLevel.low),
            ("SUP005", "MachPrecision Tools Corp.", "Detroit", "MI", "Net60", VendorStatus.active, VendorRiskLevel.medium),
        ]
        vendors: dict[str, Vendor] = {}
        for code, name, city, state, terms, st, risk in vendor_defs:
            v = Vendor(
                vendor_code=code,
                name=name,
                city=city,
                state=state,
                country="US",
                payment_terms_code=terms,
                status=st,
                risk_level=risk,
            )
            db.add(v)
            vendors[code] = v
        db.flush()
        print(f"  Created {len(vendors)} vendors")

        # ── Purchase Orders (from AP_Inputs PO_Data.csv) ──────────────
        # Each tuple: (po_number, vendor_code, status, order_date, delivery_date,
        #              lines: [(line_num, part_num, desc, qty, unit_price, line_total)])
        po_data = [
            ("PO-2025-001", "SUP001", POStatus.fully_received,
             date(2025, 1, 5), date(2025, 1, 20), [
                 (1, "SC-HR-4X8-11G", "Hot-Rolled Steel Sheet 4x8ft 11 Gauge", 200, Decimal("142.50"), Decimal("28500.00")),
                 (2, "SC-HR-4X8-14G", "Hot-Rolled Steel Sheet 4x8ft 14 Gauge", 150, Decimal("110.00"), Decimal("16500.00")),
             ]),
            ("PO-2025-002", "SUP002", POStatus.fully_received,
             date(2025, 1, 8), date(2025, 1, 25), [
                 (1, "TP-SENS-PT100-A", "PT100 Temperature Sensor Type A", 50, Decimal("145.00"), Decimal("7250.00")),
                 (2, "TP-CTRL-PLC-M3", "PLC Micro Controller Module M3", 10, Decimal("525.00"), Decimal("5250.00")),
             ]),
            ("PO-2025-003", "SUP003", POStatus.service_completed,
             date(2025, 1, 10), date(2025, 1, 31), [
                 (1, "LT-FRT-INBOUND-Q1", "Inbound Freight Services - January 2025", 1, Decimal("8200.00"), Decimal("8200.00")),
             ]),
            ("PO-2025-004", "SUP004", POStatus.fully_received,
             date(2025, 1, 12), date(2025, 1, 28), [
                 (1, "SG-HLM-ANSI-BLU", "ANSI Z89.1 Hard Hat Blue", 60, Decimal("28.00"), Decimal("1680.00")),
                 (2, "SG-VEST-HI-VIS-L", "Hi-Vis Safety Vest Size Large", 80, Decimal("24.00"), Decimal("1920.00")),
             ]),
            ("PO-2025-005", "SUP005", POStatus.partially_received,
             date(2025, 1, 15), date(2025, 2, 15), [
                 (1, "MP-CNC-TURRET-T8", "CNC Turret Assembly T8 Series", 2, Decimal("18500.00"), Decimal("37000.00")),
                 (2, "MP-CNC-SPINDLE-H", "CNC High-Speed Spindle Unit", 3, Decimal("9000.00"), Decimal("27000.00")),
                 (3, "MP-CNC-CTRL-V4", "CNC Control Panel V4", 2, Decimal("7000.00"), Decimal("14000.00")),
             ]),
            ("PO-2025-006", "SUP001", POStatus.fully_received,
             date(2025, 1, 18), date(2025, 2, 5), [
                 (1, "SC-ROD-12MM-STD", "Steel Round Rod 12mm Standard Grade", 500, Decimal("28.00"), Decimal("14000.00")),
                 (2, "SC-ROD-20MM-STD", "Steel Round Rod 20mm Standard Grade", 200, Decimal("40.00"), Decimal("8000.00")),
             ]),
            ("PO-2025-007", "SUP002", POStatus.fully_received,
             date(2025, 1, 20), date(2025, 2, 10), [
                 (1, "TP-PCB-MAIN-V7", "Main Circuit Board Assembly V7", 20, Decimal("875.00"), Decimal("17500.00")),
                 (2, "TP-PCB-IO-V3", "I/O Expansion Board V3", 30, Decimal("450.00"), Decimal("13500.00")),
             ]),
            ("PO-2025-008", "SUP003", POStatus.service_completed,
             date(2025, 1, 22), date(2025, 1, 28), [
                 (1, "LT-FRT-EXPRESS-01", "Express Freight - Urgent Parts Delivery", 1, Decimal("4100.00"), Decimal("4100.00")),
             ]),
            ("PO-2025-009", "SUP004", POStatus.fully_received,
             date(2025, 1, 25), date(2025, 2, 8), [
                 (1, "SG-FEX-CO2-5KG", "CO2 Fire Extinguisher 5kg", 20, Decimal("140.00"), Decimal("2800.00")),
             ]),
            ("PO-2025-010", "SUP005", POStatus.fully_received,
             date(2025, 1, 28), date(2025, 2, 12), [
                 (1, "MP-DRILL-HSS-SET", "HSS Drill Bit Set 1-13mm (25pc)", 10, Decimal("285.00"), Decimal("2850.00")),
                 (2, "MP-END-MILL-4F", "4-Flute End Mill Carbide 10mm", 30, Decimal("88.33"), Decimal("2650.00")),
             ]),
        ]

        purchase_orders: dict[str, PurchaseOrder] = {}
        po_lines_map: dict[str, list[POLineItem]] = {}

        for po_number, v_code, po_status, order_dt, delivery_dt, lines in po_data:
            total = sum(lt for _, _, _, _, _, lt in lines)
            po = PurchaseOrder(
                po_number=po_number,
                vendor_id=vendors[v_code].id,
                order_date=order_dt,
                delivery_date=delivery_dt,
                currency="USD",
                total_amount=total,
                status=po_status,
            )
            db.add(po)
            db.flush()

            po_line_items = []
            for line_num, part_num, desc, qty, price, lt in lines:
                pli = POLineItem(
                    po_id=po.id,
                    line_number=line_num,
                    description=desc,
                    quantity_ordered=Decimal(str(qty)),
                    unit_price=price,
                    line_total=lt,
                    quantity_received=Decimal("0"),
                    quantity_invoiced=Decimal("0"),
                )
                db.add(pli)
                po_line_items.append(pli)

            db.flush()
            purchase_orders[po_number] = po
            po_lines_map[po_number] = po_line_items

        print(f"  Created {len(purchase_orders)} purchase orders with line items")

        # ── Goods Receipts (from AP_Inputs GRN_Data.csv) ──────────────
        # GRN-2025-001: PO-2025-001, SUP001, fully received
        grn1 = GoodsReceipt(
            grn_number="GRN-2025-001", po_id=purchase_orders["PO-2025-001"].id,
            vendor_id=vendors["SUP001"].id, receipt_date=date(2025, 1, 21), warehouse="WH-CHI-01",
        )
        db.add(grn1)
        db.flush()
        for pli in po_lines_map["PO-2025-001"]:
            db.add(GRNLineItem(grn_id=grn1.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="Full delivery received in good condition."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-002: PO-2025-002, SUP002, fully received
        grn2 = GoodsReceipt(
            grn_number="GRN-2025-002", po_id=purchase_orders["PO-2025-002"].id,
            vendor_id=vendors["SUP002"].id, receipt_date=date(2025, 1, 24), warehouse="WH-CHI-01",
        )
        db.add(grn2)
        db.flush()
        for pli in po_lines_map["PO-2025-002"]:
            db.add(GRNLineItem(grn_id=grn2.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="All components tested and accepted by QC team."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-003: PO-2025-003, SUP003, service confirmed
        grn3 = GoodsReceipt(
            grn_number="GRN-2025-003", po_id=purchase_orders["PO-2025-003"].id,
            vendor_id=vendors["SUP003"].id, receipt_date=date(2025, 1, 31), warehouse=None,
        )
        db.add(grn3)
        db.flush()
        for pli in po_lines_map["PO-2025-003"]:
            db.add(GRNLineItem(grn_id=grn3.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="Service completion confirmed by SCM department."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-004: PO-2025-004, SUP004, fully received
        grn4 = GoodsReceipt(
            grn_number="GRN-2025-004", po_id=purchase_orders["PO-2025-004"].id,
            vendor_id=vendors["SUP004"].id, receipt_date=date(2025, 1, 27), warehouse="WH-CHI-02",
        )
        db.add(grn4)
        db.flush()
        for pli in po_lines_map["PO-2025-004"]:
            db.add(GRNLineItem(grn_id=grn4.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="All PPE items received and distributed to EHS store."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-005: PO-2025-005, SUP005, partially received (turrets + 2/3 spindles)
        grn5 = GoodsReceipt(
            grn_number="GRN-2025-005", po_id=purchase_orders["PO-2025-005"].id,
            vendor_id=vendors["SUP005"].id, receipt_date=date(2025, 2, 10), warehouse="WH-CHI-01",
        )
        db.add(grn5)
        db.flush()
        po5_lines = po_lines_map["PO-2025-005"]
        # Line 1: 2 turrets received (full)
        db.add(GRNLineItem(grn_id=grn5.id, po_line_id=po5_lines[0].id, quantity_received=Decimal("2"), condition_notes="PARTIAL RECEIPT: Turrets received."))
        po5_lines[0].quantity_received = Decimal("2")
        # Line 2: 2 of 3 spindles received
        db.add(GRNLineItem(grn_id=grn5.id, po_line_id=po5_lines[1].id, quantity_received=Decimal("2"), condition_notes="PARTIAL: 2 of 3 spindles received."))
        po5_lines[1].quantity_received = Decimal("2")
        # Line 3: 0 control panels received yet
        db.add(GRNLineItem(grn_id=grn5.id, po_line_id=po5_lines[2].id, quantity_received=Decimal("0"), condition_notes="Not yet shipped — supplier confirmed delivery Feb 28"))
        po5_lines[2].quantity_received = Decimal("0")

        # GRN-2025-006: PO-2025-006, SUP001, fully received
        grn6 = GoodsReceipt(
            grn_number="GRN-2025-006", po_id=purchase_orders["PO-2025-006"].id,
            vendor_id=vendors["SUP001"].id, receipt_date=date(2025, 2, 4), warehouse="WH-CHI-01",
        )
        db.add(grn6)
        db.flush()
        for pli in po_lines_map["PO-2025-006"]:
            db.add(GRNLineItem(grn_id=grn6.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="Full delivery received."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-007: PO-2025-007, SUP002, fully received
        grn7 = GoodsReceipt(
            grn_number="GRN-2025-007", po_id=purchase_orders["PO-2025-007"].id,
            vendor_id=vendors["SUP002"].id, receipt_date=date(2025, 2, 9), warehouse="WH-CHI-01",
        )
        db.add(grn7)
        db.flush()
        for pli in po_lines_map["PO-2025-007"]:
            db.add(GRNLineItem(grn_id=grn7.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="All boards received. QC testing passed."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-008: PO-2025-008, SUP003, service confirmed
        grn8 = GoodsReceipt(
            grn_number="GRN-2025-008", po_id=purchase_orders["PO-2025-008"].id,
            vendor_id=vendors["SUP003"].id, receipt_date=date(2025, 1, 28), warehouse=None,
        )
        db.add(grn8)
        db.flush()
        for pli in po_lines_map["PO-2025-008"]:
            db.add(GRNLineItem(grn_id=grn8.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="Express freight service completed on time."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-009: PO-2025-009, SUP004, fully received
        grn9 = GoodsReceipt(
            grn_number="GRN-2025-009", po_id=purchase_orders["PO-2025-009"].id,
            vendor_id=vendors["SUP004"].id, receipt_date=date(2025, 2, 7), warehouse="WH-CHI-02",
        )
        db.add(grn9)
        db.flush()
        for pli in po_lines_map["PO-2025-009"]:
            db.add(GRNLineItem(grn_id=grn9.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="All extinguishers received with valid certification."))
            pli.quantity_received = pli.quantity_ordered

        # GRN-2025-010: PO-2025-010, SUP005, fully received
        grn10 = GoodsReceipt(
            grn_number="GRN-2025-010", po_id=purchase_orders["PO-2025-010"].id,
            vendor_id=vendors["SUP005"].id, receipt_date=date(2025, 2, 11), warehouse="WH-CHI-01",
        )
        db.add(grn10)
        db.flush()
        for pli in po_lines_map["PO-2025-010"]:
            db.add(GRNLineItem(grn_id=grn10.id, po_line_id=pli.id, quantity_received=pli.quantity_ordered, condition_notes="All cutting tools received and passed inspection."))
            pli.quantity_received = pli.quantity_ordered

        db.flush()
        all_grns = [grn1, grn2, grn3, grn4, grn5, grn6, grn7, grn8, grn9, grn10]
        print(f"  Created {len(all_grns)} goods receipts with line items")

        # ── Invoices (realistic scenarios tied to AP_Inputs data) ─────
        # Helper to create invoice line items linked to PO lines
        def _make_inv_lines(
            invoice_id: uuid.UUID,
            po_number: str,
            *,
            qty_multiplier: float = 1.0,
            price_multiplier: float = 1.0,
        ) -> list[InvoiceLineItem]:
            items = []
            for pli in po_lines_map[po_number]:
                qty = Decimal(str(float(pli.quantity_ordered) * qty_multiplier))
                price = pli.unit_price * Decimal(str(price_multiplier))
                ili = InvoiceLineItem(
                    invoice_id=invoice_id,
                    line_number=pli.line_number,
                    description=pli.description,
                    quantity=qty,
                    unit_price=price,
                    line_total=qty * price,
                    po_line_id=pli.id,
                    gl_account_code="5100-00",
                    tax_amount=Decimal("0"),
                )
                db.add(ili)
                items.append(ili)
            return items

        invoices: list[Invoice] = []

        # --- POSTED: SteelCore invoice for PO-2025-001 (fully matched, processed) ---
        inv_posted_1 = Invoice(
            invoice_number="SC-INV-2025-0089",
            vendor_id=vendors["SUP001"].id,
            invoice_date=date(2025, 1, 25),
            due_date=date(2025, 2, 24),
            received_date=date(2025, 1, 26),
            currency="USD",
            total_amount=Decimal("45000.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.posted,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.96,
        )
        db.add(inv_posted_1)
        db.flush()
        _make_inv_lines(inv_posted_1.id, "PO-2025-001")
        invoices.append(inv_posted_1)

        # --- POSTED: TechParts invoice for PO-2025-002 (fully matched, processed) ---
        inv_posted_2 = Invoice(
            invoice_number="TP-2025-INV-00341",
            vendor_id=vendors["SUP002"].id,
            invoice_date=date(2025, 1, 28),
            due_date=date(2025, 3, 14),
            received_date=date(2025, 1, 29),
            currency="USD",
            total_amount=Decimal("12500.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.posted,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.94,
        )
        db.add(inv_posted_2)
        db.flush()
        _make_inv_lines(inv_posted_2.id, "PO-2025-002")
        invoices.append(inv_posted_2)

        # --- APPROVED: LogiTrans freight invoice for PO-2025-003 ---
        inv_approved_1 = Invoice(
            invoice_number="LT-25-INV-00567",
            vendor_id=vendors["SUP003"].id,
            invoice_date=date(2025, 2, 5),
            due_date=date(2025, 3, 7),
            received_date=date(2025, 2, 6),
            currency="USD",
            total_amount=Decimal("8200.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.approved,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.91,
        )
        db.add(inv_approved_1)
        db.flush()
        _make_inv_lines(inv_approved_1.id, "PO-2025-003")
        invoices.append(inv_approved_1)

        # --- APPROVED: SafeGuard PPE invoice for PO-2025-004 ---
        inv_approved_2 = Invoice(
            invoice_number="SG-INV-2025-0044",
            vendor_id=vendors["SUP004"].id,
            invoice_date=date(2025, 2, 1),
            due_date=date(2025, 3, 3),
            received_date=date(2025, 2, 2),
            currency="USD",
            total_amount=Decimal("3600.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.approved,
            source_channel=SourceChannel.manual,
        )
        db.add(inv_approved_2)
        db.flush()
        _make_inv_lines(inv_approved_2.id, "PO-2025-004")
        invoices.append(inv_approved_2)

        # --- PENDING_APPROVAL: SteelCore rod invoice for PO-2025-006 ---
        inv_pending_1 = Invoice(
            invoice_number="SC-INV-2025-0112",
            vendor_id=vendors["SUP001"].id,
            invoice_date=date(2025, 2, 8),
            due_date=date(2025, 3, 10),
            received_date=date(2025, 2, 9),
            currency="USD",
            total_amount=Decimal("22000.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.pending_approval,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.95,
        )
        db.add(inv_pending_1)
        db.flush()
        _make_inv_lines(inv_pending_1.id, "PO-2025-006")
        invoices.append(inv_pending_1)

        # --- PENDING_APPROVAL: TechParts circuit board invoice for PO-2025-007 ---
        inv_pending_2 = Invoice(
            invoice_number="TP-2025-INV-00398",
            vendor_id=vendors["SUP002"].id,
            invoice_date=date(2025, 2, 12),
            due_date=date(2025, 3, 29),
            received_date=date(2025, 2, 13),
            currency="USD",
            total_amount=Decimal("31000.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.pending_approval,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.93,
        )
        db.add(inv_pending_2)
        db.flush()
        _make_inv_lines(inv_pending_2.id, "PO-2025-007")
        invoices.append(inv_pending_2)

        # --- EXCEPTION: MachPrecision CNC invoice for PO-2025-005 (qty variance — partial GRN) ---
        inv_exc_1 = Invoice(
            invoice_number="MP-INV-2025-00231",
            vendor_id=vendors["SUP005"].id,
            invoice_date=date(2025, 2, 15),
            due_date=date(2025, 4, 16),
            received_date=date(2025, 2, 16),
            currency="USD",
            total_amount=Decimal("78000.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.exception,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.89,
        )
        db.add(inv_exc_1)
        db.flush()
        _make_inv_lines(inv_exc_1.id, "PO-2025-005")  # Full qty but only partial GRN
        invoices.append(inv_exc_1)

        # --- EXCEPTION: MachPrecision tools invoice with price variance for PO-2025-010 ---
        inv_exc_2 = Invoice(
            invoice_number="MP-INV-2025-00245",
            vendor_id=vendors["SUP005"].id,
            invoice_date=date(2025, 2, 18),
            due_date=date(2025, 4, 19),
            received_date=date(2025, 2, 19),
            currency="USD",
            total_amount=Decimal("5885.00"),  # ~7% over PO total of 5500
            tax_amount=Decimal("0"),
            status=InvoiceStatus.exception,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.92,
        )
        db.add(inv_exc_2)
        db.flush()
        _make_inv_lines(inv_exc_2.id, "PO-2025-010", price_multiplier=1.07)
        invoices.append(inv_exc_2)

        # --- EXCEPTION: Duplicate of TP-2025-INV-00341 ---
        inv_exc_dup = Invoice(
            invoice_number="TP-2025-INV-00341",  # Same number!
            vendor_id=vendors["SUP002"].id,
            invoice_date=date(2025, 1, 28),
            due_date=date(2025, 3, 14),
            received_date=date(2025, 2, 20),
            currency="USD",
            total_amount=Decimal("12500.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.exception,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.88,
        )
        db.add(inv_exc_dup)
        db.flush()
        _make_inv_lines(inv_exc_dup.id, "PO-2025-002")
        invoices.append(inv_exc_dup)

        # --- EXCEPTION: Unknown vendor invoice (no PO match) ---
        # Apex Chemicals is not in our vendor master
        apex_vendor = Vendor(
            vendor_code="ACI-EXT",
            name="Apex Chemicals International",
            city="Houston",
            state="TX",
            country="US",
            payment_terms_code="Net30",
            status=VendorStatus.active,
            risk_level=VendorRiskLevel.high,
        )
        db.add(apex_vendor)
        db.flush()

        inv_exc_nopo = Invoice(
            invoice_number="ACI-2025-00001",
            vendor_id=apex_vendor.id,
            invoice_date=date(2025, 2, 10),
            due_date=date(2025, 3, 12),
            received_date=date(2025, 2, 11),
            currency="USD",
            total_amount=Decimal("4750.00"),
            tax_amount=Decimal("237.50"),
            status=InvoiceStatus.exception,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.85,
        )
        db.add(inv_exc_nopo)
        db.flush()
        db.add(InvoiceLineItem(
            invoice_id=inv_exc_nopo.id, line_number=1,
            description="Industrial Solvent - Acetone Grade A (200L Drum)",
            quantity=Decimal("5"), unit_price=Decimal("950.00"), line_total=Decimal("4750.00"),
            tax_amount=Decimal("237.50"),
        ))
        invoices.append(inv_exc_nopo)

        # --- MATCHING: SafeGuard fire extinguisher invoice for PO-2025-009 ---
        inv_matching = Invoice(
            invoice_number="SG-INV-2025-0058",
            vendor_id=vendors["SUP004"].id,
            invoice_date=date(2025, 2, 12),
            due_date=date(2025, 3, 14),
            received_date=date(2025, 2, 13),
            currency="USD",
            total_amount=Decimal("2800.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.matching,
            source_channel=SourceChannel.manual,
        )
        db.add(inv_matching)
        db.flush()
        _make_inv_lines(inv_matching.id, "PO-2025-009")
        invoices.append(inv_matching)

        # --- EXTRACTED: LogiTrans express freight for PO-2025-008 ---
        inv_extracted = Invoice(
            invoice_number="LT-25-INV-00589",
            vendor_id=vendors["SUP003"].id,
            invoice_date=date(2025, 2, 1),
            due_date=date(2025, 3, 3),
            received_date=date(2025, 2, 14),
            currency="USD",
            total_amount=Decimal("4100.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.extracted,
            source_channel=SourceChannel.email,
            ocr_confidence_score=0.93,
        )
        db.add(inv_extracted)
        db.flush()
        db.add(InvoiceLineItem(
            invoice_id=inv_extracted.id, line_number=1,
            description="Express Freight - Urgent Parts Delivery",
            quantity=Decimal("1"), unit_price=Decimal("4100.00"), line_total=Decimal("4100.00"),
            tax_amount=Decimal("0"), ai_gl_prediction="6100-00", ai_confidence=0.91,
        ))
        invoices.append(inv_extracted)

        # --- DRAFT: MachPrecision supplemental tools (just uploaded, not yet OCR'd) ---
        inv_draft_1 = Invoice(
            invoice_number="MP-INV-2025-00260",
            vendor_id=vendors["SUP005"].id,
            invoice_date=date(2025, 2, 20),
            due_date=date(2025, 4, 21),
            received_date=date(2025, 2, 21),
            currency="USD",
            total_amount=Decimal("3200.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.draft,
            source_channel=SourceChannel.manual,
        )
        db.add(inv_draft_1)
        db.flush()
        db.add(InvoiceLineItem(
            invoice_id=inv_draft_1.id, line_number=1,
            description="Precision Tooling - Custom Order",
            quantity=Decimal("1"), unit_price=Decimal("3200.00"), line_total=Decimal("3200.00"),
            tax_amount=Decimal("0"),
        ))
        invoices.append(inv_draft_1)

        # --- DRAFT: SteelCore supplemental order ---
        inv_draft_2 = Invoice(
            invoice_number="SC-INV-2025-0128",
            vendor_id=vendors["SUP001"].id,
            invoice_date=date(2025, 2, 22),
            due_date=date(2025, 3, 24),
            received_date=date(2025, 2, 23),
            currency="USD",
            total_amount=Decimal("8500.00"),
            tax_amount=Decimal("0"),
            status=InvoiceStatus.draft,
            source_channel=SourceChannel.email,
        )
        db.add(inv_draft_2)
        db.flush()
        db.add(InvoiceLineItem(
            invoice_id=inv_draft_2.id, line_number=1,
            description="Steel Plate Special Cut",
            quantity=Decimal("10"), unit_price=Decimal("850.00"), line_total=Decimal("8500.00"),
            tax_amount=Decimal("0"),
        ))
        invoices.append(inv_draft_2)

        db.flush()
        print(f"  Created {len(invoices)} invoices with line items")

        # ── Match Results ──────────────────────────────────────────────
        # Posted invoice 1 — 3-way matched (PO-001 has GRN-001)
        db.add(MatchResult(
            invoice_id=inv_posted_1.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2025-001"].id,
            matched_grn_ids=[str(grn1.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Posted invoice 2 — 3-way matched (PO-002 has GRN-002)
        db.add(MatchResult(
            invoice_id=inv_posted_2.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2025-002"].id,
            matched_grn_ids=[str(grn2.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Approved 1 — 3-way matched (PO-003/GRN-003, freight service)
        db.add(MatchResult(
            invoice_id=inv_approved_1.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2025-003"].id,
            matched_grn_ids=[str(grn3.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Approved 2 — 3-way matched (PO-004/GRN-004, PPE)
        db.add(MatchResult(
            invoice_id=inv_approved_2.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2025-004"].id,
            matched_grn_ids=[str(grn4.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Pending 1 — 3-way matched (PO-006/GRN-006)
        db.add(MatchResult(
            invoice_id=inv_pending_1.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2025-006"].id,
            matched_grn_ids=[str(grn6.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Pending 2 — 3-way matched (PO-007/GRN-007)
        db.add(MatchResult(
            invoice_id=inv_pending_2.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2025-007"].id,
            matched_grn_ids=[str(grn7.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Exception 1 — 3-way partial (qty variance: full invoice but partial GRN on PO-005)
        db.add(MatchResult(
            invoice_id=inv_exc_1.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.partial,
            overall_score=55.0,
            details={"lines": [
                {"line": 1, "status": "matched"},
                {"line": 2, "status": "quantity_variance", "invoiced": 3, "received": 2},
                {"line": 3, "status": "quantity_variance", "invoiced": 2, "received": 0},
            ]},
            matched_po_id=purchase_orders["PO-2025-005"].id,
            matched_grn_ids=[str(grn5.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Exception 2 — 3-way partial (amount variance: 7% over on PO-010)
        db.add(MatchResult(
            invoice_id=inv_exc_2.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.partial,
            overall_score=40.0,
            details={"lines": [
                {"line": 1, "status": "amount_variance", "po_price": 285.00, "inv_price": 304.95},
                {"line": 2, "status": "amount_variance", "po_price": 88.33, "inv_price": 94.51},
            ]},
            matched_po_id=purchase_orders["PO-2025-010"].id,
            matched_grn_ids=[str(grn10.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Exception 3 — duplicate detected
        db.add(MatchResult(
            invoice_id=inv_exc_dup.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}], "duplicate_of": str(inv_posted_2.id)},
            matched_po_id=purchase_orders["PO-2025-002"].id,
            matched_grn_ids=[str(grn2.id)],
            tolerance_applied=False,
        ))

        # Exception 4 — unmatched (no PO for Apex Chemicals)
        db.add(MatchResult(
            invoice_id=inv_exc_nopo.id,
            match_type=MatchType.two_way,
            match_status=MatchStatus.unmatched,
            overall_score=0.0,
            details={"reason": "No matching PO found for vendor Apex Chemicals International. Vendor not in approved supplier list."},
            tolerance_applied=False,
        ))

        db.flush()
        print("  Created match results")

        # ── Exceptions ─────────────────────────────────────────────────
        # Exception 1: qty variance on CNC order
        db.add(Exception_(
            invoice_id=inv_exc_1.id,
            exception_type=ExceptionType.quantity_variance,
            severity=ExceptionSeverity.high,
            status=ExceptionStatus.assigned,
            assigned_to=users["analyst"].id,
            ai_suggested_resolution="Invoice amount ($78,000) covers full PO quantity but GRN shows only partial receipt: 2/3 spindles received, 0/2 control panels received. Recommend holding payment for undelivered items ($23,000) and paying only for received goods ($55,000). Request vendor to issue corrected invoice.",
            ai_severity_reasoning="High severity: $23,000 discrepancy between invoiced and received quantities on capital equipment order. Partial delivery with pending items.",
        ))

        # Exception 2: amount variance on tools
        db.add(Exception_(
            invoice_id=inv_exc_2.id,
            exception_type=ExceptionType.amount_variance,
            severity=ExceptionSeverity.medium,
            status=ExceptionStatus.assigned,
            assigned_to=users["analyst"].id,
            ai_suggested_resolution="Invoice total ($5,885) exceeds PO total ($5,500) by 7%. This exceeds the 5% tolerance. Review vendor pricing agreement. MachPrecision may have applied a price increase without PO amendment. Request credit memo for $385 or negotiate revised terms.",
            ai_severity_reasoning="Medium severity: 7% price variance above tolerance on standard tooling order. No contract price protection clause identified.",
        ))

        # Exception 3: duplicate invoice
        db.add(Exception_(
            invoice_id=inv_exc_dup.id,
            exception_type=ExceptionType.duplicate_invoice,
            severity=ExceptionSeverity.critical,
            status=ExceptionStatus.open,
            ai_suggested_resolution="DUPLICATE DETECTED: Invoice TP-2025-INV-00341 from TechParts Global was already processed and posted. Same invoice number, same amount ($12,500), same vendor. Reject immediately to prevent double payment.",
            ai_severity_reasoning="Critical severity: confirmed duplicate invoice. Payment for original already posted. Processing would result in $12,500 overpayment.",
        ))

        # Exception 4: missing PO
        db.add(Exception_(
            invoice_id=inv_exc_nopo.id,
            exception_type=ExceptionType.missing_po,
            severity=ExceptionSeverity.high,
            status=ExceptionStatus.open,
            ai_suggested_resolution="No purchase order found for Apex Chemicals International. Vendor is not in the approved supplier master. Contact the requesting department to: (1) verify the legitimacy of this purchase, (2) obtain retroactive PO approval, (3) add vendor to approved supplier list if valid.",
            ai_severity_reasoning="High severity: invoice from non-approved vendor with no PO reference. Potential unauthorized purchase requiring management approval.",
        ))

        db.flush()
        print("  Created exceptions")

        # ── Approval Tasks ─────────────────────────────────────────────
        # Pending approvals
        db.add(ApprovalTask(
            invoice_id=inv_pending_1.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.pending,
            ai_recommendation=AIRecommendation.approve,
            ai_recommendation_reason="Invoice SC-INV-2025-0112 from SteelCore Industries matches PO-2025-006 at 100% (3-way match). All goods received in full at WH-CHI-01. Vendor has clean payment history. Amount ($22,000) within normal range. Recommend approval.",
        ))
        db.add(ApprovalTask(
            invoice_id=inv_pending_2.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.pending,
            ai_recommendation=AIRecommendation.approve,
            ai_recommendation_reason="Invoice TP-2025-INV-00398 from TechParts Global matches PO-2025-007 at 100% (3-way match). Circuit boards received and QC-passed. Amount ($31,000) is above $25K threshold — requires senior approval. Recommend approval with standard authorization.",
        ))
        # Approved tasks
        db.add(ApprovalTask(
            invoice_id=inv_approved_1.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.approved,
            decision_at=_hours_ago(96),
            comments="Freight service confirmed by SCM. Approved.",
        ))
        db.add(ApprovalTask(
            invoice_id=inv_approved_2.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.approved,
            decision_at=_hours_ago(72),
            comments="PPE delivery verified. All items distributed.",
        ))
        # Posted invoice approvals
        db.add(ApprovalTask(
            invoice_id=inv_posted_1.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.approved,
            decision_at=_hours_ago(168),
            comments="Steel delivery confirmed. 3-way match verified.",
        ))
        db.add(ApprovalTask(
            invoice_id=inv_posted_2.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.approved,
            decision_at=_hours_ago(144),
            comments="Sensors and controllers received. Approved.",
        ))
        db.flush()
        print("  Created approval tasks")

        # ── Audit Logs ─────────────────────────────────────────────────
        audit_entries = [
            # Posted invoice 1 lifecycle
            ("invoice", inv_posted_1.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 240),
            ("invoice", inv_posted_1.id, "ocr_extracted", ActorType.ai_agent, None, "Claude AI", 238),
            ("invoice", inv_posted_1.id, "matched", ActorType.system, None, "System", 236),
            ("invoice", inv_posted_1.id, "approved", ActorType.user, users["approver"].id, "Sarah Kim", 168),
            ("invoice", inv_posted_1.id, "posted", ActorType.system, None, "System", 166),
            # Posted invoice 2 lifecycle
            ("invoice", inv_posted_2.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 220),
            ("invoice", inv_posted_2.id, "ocr_extracted", ActorType.ai_agent, None, "Claude AI", 218),
            ("invoice", inv_posted_2.id, "matched", ActorType.system, None, "System", 216),
            ("invoice", inv_posted_2.id, "approved", ActorType.user, users["approver"].id, "Sarah Kim", 144),
            ("invoice", inv_posted_2.id, "posted", ActorType.system, None, "System", 142),
            # Approved invoices
            ("invoice", inv_approved_1.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 160),
            ("invoice", inv_approved_1.id, "matched", ActorType.system, None, "System", 158),
            ("invoice", inv_approved_1.id, "approved", ActorType.user, users["approver"].id, "Sarah Kim", 96),
            ("invoice", inv_approved_2.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 155),
            ("invoice", inv_approved_2.id, "matched", ActorType.system, None, "System", 153),
            ("invoice", inv_approved_2.id, "approved", ActorType.user, users["approver"].id, "Sarah Kim", 72),
            # Pending approvals
            ("invoice", inv_pending_1.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 100),
            ("invoice", inv_pending_1.id, "matched", ActorType.system, None, "System", 98),
            ("approval", inv_pending_1.id, "ai_recommendation", ActorType.ai_agent, None, "Claude AI", 97),
            ("invoice", inv_pending_2.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 80),
            ("invoice", inv_pending_2.id, "matched", ActorType.system, None, "System", 78),
            ("approval", inv_pending_2.id, "ai_recommendation", ActorType.ai_agent, None, "Claude AI", 77),
            # Exceptions
            ("invoice", inv_exc_1.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 60),
            ("invoice", inv_exc_1.id, "matched", ActorType.system, None, "System", 58),
            ("exception", inv_exc_1.id, "created", ActorType.system, None, "System", 57),
            ("invoice", inv_exc_2.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 50),
            ("exception", inv_exc_2.id, "created", ActorType.system, None, "System", 48),
            ("invoice", inv_exc_dup.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 40),
            ("exception", inv_exc_dup.id, "duplicate_detected", ActorType.system, None, "Duplicate Detection AI", 39),
            ("invoice", inv_exc_nopo.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 35),
            ("exception", inv_exc_nopo.id, "created", ActorType.system, None, "System", 34),
            # Vendor activities
            ("vendor", vendors["SUP001"].id, "created", ActorType.user, users["admin"].id, "Kyle Stevens", 300),
            ("vendor", vendors["SUP002"].id, "created", ActorType.user, users["admin"].id, "Kyle Stevens", 300),
            ("vendor", vendors["SUP003"].id, "created", ActorType.user, users["admin"].id, "Kyle Stevens", 300),
            ("vendor", vendors["SUP004"].id, "created", ActorType.user, users["admin"].id, "Kyle Stevens", 300),
            ("vendor", vendors["SUP005"].id, "created", ActorType.user, users["admin"].id, "Kyle Stevens", 300),
        ]
        for entity_type, entity_id, action, actor_type, actor_id, actor_name, hours in audit_entries:
            db.add(AuditLog(
                timestamp=_hours_ago(hours),
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_name=actor_name,
            ))
        db.flush()
        print(f"  Created {len(audit_entries)} audit log entries")

        # ── Notifications ──────────────────────────────────────────────
        db.add(Notification(
            user_id=users["approver"].id,
            type=NotificationType.approval_request,
            title="Invoice SC-INV-2025-0112 Pending Approval",
            message="Invoice SC-INV-2025-0112 from SteelCore Industries ($22,000.00) requires your approval. 3-way match verified. AI recommends: Approve.",
            related_entity_type="invoice",
            related_entity_id=inv_pending_1.id,
            is_read=False,
        ))
        db.add(Notification(
            user_id=users["approver"].id,
            type=NotificationType.approval_request,
            title="Invoice TP-2025-INV-00398 Pending Approval",
            message="Invoice TP-2025-INV-00398 from TechParts Global ($31,000.00) requires your approval. Above $25K threshold. AI recommends: Approve.",
            related_entity_type="invoice",
            related_entity_id=inv_pending_2.id,
            is_read=False,
        ))
        db.add(Notification(
            user_id=users["analyst"].id,
            type=NotificationType.exception_assigned,
            title="Critical: Duplicate Invoice Detected",
            message="DUPLICATE: Invoice TP-2025-INV-00341 from TechParts Global ($12,500) is a duplicate of an already-posted invoice. Immediate review required.",
            related_entity_type="exception",
            related_entity_id=inv_exc_dup.id,
            is_read=False,
        ))
        db.add(Notification(
            user_id=users["analyst"].id,
            type=NotificationType.exception_assigned,
            title="Exception: Quantity Variance on CNC Order",
            message="Invoice MP-INV-2025-00231 ($78,000) has quantity variance against partial GRN. $23,000 of goods not yet received.",
            related_entity_type="exception",
            related_entity_id=inv_exc_1.id,
            is_read=False,
        ))
        db.add(Notification(
            user_id=users["admin"].id,
            type=NotificationType.system,
            title="System Health Check",
            message="All services running normally. 15 invoices processed this period. 4 exceptions requiring attention.",
            is_read=True,
        ))
        db.flush()
        print("  Created notifications")

        # ── Commit ─────────────────────────────────────────────────────
        db.commit()
        print("\nCore data seed complete!")

        # ── Knowledge Base: Parse AP_Inputs documents ─────────────────
        print("\n  Parsing AP_Inputs documents for Knowledge Base...")
        try:
            from app.services.document_parser import parse_all_ap_inputs

            ap_inputs_dir = "/Users/kyle/Desktop/AP-Digital-Ops-Manager/AP_Inputs"
            import os
            if os.path.exists(ap_inputs_dir):
                result = parse_all_ap_inputs(db, ap_inputs_dir, use_ai=False)
                print(f"  Parsed {len(result['documents'])} documents, extracted {result['total_rules']} rules")
                for doc_info in result["documents"]:
                    print(f"    - {doc_info['filename']}: {doc_info['rules_extracted']} rules")
            else:
                print(f"  AP_Inputs dir not found at {ap_inputs_dir} — skipping document parsing")
        except Exception as e:
            print(f"  Warning: Document parsing failed: {e}")
            # Don't fail the whole seed for optional parsing

        print("\nSeed complete!")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
