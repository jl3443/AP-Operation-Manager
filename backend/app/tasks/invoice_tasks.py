"""Celery background tasks for invoice processing.

Defines async tasks for batch processing, scheduled matching,
duplicate detection scans, and auto-resolution.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.services.auto_resolution import auto_resolve_all
from app.services.duplicate_detection import check_duplicate

logger = logging.getLogger(__name__)


def run_batch_matching() -> dict:
    """Process all invoices in 'extracted' status through the matching engine.

    This task is intended to be run on a schedule (e.g., every 15 minutes)
    to automatically pick up newly extracted invoices and run matching.
    """
    from app.models.invoice import Invoice, InvoiceStatus
    from app.services import match_service

    db = SessionLocal()
    try:
        invoices = (
            db.query(Invoice)
            .filter(Invoice.status == InvoiceStatus.extracted)
            .all()
        )

        results = {"processed": 0, "matched": 0, "exceptions": 0, "errors": []}

        for invoice in invoices:
            try:
                match_result = match_service.run_matching(db, str(invoice.id))
                results["processed"] += 1
                if match_result and match_result.get("match_status") == "matched":
                    results["matched"] += 1
                else:
                    results["exceptions"] += 1
            except Exception as e:
                results["errors"].append(f"Invoice {invoice.invoice_number}: {e}")
                logger.error(f"Batch matching failed for {invoice.invoice_number}: {e}")

        db.commit()
        logger.info(
            f"Batch matching complete: {results['processed']} processed, "
            f"{results['matched']} matched, {results['exceptions']} exceptions"
        )
        return results
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_auto_resolution() -> dict:
    """Scan open exceptions and auto-resolve those within tolerance.

    Intended to run after batch matching or on a schedule.
    """
    db = SessionLocal()
    try:
        result = auto_resolve_all(db)
        logger.info(
            f"Auto-resolution complete: {result['auto_resolved']} resolved, "
            f"{result['requires_manual']} require manual review"
        )
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_duplicate_scan() -> dict:
    """Scan recent invoices for potential duplicates.

    Checks all non-draft invoices from the last 30 days.
    """
    from datetime import timedelta

    from app.models.invoice import Invoice, InvoiceStatus

    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_invoices = (
            db.query(Invoice)
            .filter(
                Invoice.status != InvoiceStatus.draft,
                Invoice.created_at >= cutoff,
            )
            .all()
        )

        duplicates_found = []
        for invoice in recent_invoices:
            result = check_duplicate(
                db,
                invoice_number=invoice.invoice_number,
                vendor_id=str(invoice.vendor_id),
                total_amount=float(invoice.total_amount),
                invoice_date=invoice.invoice_date,
                exclude_invoice_id=str(invoice.id),
            )
            if result["is_duplicate"]:
                duplicates_found.append({
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.invoice_number,
                    "matches": result["matches"],
                })

        logger.info(
            f"Duplicate scan complete: {len(recent_invoices)} checked, "
            f"{len(duplicates_found)} potential duplicates found"
        )
        return {
            "scanned": len(recent_invoices),
            "duplicates_found": len(duplicates_found),
            "details": duplicates_found,
        }
    finally:
        db.close()


def generate_daily_report() -> dict:
    """Generate a daily AP operations summary report.

    Collects key metrics and returns a structured summary.
    """
    from sqlalchemy import func

    from app.models.approval import ApprovalStatus, ApprovalTask
    from app.models.exception import Exception_, ExceptionStatus
    from app.models.invoice import Invoice, InvoiceStatus

    db = SessionLocal()
    try:
        total_invoices = db.query(Invoice).count()
        pending = db.query(Invoice).filter(Invoice.status == InvoiceStatus.pending_approval).count()
        exceptions = db.query(Exception_).filter(
            Exception_.status.in_([ExceptionStatus.open, ExceptionStatus.assigned])
        ).count()

        pending_amount = (
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(Invoice.status == InvoiceStatus.pending_approval)
            .scalar()
        )

        posted_today = (
            db.query(Invoice)
            .filter(
                Invoice.status == InvoiceStatus.posted,
                func.date(Invoice.updated_at) == func.current_date(),
            )
            .count()
        )

        report = {
            "date": datetime.now(timezone.utc).isoformat(),
            "total_invoices": total_invoices,
            "pending_approval": pending,
            "pending_amount": float(pending_amount),
            "open_exceptions": exceptions,
            "posted_today": posted_today,
        }

        logger.info(f"Daily report generated: {report}")
        return report
    finally:
        db.close()
