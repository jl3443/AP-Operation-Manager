"""Invoice CRUD service."""

from __future__ import annotations

import math
import uuid
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


def create_invoice(db: Session, payload: InvoiceCreate) -> Invoice:
    """Create an invoice with its line items."""
    invoice = Invoice(
        invoice_number=payload.invoice_number,
        vendor_id=payload.vendor_id,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        received_date=payload.received_date,
        currency=payload.currency,
        total_amount=payload.total_amount,
        tax_amount=payload.tax_amount,
        freight_amount=payload.freight_amount,
        discount_amount=payload.discount_amount,
        document_type=payload.document_type,
        source_channel=payload.source_channel,
        file_storage_path=payload.file_storage_path,
        status=InvoiceStatus.draft,
    )
    db.add(invoice)
    db.flush()  # get the id

    for li in payload.line_items:
        line = InvoiceLineItem(
            invoice_id=invoice.id,
            line_number=li.line_number,
            description=li.description,
            quantity=li.quantity,
            unit_price=li.unit_price,
            line_total=li.line_total,
            po_line_id=li.po_line_id,
            gl_account_code=li.gl_account_code,
            cost_center_code=li.cost_center_code,
            tax_code=li.tax_code,
            tax_amount=li.tax_amount,
        )
        db.add(line)

    db.commit()
    db.refresh(invoice)
    return invoice


def get_invoice(db: Session, invoice_id: uuid.UUID) -> Optional[Invoice]:
    """Return a single invoice with eager-loaded line items."""
    return (
        db.query(Invoice)
        .options(joinedload(Invoice.line_items))
        .filter(Invoice.id == invoice_id)
        .first()
    )


def list_invoices(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    vendor_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    """Return a paginated, filterable list of invoices."""
    query = db.query(Invoice)

    if status:
        query = query.filter(Invoice.status == status)
    if vendor_id:
        query = query.filter(Invoice.vendor_id == vendor_id)
    if search:
        query = query.filter(Invoice.invoice_number.ilike(f"%{search}%"))

    total = query.count()

    # sorting
    sort_col = getattr(Invoice, sort_by, Invoice.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    items = (
        query.options(joinedload(Invoice.line_items))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # deduplicate items from joinedload
    seen: set[uuid.UUID] = set()
    unique_items = []
    for item in items:
        if item.id not in seen:
            seen.add(item.id)
            unique_items.append(item)

    return {
        "items": unique_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, math.ceil(total / page_size)),
    }


def update_invoice(
    db: Session, invoice_id: uuid.UUID, payload: InvoiceUpdate
) -> Optional[Invoice]:
    """Partially update an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return None

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)
    return invoice
