"""ApprovalTask and ApprovalMatrix ORM models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    escalated = "escalated"
    timed_out = "timed_out"


class AIRecommendation(str, enum.Enum):
    approve = "approve"
    reject = "reject"
    review = "review"


class ApprovalTask(TimestampMixin, Base):
    __tablename__ = "approval_tasks"
    __table_args__ = (
        Index("ix_approval_tasks_invoice_id", "invoice_id"),
        Index("ix_approval_tasks_approver_id", "approver_id"),
        Index("ix_approval_tasks_status", "status"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approval_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approval_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status", native_enum=False),
        nullable=False,
        default=ApprovalStatus.pending,
    )
    ai_recommendation: Mapped[AIRecommendation | None] = mapped_column(
        Enum(AIRecommendation, name="ai_recommendation", native_enum=False), nullable=True
    )
    ai_recommendation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    invoice = relationship("Invoice", back_populates="approval_tasks")
    approver = relationship("User", back_populates="approval_tasks", foreign_keys=[approver_id])


class ApprovalMatrix(TimestampMixin, Base):
    __tablename__ = "approval_matrix"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conditions: Mapped[dict] = mapped_column(JSON, nullable=False)
    approver_role: Mapped[str] = mapped_column(String(100), nullable=False)
    approver_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
