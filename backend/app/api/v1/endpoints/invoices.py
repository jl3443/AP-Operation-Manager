"""Invoice endpoints: CRUD, OCR extract, match, audit trail."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit import ActorType, AuditLog
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
)
from app.services import audit_service, invoice_service, match_service
from app.services.ocr_service import mock_extract_invoice

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/upload", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def upload_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an invoice (manual entry or after OCR extraction)."""
    invoice = invoice_service.create_invoice(db, payload)
    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="created",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
    )
    db.commit()
    return invoice


@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    vendor_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List invoices with pagination, filtering, and sorting."""
    vid = uuid.UUID(vendor_id) if vendor_id else None
    result = invoice_service.list_invoices(
        db,
        page=page,
        page_size=page_size,
        status=status,
        vendor_id=vid,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return result


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single invoice by ID."""
    invoice = invoice_service.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: uuid.UUID,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Partially update an invoice."""
    invoice = invoice_service.update_invoice(db, invoice_id, payload)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="updated",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        changes=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    return invoice


@router.post("/{invoice_id}/extract")
def extract_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger mock OCR extraction for an invoice."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    result = mock_extract_invoice(invoice.file_storage_path)

    invoice.ocr_confidence_score = result["confidence"]
    invoice.status = InvoiceStatus.extracted
    db.commit()

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="ocr_extracted",
        actor_type=ActorType.ai_agent,
        actor_name="OCR Service",
        evidence={"confidence": result["confidence"]},
    )
    db.commit()

    return {"message": "OCR extraction complete", "data": result}


@router.post("/{invoice_id}/match")
def match_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run two-way matching for an invoice against PO data."""
    try:
        result = match_service.run_two_way_match(db, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice_id,
        action="matched",
        actor_type=ActorType.system,
        actor_name="Match Engine",
        changes={"match_status": result.match_status.value, "score": result.overall_score},
    )
    db.commit()

    return {
        "match_id": str(result.id),
        "match_status": result.match_status,
        "overall_score": result.overall_score,
        "details": result.details,
    }


@router.get("/{invoice_id}/audit-trail")
def get_audit_trail(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return audit log entries for a specific invoice."""
    entries = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == "invoice",
            AuditLog.entity_id == invoice_id,
        )
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return [
        {
            "id": str(e.id),
            "timestamp": e.timestamp.isoformat(),
            "action": e.action,
            "actor_type": e.actor_type,
            "actor_name": e.actor_name,
            "changes": e.changes,
            "evidence": e.evidence,
        }
        for e in entries
    ]
