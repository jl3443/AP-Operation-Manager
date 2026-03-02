"""Vendor ORM model."""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Index, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class VendorStatus(str, enum.Enum):
    active = "active"
    on_hold = "on_hold"
    blocked = "blocked"


class VendorRiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Vendor(TimestampMixin, Base):
    __tablename__ = "vendors"
    __table_args__ = (
        Index("ix_vendors_name", "name"),
        Index("ix_vendors_status", "status"),
    )

    vendor_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True, default="US")
    payment_terms_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_account_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus, name="vendor_status", native_enum=False),
        nullable=False,
        default=VendorStatus.active,
    )
    risk_level: Mapped[VendorRiskLevel] = mapped_column(
        Enum(VendorRiskLevel, name="vendor_risk_level", native_enum=False),
        nullable=False,
        default=VendorRiskLevel.low,
    )

    # relationships
    invoices = relationship("Invoice", back_populates="vendor")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    goods_receipts = relationship("GoodsReceipt", back_populates="vendor")
