"""Invoice-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.invoice import DocumentType, InvoiceStatus, SourceChannel
from app.schemas.common import PaginatedResponse


# ── Line Items ───────────────────────────────────────────────────────────


class InvoiceLineItemCreate(BaseModel):
    line_number: int
    description: Optional[str] = None
    quantity: float = 1.0
    unit_price: float
    line_total: float
    po_line_id: Optional[uuid.UUID] = None
    gl_account_code: Optional[str] = None
    cost_center_code: Optional[str] = None
    tax_code: Optional[str] = None
    tax_amount: float = 0.0


class InvoiceLineItemResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    line_number: int
    description: Optional[str] = None
    quantity: float
    unit_price: float
    line_total: float
    po_line_id: Optional[uuid.UUID] = None
    gl_account_code: Optional[str] = None
    cost_center_code: Optional[str] = None
    tax_code: Optional[str] = None
    tax_amount: float
    ai_gl_prediction: Optional[str] = None
    ai_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Invoice ──────────────────────────────────────────────────────────────


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=100)
    vendor_id: Optional[uuid.UUID] = None
    invoice_date: date
    due_date: date
    received_date: Optional[date] = None
    currency: str = "USD"
    total_amount: float
    tax_amount: float = 0.0
    freight_amount: float = 0.0
    discount_amount: float = 0.0
    document_type: DocumentType = DocumentType.invoice
    source_channel: SourceChannel = SourceChannel.manual
    file_storage_path: Optional[str] = None
    line_items: List[InvoiceLineItemCreate] = []


class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    received_date: Optional[date] = None
    currency: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    freight_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    status: Optional[InvoiceStatus] = None
    document_type: Optional[DocumentType] = None
    source_channel: Optional[SourceChannel] = None
    file_storage_path: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    vendor_id: Optional[uuid.UUID] = None
    invoice_date: date
    due_date: date
    received_date: Optional[date] = None
    currency: str
    total_amount: float
    tax_amount: float
    freight_amount: float
    discount_amount: float
    status: InvoiceStatus
    document_type: DocumentType
    source_channel: SourceChannel
    file_storage_path: Optional[str] = None
    ocr_confidence_score: Optional[float] = None
    posted_at: Optional[datetime] = None
    line_items: List[InvoiceLineItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Paginated list of invoices."""

    pass
