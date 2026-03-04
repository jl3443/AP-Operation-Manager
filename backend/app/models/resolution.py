"""ResolutionPlan and AutomationAction ORM models for the AI Exception Resolution Engine."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class PlanStatus(enum.StrEnum):
    draft = "draft"
    approved = "approved"
    executing = "executing"
    completed = "completed"
    failed = "failed"


class AutomationLevel(enum.StrEnum):
    auto = "auto"
    assisted = "assisted"
    manual = "manual"


class ActionStatus(enum.StrEnum):
    pending = "pending"
    awaiting_approval = "awaiting_approval"
    running = "running"
    done = "done"
    failed = "failed"
    skipped = "skipped"


class ResolutionPlan(TimestampMixin, Base):
    """AI-generated resolution plan for an exception."""

    __tablename__ = "resolution_plans"
    __table_args__ = (
        Index("ix_resolution_plans_exception_id", "exception_id"),
        Index("ix_resolution_plans_status", "status"),
    )

    exception_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exceptions.id"), nullable=False)
    plan_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status", native_enum=False),
        nullable=False,
        default=PlanStatus.draft,
    )
    automation_level: Mapped[AutomationLevel] = mapped_column(
        Enum(AutomationLevel, name="automation_level", native_enum=False),
        nullable=False,
        default=AutomationLevel.assisted,
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    recheck_strategy: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    audit_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    exception = relationship("Exception_", backref="resolution_plans")
    approver = relationship("User", foreign_keys=[approved_by])
    actions: Mapped[list[AutomationAction]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="AutomationAction.step_id"
    )


class AutomationAction(TimestampMixin, Base):
    """A single executable step within a resolution plan."""

    __tablename__ = "automation_actions"
    __table_args__ = (
        Index("ix_automation_actions_plan_id", "plan_id"),
        Index("ix_automation_actions_status", "status"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resolution_plans.id"), nullable=False)
    step_id: Mapped[str] = mapped_column(String(20), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    params_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, name="action_status", native_enum=False),
        nullable=False,
        default=ActionStatus.pending,
    )
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    plan: Mapped[ResolutionPlan] = relationship(back_populates="actions")
