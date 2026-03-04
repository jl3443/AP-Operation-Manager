"""User ORM model."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(enum.StrEnum):
    ap_clerk = "ap_clerk"
    ap_analyst = "ap_analyst"
    approver = "approver"
    admin = "admin"
    auditor = "auditor"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.ap_clerk,
    )
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cost_center_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # relationships
    approval_tasks = relationship("ApprovalTask", back_populates="approver", foreign_keys="ApprovalTask.approver_id")
    assigned_exceptions = relationship(
        "Exception_", back_populates="assigned_user", foreign_keys="Exception_.assigned_to"
    )
    exception_comments = relationship("ExceptionComment", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
