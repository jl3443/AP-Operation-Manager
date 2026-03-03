"""PurchaseOrder and POLineItem ORM models."""

from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class POStatus(str, enum.Enum):
    open = "open"
    partially_received = "partially_received"
    fully_received = "fully_received"
    service_completed = "service_completed"
    closed = "closed"
    cancelled = "cancelled"


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_status", "status"),
    )

    po_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    total_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus, name="po_status", native_enum=False),
        nullable=False,
        default=POStatus.open,
    )

    # relationships
    vendor = relationship("Vendor", back_populates="purchase_orders")
    line_items = relationship("POLineItem", back_populates="purchase_order", cascade="all, delete-orphan")
    goods_receipts = relationship("GoodsReceipt", back_populates="purchase_order")
    match_results = relationship("MatchResult", back_populates="matched_po")


class POLineItem(TimestampMixin, Base):
    __tablename__ = "po_line_items"
    __table_args__ = (
        Index("ix_po_line_items_po_id", "po_id"),
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quantity_ordered: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    quantity_received: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    quantity_invoiced: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)

    # relationships
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")
    grn_line_items = relationship("GRNLineItem", back_populates="po_line")
    invoice_line_items = relationship("InvoiceLineItem", back_populates="po_line")
