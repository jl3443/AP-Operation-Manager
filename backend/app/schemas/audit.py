"""Audit log response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    entity_type: str
    entity_id: uuid.UUID
    action: str
    actor_type: str
    actor_id: uuid.UUID | None = None
    actor_name: str | None = None
    changes: dict | None = None
    evidence: dict | None = None

    model_config = {"from_attributes": True}
