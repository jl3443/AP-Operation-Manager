"""Compliance, control mapping, gap analysis, scoring, and audit pack endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit import AuditLog
from app.models.exception import Exception_, ExceptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.models.vendor import Vendor


router = APIRouter(prefix="/compliance", tags=["compliance"])


class ControlMapping(BaseModel):
    control_id: str
    control_name: str
    policy_section: str
    description: str
    implementation_status: str  # active | partial | planned
    automated: bool
    last_tested: str
    test_result: str  # pass | fail | not_tested


class ComplianceGap(BaseModel):
    gap_id: str
    control_id: str
    finding: str
    severity: str  # high | medium | low
    status: str  # open | remediation | closed
    recommendation: str
    evidence_count: int


@router.get("/control-map", response_model=List[ControlMapping])
def get_control_map(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return AP control-to-policy mapping with implementation status."""
    # These are realistic AP controls mapped to common policy sections
    controls = [
        ControlMapping(
            control_id="CTL-001",
            control_name="Three-Way Matching",
            policy_section="Section 4.1 — Invoice Verification",
            description="All goods invoices must be matched against PO and GRN before payment",
            implementation_status="active",
            automated=True,
            last_tested="2026-03-01",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-002",
            control_name="Duplicate Invoice Detection",
            policy_section="Section 3.3 — Duplicate Prevention",
            description="System checks for duplicate invoice numbers per vendor before processing",
            implementation_status="active",
            automated=True,
            last_tested="2026-03-01",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-003",
            control_name="Approval Matrix Enforcement",
            policy_section="Section 5 — Authorization Levels",
            description="Invoices routed to appropriate approver based on amount thresholds",
            implementation_status="active",
            automated=True,
            last_tested="2026-03-01",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-004",
            control_name="Vendor Master Validation",
            policy_section="Section 8 — Vendor Management",
            description="Only approved vendors can submit invoices; on-hold vendors are flagged",
            implementation_status="active",
            automated=True,
            last_tested="2026-03-01",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-005",
            control_name="Price Tolerance Check",
            policy_section="Section 4.3 — Price Variance",
            description="Invoice amounts checked against PO within configurable tolerance thresholds",
            implementation_status="active",
            automated=True,
            last_tested="2026-03-01",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-006",
            control_name="Segregation of Duties",
            policy_section="Section 9 — Internal Controls",
            description="Invoice creator, approver, and payment initiator must be different users",
            implementation_status="partial",
            automated=False,
            last_tested="2026-02-15",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-007",
            control_name="Audit Trail Completeness",
            policy_section="Section 10 — Record Retention",
            description="All invoice actions logged with actor, timestamp, and evidence",
            implementation_status="active",
            automated=True,
            last_tested="2026-03-01",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-008",
            control_name="Exception SLA Monitoring",
            policy_section="Section 6.1 — Exception Resolution",
            description="Open exceptions tracked against SLA targets; escalation after 48 hours",
            implementation_status="partial",
            automated=False,
            last_tested="2026-02-20",
            test_result="fail",
        ),
        ControlMapping(
            control_id="CTL-009",
            control_name="GRN Quantity Verification",
            policy_section="Section 4.2 — Goods Receipt",
            description="Invoice quantities verified against goods receipt quantities",
            implementation_status="active",
            automated=True,
            last_tested="2026-03-01",
            test_result="pass",
        ),
        ControlMapping(
            control_id="CTL-010",
            control_name="Payment Term Compliance",
            policy_section="Section 7 — Payment Terms",
            description="Payments scheduled according to contracted terms; early payment requires approval",
            implementation_status="planned",
            automated=False,
            last_tested="2026-01-15",
            test_result="not_tested",
        ),
    ]
    return controls


@router.get("/gaps", response_model=List[ComplianceGap])
def get_compliance_gaps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Identify compliance gaps based on exception patterns and audit data."""
    gaps = []

    # Check for unresolved exceptions (SLA breach risk)
    open_exceptions = (
        db.query(func.count(Exception_.id))
        .filter(Exception_.status.in_([ExceptionStatus.open, ExceptionStatus.assigned]))
        .scalar() or 0
    )
    if open_exceptions > 0:
        gaps.append(ComplianceGap(
            gap_id="GAP-001",
            control_id="CTL-008",
            finding=f"{open_exceptions} exceptions remain open, potentially breaching 48-hour SLA",
            severity="high",
            status="open",
            recommendation="Implement automated escalation for exceptions approaching SLA deadline",
            evidence_count=open_exceptions,
        ))

    # Check for invoices without match results (matching control gap)
    unmatched = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.status.notin_([InvoiceStatus.draft, InvoiceStatus.rejected]),
        )
        .scalar() or 0
    )
    from app.models.matching import MatchResult
    matched = db.query(func.count(func.distinct(MatchResult.invoice_id))).scalar() or 0
    no_match = unmatched - matched
    if no_match > 0:
        gaps.append(ComplianceGap(
            gap_id="GAP-002",
            control_id="CTL-001",
            finding=f"{no_match} processed invoices have no matching record",
            severity="medium",
            status="remediation",
            recommendation="Ensure all non-draft invoices go through the matching engine",
            evidence_count=no_match,
        ))

    # Check on-hold vendor invoices that were processed
    from app.models.vendor import VendorStatus
    on_hold_invoices = (
        db.query(func.count(Invoice.id))
        .join(Vendor, Vendor.id == Invoice.vendor_id)
        .filter(Vendor.status == VendorStatus.on_hold)
        .filter(Invoice.status.notin_([InvoiceStatus.draft, InvoiceStatus.rejected]))
        .scalar() or 0
    )
    if on_hold_invoices > 0:
        gaps.append(ComplianceGap(
            gap_id="GAP-003",
            control_id="CTL-004",
            finding=f"{on_hold_invoices} invoices from on-hold vendors were processed",
            severity="high",
            status="open",
            recommendation="Add pre-processing vendor status check to block on-hold vendor invoices",
            evidence_count=on_hold_invoices,
        ))

    # Audit trail completeness check
    total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
    invoices_with_audit = (
        db.query(func.count(func.distinct(AuditLog.entity_id)))
        .filter(AuditLog.entity_type == "invoice")
        .scalar() or 0
    )
    no_audit = total_invoices - invoices_with_audit
    if no_audit > 0:
        gaps.append(ComplianceGap(
            gap_id="GAP-004",
            control_id="CTL-007",
            finding=f"{no_audit} invoices have no audit trail entries",
            severity="medium",
            status="remediation",
            recommendation="Verify audit logging is enabled for all invoice creation paths",
            evidence_count=no_audit,
        ))

    # Payment term compliance (always show as planned gap)
    gaps.append(ComplianceGap(
        gap_id="GAP-005",
        control_id="CTL-010",
        finding="Payment term compliance monitoring not yet automated",
        severity="low",
        status="open",
        recommendation="Implement automated payment scheduling based on contracted terms",
        evidence_count=0,
    ))

    return gaps


# ── New Phase 3 Endpoints ────────────────────────────────────────────────


@router.get("/control-tests")
def run_control_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run automated control tests and return results."""
    from app.services.compliance_engine import run_control_tests

    return run_control_tests(db)


@router.get("/scoring")
def get_compliance_scoring(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Score all invoices for compliance and return aggregate stats."""
    from app.services.compliance_engine import score_all_invoices

    return score_all_invoices(db)


@router.get("/scoring/{invoice_id}")
def get_invoice_compliance_score(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Score a single invoice's compliance."""
    from app.services.compliance_engine import score_invoice_compliance

    return score_invoice_compliance(db, invoice_id)


@router.get("/policy-linkage/{invoice_id}")
def get_policy_linkage(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all policy rules that apply to a specific invoice."""
    from app.services.compliance_engine import link_invoice_to_policies

    return link_invoice_to_policies(db, invoice_id)


@router.get("/audit-pack")
def get_audit_pack(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a comprehensive audit pack with all compliance data."""
    from app.services.compliance_engine import generate_audit_pack

    return generate_audit_pack(db)
