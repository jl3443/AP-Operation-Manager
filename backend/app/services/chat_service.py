"""AI chat assistant service for AP operations."""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.approval import ApprovalStatus, ApprovalTask
from app.models.exception import Exception_, ExceptionStatus
from app.models.goods_receipt import GoodsReceipt, GRNLineItem
from app.models.invoice import Invoice, InvoiceStatus
from app.models.matching import MatchResult
from app.models.purchase_order import POLineItem, PurchaseOrder
from app.models.vendor import Vendor
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """\
You are an AI assistant specialised in Accounts Payable operations. You help \
AP clerks, analysts, and managers with their daily work.

You have access to LIVE system data including purchase orders, goods receipts, \
invoices, vendors, exceptions, and approvals. This data is refreshed with every \
message and reflects the current state of the system.

Your capabilities:
- Answer questions about AP workflows: invoice processing, matching, \
exceptions, approvals, vendor management
- Analyze uploaded datasets: PO data, GRN data, vendor master data
- Explain exception types and suggest resolution approaches
- Provide guidance on approval decisions
- Help interpret matching results and discrepancy details
- Identify patterns, trends, and anomalies in the data
- Offer best-practice advice for AP operations
- Cross-reference POs, GRNs, and invoices for 3-way match analysis

Keep answers concise and actionable. Use bullet points for lists. \
When referencing amounts, always include the currency. \
When asked about uploaded data or datasets, refer to the PO, GRN, and \
vendor data provided below — this IS the uploaded data."""

# Maximum messages stored per conversation
MAX_HISTORY = 20

# Maximum number of conversations to keep in memory (per-process)
MAX_CONVERSATIONS = 100


def _get_system_stats(db: Session) -> str:
    """Query live stats and full dataset context to embed in the system prompt."""
    total_invoices = db.query(Invoice).count()
    pending_approval = (
        db.query(Invoice)
        .filter(Invoice.status == InvoiceStatus.pending_approval)
        .count()
    )
    open_exceptions = (
        db.query(Exception_)
        .filter(Exception_.status == ExceptionStatus.open)
        .count()
    )
    pending_tasks = (
        db.query(ApprovalTask)
        .filter(ApprovalTask.status == ApprovalStatus.pending)
        .count()
    )
    active_vendors = db.query(Vendor).filter(Vendor.status == "active").count()

    total_pending_amount = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
        .filter(Invoice.status == InvoiceStatus.pending_approval)
        .scalar()
    )

    # Status breakdown
    status_counts = (
        db.query(Invoice.status, func.count(Invoice.id))
        .group_by(Invoice.status)
        .all()
    )
    status_breakdown = ", ".join(
        f"{s.value}: {c}" for s, c in status_counts
    )

    # Exception breakdown
    exc_counts = (
        db.query(Exception_.exception_type, func.count(Exception_.id))
        .filter(Exception_.status == ExceptionStatus.open)
        .group_by(Exception_.exception_type)
        .all()
    )
    exc_breakdown = ", ".join(
        f"{t.value}: {c}" for t, c in exc_counts
    ) or "none"

    stats = (
        f"=== LIVE SYSTEM STATS ===\n"
        f"Total invoices: {total_invoices}\n"
        f"Pending approval: {pending_approval}\n"
        f"Pending approval amount: USD {total_pending_amount:,.2f}\n"
        f"Open exceptions: {open_exceptions}\n"
        f"Pending approval tasks: {pending_tasks}\n"
        f"Active vendors: {active_vendors}\n"
        f"Invoice status breakdown: {status_breakdown}\n"
        f"Open exception types: {exc_breakdown}\n"
        f"=========================\n"
    )

    # ── Vendor Master Data ─────────────────────────────────────────
    vendors = db.query(Vendor).order_by(Vendor.vendor_code).all()
    vendor_lines = []
    for v in vendors:
        vendor_lines.append(
            f"  {v.vendor_code} | {v.name} | {v.city}, {v.state} | "
            f"Terms: {v.payment_terms_code} | Status: {v.status.value} | "
            f"Risk: {v.risk_level.value}"
        )
    stats += (
        f"\n=== VENDOR MASTER DATA ({len(vendors)} records) ===\n"
        + "\n".join(vendor_lines)
        + "\n"
    )

    # ── Purchase Order Data ────────────────────────────────────────
    pos = (
        db.query(PurchaseOrder)
        .options(joinedload(PurchaseOrder.vendor), joinedload(PurchaseOrder.line_items))
        .order_by(PurchaseOrder.po_number)
        .all()
    )
    po_lines = []
    for po in pos:
        vendor_name = po.vendor.name if po.vendor else "Unknown"
        line_count = len(po.line_items) if po.line_items else 0
        line_details = []
        for li in (po.line_items or []):
            line_details.append(
                f"    Line {li.line_number}: {li.description} | "
                f"Qty: {li.quantity_ordered} | Price: ${float(li.unit_price):,.2f} | "
                f"Total: ${float(li.line_total):,.2f} | "
                f"Received: {li.quantity_received}"
            )
        po_lines.append(
            f"  {po.po_number} | Vendor: {vendor_name} | "
            f"Date: {po.order_date} | Delivery: {po.delivery_date} | "
            f"Total: ${float(po.total_amount):,.2f} | Status: {po.status.value} | "
            f"{line_count} line items"
        )
        po_lines.extend(line_details)
    stats += (
        f"\n=== PURCHASE ORDER DATA ({len(pos)} records) ===\n"
        + "\n".join(po_lines)
        + "\n"
    )

    # ── Goods Receipt (GRN) Data ───────────────────────────────────
    grns = (
        db.query(GoodsReceipt)
        .options(
            joinedload(GoodsReceipt.vendor),
            joinedload(GoodsReceipt.purchase_order),
            joinedload(GoodsReceipt.line_items).joinedload(GRNLineItem.po_line),
        )
        .order_by(GoodsReceipt.grn_number)
        .all()
    )
    grn_lines = []
    for grn in grns:
        vendor_name = grn.vendor.name if grn.vendor else "Unknown"
        po_num = grn.purchase_order.po_number if grn.purchase_order else "N/A"
        line_count = len(grn.line_items) if grn.line_items else 0
        line_details = []
        for li in (grn.line_items or []):
            desc = li.po_line.description if li.po_line else "N/A"
            line_details.append(
                f"    Line: {desc} | Qty Received: {li.quantity_received} | "
                f"Notes: {li.condition_notes or 'N/A'}"
            )
        grn_lines.append(
            f"  {grn.grn_number} | PO: {po_num} | Vendor: {vendor_name} | "
            f"Date: {grn.receipt_date} | Warehouse: {grn.warehouse or 'N/A'} | "
            f"{line_count} line items"
        )
        grn_lines.extend(line_details)
    stats += (
        f"\n=== GOODS RECEIPT (GRN) DATA ({len(grns)} records) ===\n"
        + "\n".join(grn_lines)
        + "\n"
    )

    # ── Invoice Data ───────────────────────────────────────────────
    invs = (
        db.query(Invoice)
        .options(joinedload(Invoice.vendor))
        .order_by(Invoice.invoice_date.desc())
        .all()
    )
    inv_lines = []
    for inv in invs:
        vendor_name = inv.vendor.name if inv.vendor else "Unknown"
        inv_lines.append(
            f"  {inv.invoice_number} | Vendor: {vendor_name} | "
            f"Date: {inv.invoice_date} | Due: {inv.due_date} | "
            f"Amount: ${float(inv.total_amount):,.2f} | "
            f"Status: {inv.status.value} | Source: {inv.source_channel.value}"
        )
    stats += (
        f"\n=== INVOICE DATA ({len(invs)} records) ===\n"
        + "\n".join(inv_lines)
        + "\n"
    )

    # ── Exception Details ──────────────────────────────────────────
    exceptions = (
        db.query(Exception_)
        .options(joinedload(Exception_.invoice))
        .filter(Exception_.status.in_([ExceptionStatus.open, ExceptionStatus.assigned]))
        .all()
    )
    exc_lines = []
    for exc in exceptions:
        inv_num = exc.invoice.invoice_number if exc.invoice else "N/A"
        exc_lines.append(
            f"  Invoice: {inv_num} | Type: {exc.exception_type.value} | "
            f"Severity: {exc.severity.value} | Status: {exc.status.value}\n"
            f"    AI Suggestion: {exc.ai_suggested_resolution or 'N/A'}"
        )
    if exc_lines:
        stats += (
            f"\n=== OPEN EXCEPTIONS ({len(exceptions)} records) ===\n"
            + "\n".join(exc_lines)
            + "\n"
        )

    # ── Match Results ──────────────────────────────────────────────
    matches = (
        db.query(MatchResult)
        .options(
            joinedload(MatchResult.invoice),
            joinedload(MatchResult.matched_po),
        )
        .all()
    )
    match_lines = []
    for m in matches:
        inv_num = m.invoice.invoice_number if m.invoice else "N/A"
        po_num = m.matched_po.po_number if m.matched_po else "N/A"
        match_lines.append(
            f"  Invoice: {inv_num} → PO: {po_num} | "
            f"Type: {m.match_type.value} | Status: {m.match_status.value} | "
            f"Score: {m.overall_score}%"
        )
    stats += (
        f"\n=== MATCH RESULTS ({len(matches)} records) ===\n"
        + "\n".join(match_lines)
        + "\n"
    )

    return stats


# In-memory conversation store keyed by (user_id, conversation_id).
# Capped at MAX_CONVERSATIONS to prevent unbounded memory growth.
_conversations: dict[str, list[dict[str, str]]] = {}


def _conv_key(user_id: str, conversation_id: str) -> str:
    """Build a composite key that isolates conversations per user."""
    return f"{user_id}:{conversation_id}"


def chat(
    db: Session,
    message: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict[str, str]:
    """Process a chat message and return the AI response.

    Args:
        user_id: If provided, scopes the conversation to this user so that
            other users cannot access or inject messages into it.
    """
    if not ai_service.available:
        return {
            "response": (
                "AI assistant is not available. Please configure the "
                "LLM_API_KEY in your environment settings to enable "
                "the AI chat assistant."
            ),
            "conversation_id": conversation_id or str(uuid.uuid4()),
        }

    # Get or create conversation
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
    key = _conv_key(user_id or "anonymous", conversation_id)

    if key not in _conversations:
        # Evict oldest conversation if at capacity
        if len(_conversations) >= MAX_CONVERSATIONS:
            oldest_key = next(iter(_conversations))
            del _conversations[oldest_key]
            logger.info("Evicted oldest conversation to stay within limit")
        _conversations[key] = []

    history = _conversations[key]

    # Build system prompt with live stats
    stats = _get_system_stats(db)
    system = f"{CHAT_SYSTEM_PROMPT}\n\n{stats}"

    # Add user message to history
    history.append({"role": "user", "content": message})

    # Cap stored history to MAX_HISTORY to prevent unbounded growth
    if len(history) > MAX_HISTORY:
        _conversations[key] = history[-MAX_HISTORY:]
        history = _conversations[key]

    # Call Claude with conversation history (larger max_tokens for data-rich context)
    raw = ai_service.call_claude_conversation(
        system_prompt=system,
        messages=history,
        max_tokens=2048,
    )

    response_text = raw or "I'm sorry, I wasn't able to process that request. Please try again."

    # Add assistant response to history
    history.append({"role": "assistant", "content": response_text})

    return {
        "response": response_text,
        "conversation_id": conversation_id,
    }
