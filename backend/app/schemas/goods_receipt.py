"""Goods-receipt-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class GRNLineItemCreate(BaseModel):
    po_line_id: uuid.UUID
    quantity_received: float
    condition_notes: str | None = None


class GRNLineItemResponse(BaseModel):
    id: uuid.UUID
    grn_id: uuid.UUID
    po_line_id: uuid.UUID
    quantity_received: float
    condition_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GRNCreate(BaseModel):
    grn_number: str = Field(..., min_length=1, max_length=100)
    po_id: uuid.UUID
    vendor_id: uuid.UUID
    receipt_date: date
    warehouse: str | None = None
    line_items: list[GRNLineItemCreate] = []


class GRNResponse(BaseModel):
    id: uuid.UUID
    grn_number: str
    po_id: uuid.UUID
    vendor_id: uuid.UUID
    receipt_date: date
    warehouse: str | None = None
    line_items: list[GRNLineItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
