"""Exception_ and ExceptionComment ORM models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ExceptionType(enum.StrEnum):
    missing_po = "missing_po"
    amount_variance = "amount_variance"
    quantity_variance = "quantity_variance"
    duplicate_invoice = "duplicate_invoice"
    vendor_mismatch = "vendor_mismatch"
    tax_variance = "tax_variance"
    expired_po = "expired_po"
    prepayment = "prepayment"
    currency_variance = "currency_variance"
    contract_price_variance = "contract_price_variance"
    vendor_on_hold = "vendor_on_hold"
    partial_delivery_overrun = "partial_delivery_overrun"


class ExceptionSeverity(enum.StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ExceptionStatus(enum.StrEnum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"


class ResolutionType(enum.StrEnum):
    auto_resolved = "auto_resolved"
    manual_override = "manual_override"
    vendor_credit = "vendor_credit"
    po_amendment = "po_amendment"
    tolerance_applied = "tolerance_applied"
    rejected = "rejected"


class Exception_(TimestampMixin, Base):
    """Named Exception_ to avoid conflict with the built-in Exception class."""

    __tablename__ = "exceptions"
    __table_args__ = (
        Index("ix_exceptions_invoice_id", "invoice_id"),
        Index("ix_exceptions_status", "status"),
        Index("ix_exceptions_severity", "severity"),
        Index("ix_exceptions_assigned_to", "assigned_to"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    exception_type: Mapped[ExceptionType] = mapped_column(
        Enum(ExceptionType, name="exception_type", native_enum=False), nullable=False
    )
    severity: Mapped[ExceptionSeverity] = mapped_column(
        Enum(ExceptionSeverity, name="exception_severity", native_enum=False), nullable=False
    )
    status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus, name="exception_status", native_enum=False),
        nullable=False,
        default=ExceptionStatus.open,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_type: Mapped[ResolutionType | None] = mapped_column(
        Enum(ResolutionType, name="resolution_type", native_enum=False), nullable=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # AI-powered analysis fields
    ai_suggested_resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_severity_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    invoice = relationship("Invoice", back_populates="exceptions")
    assigned_user = relationship("User", back_populates="assigned_exceptions", foreign_keys=[assigned_to])
    comments = relationship("ExceptionComment", back_populates="exception", cascade="all, delete-orphan")


class ExceptionComment(TimestampMixin, Base):
    __tablename__ = "exception_comments"
    __table_args__ = (Index("ix_exception_comments_exception_id", "exception_id"),)

    exception_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exceptions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # relationships
    exception = relationship("Exception_", back_populates="comments")
    user = relationship("User", back_populates="exception_comments")
