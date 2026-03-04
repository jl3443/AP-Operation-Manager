"""Celery background tasks for invoice processing.

Defines async tasks for batch processing, scheduled matching,
duplicate detection scans, and auto-resolution.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.auto_resolution import auto_resolve_all
from app.services.duplicate_detection import check_duplicate

logger = logging.getLogger(__name__)


@celery_app.task(name="run_batch_matching")
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


@celery_app.task(name="run_auto_resolution")
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


@celery_app.task(name="run_duplicate_scan")
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


@celery_app.task(name="execute_resolution_plan_auto")
def execute_resolution_plan_auto(exception_id: str) -> dict:
    """Auto-generate a resolution plan and execute non-approval steps.

    Triggered automatically when an exception is created.
    Flow: generate plan → auto-approve → execute until human-approval step.
    """
    from app.models.resolution import PlanStatus
    from app.services import resolution_orchestrator

    db = SessionLocal()
    try:
        import uuid as _uuid

        # 1. Generate the plan
        plan = resolution_orchestrator.plan(db, _uuid.UUID(exception_id))
        logger.info(f"Auto-generated resolution plan for exception {exception_id}")

        # 2. Auto-approve
        plan.status = PlanStatus.approved
        db.commit()
        logger.info(f"Auto-approved plan {plan.id}")

        # 3. Execute until blocked at human-approval step
        result = resolution_orchestrator.execute(db, plan.id)
        logger.info(
            f"Auto-executed plan {plan.id}: status={result['plan_status']}, "
            f"blocked_at={result.get('blocked_at')}"
        )

        return {
            "exception_id": exception_id,
            "plan_id": str(plan.id),
            "plan_status": result["plan_status"],
            "blocked_at": result.get("blocked_at"),
        }
    except Exception as e:
        db.rollback()
        logger.warning(f"Auto plan generation failed for {exception_id}: {e}")
        return {"exception_id": exception_id, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="execute_resolution_plan_task")
def execute_resolution_plan_task(plan_id: str) -> dict:
    """Execute a resolution plan in the background.

    Called after a plan is approved and the user clicks 'Execute'.
    """
    from app.services import resolution_orchestrator

    db = SessionLocal()
    try:
        import uuid as _uuid

        result = resolution_orchestrator.execute(db, _uuid.UUID(plan_id))
        logger.info(f"Resolution plan {plan_id} execution: {result.get('plan_status')}")
        return result
    except Exception as e:
        db.rollback()
        logger.exception(f"Resolution plan {plan_id} execution failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="generate_resolution_plans_batch")
def generate_resolution_plans_batch() -> dict:
    """Generate AI resolution plans for all open exceptions that don't have one.

    Intended to run on a schedule (e.g., every 30 minutes) to automatically
    generate plans for new exceptions.
    """
    from app.models.exception import Exception_, ExceptionStatus
    from app.models.resolution import ResolutionPlan
    from app.services import resolution_orchestrator

    db = SessionLocal()
    try:
        # Find open/assigned exceptions without a resolution plan
        exceptions_with_plans = (
            db.query(ResolutionPlan.exception_id).distinct()
        )
        open_exceptions = (
            db.query(Exception_)
            .filter(
                Exception_.status.in_([
                    ExceptionStatus.open,
                    ExceptionStatus.assigned,
                ]),
                ~Exception_.id.in_(exceptions_with_plans),
            )
            .all()
        )

        results = {"planned": 0, "errors": []}
        for exc in open_exceptions:
            try:
                resolution_orchestrator.plan(db, exc.id)
                results["planned"] += 1
            except Exception as e:
                results["errors"].append(f"Exception {exc.id}: {e}")
                logger.error(f"Plan generation failed for exception {exc.id}: {e}")

        logger.info(
            f"Batch plan generation: {results['planned']} plans created, "
            f"{len(results['errors'])} errors"
        )
        return results
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="generate_daily_report")
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
