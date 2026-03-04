"""Invoice-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.invoice import DocumentType, InvoiceStatus, SourceChannel
from app.schemas.common import PaginatedResponse

# ── Line Items ───────────────────────────────────────────────────────────


class InvoiceLineItemCreate(BaseModel):
    line_number: int
    description: str | None = None
    quantity: float = 1.0
    unit_price: float
    line_total: float
    po_line_id: uuid.UUID | None = None
    gl_account_code: str | None = None
    cost_center_code: str | None = None
    tax_code: str | None = None
    tax_amount: float = 0.0


class InvoiceLineItemResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    line_number: int
    description: str | None = None
    quantity: float
    unit_price: float
    line_total: float
    po_line_id: uuid.UUID | None = None
    gl_account_code: str | None = None
    cost_center_code: str | None = None
    tax_code: str | None = None
    tax_amount: float
    ai_gl_prediction: str | None = None
    ai_confidence: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Invoice ──────────────────────────────────────────────────────────────


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=100)
    vendor_id: uuid.UUID | None = None
    invoice_date: date
    due_date: date
    received_date: date | None = None
    currency: str = "USD"
    total_amount: float
    tax_amount: float = 0.0
    freight_amount: float = 0.0
    discount_amount: float = 0.0
    document_type: DocumentType = DocumentType.invoice
    source_channel: SourceChannel = SourceChannel.manual
    file_storage_path: str | None = None
    line_items: list[InvoiceLineItemCreate] = []


class InvoiceUpdate(BaseModel):
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    received_date: date | None = None
    currency: str | None = None
    total_amount: float | None = None
    tax_amount: float | None = None
    freight_amount: float | None = None
    discount_amount: float | None = None
    status: InvoiceStatus | None = None
    document_type: DocumentType | None = None
    source_channel: SourceChannel | None = None
    file_storage_path: str | None = None


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    vendor_id: uuid.UUID | None = None
    invoice_date: date
    due_date: date
    received_date: date | None = None
    currency: str
    total_amount: float
    tax_amount: float
    freight_amount: float
    discount_amount: float
    status: InvoiceStatus
    document_type: DocumentType
    source_channel: SourceChannel
    file_storage_path: str | None = None
    ocr_confidence_score: float | None = None
    posted_at: datetime | None = None
    line_items: list[InvoiceLineItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(PaginatedResponse[InvoiceResponse]):
    """Paginated list of invoices."""

    pass
