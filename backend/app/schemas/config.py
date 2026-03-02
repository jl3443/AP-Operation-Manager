"""Tolerance configuration schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ToleranceConfigResponse(BaseModel):
    id: uuid.UUID
    name: str
    scope: str
    scope_value: Optional[str] = None
    amount_tolerance_pct: float
    amount_tolerance_abs: float
    quantity_tolerance_pct: float
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ToleranceConfigCreate(BaseModel):
    name: str
    scope: str = "global"
    scope_value: Optional[str] = None
    amount_tolerance_pct: float = 5.0
    amount_tolerance_abs: float = 100.0
    quantity_tolerance_pct: float = 2.0
    is_active: bool = True


class ToleranceConfigUpdate(BaseModel):
    name: Optional[str] = None
    amount_tolerance_pct: Optional[float] = None
    amount_tolerance_abs: Optional[float] = None
    quantity_tolerance_pct: Optional[float] = None
    is_active: Optional[bool] = None
