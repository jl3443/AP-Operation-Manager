"""Goods-receipt-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GRNLineItemCreate(BaseModel):
    po_line_id: uuid.UUID
    quantity_received: float
    condition_notes: Optional[str] = None


class GRNLineItemResponse(BaseModel):
    id: uuid.UUID
    grn_id: uuid.UUID
    po_line_id: uuid.UUID
    quantity_received: float
    condition_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GRNCreate(BaseModel):
    grn_number: str = Field(..., min_length=1, max_length=100)
    po_id: uuid.UUID
    vendor_id: uuid.UUID
    receipt_date: date
    warehouse: Optional[str] = None
    line_items: List[GRNLineItemCreate] = []


class GRNResponse(BaseModel):
    id: uuid.UUID
    grn_number: str
    po_id: uuid.UUID
    vendor_id: uuid.UUID
    receipt_date: date
    warehouse: Optional[str] = None
    line_items: List[GRNLineItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
