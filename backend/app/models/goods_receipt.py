"""GoodsReceipt and GRNLineItem ORM models."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class GoodsReceipt(TimestampMixin, Base):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        Index("ix_goods_receipts_po_id", "po_id"),
        Index("ix_goods_receipts_vendor_id", "vendor_id"),
    )

    grn_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False
    )
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    warehouse: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # relationships
    purchase_order = relationship("PurchaseOrder", back_populates="goods_receipts")
    vendor = relationship("Vendor", back_populates="goods_receipts")
    line_items = relationship("GRNLineItem", back_populates="goods_receipt", cascade="all, delete-orphan")


class GRNLineItem(TimestampMixin, Base):
    __tablename__ = "grn_line_items"
    __table_args__ = (
        Index("ix_grn_line_items_grn_id", "grn_id"),
    )

    grn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False
    )
    po_line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("po_line_items.id"), nullable=False
    )
    quantity_received: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    condition_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # relationships
    goods_receipt = relationship("GoodsReceipt", back_populates="line_items")
    po_line = relationship("POLineItem", back_populates="grn_line_items")
