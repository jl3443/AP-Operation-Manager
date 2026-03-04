"""AI Exception Resolver — generates structured Resolution Plans using Claude."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.audit import ActorType
from app.models.exception import Exception_
from app.models.goods_receipt import GoodsReceipt, GRNLineItem
from app.models.invoice import Invoice, InvoiceLineItem
from app.models.matching import MatchResult
from app.models.purchase_order import POLineItem, PurchaseOrder
from app.models.resolution import (
    ActionStatus,
    AutomationAction,
    AutomationLevel,
    PlanStatus,
    ResolutionPlan,
)
from app.models.vendor import Vendor
from app.services import audit_service
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for generating resolution plans
# ---------------------------------------------------------------------------

RESOLVER_SYSTEM_PROMPT = """\
You are an expert Accounts Payable exception resolution engine.

Given exception context, produce a structured JSON resolution plan.

Return ONLY a JSON object (no markdown, no code fences):
{
  "exception_type": "<snake_case type>",
  "diagnosis": "<1-3 sentence explanation of what happened and why, citing evidence>",
  "confidence": <0.0-1.0>,
  "automation_level": "auto" | "assisted" | "manual",
  "resolution_steps": [
    {
      "step_id": "S1",
      "action_type": "<ACTION_TYPE>",
      "params": { ... },
      "requires_human_approval": true|false,
      "risk": "low" | "medium" | "high",
      "expected_result": "<what this step produces>"
    }
  ],
  "recheck_strategy": {
    "trigger": "<condition to rerun match>"
  },
  "audit_evidence": [
    { "source": "<table/field>", "field": "<column>", "value": "<current value>" }
  ]
}

AVAILABLE ACTION TYPES (use ONLY these):
- GENERATE_EXPLANATION: Generate human-readable variance explanation (good first step)
- COMPARE_LINE_ITEMS: Detailed line-by-line comparison between invoice and PO
- CHECK_TOLERANCE: Look up tolerance config and evaluate if variance is within bounds
- CALCULATE_VARIANCE_BREAKDOWN: Structured breakdown of variance by category (subtotal, tax, freight, discount)
- RECALCULATE_INVOICE_TOTAL: Recompute total from line items
- RECALC_LINE_TOTALS: Recalculate line totals from qty * unit_price
- RECALC_TAX: Deterministic tax recalculation
- SEARCH_PO_CANDIDATES: Find POs by vendor, amount, date range
- AUTO_LINK_PO: Attempt to auto-link invoice line items to PO lines
- CHECK_GRN_STATUS: Query GRN records for PO
- VERIFY_VENDOR_DETAILS: Cross-check vendor details between invoice and vendor master
- SUGGEST_VENDOR_ALIAS: Suggest vendor alias mapping from invoice text
- LINK_INVOICE_VENDOR: Link invoice to a specific vendor_id
- CHECK_VENDOR_COMPLIANCE: Check vendor status and compliance docs
- FIND_POSSIBLE_DUPLICATES: Find duplicate invoices
- LOCK_INVOICE_FOR_PAYMENT: Prevent invoice from entering payment
- DRAFT_VENDOR_EMAIL: Generate email draft for vendor communication (requires_human_approval=true)
- DRAFT_INTERNAL_MESSAGE: Generate message for internal team
- CREATE_HUMAN_TASK: Create task for a team (warehouse/procurement/finance)
- REASSIGN_EXCEPTION: Route exception to different queue/user
- ESCALATE_TO_MANAGER: Escalate exception to AP manager
- LOOKUP_POLICY_RULES: Query policy rules for vendor/category
- PROPOSE_AUTO_RESOLVE: Evaluate if exception can be auto-resolved via tolerance
- CLOSE_EXCEPTION: Resolve exception and advance invoice
- PROCEED_TO_APPROVAL: Move invoice to approval workflow
- FETCH_FX_RATE: Look up exchange rate
- CONVERT_AMOUNTS: Normalize amounts to base currency
- NORMALIZE_UOM: Unit-of-measure conversion (e.g., box=10ea)
- RERUN_OCR: Re-extract invoice from PDF
- RERUN_MATCH: Trigger 2-way or 3-way matching
- PATCH_INVOICE_FIELDS: Update specific invoice fields (requires_human_approval=true)
- PROPOSE_TERMS_OVERRIDE: Suggest payment terms correction
- CREATE_WAIT_TIMER: Set timeout for expected event
- WAIT_FOR_REPLY: Pause execution until manual trigger
- SUMMARIZE_FINDINGS: AI summary of all completed steps (use as final step)

PLAYBOOK GUIDELINES BY EXCEPTION TYPE:

1. missing_po: Search PO candidates → Auto-link PO (if found) → Compare line items → Draft vendor email (if not found) → Rerun match
2. amount_variance (within tolerance): Compare line items → Check tolerance → Generate explanation → Propose auto-resolve → Close exception
3. amount_variance (outside tolerance): Compare line items → Calculate variance breakdown → Recalculate total → Draft vendor email → Rerun match
4. contract_price_variance: Compare line items → Calculate variance breakdown → Normalize UOM or draft clarification email → Rerun match
5. quantity_variance: Check GRN status → Compare line items → Draft internal message to warehouse → Rerun match
6. vendor_mismatch: Verify vendor details → Suggest vendor alias → human confirms → Link vendor → Rerun match
7. duplicate_invoice: Find duplicates → Lock for payment → Create review task → Draft credit memo email
8. tax_variance: Recalc tax → Calculate variance breakdown → Generate explanation → Check tolerance → Draft vendor email or auto-resolve
9. currency_variance: Fetch FX rate → Convert amounts → Compare line items → Rerun match
10. partial_delivery_overrun: Check GRN status → Compare line items → Draft internal message → Create wait timer
11. expired_po: Lookup policy rules → Propose terms override → Draft vendor email → Escalate to manager
12. vendor_on_hold: Check vendor compliance → Verify vendor details → Draft vendor email → Reassign to vendor enablement

RULES:
- Use the minimum number of steps needed
- Always end with RERUN_MATCH when the resolution should re-trigger matching
- External communications (emails) always require human approval
- Internal reassignments and lookups do NOT require human approval
- For amount/tax calculations, use deterministic actions (RECALCULATE/RECALC_TAX), not AI
- automation_level: "auto" only if NO steps need human approval; "assisted" if some do; "manual" if all do
"""


def _build_resolver_context(db: Session, exception: Exception_) -> str:
    """Build rich context for Claude to generate a resolution plan."""
    invoice = db.query(Invoice).options(
        joinedload(Invoice.line_items)
    ).filter(Invoice.id == exception.invoice_id).first()

    vendor = db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first() if invoice else None

    # Match result
    match = (
        db.query(MatchResult)
        .filter(MatchResult.invoice_id == exception.invoice_id)
        .order_by(MatchResult.created_at.desc())
        .first()
    )

    # PO data
    po_info = "No PO linked."
    po = None
    if match and match.matched_po_id:
        po = db.query(PurchaseOrder).options(
            joinedload(PurchaseOrder.line_items)
        ).filter(PurchaseOrder.id == match.matched_po_id).first()
    if not po and invoice:
        # Try to find PO via line items
        po_line_ids = [li.po_line_id for li in invoice.line_items if li.po_line_id]
        if po_line_ids:
            po_line = db.query(POLineItem).filter(POLineItem.id == po_line_ids[0]).first()
            if po_line:
                po = db.query(PurchaseOrder).options(
                    joinedload(PurchaseOrder.line_items)
                ).filter(PurchaseOrder.id == po_line.po_id).first()

    if po:
        po_lines_str = "\n".join(
            f"  Line {pl.line_number}: {pl.description} | Qty: {pl.quantity_ordered} | "
            f"Unit: ${float(pl.unit_price):,.2f} | Total: ${float(pl.line_total):,.2f}"
            for pl in po.line_items
        )
        po_info = (
            f"PO: {po.po_number} | Status: {po.status.value} | "
            f"Total: ${float(po.total_amount):,.2f} | Currency: {po.currency}\n"
            f"PO Lines:\n{po_lines_str}"
        )

    # GRN data
    grn_info = "No GRN records."
    if po:
        grns = db.query(GoodsReceipt).filter(GoodsReceipt.po_id == po.id).all()
        if grns:
            grn_parts = []
            for grn in grns:
                grn_lines = db.query(GRNLineItem).filter(GRNLineItem.grn_id == grn.id).all()
                lines_str = ", ".join(
                    f"Qty received: {gl.quantity_received}" for gl in grn_lines
                )
                grn_parts.append(f"GRN {grn.grn_number} ({grn.receipt_date}): {lines_str}")
            grn_info = "\n".join(grn_parts)

    # Invoice line items
    inv_lines_str = "No line items."
    if invoice and invoice.line_items:
        inv_lines_str = "\n".join(
            f"  Line {li.line_number}: {li.description} | Qty: {float(li.quantity)} | "
            f"Unit: ${float(li.unit_price):,.2f} | Total: ${float(li.line_total):,.2f} | "
            f"PO Line linked: {'Yes' if li.po_line_id else 'No'}"
            for li in invoice.line_items
        )

    # Match details
    match_info = "No match result."
    if match:
        match_info = (
            f"Match type: {match.match_type.value} | Status: {match.match_status.value} | "
            f"Score: {match.overall_score:.1f}%\n"
            f"Details: {match.details}"
        )

    vendor_info = "Unknown vendor"
    if vendor:
        vendor_info = (
            f"{vendor.name} ({vendor.vendor_code}) | Status: {vendor.status.value} | "
            f"Risk: {vendor.risk_level.value} | Payment terms: {vendor.payment_terms_code or 'N/A'}"
        )

    return (
        f"=== EXCEPTION ===\n"
        f"Type: {exception.exception_type.value}\n"
        f"Severity: {exception.severity.value}\n"
        f"Status: {exception.status.value}\n"
        f"AI suggested resolution: {exception.ai_suggested_resolution or 'None'}\n\n"
        f"=== INVOICE ===\n"
        f"Number: {invoice.invoice_number if invoice else 'N/A'}\n"
        f"Amount: {invoice.currency} {float(invoice.total_amount):,.2f}\n"
        f"Tax: ${float(invoice.tax_amount):,.2f}\n"
        f"Date: {invoice.invoice_date} | Due: {invoice.due_date}\n"
        f"Status: {invoice.status.value}\n"
        f"Invoice Lines:\n{inv_lines_str}\n\n"
        f"=== VENDOR ===\n{vendor_info}\n\n"
        f"=== PURCHASE ORDER ===\n{po_info}\n\n"
        f"=== GOODS RECEIPTS ===\n{grn_info}\n\n"
        f"=== MATCH RESULT ===\n{match_info}"
    )


def generate_resolution_plan(db: Session, exception_id: uuid.UUID) -> ResolutionPlan:
    """Generate an AI-powered resolution plan for an exception.

    Calls Claude to produce a structured Action Plan, then persists it as
    ResolutionPlan + AutomationAction records.
    """
    exception = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not exception:
        raise ValueError(f"Exception {exception_id} not found")

    context = _build_resolver_context(db, exception)

    # Call Claude
    if not ai_service.available:
        raise RuntimeError("AI service is not available (no API key configured)")

    raw = ai_service.call_claude(
        system_prompt=RESOLVER_SYSTEM_PROMPT,
        user_message=context,
        max_tokens=4096,
    )

    if not raw:
        raise RuntimeError("Claude returned empty response for resolution plan")

    parsed = ai_service.extract_json(raw)
    if not parsed:
        raise RuntimeError(f"Could not parse Claude response as JSON: {raw[:200]}")

    # Map automation level
    level_map = {
        "auto": AutomationLevel.auto,
        "assisted": AutomationLevel.assisted,
        "manual": AutomationLevel.manual,
    }
    automation_level = level_map.get(
        parsed.get("automation_level", "assisted"), AutomationLevel.assisted
    )

    # Create plan
    plan = ResolutionPlan(
        exception_id=exception_id,
        plan_json=parsed,
        status=PlanStatus.draft,
        automation_level=automation_level,
        confidence=parsed.get("confidence"),
        diagnosis=parsed.get("diagnosis"),
        recheck_strategy=parsed.get("recheck_strategy"),
        audit_evidence=parsed.get("audit_evidence"),
    )
    db.add(plan)
    db.flush()

    # Create actions from resolution_steps
    for step in parsed.get("resolution_steps", []):
        action = AutomationAction(
            plan_id=plan.id,
            step_id=step.get("step_id", "S0"),
            action_type=step.get("action_type", "UNKNOWN"),
            params_json=step.get("params"),
            status=ActionStatus.pending,
            requires_human_approval=step.get("requires_human_approval", False),
            risk=step.get("risk"),
            expected_result=step.get("expected_result"),
        )
        db.add(action)

    db.commit()
    db.refresh(plan)

    # Audit log
    audit_service.log_action(
        db,
        entity_type="resolution_plan",
        entity_id=plan.id,
        action="plan_generated",
        actor_type=ActorType.ai_agent,
        actor_name="AI Exception Resolver",
        evidence={
            "exception_id": str(exception_id),
            "exception_type": exception.exception_type.value,
            "confidence": plan.confidence,
            "automation_level": plan.automation_level.value,
            "steps_count": len(plan.actions),
        },
    )
    db.commit()

    return plan
