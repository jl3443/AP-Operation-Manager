"""Audit log response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    entity_type: str
    entity_id: uuid.UUID
    action: str
    actor_type: str
    actor_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    changes: Optional[dict] = None
    evidence: Optional[dict] = None

    model_config = {"from_attributes": True}
