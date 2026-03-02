"""Configuration / reference-data ORM models.

Includes: ToleranceConfig, RuleVersion, PolicyDocument, PolicyRule,
GLAccount, CostCenter, PaymentTerms, Currency, ExchangeRate, Notification.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


# ── Enums ────────────────────────────────────────────────────────────────


class ToleranceScope(str, enum.Enum):
    global_ = "global"
    vendor = "vendor"
    category = "category"
    currency = "currency"


class RuleVersionStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    published = "published"
    archived = "archived"


class ExtractionStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class PolicyRuleStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class NotificationType(str, enum.Enum):
    approval_request = "approval_request"
    exception_assigned = "exception_assigned"
    invoice_status_change = "invoice_status_change"
    escalation = "escalation"
    system = "system"


# ── Models ───────────────────────────────────────────────────────────────


class ToleranceConfig(TimestampMixin, Base):
    __tablename__ = "tolerance_configs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[ToleranceScope] = mapped_column(
        Enum(ToleranceScope, name="tolerance_scope", native_enum=False), nullable=False
    )
    scope_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount_tolerance_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    amount_tolerance_abs: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    quantity_tolerance_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class RuleVersion(TimestampMixin, Base):
    __tablename__ = "rule_versions"

    rule_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[RuleVersionStatus] = mapped_column(
        Enum(RuleVersionStatus, name="rule_version_status", native_enum=False),
        nullable=False,
        default=RuleVersionStatus.draft,
    )
    rule_definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policy_documents.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    published_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    source_document = relationship("PolicyDocument", back_populates="rule_versions")


class PolicyDocument(TimestampMixin, Base):
    __tablename__ = "policy_documents"

    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, name="extraction_status", native_enum=False),
        nullable=False,
        default=ExtractionStatus.pending,
    )
    extracted_rules_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # relationships
    rule_versions = relationship("RuleVersion", back_populates="source_document")
    policy_rules = relationship("PolicyRule", back_populates="policy_document", cascade="all, delete-orphan")


class PolicyRule(TimestampMixin, Base):
    __tablename__ = "policy_rules"

    policy_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policy_documents.id", ondelete="CASCADE"), nullable=False
    )
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(100), nullable=False)
    conditions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[PolicyRuleStatus] = mapped_column(
        Enum(PolicyRuleStatus, name="policy_rule_status", native_enum=False),
        nullable=False,
        default=PolicyRuleStatus.pending,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    policy_document = relationship("PolicyDocument", back_populates="policy_rules")


class GLAccount(TimestampMixin, Base):
    __tablename__ = "gl_accounts"

    account_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(100), nullable=False)


class CostCenter(TimestampMixin, Base):
    __tablename__ = "cost_centers"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    manager = relationship("User")


class PaymentTerms(TimestampMixin, Base):
    __tablename__ = "payment_terms"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    days_due: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    discount_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    discount_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Currency(TimestampMixin, Base):
    __tablename__ = "currencies"

    currency_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


class ExchangeRate(TimestampMixin, Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        Index("ix_exchange_rates_pair_date", "from_currency", "to_currency", "effective_date"),
    )

    from_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    to_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type", native_enum=False), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationships
    user = relationship("User", back_populates="notifications")
