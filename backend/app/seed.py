"""Seed the database with realistic demo data.

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

        # ── Vendors ────────────────────────────────────────────────────
        vendor_defs = [
            ("V-001", "Acme Corp", "New York", "NY", "Net30", VendorStatus.active, VendorRiskLevel.low),
            ("V-002", "TechParts Ltd", "San Jose", "CA", "Net45", VendorStatus.active, VendorRiskLevel.low),
            ("V-003", "Global Supply Co", "Chicago", "IL", "Net30", VendorStatus.active, VendorRiskLevel.medium),
            ("V-004", "Steel Works Ltd", "Pittsburgh", "PA", "Net60", VendorStatus.active, VendorRiskLevel.high),
            ("V-005", "Office Depot", "Boca Raton", "FL", "Net15", VendorStatus.active, VendorRiskLevel.low),
            ("V-006", "CloudServ Inc", "Seattle", "WA", "Net30", VendorStatus.active, VendorRiskLevel.low),
            ("V-007", "Metro Electric", "Denver", "CO", "Net30", VendorStatus.on_hold, VendorRiskLevel.medium),
            ("V-008", "PackRight Inc", "Dallas", "TX", "Net45", VendorStatus.active, VendorRiskLevel.low),
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

        # ── Purchase Orders ────────────────────────────────────────────
        po_data = [
            # (po_number, vendor_code, status, order_date, lines: [(desc, qty, price)])
            ("PO-2024-001", "V-001", POStatus.fully_received, _days_ago(60), [
                ("Industrial Bearings 6205-2RS", 100, Decimal("12.50")),
                ("Lubricant - Synthetic 5L", 20, Decimal("45.00")),
                ("Conveyor Belt Segment 2m", 10, Decimal("225.00")),
            ]),
            ("PO-2024-002", "V-002", POStatus.fully_received, _days_ago(45), [
                ("Circuit Board PCB-A100", 200, Decimal("35.00")),
                ("LED Panel 12V 50W", 50, Decimal("68.00")),
            ]),
            ("PO-2024-003", "V-003", POStatus.partially_received, _days_ago(30), [
                ("Steel Pipe DN50 6m", 150, Decimal("42.00")),
                ("Flange DN50 PN16", 300, Decimal("15.50")),
                ("Gasket Set DN50", 300, Decimal("4.25")),
            ]),
            ("PO-2024-004", "V-005", POStatus.open, _days_ago(20), [
                ("Copy Paper A4 Ream", 500, Decimal("8.99")),
                ("Ink Cartridge Black HP", 30, Decimal("42.00")),
            ]),
            ("PO-2024-005", "V-004", POStatus.fully_received, _days_ago(55), [
                ("Steel Plate 4x8 1/4in", 25, Decimal("310.00")),
                ("Angle Iron 2x2 20ft", 40, Decimal("85.00")),
                ("Welding Rod E7018 50lb", 10, Decimal("125.00")),
                ("Cutting Disc 14in", 100, Decimal("6.50")),
            ]),
        ]

        purchase_orders: dict[str, PurchaseOrder] = {}
        po_lines_map: dict[str, list[POLineItem]] = {}  # po_number -> lines

        for po_number, v_code, po_status, order_dt, lines in po_data:
            total = sum(qty * price for _, qty, price in lines)
            po = PurchaseOrder(
                po_number=po_number,
                vendor_id=vendors[v_code].id,
                order_date=order_dt,
                delivery_date=order_dt + timedelta(days=14),
                currency="USD",
                total_amount=total,
                status=po_status,
            )
            db.add(po)
            db.flush()

            po_line_items = []
            for idx, (desc, qty, price) in enumerate(lines, start=1):
                pli = POLineItem(
                    po_id=po.id,
                    line_number=idx,
                    description=desc,
                    quantity_ordered=Decimal(str(qty)),
                    unit_price=price,
                    line_total=Decimal(str(qty)) * price,
                    quantity_received=Decimal("0"),
                    quantity_invoiced=Decimal("0"),
                )
                db.add(pli)
                po_line_items.append(pli)

            db.flush()
            purchase_orders[po_number] = po
            po_lines_map[po_number] = po_line_items

        print(f"  Created {len(purchase_orders)} purchase orders with line items")

        # ── Goods Receipts ─────────────────────────────────────────────
        # GRN for PO-001 (full receipt)
        grn1 = GoodsReceipt(
            grn_number="GRN-2024-001",
            po_id=purchase_orders["PO-2024-001"].id,
            vendor_id=vendors["V-001"].id,
            receipt_date=_days_ago(50),
            warehouse="Warehouse A",
        )
        db.add(grn1)
        db.flush()
        for pli in po_lines_map["PO-2024-001"]:
            db.add(GRNLineItem(
                grn_id=grn1.id,
                po_line_id=pli.id,
                quantity_received=pli.quantity_ordered,
            ))
            pli.quantity_received = pli.quantity_ordered
        db.flush()

        # GRN for PO-005 (full receipt)
        grn2 = GoodsReceipt(
            grn_number="GRN-2024-002",
            po_id=purchase_orders["PO-2024-005"].id,
            vendor_id=vendors["V-004"].id,
            receipt_date=_days_ago(40),
            warehouse="Warehouse B",
        )
        db.add(grn2)
        db.flush()
        for pli in po_lines_map["PO-2024-005"]:
            db.add(GRNLineItem(
                grn_id=grn2.id,
                po_line_id=pli.id,
                quantity_received=pli.quantity_ordered,
            ))
            pli.quantity_received = pli.quantity_ordered
        db.flush()

        # GRN for PO-003 (partial receipt — 80%)
        grn3 = GoodsReceipt(
            grn_number="GRN-2024-003",
            po_id=purchase_orders["PO-2024-003"].id,
            vendor_id=vendors["V-003"].id,
            receipt_date=_days_ago(20),
            warehouse="Warehouse A",
        )
        db.add(grn3)
        db.flush()
        for pli in po_lines_map["PO-2024-003"]:
            partial_qty = (pli.quantity_ordered * Decimal("0.8")).quantize(Decimal("0.01"))
            db.add(GRNLineItem(
                grn_id=grn3.id,
                po_line_id=pli.id,
                quantity_received=partial_qty,
            ))
            pli.quantity_received = partial_qty
        db.flush()

        grn_ids = [grn1.id, grn2.id, grn3.id]
        print(f"  Created {len(grn_ids)} goods receipts with line items")

        # ── Invoices ───────────────────────────────────────────────────
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
                    tax_amount=Decimal("0"),
                )
                db.add(ili)
                items.append(ili)
            return items

        invoices: list[Invoice] = []

        # --- 3 draft invoices ---
        for i, (v_code, num) in enumerate([("V-006", "INV-D-001"), ("V-008", "INV-D-002"), ("V-007", "INV-D-003")]):
            inv = Invoice(
                invoice_number=num,
                vendor_id=vendors[v_code].id,
                invoice_date=_days_ago(5 + i),
                due_date=_days_ago(5 + i) + timedelta(days=30),
                received_date=_days_ago(5 + i),
                currency="USD",
                total_amount=Decimal("1500.00") + Decimal(str(i * 500)),
                tax_amount=Decimal("0"),
                freight_amount=Decimal("0"),
                discount_amount=Decimal("0"),
                status=InvoiceStatus.draft,
                source_channel=SourceChannel.manual,
            )
            db.add(inv)
            db.flush()
            # Draft invoices: no PO link, standalone line items
            db.add(InvoiceLineItem(
                invoice_id=inv.id, line_number=1, description="General Services",
                quantity=Decimal("1"), unit_price=inv.total_amount, line_total=inv.total_amount,
                tax_amount=Decimal("0"),
            ))
            invoices.append(inv)

        # --- 2 extracted invoices ---
        for i, (v_code, num) in enumerate([("V-005", "INV-E-001"), ("V-002", "INV-E-002")]):
            inv = Invoice(
                invoice_number=num,
                vendor_id=vendors[v_code].id,
                invoice_date=_days_ago(8 + i),
                due_date=_days_ago(8 + i) + timedelta(days=30),
                received_date=_days_ago(8 + i),
                currency="USD",
                total_amount=Decimal("3200.00") + Decimal(str(i * 800)),
                tax_amount=Decimal("250.00"),
                status=InvoiceStatus.extracted,
                ocr_confidence_score=0.92 - (i * 0.05),
                source_channel=SourceChannel.email,
            )
            db.add(inv)
            db.flush()
            db.add(InvoiceLineItem(
                invoice_id=inv.id, line_number=1, description="Office Supplies Batch",
                quantity=Decimal("10"), unit_price=Decimal("320.00"),
                line_total=Decimal("3200.00"), tax_amount=Decimal("250.00"),
                ai_gl_prediction="6100-00", ai_confidence=0.88,
            ))
            invoices.append(inv)

        # --- 2 matching invoices ---
        for i, (v_code, num) in enumerate([("V-003", "INV-M-001"), ("V-001", "INV-M-002")]):
            inv = Invoice(
                invoice_number=num,
                vendor_id=vendors[v_code].id,
                invoice_date=_days_ago(12 + i),
                due_date=_days_ago(12 + i) + timedelta(days=45),
                currency="USD",
                total_amount=Decimal("5600.00") + Decimal(str(i * 1200)),
                status=InvoiceStatus.matching,
                source_channel=SourceChannel.manual,
            )
            db.add(inv)
            db.flush()
            db.add(InvoiceLineItem(
                invoice_id=inv.id, line_number=1, description="Raw Materials",
                quantity=Decimal("50"), unit_price=Decimal("112.00"),
                line_total=Decimal("5600.00"), tax_amount=Decimal("0"),
            ))
            invoices.append(inv)

        # --- 3 exception invoices (linked to POs) ---
        # Exception invoice 1: linked to PO-001, amount variance
        inv_exc1 = Invoice(
            invoice_number="INV-X-001",
            vendor_id=vendors["V-001"].id,
            invoice_date=_days_ago(18),
            due_date=_days_ago(18) + timedelta(days=30),
            currency="USD",
            total_amount=Decimal("5200.00"),
            status=InvoiceStatus.exception,
            source_channel=SourceChannel.email,
        )
        db.add(inv_exc1)
        db.flush()
        _make_inv_lines(inv_exc1.id, "PO-2024-001", price_multiplier=1.08)  # 8% over PO price
        invoices.append(inv_exc1)

        # Exception invoice 2: missing PO
        inv_exc2 = Invoice(
            invoice_number="INV-X-002",
            vendor_id=vendors["V-003"].id,
            invoice_date=_days_ago(15),
            due_date=_days_ago(15) + timedelta(days=30),
            currency="USD",
            total_amount=Decimal("2800.00"),
            status=InvoiceStatus.exception,
            source_channel=SourceChannel.manual,
        )
        db.add(inv_exc2)
        db.flush()
        db.add(InvoiceLineItem(
            invoice_id=inv_exc2.id, line_number=1, description="Consulting Services",
            quantity=Decimal("1"), unit_price=Decimal("2800.00"), line_total=Decimal("2800.00"),
            tax_amount=Decimal("0"),
        ))
        invoices.append(inv_exc2)

        # Exception invoice 3: linked to PO-003, qty variance (invoiced > received due to partial GRN)
        inv_exc3 = Invoice(
            invoice_number="INV-X-003",
            vendor_id=vendors["V-003"].id,
            invoice_date=_days_ago(10),
            due_date=_days_ago(10) + timedelta(days=30),
            currency="USD",
            total_amount=Decimal("12250.00"),
            status=InvoiceStatus.exception,
            source_channel=SourceChannel.email,
        )
        db.add(inv_exc3)
        db.flush()
        _make_inv_lines(inv_exc3.id, "PO-2024-003")  # Full qty but only 80% received
        invoices.append(inv_exc3)

        db.flush()

        # --- 2 pending_approval invoices (linked to POs, matched) ---
        inv_pa1 = Invoice(
            invoice_number="INV-A-001",
            vendor_id=vendors["V-002"].id,
            invoice_date=_days_ago(14),
            due_date=_days_ago(14) + timedelta(days=45),
            currency="USD",
            total_amount=Decimal("10400.00"),
            status=InvoiceStatus.pending_approval,
            source_channel=SourceChannel.email,
        )
        db.add(inv_pa1)
        db.flush()
        _make_inv_lines(inv_pa1.id, "PO-2024-002")
        invoices.append(inv_pa1)

        inv_pa2 = Invoice(
            invoice_number="INV-A-002",
            vendor_id=vendors["V-004"].id,
            invoice_date=_days_ago(12),
            due_date=_days_ago(12) + timedelta(days=60),
            currency="USD",
            total_amount=Decimal("12600.00"),
            status=InvoiceStatus.pending_approval,
            source_channel=SourceChannel.manual,
        )
        db.add(inv_pa2)
        db.flush()
        _make_inv_lines(inv_pa2.id, "PO-2024-005")
        invoices.append(inv_pa2)

        # --- 2 approved invoices ---
        inv_ap1 = Invoice(
            invoice_number="INV-P-001",
            vendor_id=vendors["V-001"].id,
            invoice_date=_days_ago(25),
            due_date=_days_ago(25) + timedelta(days=30),
            currency="USD",
            total_amount=Decimal("4150.00"),
            status=InvoiceStatus.approved,
            source_channel=SourceChannel.email,
        )
        db.add(inv_ap1)
        db.flush()
        _make_inv_lines(inv_ap1.id, "PO-2024-001")
        invoices.append(inv_ap1)

        inv_ap2 = Invoice(
            invoice_number="INV-P-002",
            vendor_id=vendors["V-005"].id,
            invoice_date=_days_ago(22),
            due_date=_days_ago(22) + timedelta(days=15),
            currency="USD",
            total_amount=Decimal("5755.00"),
            status=InvoiceStatus.approved,
            source_channel=SourceChannel.manual,
        )
        db.add(inv_ap2)
        db.flush()
        _make_inv_lines(inv_ap2.id, "PO-2024-004")
        invoices.append(inv_ap2)

        # --- 1 posted invoice ---
        inv_posted = Invoice(
            invoice_number="INV-Z-001",
            vendor_id=vendors["V-002"].id,
            invoice_date=_days_ago(35),
            due_date=_days_ago(35) + timedelta(days=45),
            currency="USD",
            total_amount=Decimal("10400.00"),
            status=InvoiceStatus.posted,
            source_channel=SourceChannel.email,
        )
        db.add(inv_posted)
        db.flush()
        _make_inv_lines(inv_posted.id, "PO-2024-002")
        invoices.append(inv_posted)

        db.flush()
        print(f"  Created {len(invoices)} invoices with line items")

        # ── Match Results ──────────────────────────────────────────────
        # Exception invoice 1 — 2-way partial match (amount variance)
        db.add(MatchResult(
            invoice_id=inv_exc1.id,
            match_type=MatchType.two_way,
            match_status=MatchStatus.partial,
            overall_score=33.3,
            details={"lines": [{"line": 1, "status": "amount_variance"}]},
            matched_po_id=purchase_orders["PO-2024-001"].id,
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Exception invoice 2 — unmatched (missing PO)
        db.add(MatchResult(
            invoice_id=inv_exc2.id,
            match_type=MatchType.two_way,
            match_status=MatchStatus.unmatched,
            overall_score=0.0,
            details={"reason": "No PO references on invoice line items"},
            tolerance_applied=False,
        ))

        # Exception invoice 3 — 3-way partial (qty variance vs GRN)
        db.add(MatchResult(
            invoice_id=inv_exc3.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.partial,
            overall_score=66.7,
            details={"lines": [{"line": 1, "status": "partial_delivery_overrun"}]},
            matched_po_id=purchase_orders["PO-2024-003"].id,
            matched_grn_ids=[str(grn3.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Pending-approval invoice 1 — 2-way matched
        db.add(MatchResult(
            invoice_id=inv_pa1.id,
            match_type=MatchType.two_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2024-002"].id,
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Pending-approval invoice 2 — 3-way matched (PO-005 has GRN)
        db.add(MatchResult(
            invoice_id=inv_pa2.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.tolerance_passed,
            overall_score=100.0,
            details={"lines": [{"line": i, "status": "matched"} for i in range(1, 5)]},
            matched_po_id=purchase_orders["PO-2024-005"].id,
            matched_grn_ids=[str(grn2.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Approved invoice 1 — 3-way matched (PO-001 has GRN)
        db.add(MatchResult(
            invoice_id=inv_ap1.id,
            match_type=MatchType.three_way,
            match_status=MatchStatus.tolerance_passed,
            overall_score=100.0,
            details={"lines": [{"line": i, "status": "matched"} for i in range(1, 4)]},
            matched_po_id=purchase_orders["PO-2024-001"].id,
            matched_grn_ids=[str(grn1.id)],
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Approved invoice 2 — 2-way matched
        db.add(MatchResult(
            invoice_id=inv_ap2.id,
            match_type=MatchType.two_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2024-004"].id,
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        # Posted invoice — 2-way matched
        db.add(MatchResult(
            invoice_id=inv_posted.id,
            match_type=MatchType.two_way,
            match_status=MatchStatus.matched,
            overall_score=100.0,
            details={"lines": [{"line": 1, "status": "matched"}, {"line": 2, "status": "matched"}]},
            matched_po_id=purchase_orders["PO-2024-002"].id,
            tolerance_applied=True,
            tolerance_config_id=tol.id,
        ))

        db.flush()
        print("  Created match results")

        # ── Exceptions ─────────────────────────────────────────────────
        db.add(Exception_(
            invoice_id=inv_exc1.id,
            exception_type=ExceptionType.amount_variance,
            severity=ExceptionSeverity.medium,
            status=ExceptionStatus.assigned,
            assigned_to=users["analyst"].id,
            ai_suggested_resolution="Review vendor pricing against PO terms. The 8% variance exceeds the 5% tolerance. Request a credit memo or negotiate revised pricing.",
            ai_severity_reasoning="Medium severity: amount variance is above tolerance but below $500 absolute difference per line.",
        ))
        db.add(Exception_(
            invoice_id=inv_exc2.id,
            exception_type=ExceptionType.missing_po,
            severity=ExceptionSeverity.high,
            status=ExceptionStatus.open,
            ai_suggested_resolution="Contact the requesting department to obtain a retroactive PO or process as a non-PO invoice with appropriate approvals.",
            ai_severity_reasoning="High severity: invoice has no purchase order reference, requiring manual review and approval.",
        ))
        db.add(Exception_(
            invoice_id=inv_exc3.id,
            exception_type=ExceptionType.partial_delivery_overrun,
            severity=ExceptionSeverity.medium,
            status=ExceptionStatus.assigned,
            assigned_to=users["analyst"].id,
            ai_suggested_resolution="Invoice quantity exceeds goods received. Hold payment until remaining goods are received or request vendor to issue a corrected invoice for received quantities only.",
            ai_severity_reasoning="Medium severity: quantity invoiced exceeds quantity received by ~20%, indicating partial delivery.",
        ))
        db.add(Exception_(
            invoice_id=inv_exc1.id,
            exception_type=ExceptionType.duplicate_invoice,
            severity=ExceptionSeverity.low,
            status=ExceptionStatus.open,
            ai_suggested_resolution="Compare with previously processed invoices for the same vendor and PO. If confirmed duplicate, reject and notify vendor.",
            ai_severity_reasoning="Low severity: potential duplicate flagged by system, requires verification.",
        ))
        db.flush()
        print("  Created exceptions")

        # ── Approval Tasks ─────────────────────────────────────────────
        db.add(ApprovalTask(
            invoice_id=inv_pa1.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.pending,
            ai_recommendation=AIRecommendation.approve,
            ai_recommendation_reason="Invoice matches PO-2024-002 at 100% score. Vendor TechParts Ltd has a clean history with 0 exceptions. Amount ($10,400) is within normal range for this vendor. Recommend approval.",
        ))
        db.add(ApprovalTask(
            invoice_id=inv_pa2.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.pending,
            ai_recommendation=AIRecommendation.review,
            ai_recommendation_reason="Invoice matches PO-2024-005 via 3-way match (tolerance passed). Vendor Steel Works Ltd is flagged high-risk. Amount ($12,600) is above $10k threshold. Recommend careful review before approval.",
        ))
        # Approved task for posted invoice
        db.add(ApprovalTask(
            invoice_id=inv_posted.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.approved,
            decision_at=_hours_ago(72),
            comments="Verified against PO. All good.",
        ))
        # Approved tasks for approved invoices
        db.add(ApprovalTask(
            invoice_id=inv_ap1.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.approved,
            decision_at=_hours_ago(48),
            ai_recommendation=AIRecommendation.approve,
        ))
        db.add(ApprovalTask(
            invoice_id=inv_ap2.id,
            approver_id=users["approver"].id,
            approval_level=1,
            approval_order=1,
            status=ApprovalStatus.approved,
            decision_at=_hours_ago(36),
        ))
        db.flush()
        print("  Created approval tasks")

        # ── Audit Logs ─────────────────────────────────────────────────
        audit_entries = [
            ("invoice", inv_posted.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 200),
            ("invoice", inv_posted.id, "ocr_extracted", ActorType.ai_agent, None, "Claude AI", 195),
            ("invoice", inv_posted.id, "matched", ActorType.system, None, "System", 190),
            ("invoice", inv_posted.id, "approved", ActorType.user, users["approver"].id, "Sarah Kim", 180),
            ("invoice", inv_posted.id, "posted", ActorType.system, None, "System", 170),
            ("vendor", vendors["V-001"].id, "created", ActorType.user, users["admin"].id, "Kyle Stevens", 300),
            ("vendor", vendors["V-007"].id, "status_changed", ActorType.user, users["admin"].id, "Kyle Stevens", 100),
            ("invoice", inv_pa1.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 160),
            ("invoice", inv_pa1.id, "matched", ActorType.system, None, "System", 155),
            ("exception", inv_exc1.id, "created", ActorType.system, None, "System", 150),
            ("exception", inv_exc2.id, "created", ActorType.system, None, "System", 145),
            ("invoice", inv_ap1.id, "approved", ActorType.user, users["approver"].id, "Sarah Kim", 100),
            ("invoice", inv_exc3.id, "created", ActorType.user, users["clerk"].id, "Maria Garcia", 90),
            ("invoice", inv_exc3.id, "matched", ActorType.system, None, "System", 85),
            ("exception", inv_exc3.id, "created", ActorType.system, None, "System", 80),
            ("vendor", vendors["V-003"].id, "risk_level_changed", ActorType.user, users["admin"].id, "Kyle Stevens", 60),
            ("approval", inv_pa2.id, "ai_recommendation", ActorType.ai_agent, None, "Claude AI", 50),
            ("invoice", inv_ap2.id, "approved", ActorType.user, users["approver"].id, "Sarah Kim", 40),
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
            title="Invoice INV-A-001 Pending Approval",
            message="Invoice INV-A-001 from TechParts Ltd ($10,400.00) requires your approval. AI recommends: Approve.",
            related_entity_type="invoice",
            related_entity_id=inv_pa1.id,
            is_read=False,
        ))
        db.add(Notification(
            user_id=users["approver"].id,
            type=NotificationType.approval_request,
            title="Invoice INV-A-002 Pending Approval",
            message="Invoice INV-A-002 from Steel Works Ltd ($12,600.00) requires your approval. AI recommends: Review carefully.",
            related_entity_type="invoice",
            related_entity_id=inv_pa2.id,
            is_read=False,
        ))
        db.add(Notification(
            user_id=users["analyst"].id,
            type=NotificationType.exception_assigned,
            title="Exception Assigned: Amount Variance",
            message="An amount variance exception for INV-X-001 (Acme Corp) has been assigned to you.",
            related_entity_type="exception",
            related_entity_id=inv_exc1.id,
            is_read=False,
        ))
        db.add(Notification(
            user_id=users["admin"].id,
            type=NotificationType.system,
            title="System Health Check",
            message="All services are running normally. 15 invoices processed this period.",
            is_read=True,
        ))
        db.flush()
        print("  Created notifications")

        # ── Commit ─────────────────────────────────────────────────────
        db.commit()
        print("\nSeed complete!")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
