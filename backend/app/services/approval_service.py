"""Approval workflow service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    AIRecommendation,
    ApprovalMatrix,
    ApprovalStatus,
    ApprovalTask,
)
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User, UserRole


def create_approval_tasks(db: Session, invoice_id: uuid.UUID) -> List[ApprovalTask]:
    """Generate approval tasks for an invoice based on the approval matrix.

    Falls back to a simple default rule if no matrix rows are active.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    # Fetch active matrix rules ordered by priority
    matrix_rules = (
        db.query(ApprovalMatrix)
        .filter(ApprovalMatrix.is_active == True)
        .order_by(ApprovalMatrix.priority.asc())
        .all()
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
            approver = (
                db.query(User)
                .filter(User.role == rule.approver_role, User.is_active == True)
                .first()
            )
            if not approver:
                continue

            task = ApprovalTask(
                invoice_id=invoice.id,
                approver_id=approver.id,
                approval_level=rule.approver_level,
                approval_order=rule.priority,
                status=ApprovalStatus.pending,
                ai_recommendation=AIRecommendation.approve
                if float(invoice.total_amount) < 5000
                else AIRecommendation.review,
                ai_recommendation_reason="Auto-recommendation based on invoice amount",
            )
            db.add(task)
            tasks_created.append(task)
    else:
        # Default: assign to any active approver
        approver = (
            db.query(User)
            .filter(User.role == UserRole.approver, User.is_active == True)
            .first()
        )
        if approver:
            task = ApprovalTask(
                invoice_id=invoice.id,
                approver_id=approver.id,
                approval_level=1,
                approval_order=1,
                status=ApprovalStatus.pending,
                ai_recommendation=AIRecommendation.approve,
                ai_recommendation_reason="Default single-level approval",
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
    comments: Optional[str] = None,
) -> ApprovalTask:
    """Approve or reject an approval task."""
    task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
    if not task:
        raise ValueError(f"ApprovalTask {task_id} not found")
    if task.status != ApprovalStatus.pending:
        raise ValueError(f"ApprovalTask {task_id} is not pending (status={task.status})")

    task.status = ApprovalStatus.approved if approved else ApprovalStatus.rejected
    task.decision_at = datetime.now(timezone.utc)
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
