"""Resolution Orchestrator — plan, execute, and recheck resolution plans."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.audit import ActorType
from app.models.exception import Exception_, ExceptionStatus, ResolutionType
from app.models.goods_receipt import GRNLineItem
from app.models.invoice import Invoice, InvoiceStatus
from app.models.resolution import (
    ActionStatus,
    AutomationAction,
    PlanStatus,
    ResolutionPlan,
)
from app.services import audit_service
from app.services.action_handlers import get_handler
from app.services.ai_exception_resolver import generate_resolution_plan

logger = logging.getLogger(__name__)


def plan(db: Session, exception_id: uuid.UUID) -> ResolutionPlan:
    """Generate an AI resolution plan for the given exception."""
    return generate_resolution_plan(db, exception_id)


def execute(db: Session, plan_id: uuid.UUID) -> dict:
    """Execute an approved resolution plan step by step.

    Stops at any step that requires human approval and has not been approved yet.
    Returns a summary of execution progress.
    """
    rp = (
        db.query(ResolutionPlan)
        .options(joinedload(ResolutionPlan.actions))
        .filter(ResolutionPlan.id == plan_id)
        .first()
    )
    if not rp:
        raise ValueError(f"Resolution plan {plan_id} not found")

    if rp.status not in (PlanStatus.approved, PlanStatus.executing):
        raise ValueError(f"Plan must be approved before execution (current: {rp.status.value})")

    rp.status = PlanStatus.executing
    db.commit()

    executed = []
    blocked_at = None

    # Process actions in step_id order
    # Natural sort: extract numeric suffix so "S2" < "S10"
    def _step_sort_key(a):
        sid = a.step_id or "S0"
        num = "".join(c for c in sid if c.isdigit())
        return int(num) if num else 0

    actions = sorted(rp.actions, key=_step_sort_key)

    for action in actions:
        # Skip already-completed or failed actions
        if action.status in (ActionStatus.done, ActionStatus.failed, ActionStatus.skipped):
            executed.append({
                "step_id": action.step_id,
                "action_type": action.action_type,
                "status": action.status.value,
                "result": action.result_json,
            })
            continue

        # Check if human approval required but not yet given
        if action.requires_human_approval and action.status != ActionStatus.done:
            if not action.approved_at:
                action.status = ActionStatus.awaiting_approval
                db.commit()
                blocked_at = action.step_id
                executed.append({
                    "step_id": action.step_id,
                    "action_type": action.action_type,
                    "status": "awaiting_approval",
                    "message": "Requires human approval before execution",
                })
                break

        # Execute the action
        handler = get_handler(action.action_type)
        if not handler:
            action.status = ActionStatus.failed
            action.error_message = f"No handler for action type: {action.action_type}"
            db.commit()
            executed.append({
                "step_id": action.step_id,
                "action_type": action.action_type,
                "status": "failed",
                "error": action.error_message,
            })
            continue

        action.status = ActionStatus.running
        db.commit()

        try:
            result = handler(db, action)
            action.status = ActionStatus.done
            action.result_json = result
            action.executed_at = datetime.now(timezone.utc)
            db.commit()

            # Audit log
            audit_service.log_action(
                db,
                entity_type="automation_action",
                entity_id=action.id,
                action="action_executed",
                actor_type=ActorType.system,
                actor_name="Resolution Orchestrator",
                evidence={
                    "action_type": action.action_type,
                    "step_id": action.step_id,
                    "result_summary": str(result)[:500],
                },
            )
            db.commit()

            executed.append({
                "step_id": action.step_id,
                "action_type": action.action_type,
                "status": "done",
                "result": result,
            })

        except Exception as e:
            logger.exception("Action %s failed: %s", action.action_type, e)
            action.status = ActionStatus.failed
            action.error_message = str(e)
            db.commit()
            executed.append({
                "step_id": action.step_id,
                "action_type": action.action_type,
                "status": "failed",
                "error": str(e),
            })

    # Update plan status
    all_done = all(a.status in (ActionStatus.done, ActionStatus.skipped) for a in actions)
    any_failed = any(a.status == ActionStatus.failed for a in actions)

    if all_done:
        rp.status = PlanStatus.completed
    elif any_failed:
        rp.status = PlanStatus.failed
    # else: still executing (blocked at approval step)

    db.commit()

    return {
        "plan_id": str(plan_id),
        "plan_status": rp.status.value,
        "steps_executed": executed,
        "blocked_at": blocked_at,
        "all_complete": all_done,
    }


def recheck(db: Session, exception_id: uuid.UUID) -> dict:
    """Re-run matching for the exception's invoice and update statuses."""
    from app.services.match_service import auto_link_po_lines, run_three_way_match, run_two_way_match

    exc = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not exc:
        raise ValueError(f"Exception {exception_id} not found")

    inv = (
        db.query(Invoice)
        .options(joinedload(Invoice.line_items))
        .filter(Invoice.id == exc.invoice_id)
        .first()
    )
    if not inv:
        raise ValueError("Invoice not found for exception")

    # Auto-link PO lines first
    link_result = auto_link_po_lines(db, inv.id)
    db.refresh(inv)
    for li in inv.line_items:
        db.refresh(li)

    # Determine match type
    po_line_ids = [li.po_line_id for li in inv.line_items if li.po_line_id]
    use_three_way = False
    if po_line_ids:
        grn_count = (
            db.query(func.count(GRNLineItem.id))
            .filter(GRNLineItem.po_line_id.in_(po_line_ids))
            .scalar()
        ) or 0
        use_three_way = grn_count > 0

    if use_three_way:
        result = run_three_way_match(db, inv.id)
    else:
        result = run_two_way_match(db, inv.id)

    db.commit()

    # If match passed, close exception and advance invoice
    match_passed = result.match_status.value in ("matched", "tolerance_passed")
    if match_passed:
        exc.status = ExceptionStatus.resolved
        exc.resolution_type = ResolutionType.auto_resolved
        exc.resolution_notes = f"Resolved after recheck (score: {result.overall_score}%)"
        exc.resolved_at = datetime.now(timezone.utc)

        if inv.status == InvoiceStatus.exception:
            inv.status = InvoiceStatus.pending_approval

        db.commit()

    audit_service.log_action(
        db,
        entity_type="exception",
        entity_id=exception_id,
        action="recheck_match",
        actor_type=ActorType.system,
        actor_name="Resolution Orchestrator",
        evidence={
            "match_status": result.match_status.value,
            "score": result.overall_score,
            "exception_resolved": match_passed,
        },
    )
    db.commit()

    return {
        "match_status": result.match_status.value,
        "overall_score": result.overall_score,
        "match_type": result.match_type.value,
        "exception_resolved": match_passed,
        "po_link": link_result,
    }
