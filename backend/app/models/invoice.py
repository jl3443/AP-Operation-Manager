"""Invoice and InvoiceLineItem ORM models."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class InvoiceStatus(enum.StrEnum):
    draft = "draft"
    extracted = "extracted"
    matching = "matching"
    exception = "exception"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    posted = "posted"


class DocumentType(enum.StrEnum):
    invoice = "invoice"
    credit_memo = "credit_memo"
    debit_memo = "debit_memo"


class SourceChannel(enum.StrEnum):
    manual = "manual"
    email = "email"
    api = "api"
    csv = "csv"


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_due_date", "due_date"),
        Index("ix_invoices_created_at", "created_at"),
    )

    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    freight_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status", native_enum=False),
        nullable=False,
        default=InvoiceStatus.draft,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", native_enum=False),
        nullable=False,
        default=DocumentType.invoice,
    )
    source_channel: Mapped[SourceChannel] = mapped_column(
        Enum(SourceChannel, name="source_channel", native_enum=False),
        nullable=False,
        default=SourceChannel.manual,
    )
    file_storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    ocr_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    payment_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    posted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # relationships
    vendor = relationship("Vendor", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="invoice")
    exceptions = relationship("Exception_", back_populates="invoice")
    approval_tasks = relationship("ApprovalTask", back_populates="invoice")


class InvoiceLineItem(TimestampMixin, Base):
    __tablename__ = "invoice_line_items"
    __table_args__ = (Index("ix_invoice_line_items_invoice_id", "invoice_id"),)

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    po_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("po_line_items.id"), nullable=True
    )
    gl_account_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cost_center_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tax_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tax_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    ai_gl_prediction: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # relationships
    invoice = relationship("Invoice", back_populates="line_items")
    po_line = relationship("POLineItem", back_populates="invoice_line_items")
