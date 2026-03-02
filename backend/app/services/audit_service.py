"""Generic audit-logging service."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit import ActorType, AuditLog


def log_action(
    db: Session,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    actor_type: ActorType = ActorType.user,
    actor_id: Optional[uuid.UUID] = None,
    actor_name: Optional[str] = None,
    changes: Optional[dict[str, Any]] = None,
    evidence: Optional[dict[str, Any]] = None,
    rule_version_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    session_id: Optional[str] = None,
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
