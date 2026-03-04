"""Generic audit-logging service."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import ActorType, AuditLog


def log_action(
    db: Session,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    actor_type: ActorType = ActorType.user,
    actor_id: uuid.UUID | None = None,
    actor_name: str | None = None,
    changes: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    rule_version_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    session_id: str | None = None,
) -> AuditLog:
    """Insert an audit-log row and return it."""
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_name=actor_name,
        changes=changes,
        evidence=evidence,
        rule_version_id=rule_version_id,
        ip_address=ip_address,
        session_id=session_id,
    )
    db.add(entry)
    db.flush()
    return entry
