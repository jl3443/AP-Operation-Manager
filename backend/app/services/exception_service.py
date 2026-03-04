"""Exception management service."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.exception import (
    Exception_,
    ExceptionComment,
    ExceptionSeverity,
    ExceptionStatus,
    ExceptionType,
)
from app.models.invoice import Invoice
from app.models.matching import MatchResult
from app.models.vendor import Vendor
from app.schemas.exception import ExceptionUpdate
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

EXCEPTION_SYSTEM_PROMPT = """\
You are an expert accounts-payable exception analyst. Given the exception \
context below, analyse it and provide actionable guidance.

Return ONLY a JSON object (no markdown, no explanation):
{
  "suggested_severity": "low" | "medium" | "high" | "critical",
  "severity_reasoning": "1-2 sentence explanation of severity assessment",
  "resolution_suggestion": "2-3 sentence actionable resolution guidance"
}

Severity guidelines:
- low: minor discrepancy, likely auto-resolvable or within normal tolerance
- medium: requires manual review but not urgent
- high: significant variance or compliance risk, needs prompt attention
- critical: potential fraud, duplicate payment risk, or vendor-on-hold violation"""


def _build_exception_context(
    db: Session,
    invoice: Invoice,
    exception_type: ExceptionType,
    severity: ExceptionSeverity,
) -> str:
    """Build context string for Claude to analyse an exception."""
    # Match results
    match = (
        db.query(MatchResult)
        .filter(MatchResult.invoice_id == invoice.id)
        .order_by(MatchResult.created_at.desc())
        .first()
    )
    match_info = "No match result available."
    if match:
        match_info = (
            f"Match status: {match.match_status.value}, "
            f"Score: {match.overall_score:.1f}%, "
            f"Details: {match.details}"
        )

    # Resolve vendor name
    vendor = db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()
    vendor_label = f"{vendor.name} ({vendor.vendor_code})" if vendor else str(invoice.vendor_id)

    return (
        f"Exception type: {exception_type.value}\n"
        f"Current severity: {severity.value}\n"
        f"Invoice: {invoice.invoice_number}\n"
        f"Amount: {invoice.currency} {invoice.total_amount:,.2f}\n"
        f"Vendor: {vendor_label}\n"
        f"Invoice date: {invoice.invoice_date}\n"
        f"Due date: {invoice.due_date}\n"
        f"Match result: {match_info}"
    )


def create_exception(
    db: Session,
    *,
    invoice_id: uuid.UUID,
    exception_type: ExceptionType,
    severity: ExceptionSeverity = ExceptionSeverity.medium,
    auto_commit: bool = True,
) -> Exception_:
    """Create a new exception record with optional AI analysis.

    Args:
        auto_commit: If True (default), commits the transaction.  Set to False
            when the caller manages the transaction (e.g. during matching).
    """
    exc = Exception_(
        invoice_id=invoice_id,
        exception_type=exception_type,
        severity=severity,
        status=ExceptionStatus.open,
    )
    db.add(exc)
    db.flush()

    # AI-powered analysis
    if ai_service.available:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if invoice:
            context = _build_exception_context(db, invoice, exception_type, severity)
            raw = ai_service.call_claude(
                system_prompt=EXCEPTION_SYSTEM_PROMPT,
                user_message=context,
                max_tokens=512,
            )
            parsed = ai_service.extract_json(raw) if raw else None
            if parsed:
                exc.ai_suggested_resolution = parsed.get("resolution_suggestion")
                exc.ai_severity_reasoning = parsed.get("severity_reasoning")

                # Optionally adjust severity if AI suggests different
                suggested = parsed.get("suggested_severity")
                severity_map = {
                    "low": ExceptionSeverity.low,
                    "medium": ExceptionSeverity.medium,
                    "high": ExceptionSeverity.high,
                    "critical": ExceptionSeverity.critical,
                }
                if suggested in severity_map and severity_map[suggested] != severity:
                    exc.severity = severity_map[suggested]
                    logger.info(
                        "AI adjusted exception severity from %s to %s",
                        severity.value,
                        suggested,
                    )

    if auto_commit:
        db.commit()
        db.refresh(exc)

        # Auto-generate resolution plan in background
        try:
            from app.tasks.invoice_tasks import execute_resolution_plan_auto
            execute_resolution_plan_auto.delay(str(exc.id))
        except Exception as e:
            # Don't block exception creation if Celery is down — plan can be
            # generated lazily when the detail page is viewed.
            logger.warning("Could not queue auto-plan generation: %s", e)

    return exc


def update_exception(
    db: Session,
    exception_id: uuid.UUID,
    payload: ExceptionUpdate,
    resolved_by: Optional[uuid.UUID] = None,
) -> Optional[Exception_]:
    """Update an exception (assign, resolve, escalate, etc.)."""
    exc = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not exc:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exc, field, value)

    # If resolving, stamp the timestamp
    if payload.status == ExceptionStatus.resolved:
        exc.resolved_at = datetime.now(timezone.utc)
        exc.resolved_by = resolved_by

    db.commit()
    db.refresh(exc)
    return exc


def detect_duplicate_invoice(
    db: Session, invoice_number: str, vendor_id: uuid.UUID
) -> bool:
    """Return True if an invoice with the same number + vendor already exists."""
    existing = (
        db.query(Invoice)
        .filter(
            Invoice.invoice_number == invoice_number,
            Invoice.vendor_id == vendor_id,
        )
        .first()
    )
    return existing is not None


def add_comment(
    db: Session,
    exception_id: uuid.UUID,
    user_id: uuid.UUID,
    comment_text: str,
    mentions: Optional[list[str]] = None,
) -> ExceptionComment:
    """Add a comment to an exception."""
    comment = ExceptionComment(
        exception_id=exception_id,
        user_id=user_id,
        comment_text=comment_text,
        mentions=mentions,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
