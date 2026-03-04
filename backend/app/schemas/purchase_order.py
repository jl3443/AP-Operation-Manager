"""Purchase-order-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.purchase_order import POStatus


class POLineItemCreate(BaseModel):
    line_number: int
    description: str | None = None
    quantity_ordered: float
    unit_price: float
    line_total: float
    quantity_received: float = 0.0
    quantity_invoiced: float = 0.0


class POLineItemResponse(BaseModel):
    id: uuid.UUID
    po_id: uuid.UUID
    line_number: int
    description: str | None = None
    quantity_ordered: float
    unit_price: float
    line_total: float
    quantity_received: float
    quantity_invoiced: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class POCreate(BaseModel):
    po_number: str = Field(..., min_length=1, max_length=100)
    vendor_id: uuid.UUID
    order_date: date
    delivery_date: date | None = None
    currency: str = "USD"
    total_amount: float
    status: POStatus = POStatus.open
    line_items: list[POLineItemCreate] = []


class POResponse(BaseModel):
    id: uuid.UUID
    po_number: str
    vendor_id: uuid.UUID
    order_date: date
    delivery_date: date | None = None
    currency: str
    total_amount: float
    status: POStatus
    line_items: list[POLineItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
