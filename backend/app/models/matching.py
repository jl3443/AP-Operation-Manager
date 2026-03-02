"""MatchResult ORM model."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class MatchType(str, enum.Enum):
    two_way = "two_way"
    three_way = "three_way"


class MatchStatus(str, enum.Enum):
    matched = "matched"
    partial = "partial"
    unmatched = "unmatched"
    tolerance_passed = "tolerance_passed"


class MatchResult(TimestampMixin, Base):
    __tablename__ = "match_results"
    __table_args__ = (
        Index("ix_match_results_invoice_id", "invoice_id"),
        Index("ix_match_results_match_status", "match_status"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False
    )
    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType, name="match_type", native_enum=False), nullable=False
    )
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="match_status", native_enum=False), nullable=False
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    matched_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True
    )
    matched_grn_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    tolerance_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tolerance_config_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tolerance_configs.id"), nullable=True
    )

    # relationships
    invoice = relationship("Invoice", back_populates="match_results")
    matched_po = relationship("PurchaseOrder", back_populates="match_results")
    tolerance_config = relationship("ToleranceConfig")
