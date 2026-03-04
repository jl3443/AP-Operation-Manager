"""Approval workflow service."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.approval import (
    AIRecommendation,
    ApprovalMatrix,
    ApprovalStatus,
    ApprovalTask,
)
from app.models.exception import Exception_
from app.models.invoice import Invoice, InvoiceStatus
from app.models.matching import MatchResult
from app.models.user import User, UserRole
from app.models.vendor import Vendor
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

APPROVAL_SYSTEM_PROMPT = """\
You are a senior accounts-payable approval analyst. Given the invoice context \
below, analyse risk and recommend an approval action.

Return ONLY a JSON object (no markdown, no explanation):
{
  "recommendation": "approve" | "review" | "reject",
  "reasoning": "1-3 sentence explanation",
  "risk_factors": ["list", "of", "risk", "factors"]
}

Guidelines:
- "approve" if the invoice looks routine, amounts match, vendor history is clean.
- "review" if there are minor discrepancies, high amounts, or limited history.
- "reject" if there are significant red flags (large variance, vendor on hold, \
duplicate indicators)."""


def _build_approval_context(db: Session, invoice: Invoice) -> str:
    """Build a context string for Claude to analyse an invoice."""
    # Match results
    match = (
        db.query(MatchResult)
        .filter(MatchResult.invoice_id == invoice.id)
        .order_by(MatchResult.created_at.desc())
        .first()
    )
    match_info = "No match performed yet."
    if match:
        match_info = (
            f"Match status: {match.match_status.value}, Score: {match.overall_score:.1f}%, Details: {match.details}"
        )

    # Exception count
    exc_count = db.query(Exception_).filter(Exception_.invoice_id == invoice.id).count()

    # Vendor history
    vendor_total = db.query(Invoice).filter(Invoice.vendor_id == invoice.vendor_id).count()
    vendor_exceptions = (
        db.query(Exception_)
        .join(Invoice, Exception_.invoice_id == Invoice.id)
        .filter(Invoice.vendor_id == invoice.vendor_id)
        .count()
    )
    exc_rate = (vendor_exceptions / vendor_total * 100) if vendor_total > 0 else 0

    # Resolve vendor name
    vendor = db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
    vendor_label = f"{vendor.name} ({vendor.vendor_code})" if vendor else str(invoice.vendor_id)

    return (
        f"Invoice: {invoice.invoice_number}\n"
        f"Amount: {invoice.currency} {invoice.total_amount:,.2f}\n"
        f"Vendor: {vendor_label}\n"
        f"Invoice date: {invoice.invoice_date}\n"
        f"Due date: {invoice.due_date}\n"
        f"Line items: {len(invoice.line_items)}\n"
        f"Match result: {match_info}\n"
        f"Exceptions on this invoice: {exc_count}\n"
        f"Vendor history: {vendor_total} invoices, "
        f"{vendor_exceptions} exceptions ({exc_rate:.1f}% exception rate)"
    )


def _get_ai_recommendation(db: Session, invoice: Invoice) -> tuple[AIRecommendation, str]:
    """Get AI-powered approval recommendation, with rule-based fallback."""
    if not ai_service.available:
        # Fallback: simple amount-based rule
        if float(invoice.total_amount) < 5000:
            return AIRecommendation.approve, "Auto-recommendation based on invoice amount (<$5,000)"
        return AIRecommendation.review, "Auto-recommendation: amount exceeds $5,000 threshold"

    context = _build_approval_context(db, invoice)
    raw = ai_service.call_claude(
        system_prompt=APPROVAL_SYSTEM_PROMPT,
        user_message=context,
        max_tokens=512,
    )

    parsed = ai_service.extract_json(raw) if raw else None
    if parsed:
        rec_str = parsed.get("recommendation", "review").lower()
        reasoning = parsed.get("reasoning", "")
        risk_factors = parsed.get("risk_factors", [])
        if risk_factors:
            reasoning += " Risk factors: " + ", ".join(risk_factors) + "."

        rec_map = {
            "approve": AIRecommendation.approve,
            "reject": AIRecommendation.reject,
            "review": AIRecommendation.review,
        }
        return rec_map.get(rec_str, AIRecommendation.review), reasoning

    # Fallback if AI response unparseable
    logger.warning("AI recommendation unparseable – using rule-based fallback")
    if float(invoice.total_amount) < 5000:
        return AIRecommendation.approve, "Auto-recommendation based on invoice amount (<$5,000)"
    return AIRecommendation.review, "Auto-recommendation: amount exceeds $5,000 threshold"


def create_approval_tasks(db: Session, invoice_id: uuid.UUID) -> list[ApprovalTask]:
    """Generate approval tasks for an invoice based on the approval matrix.

    Falls back to a simple default rule if no matrix rows are active.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    # Get AI recommendation once for all tasks
    ai_rec, ai_reason = _get_ai_recommendation(db, invoice)

    # Fetch active matrix rules ordered by priority
    matrix_rules = (
        db.query(ApprovalMatrix).filter(ApprovalMatrix.is_active).order_by(ApprovalMatrix.priority.asc()).all()
    )

    tasks_created: list[ApprovalTask] = []

    if matrix_rules:
        for rule in matrix_rules:
            conditions = rule.conditions or {}
            # Simple condition evaluation: check amount threshold
            min_amount = conditions.get("min_amount", 0)
            max_amount = conditions.get("max_amount", float("inf"))
            if not (min_amount <= float(invoice.total_amount) <= max_amount):
                continue

            # Find an approver matching the role
            approver = db.query(User).filter(User.role == rule.approver_role, User.is_active).first()
            if not approver:
                continue

            task = ApprovalTask(
                invoice_id=invoice.id,
                approver_id=approver.id,
                approval_level=rule.approver_level,
                approval_order=rule.priority,
                status=ApprovalStatus.pending,
                ai_recommendation=ai_rec,
                ai_recommendation_reason=ai_reason,
            )
            db.add(task)
            tasks_created.append(task)
    else:
        # Default: assign to any active approver
        approver = db.query(User).filter(User.role == UserRole.approver, User.is_active).first()
        if approver:
            task = ApprovalTask(
                invoice_id=invoice.id,
                approver_id=approver.id,
                approval_level=1,
                approval_order=1,
                status=ApprovalStatus.pending,
                ai_recommendation=ai_rec,
                ai_recommendation_reason=ai_reason,
            )
            db.add(task)
            tasks_created.append(task)

    invoice.status = InvoiceStatus.pending_approval
    db.commit()
    for t in tasks_created:
        db.refresh(t)
    return tasks_created


def process_approval(
    db: Session,
    task_id: uuid.UUID,
    approved: bool,
    comments: str | None = None,
) -> ApprovalTask:
    """Approve or reject an approval task."""
    task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
    if not task:
        raise ValueError(f"ApprovalTask {task_id} not found")
    if task.status != ApprovalStatus.pending:
        raise ValueError(f"ApprovalTask {task_id} is not pending (status={task.status})")

    task.status = ApprovalStatus.approved if approved else ApprovalStatus.rejected
    task.decision_at = datetime.now(UTC)
    task.comments = comments

    # Update invoice status based on decision
    invoice = db.query(Invoice).filter(Invoice.id == task.invoice_id).first()
    if invoice:
        if approved:
            # Check if all tasks for this invoice are approved
            pending = (
                db.query(ApprovalTask)
                .filter(
                    ApprovalTask.invoice_id == invoice.id,
                    ApprovalTask.id != task.id,
                    ApprovalTask.status == ApprovalStatus.pending,
                )
                .count()
            )
            if pending == 0:
                invoice.status = InvoiceStatus.approved
        else:
            invoice.status = InvoiceStatus.rejected

    db.commit()
    db.refresh(task)
    return task
