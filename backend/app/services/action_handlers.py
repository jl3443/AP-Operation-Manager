"""Action handler registry for the Resolution Orchestrator.

Each handler takes (db, action) and returns a result_json dict.
Handlers reuse existing services where possible.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Callable

from sqlalchemy.orm import Session, joinedload

from app.models.config import ExchangeRate, PolicyRule, ToleranceConfig
from app.models.exception import Exception_, ExceptionStatus, ResolutionType
from app.models.goods_receipt import GoodsReceipt, GRNLineItem
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.matching import MatchResult
from app.models.purchase_order import POLineItem, PurchaseOrder
from app.models.resolution import AutomationAction
from app.models.vendor import Vendor
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Handler type
# ---------------------------------------------------------------------------
HandlerFn = Callable[[Session, AutomationAction], dict[str, Any]]
_HANDLERS: dict[str, HandlerFn] = {}


def register(action_type: str):
    """Decorator to register a handler for an action_type."""
    def decorator(fn: HandlerFn) -> HandlerFn:
        _HANDLERS[action_type] = fn
        return fn
    return decorator


def get_handler(action_type: str) -> HandlerFn | None:
    return _HANDLERS.get(action_type)


def run_handler_safe(db: Session, action) -> tuple[dict[str, Any] | None, str | None]:
    """Execute the handler for *action* with full error isolation.

    Returns ``(result_dict, None)`` on success or ``(None, error_str)`` on failure.
    If the action_type has no registered handler a generic fallback is used so
    execution never fails due to a missing handler.
    """
    handler = get_handler(action.action_type)
    if handler is None:
        # Generic fallback — record what was requested so the user can see it
        return _fallback_handler(db, action), None

    try:
        result = handler(db, action)
        return result, None
    except Exception as exc:
        logger.exception("Handler %s raised: %s", action.action_type, exc)
        return None, f"{action.action_type} error: {exc}"


def _fallback_handler(db: Session, action) -> dict[str, Any]:
    """Best-effort handler for action types with no dedicated implementation."""
    logger.info(
        "No handler for %s — using generic fallback (step %s)",
        action.action_type,
        action.step_id,
    )
    return {
        "action_type": action.action_type,
        "status": "completed_via_fallback",
        "params_received": action.params_json or {},
        "expected_result": action.expected_result or "N/A",
        "note": f"No dedicated handler for '{action.action_type}'. "
                "Step recorded; manual follow-up may be needed.",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_exception_and_invoice(db: Session, action: AutomationAction):
    """Walk action → plan → exception → invoice."""
    from app.models.resolution import ResolutionPlan
    plan = db.query(ResolutionPlan).filter(ResolutionPlan.id == action.plan_id).first()
    exc = db.query(Exception_).filter(Exception_.id == plan.exception_id).first() if plan else None
    inv = db.query(Invoice).options(joinedload(Invoice.line_items)).filter(
        Invoice.id == exc.invoice_id
    ).first() if exc else None
    return exc, inv


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

@register("SEARCH_PO_CANDIDATES")
def handle_search_po_candidates(db: Session, action: AutomationAction) -> dict:
    """Find PO candidates by vendor, amount, date. Reuses auto_link_po_lines logic."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found", "candidates": []}

    params = action.params_json or {}
    vendor_id = inv.vendor_id

    candidate_pos = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.line_items))
        .filter(PurchaseOrder.vendor_id == vendor_id)
        .all()
    )

    scored = []
    for po in candidate_pos:
        po_total = float(po.total_amount)
        inv_total = float(inv.total_amount)
        if max(po_total, inv_total) > 0:
            diff_ratio = abs(inv_total - po_total) / max(po_total, inv_total)
            amount_score = max(0, 1.0 - diff_ratio)
        else:
            amount_score = 0.0
        line_score = 1.0 if len(po.line_items) == len(inv.line_items) else 0.5
        combined = amount_score * 0.7 + line_score * 0.3

        scored.append({
            "po_id": str(po.id),
            "po_number": po.po_number,
            "total_amount": po_total,
            "currency": po.currency,
            "status": po.status.value,
            "line_count": len(po.line_items),
            "match_score": round(combined, 3),
            "amount_similarity": round(amount_score, 3),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return {"candidates": scored[:5], "vendor_id": str(vendor_id)}


@register("FIND_POSSIBLE_DUPLICATES")
def handle_find_duplicates(db: Session, action: AutomationAction) -> dict:
    """Find possible duplicate invoices. Reuses duplicate_detection patterns."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found", "duplicates": []}

    from app.services.duplicate_detection import check_duplicate
    result = check_duplicate(
        db,
        invoice_number=inv.invoice_number,
        vendor_id=str(inv.vendor_id),
        total_amount=float(inv.total_amount),
        invoice_date=inv.invoice_date,
        exclude_invoice_id=str(inv.id),
    )
    return {
        "duplicates": result.get("matches", []),
        "is_duplicate": result.get("is_duplicate", False),
        "confidence": result.get("confidence", 0.0),
        "invoice_id": str(inv.id),
    }


@register("RERUN_MATCH")
def handle_rerun_match(db: Session, action: AutomationAction) -> dict:
    """Trigger 2-way or 3-way matching. Reuses match_service."""
    from app.models.goods_receipt import GRNLineItem
    from sqlalchemy import func

    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    from app.services.match_service import auto_link_po_lines, run_three_way_match, run_two_way_match

    # Auto-link first
    link_result = auto_link_po_lines(db, inv.id)
    db.refresh(inv)
    for li in inv.line_items:
        db.refresh(li)

    po_line_ids = [li.po_line_id for li in inv.line_items if li.po_line_id]
    use_three_way = False
    if po_line_ids:
        grn_count = db.query(func.count(GRNLineItem.id)).filter(
            GRNLineItem.po_line_id.in_(po_line_ids)
        ).scalar() or 0
        use_three_way = grn_count > 0

    if use_three_way:
        result = run_three_way_match(db, inv.id)
    else:
        result = run_two_way_match(db, inv.id)

    # If match passed, close exception
    if result.match_status.value in ("matched", "tolerance_passed"):
        if exc:
            exc.status = ExceptionStatus.resolved
            exc.resolution_type = ResolutionType.auto_resolved
            exc.resolution_notes = f"Auto-resolved after rerun match (score: {result.overall_score}%)"
            exc.resolved_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "match_status": result.match_status.value,
        "overall_score": result.overall_score,
        "match_type": result.match_type.value,
        "po_link": link_result,
        "exception_resolved": result.match_status.value in ("matched", "tolerance_passed"),
    }


@register("DRAFT_VENDOR_EMAIL")
def handle_draft_vendor_email(db: Session, action: AutomationAction) -> dict:
    """Generate an email draft using Claude. Does NOT send."""
    exc, inv = _get_exception_and_invoice(db, action)
    params = action.params_json or {}

    vendor = db.query(Vendor).filter(Vendor.id == inv.vendor_id).first() if inv else None
    vendor_name = vendor.name if vendor else "Vendor"

    subject = params.get("subject", f"Inquiry regarding Invoice {inv.invoice_number if inv else 'N/A'}")

    prompt = (
        f"Draft a professional AP department email.\n"
        f"Vendor: {vendor_name}\n"
        f"Invoice: {inv.invoice_number if inv else 'N/A'}\n"
        f"Amount: {inv.currency} {float(inv.total_amount):,.2f}\n"
        f"Exception: {exc.exception_type.value if exc else 'unknown'}\n"
        f"Subject: {subject}\n"
        f"Purpose: {params.get('purpose', 'Request clarification or correction')}\n\n"
        f"Write a concise, professional email body (no greeting/signature). 3-5 sentences."
    )

    body = ai_service.call_claude(
        system_prompt="You write professional AP department emails. Return only the email body text, no subject line or greeting.",
        user_message=prompt,
        max_tokens=512,
    ) or params.get("body", "")

    return {
        "to": params.get("to", f"ap@{vendor_name.lower().replace(' ', '')}.com"),
        "subject": subject,
        "body": body,
        "vendor_name": vendor_name,
        "status": "draft_ready",
    }


@register("DRAFT_INTERNAL_MESSAGE")
def handle_draft_internal_message(db: Session, action: AutomationAction) -> dict:
    """Generate an internal message for warehouse/procurement/finance."""
    exc, inv = _get_exception_and_invoice(db, action)
    params = action.params_json or {}

    team = params.get("team", "operations")
    message = ai_service.call_claude(
        system_prompt="You write concise internal messages for AP operations. 2-3 sentences.",
        user_message=(
            f"Write a message to the {team} team about:\n"
            f"Invoice: {inv.invoice_number if inv else 'N/A'}\n"
            f"Exception: {exc.exception_type.value if exc else 'unknown'}\n"
            f"Context: {params.get('context', 'Please review and take action')}"
        ),
        max_tokens=256,
    ) or "Please review the referenced invoice exception."

    return {"team": team, "message": message, "status": "draft_ready"}


@register("GENERATE_EXPLANATION")
def handle_generate_explanation(db: Session, action: AutomationAction) -> dict:
    """Generate a human-readable explanation of a variance."""
    exc, inv = _get_exception_and_invoice(db, action)

    if not inv:
        return {"error": "Invoice not found", "explanation": "Unable to generate explanation."}

    match = db.query(MatchResult).filter(
        MatchResult.invoice_id == inv.id
    ).order_by(MatchResult.created_at.desc()).first()

    explanation = ai_service.call_claude(
        system_prompt="You explain AP variances clearly for finance analysts. 2-4 sentences. Reference specific numbers.",
        user_message=(
            f"Explain this exception:\n"
            f"Type: {exc.exception_type.value if exc else 'unknown'}\n"
            f"Invoice total: ${float(inv.total_amount):,.2f}\n"
            f"Match details: {match.details if match else 'No match'}\n"
            f"Tax: ${float(inv.tax_amount):,.2f}"
        ),
        max_tokens=512,
    ) or "Unable to generate explanation."

    return {"explanation": explanation}


@register("RECALCULATE_INVOICE_TOTAL")
def handle_recalculate_total(db: Session, action: AutomationAction) -> dict:
    """Deterministic recalculation of invoice total from line items."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    lines_total = sum(float(li.line_total) for li in inv.line_items)
    tax = float(inv.tax_amount)
    freight = float(inv.freight_amount)
    discount = float(inv.discount_amount)
    computed = lines_total + tax + freight - discount
    current = float(inv.total_amount)
    diff = abs(computed - current)

    return {
        "lines_subtotal": round(lines_total, 2),
        "tax": round(tax, 2),
        "freight": round(freight, 2),
        "discount": round(discount, 2),
        "computed_total": round(computed, 2),
        "current_total": round(current, 2),
        "difference": round(diff, 2),
        "totals_match": diff < 0.01,
    }


@register("RECALC_TAX")
def handle_recalc_tax(db: Session, action: AutomationAction) -> dict:
    """Deterministic tax recalculation."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    line_tax_total = sum(float(li.tax_amount) for li in inv.line_items if li.tax_amount)
    invoice_tax = float(inv.tax_amount)
    diff = abs(line_tax_total - invoice_tax)

    return {
        "line_items_tax_sum": round(line_tax_total, 2),
        "invoice_tax_amount": round(invoice_tax, 2),
        "difference": round(diff, 2),
        "consistent": diff < 0.01,
    }


@register("PROPOSE_AUTO_RESOLVE")
def handle_propose_auto_resolve(db: Session, action: AutomationAction) -> dict:
    """Evaluate if exception can be auto-resolved."""
    from app.services.auto_resolution import evaluate_exception
    exc, inv = _get_exception_and_invoice(db, action)
    if not exc:
        return {"error": "Exception not found"}
    result = evaluate_exception(db, exc, dry_run=True)
    return result


@register("CLOSE_EXCEPTION")
def handle_close_exception(db: Session, action: AutomationAction) -> dict:
    """Resolve exception and optionally advance invoice."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not exc:
        return {"error": "Exception not found"}

    exc.status = ExceptionStatus.resolved
    exc.resolution_type = ResolutionType.auto_resolved
    exc.resolution_notes = action.params_json.get("reason", "Closed by resolution plan") if action.params_json else "Closed by resolution plan"
    exc.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "resolved", "exception_id": str(exc.id)}


@register("PROCEED_TO_APPROVAL")
def handle_proceed_to_approval(db: Session, action: AutomationAction) -> dict:
    """Move invoice to approval workflow."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    from app.services.approval_service import create_approval_tasks
    inv.status = InvoiceStatus.pending_approval
    db.commit()

    try:
        tasks = create_approval_tasks(db, inv.id)
        db.commit()
        return {"status": "pending_approval", "approval_tasks_created": len(tasks)}
    except Exception as e:
        return {"status": "pending_approval", "note": str(e)}


@register("LOCK_INVOICE_FOR_PAYMENT")
def handle_lock_payment(db: Session, action: AutomationAction) -> dict:
    """Prevent invoice from entering payment."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}
    inv.payment_locked = True
    db.commit()
    return {"locked": True, "invoice_id": str(inv.id)}


@register("CHECK_GRN_STATUS")
def handle_check_grn(db: Session, action: AutomationAction) -> dict:
    """Query GRN records for the PO linked to the invoice."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    po_line_ids = [li.po_line_id for li in inv.line_items if li.po_line_id]
    if not po_line_ids:
        return {"grn_found": False, "message": "No PO lines linked"}

    po_line = db.query(POLineItem).filter(POLineItem.id == po_line_ids[0]).first()
    if not po_line:
        return {"grn_found": False}

    grns = db.query(GoodsReceipt).filter(GoodsReceipt.po_id == po_line.po_id).all()
    grn_list = []
    for grn in grns:
        lines = db.query(GRNLineItem).filter(GRNLineItem.grn_id == grn.id).all()
        grn_list.append({
            "grn_number": grn.grn_number,
            "receipt_date": str(grn.receipt_date),
            "lines": [{"qty_received": float(gl.quantity_received)} for gl in lines],
        })
    return {"grn_found": len(grn_list) > 0, "grn_records": grn_list}


@register("SUGGEST_VENDOR_ALIAS")
def handle_suggest_vendor_alias(db: Session, action: AutomationAction) -> dict:
    """Fuzzy match invoice vendor text to vendor master."""
    params = action.params_json or {}
    search_text = params.get("invoice_vendor_text", "").lower().strip()
    if not search_text:
        return {"error": "No vendor text provided"}

    vendors = db.query(Vendor).all()
    scored = []
    for v in vendors:
        ratio = SequenceMatcher(None, search_text, v.name.lower()).ratio()
        if ratio > 0.4:
            scored.append({
                "vendor_id": str(v.id),
                "vendor_name": v.name,
                "vendor_code": v.vendor_code,
                "similarity": round(ratio, 3),
            })
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return {"suggestions": scored[:5]}


@register("LINK_INVOICE_VENDOR")
def handle_link_vendor(db: Session, action: AutomationAction) -> dict:
    """Link invoice to a vendor_id."""
    exc, inv = _get_exception_and_invoice(db, action)
    params = action.params_json or {}
    vendor_id = params.get("vendor_id")
    if not inv or not vendor_id:
        return {"error": "Missing invoice or vendor_id"}
    inv.vendor_id = uuid.UUID(vendor_id)
    db.commit()
    return {"linked": True, "vendor_id": vendor_id}


@register("CREATE_HUMAN_TASK")
def handle_create_human_task(db: Session, action: AutomationAction) -> dict:
    """Create a task note for human review (stored as exception comment)."""
    from app.models.exception import ExceptionComment
    exc, inv = _get_exception_and_invoice(db, action)
    params = action.params_json or {}

    if exc:
        # Use assigned_to as author if available, otherwise store as system comment
        from app.models.user import User
        system_user = db.query(User).filter(User.role == "admin").first()
        user_id = system_user.id if system_user else exc.id  # fallback to exception id as placeholder

        comment = ExceptionComment(
            exception_id=exc.id,
            user_id=user_id,
            comment_text=f"[AUTO-TASK] {params.get('description', 'Review required')}",
            mentions=params.get("assign_to", []),
        )
        db.add(comment)
        db.commit()
        return {"task_created": True, "description": params.get("description")}
    return {"error": "Exception not found"}


@register("REASSIGN_EXCEPTION")
def handle_reassign(db: Session, action: AutomationAction) -> dict:
    """Route exception to a different queue/user."""
    exc, inv = _get_exception_and_invoice(db, action)
    params = action.params_json or {}
    if not exc:
        return {"error": "Exception not found"}
    exc.status = ExceptionStatus.assigned
    db.commit()
    return {"reassigned": True, "queue": params.get("queue", "default")}


@register("FETCH_FX_RATE")
def handle_fetch_fx_rate(db: Session, action: AutomationAction) -> dict:
    """Look up exchange rate from the ExchangeRate model."""
    params = action.params_json or {}
    from_ccy = params.get("from_currency", "USD")
    to_ccy = params.get("to_currency", "USD")

    rate = (
        db.query(ExchangeRate)
        .filter(ExchangeRate.from_currency == from_ccy, ExchangeRate.to_currency == to_ccy)
        .order_by(ExchangeRate.effective_date.desc())
        .first()
    )
    if rate:
        return {"from": from_ccy, "to": to_ccy, "rate": float(rate.rate), "date": str(rate.effective_date)}
    return {"from": from_ccy, "to": to_ccy, "rate": 1.0, "note": "No rate found, using 1.0"}


@register("CONVERT_AMOUNTS")
def handle_convert_amounts(db: Session, action: AutomationAction) -> dict:
    """Normalize invoice amounts to base currency."""
    exc, inv = _get_exception_and_invoice(db, action)
    params = action.params_json or {}
    rate = params.get("rate", 1.0)
    if not inv:
        return {"error": "Invoice not found"}
    converted_total = round(float(inv.total_amount) * rate, 2)
    return {
        "original_amount": float(inv.total_amount),
        "original_currency": inv.currency,
        "rate": rate,
        "converted_amount": converted_total,
        "target_currency": params.get("target_currency", "USD"),
    }


@register("NORMALIZE_UOM")
def handle_normalize_uom(db: Session, action: AutomationAction) -> dict:
    """Simple UOM conversion mapping."""
    UOM_MAP = {"box": 10, "case": 12, "dozen": 12, "pack": 6, "pair": 2}
    params = action.params_json or {}
    from_uom = params.get("from_uom", "").lower()
    factor = UOM_MAP.get(from_uom, 1)
    return {"from_uom": from_uom, "to_uom": "ea", "conversion_factor": factor}


@register("PATCH_INVOICE_FIELDS")
def handle_patch_fields(db: Session, action: AutomationAction) -> dict:
    """Update specific invoice fields."""
    exc, inv = _get_exception_and_invoice(db, action)
    params = action.params_json or {}
    if not inv:
        return {"error": "Invoice not found"}

    patched = {}
    for field in ("total_amount", "tax_amount", "freight_amount", "discount_amount", "currency"):
        if field in params:
            setattr(inv, field, params[field])
            patched[field] = params[field]

    db.commit()
    return {"patched": patched}


@register("RERUN_OCR")
def handle_rerun_ocr(db: Session, action: AutomationAction) -> dict:
    """Re-extract invoice from PDF."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv or not inv.file_storage_path:
        return {"error": "No file available"}

    from app.services.s3_service import download_file
    from app.services.ocr_service import extract_invoice

    file_content = download_file(inv.file_storage_path)
    filename = inv.file_storage_path.rsplit("/", 1)[-1] if "/" in inv.file_storage_path else "invoice.pdf"
    result = extract_invoice(file_content, filename=filename)
    return {
        "confidence": result.get("confidence"),
        "extraction_method": result.get("extraction_method"),
        "fields_extracted": list(result.get("extracted_data", {}).keys()),
    }


@register("LOOKUP_POLICY_RULES")
def handle_lookup_policy(db: Session, action: AutomationAction) -> dict:
    """Query policy rules."""
    from app.models.config import PolicyRuleStatus
    rules = db.query(PolicyRule).filter(PolicyRule.status == PolicyRuleStatus.approved).limit(10).all()
    return {"rules": [{"type": r.rule_type, "conditions": r.conditions, "action": r.action} for r in rules]}


@register("CHECK_VENDOR_COMPLIANCE")
def handle_check_compliance(db: Session, action: AutomationAction) -> dict:
    """Check vendor status and compliance."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}
    vendor = db.query(Vendor).filter(Vendor.id == inv.vendor_id).first()
    if not vendor:
        return {"error": "Vendor not found"}
    return {
        "vendor_name": vendor.name,
        "status": vendor.status.value,
        "risk_level": vendor.risk_level.value,
        "on_hold": vendor.status.value == "on_hold",
    }


@register("CREATE_WAIT_TIMER")
def handle_wait_timer(db: Session, action: AutomationAction) -> dict:
    """Record a wait timer (MVP: just store in result, no real scheduler)."""
    params = action.params_json or {}
    return {
        "timeout_hours": params.get("timeout_hours", 48),
        "trigger": params.get("trigger", "manual"),
        "note": "Timer recorded. Manual follow-up required.",
    }


@register("PROPOSE_TERMS_OVERRIDE")
def handle_terms_override(db: Session, action: AutomationAction) -> dict:
    """Suggest payment terms correction."""
    params = action.params_json or {}
    return {
        "suggested_terms": params.get("new_terms", "Net 30"),
        "reason": params.get("reason", "Terms mismatch with vendor master"),
        "status": "proposal_ready",
    }


@register("WAIT_FOR_REPLY")
def handle_wait_for_reply(db: Session, action: AutomationAction) -> dict:
    """Stub — pauses execution until manual trigger."""
    return {"status": "waiting", "note": "Awaiting external reply. Resume execution manually."}


@register("RECALC_LINE_TOTALS")
def handle_recalc_lines(db: Session, action: AutomationAction) -> dict:
    """Recalculate line totals from qty * unit_price."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}
    recalculated = []
    for li in inv.line_items:
        computed = round(float(li.quantity) * float(li.unit_price), 2)
        current = float(li.line_total)
        recalculated.append({
            "line_number": li.line_number,
            "computed": computed,
            "current": current,
            "match": abs(computed - current) < 0.01,
        })
    return {"lines": recalculated}


# ---------------------------------------------------------------------------
# NEW: Additional robust handlers
# ---------------------------------------------------------------------------

@register("COMPARE_LINE_ITEMS")
def handle_compare_line_items(db: Session, action: AutomationAction) -> dict:
    """Detailed line-by-line comparison between invoice and PO."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found", "comparisons": []}

    # Gather PO lines via linked line items
    po_lines_map: dict[str, Any] = {}
    for li in inv.line_items:
        if li.po_line_id:
            po_line = db.query(POLineItem).filter(POLineItem.id == li.po_line_id).first()
            if po_line:
                po_lines_map[str(li.id)] = po_line

    comparisons = []
    total_inv = 0.0
    total_po = 0.0
    mismatches = 0

    for li in inv.line_items:
        inv_total = round(float(li.line_total), 2)
        total_inv += inv_total
        row: dict[str, Any] = {
            "line_number": li.line_number,
            "description": li.description,
            "inv_qty": float(li.quantity),
            "inv_unit_price": float(li.unit_price),
            "inv_total": inv_total,
        }

        po_line = po_lines_map.get(str(li.id))
        if po_line:
            po_total = round(float(po_line.line_total), 2)
            total_po += po_total
            qty_diff = float(li.quantity) - float(po_line.quantity_ordered)
            price_diff = round(float(li.unit_price) - float(po_line.unit_price), 4)
            total_diff = round(inv_total - po_total, 2)
            row.update({
                "po_qty": float(po_line.quantity_ordered),
                "po_unit_price": float(po_line.unit_price),
                "po_total": po_total,
                "qty_diff": qty_diff,
                "price_diff": price_diff,
                "total_diff": total_diff,
                "match": abs(total_diff) < 0.01,
            })
            if abs(total_diff) >= 0.01:
                mismatches += 1
        else:
            row.update({"po_qty": None, "po_unit_price": None, "po_total": None, "match": False, "note": "No PO line linked"})
            mismatches += 1

        comparisons.append(row)

    return {
        "comparisons": comparisons,
        "total_invoice": round(total_inv, 2),
        "total_po": round(total_po, 2),
        "total_diff": round(total_inv - total_po, 2),
        "lines_matched": len(comparisons) - mismatches,
        "lines_mismatched": mismatches,
    }


@register("CHECK_TOLERANCE")
def handle_check_tolerance(db: Session, action: AutomationAction) -> dict:
    """Look up tolerance configuration and evaluate if variance is within bounds."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    tol = (
        db.query(ToleranceConfig)
        .filter(ToleranceConfig.is_active == True)
        .first()
    )
    if not tol:
        return {"has_tolerance": False, "note": "No active tolerance config"}

    # Find match result for variance data
    match = db.query(MatchResult).filter(
        MatchResult.invoice_id == inv.id
    ).order_by(MatchResult.created_at.desc()).first()

    inv_total = float(inv.total_amount)
    result: dict[str, Any] = {
        "has_tolerance": True,
        "amount_tolerance_pct": float(tol.amount_tolerance_pct),
        "amount_tolerance_abs": float(tol.amount_tolerance_abs),
        "quantity_tolerance_pct": float(tol.quantity_tolerance_pct),
        "invoice_total": inv_total,
    }

    if match and match.matched_po_id:
        po_lines = db.query(POLineItem).filter(POLineItem.po_id == match.matched_po_id).all()
        po_total = sum(float(pl.line_total) for pl in po_lines)
        variance_abs = abs(inv_total - po_total)
        variance_pct = (variance_abs / po_total * 100) if po_total > 0 else 0
        result.update({
            "po_total": po_total,
            "variance_abs": round(variance_abs, 2),
            "variance_pct": round(variance_pct, 2),
            "within_pct_tolerance": variance_pct <= float(tol.amount_tolerance_pct),
            "within_abs_tolerance": variance_abs <= float(tol.amount_tolerance_abs),
            "within_any_tolerance": (
                variance_pct <= float(tol.amount_tolerance_pct)
                or variance_abs <= float(tol.amount_tolerance_abs)
            ),
        })

    return result


@register("SUMMARIZE_FINDINGS")
def handle_summarize_findings(db: Session, action: AutomationAction) -> dict:
    """AI-generated summary of all prior steps' findings in the plan."""
    from app.models.resolution import ResolutionPlan

    plan = db.query(ResolutionPlan).options(
        joinedload(ResolutionPlan.actions)
    ).filter(ResolutionPlan.id == action.plan_id).first()
    if not plan:
        return {"summary": "No plan found."}

    # Collect results from completed steps
    completed_results = []
    for a in sorted(plan.actions, key=lambda x: x.step_id or ""):
        if a.id == action.id:
            continue  # skip self
        if a.result_json:
            completed_results.append(f"[{a.step_id}] {a.action_type}: {str(a.result_json)[:300]}")

    if not completed_results:
        return {"summary": "No completed steps to summarize."}

    prompt = (
        f"Summarize these resolution findings for exception type '{plan.plan_json.get('exception_type', 'unknown')}':\n\n"
        + "\n".join(completed_results)
        + "\n\nProvide a 2-4 sentence executive summary for an AP analyst."
    )
    summary = ai_service.call_claude(
        system_prompt="You summarize AP exception resolution findings concisely for finance analysts.",
        user_message=prompt,
        max_tokens=512,
    ) or "Resolution steps completed. Review individual step results for details."

    return {"summary": summary, "steps_reviewed": len(completed_results)}


@register("ESCALATE_TO_MANAGER")
def handle_escalate_to_manager(db: Session, action: AutomationAction) -> dict:
    """Escalate exception to AP manager with context."""
    from app.models.user import User, UserRole

    exc, inv = _get_exception_and_invoice(db, action)
    if not exc:
        return {"error": "Exception not found"}

    exc.status = ExceptionStatus.escalated
    params = action.params_json or {}

    # Find an approver/admin user to assign to
    manager = db.query(User).filter(
        User.role.in_([UserRole.approver, UserRole.admin]),
        User.is_active == True,
    ).first()

    if manager:
        exc.assigned_to = manager.id

    db.commit()
    return {
        "escalated": True,
        "assigned_to": manager.name if manager else "Unassigned",
        "reason": params.get("reason", "Requires management review"),
        "exception_id": str(exc.id),
    }


@register("AUTO_LINK_PO")
def handle_auto_link_po(db: Session, action: AutomationAction) -> dict:
    """Attempt to auto-link invoice line items to PO lines."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    from app.services.match_service import auto_link_po_lines
    result = auto_link_po_lines(db, inv.id)
    db.refresh(inv)

    linked = sum(1 for li in inv.line_items if li.po_line_id)
    return {
        "total_lines": len(inv.line_items),
        "lines_linked": linked,
        "lines_unlinked": len(inv.line_items) - linked,
        "link_result": result,
    }


@register("VERIFY_VENDOR_DETAILS")
def handle_verify_vendor_details(db: Session, action: AutomationAction) -> dict:
    """Cross-check vendor details between invoice and vendor master."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    vendor = db.query(Vendor).filter(Vendor.id == inv.vendor_id).first() if inv.vendor_id else None
    if not vendor:
        return {
            "verified": False,
            "vendor_in_master": False,
            "note": "No vendor linked to invoice",
        }

    return {
        "verified": True,
        "vendor_in_master": True,
        "vendor_name": vendor.name,
        "vendor_code": vendor.vendor_code,
        "vendor_status": vendor.status.value,
        "risk_level": vendor.risk_level.value,
        "payment_terms": vendor.payment_terms_code or "N/A",
        "on_hold": vendor.status.value == "on_hold",
        "is_active": vendor.status.value == "active",
    }


@register("CALCULATE_VARIANCE_BREAKDOWN")
def handle_variance_breakdown(db: Session, action: AutomationAction) -> dict:
    """Produce a structured breakdown of the total variance by category."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    inv_subtotal = sum(float(li.line_total) for li in inv.line_items)
    inv_tax = float(inv.tax_amount)
    inv_freight = float(inv.freight_amount)
    inv_discount = float(inv.discount_amount)
    inv_total = float(inv.total_amount)

    # Try to get PO total for comparison
    match = db.query(MatchResult).filter(
        MatchResult.invoice_id == inv.id
    ).order_by(MatchResult.created_at.desc()).first()

    po_total = 0.0
    po_subtotal = 0.0
    if match and match.matched_po_id:
        po_lines = db.query(POLineItem).filter(POLineItem.po_id == match.matched_po_id).all()
        po_subtotal = sum(float(pl.line_total) for pl in po_lines)
        po_total = po_subtotal  # POs typically don't include tax/freight

    breakdown = {
        "invoice": {
            "subtotal": round(inv_subtotal, 2),
            "tax": round(inv_tax, 2),
            "freight": round(inv_freight, 2),
            "discount": round(inv_discount, 2),
            "total": round(inv_total, 2),
        },
        "po": {
            "subtotal": round(po_subtotal, 2),
            "total": round(po_total, 2),
        },
        "variances": {
            "subtotal_diff": round(inv_subtotal - po_subtotal, 2),
            "tax_component": round(inv_tax, 2),
            "freight_component": round(inv_freight, 2),
            "discount_component": round(-inv_discount, 2),
            "total_diff": round(inv_total - po_total, 2),
        },
        "computed_total": round(inv_subtotal + inv_tax + inv_freight - inv_discount, 2),
        "total_matches_computed": abs(inv_total - (inv_subtotal + inv_tax + inv_freight - inv_discount)) < 0.01,
    }
    return breakdown


# ---------------------------------------------------------------------------
# Scenario-specific handlers (5 demo scenarios)
# ---------------------------------------------------------------------------


@register("APPLY_CORRECTIONS")
def handle_apply_corrections(db: Session, action: AutomationAction) -> dict:
    """Apply recalculated line totals (qty * unit_price) to invoice and update total."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    corrections = []
    old_total = float(inv.total_amount)

    for li in inv.line_items:
        computed = round(float(li.quantity) * float(li.unit_price), 2)
        current = float(li.line_total)
        if abs(computed - current) >= 0.01:
            corrections.append({
                "line_number": li.line_number,
                "description": li.description,
                "old_total": current,
                "new_total": computed,
                "difference": round(computed - current, 2),
            })
            li.line_total = computed

    # Recalculate invoice total
    new_subtotal = sum(float(li.line_total) for li in inv.line_items)
    new_total = round(new_subtotal + float(inv.tax_amount) + float(inv.freight_amount) - float(inv.discount_amount), 2)
    inv.total_amount = new_total
    db.commit()

    return {
        "corrections_applied": corrections,
        "old_total": old_total,
        "new_total": new_total,
        "difference": round(new_total - old_total, 2),
        "status": "corrections_applied",
    }


@register("GENERATE_CREDIT_REQUEST")
def handle_generate_credit_request(db: Session, action: AutomationAction) -> dict:
    """Generate a credit request for quantity overruns (invoice qty > PO qty)."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    vendor = db.query(Vendor).filter(Vendor.id == inv.vendor_id).first() if inv.vendor_id else None
    vendor_name = vendor.name if vendor else "Unknown Vendor"

    overrun_lines = []
    total_credit = 0.0

    for li in inv.line_items:
        if not li.po_line_id:
            continue
        po_line = db.query(POLineItem).filter(POLineItem.id == li.po_line_id).first()
        if not po_line:
            continue

        inv_qty = float(li.quantity)
        po_qty = float(po_line.quantity_ordered)
        if inv_qty > po_qty:
            excess = inv_qty - po_qty
            credit_amount = round(excess * float(li.unit_price), 2)
            total_credit += credit_amount
            overrun_lines.append({
                "line_number": li.line_number,
                "description": li.description,
                "invoiced_qty": inv_qty,
                "po_qty": po_qty,
                "excess_qty": excess,
                "unit_price": float(li.unit_price),
                "credit_amount": credit_amount,
            })

    # Generate narrative via Claude
    narrative = ""
    if overrun_lines:
        lines_desc = "; ".join(
            f"Line {ol['line_number']}: {ol['description']} — invoiced {ol['invoiced_qty']} vs PO {ol['po_qty']}, excess {ol['excess_qty']}"
            for ol in overrun_lines
        )
        narrative = ai_service.call_claude(
            system_prompt="You write concise credit request justifications for AP departments. 2-3 sentences.",
            user_message=(
                f"Write a credit request justification for invoice {inv.invoice_number} from {vendor_name}.\n"
                f"Overrun details: {lines_desc}\n"
                f"Total credit requested: ${total_credit:,.2f}"
            ),
            max_tokens=256,
        ) or f"Credit requested for quantity overrun on invoice {inv.invoice_number}."

    credit_number = f"CR-{inv.invoice_number}"

    return {
        "credit_request_number": credit_number,
        "vendor_name": vendor_name,
        "invoice_number": inv.invoice_number,
        "invoice_date": str(inv.invoice_date),
        "overrun_lines": overrun_lines,
        "total_credit_amount": round(total_credit, 2),
        "narrative": narrative,
        "status": "credit_request_ready",
    }


@register("ADJUST_INVOICE_QUANTITIES")
def handle_adjust_invoice_quantities(db: Session, action: AutomationAction) -> dict:
    """Cap invoice line quantities to PO quantities and recalculate totals."""
    exc, inv = _get_exception_and_invoice(db, action)
    if not inv:
        return {"error": "Invoice not found"}

    adjusted_lines = []
    old_total = float(inv.total_amount)

    for li in inv.line_items:
        if not li.po_line_id:
            continue
        po_line = db.query(POLineItem).filter(POLineItem.id == li.po_line_id).first()
        if not po_line:
            continue

        inv_qty = float(li.quantity)
        po_qty = float(po_line.quantity_ordered)
        if inv_qty > po_qty:
            old_line_total = float(li.line_total)
            li.quantity = po_qty
            li.line_total = round(po_qty * float(li.unit_price), 2)
            adjusted_lines.append({
                "line_number": li.line_number,
                "description": li.description,
                "old_qty": inv_qty,
                "new_qty": po_qty,
                "old_line_total": old_line_total,
                "new_line_total": float(li.line_total),
            })

    # Recalculate invoice total
    new_subtotal = sum(float(li.line_total) for li in inv.line_items)
    new_total = round(new_subtotal + float(inv.tax_amount) + float(inv.freight_amount) - float(inv.discount_amount), 2)
    inv.total_amount = new_total
    db.commit()

    return {
        "adjusted_lines": adjusted_lines,
        "old_invoice_total": old_total,
        "new_invoice_total": new_total,
        "status": "quantities_adjusted",
    }
