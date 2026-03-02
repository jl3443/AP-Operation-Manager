"""Invoice endpoints: CRUD, OCR extract, file upload, match, audit trail."""

from __future__ import annotations

import uuid
from datetime import date as _date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.audit import ActorType, AuditLog
from app.models.goods_receipt import GRNLineItem
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
)
from app.services import audit_service, invoice_service, match_service, s3_service
from app.services.classification_service import classify_and_validate
from app.services.ocr_service import extract_invoice, mock_extract_invoice

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


@router.post("/upload-file", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def upload_invoice_file(
    file: UploadFile = File(...),
    vendor_id: uuid.UUID = Query(..., description="Vendor ID for the invoice"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an invoice PDF/image, store in S3, and create a draft invoice record."""
    from app.models.vendor import Vendor

    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    file_content = file.file.read()
    file_id = str(uuid.uuid4())
    filename = file.filename or "invoice.pdf"
    s3_key = f"invoices/{file_id}/{filename}"

    s3_service.upload_file(file_content, s3_key, content_type=file.content_type or "application/pdf")

    invoice = Invoice(
        invoice_number=f"DRAFT-{file_id[:8].upper()}",
        vendor_id=vendor_id,
        invoice_date=_date.today(),
        due_date=_date.today(),
        currency="USD",
        total_amount=0,
        status=InvoiceStatus.draft,
        file_storage_path=s3_key,
    )
    db.add(invoice)
    db.flush()

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="uploaded",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        evidence={"filename": filename, "size_bytes": len(file_content)},
    )
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}/download")
def download_invoice_file(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a presigned URL for the invoice document."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if not invoice.file_storage_path:
        raise HTTPException(status_code=404, detail="No file associated with this invoice")

    download_url = s3_service.generate_presigned_url(invoice.file_storage_path)
    return {"download_url": download_url}


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
def extract_invoice_endpoint(
    invoice_id: uuid.UUID,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extract data from an invoice using AI Vision or fallback to mock.

    Runs as a sync handler so that the blocking Claude API call is executed
    in FastAPI's thread pool instead of blocking the async event loop.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if file:
        file_content = file.file.read()
        result = extract_invoice(file_content, filename=file.filename or "invoice.pdf")
    elif invoice.file_storage_path:
        # Download from S3 and extract
        file_content = s3_service.download_file(invoice.file_storage_path)
        filename = invoice.file_storage_path.rsplit("/", 1)[-1] if "/" in invoice.file_storage_path else "invoice.pdf"
        result = extract_invoice(file_content, filename=filename)
    else:
        result = mock_extract_invoice(invoice.file_storage_path)

    # Update invoice fields from extraction
    extracted = result.get("extracted_data", {})
    invoice.ocr_confidence_score = result["confidence"]
    if extracted.get("invoice_number"):
        invoice.invoice_number = extracted["invoice_number"]
    if extracted.get("invoice_date"):
        try:
            invoice.invoice_date = _date.fromisoformat(extracted["invoice_date"])
        except ValueError:
            pass
    if extracted.get("due_date"):
        try:
            invoice.due_date = _date.fromisoformat(extracted["due_date"])
        except ValueError:
            pass
    if extracted.get("total_amount"):
        invoice.total_amount = extracted["total_amount"]
    if extracted.get("tax_amount") is not None:
        invoice.tax_amount = extracted["tax_amount"]
    if extracted.get("freight_amount") is not None:
        invoice.freight_amount = extracted["freight_amount"]
    if extracted.get("discount_amount") is not None:
        invoice.discount_amount = extracted["discount_amount"]
    if extracted.get("currency"):
        invoice.currency = extracted["currency"]

    # Persist extracted line items (replace existing ones)
    extracted_lines = extracted.get("line_items", [])
    if extracted_lines:
        db.query(InvoiceLineItem).filter(
            InvoiceLineItem.invoice_id == invoice.id
        ).delete()
        for li in extracted_lines:
            db.add(InvoiceLineItem(
                invoice_id=invoice.id,
                line_number=li.get("line_number", 1),
                description=li.get("description"),
                quantity=li.get("quantity", 1),
                unit_price=li.get("unit_price", 0),
                line_total=li.get("line_total", 0),
                tax_amount=li.get("tax_amount", 0),
                ai_gl_prediction=li.get("ai_gl_prediction"),
                ai_confidence=li.get("ai_confidence"),
            ))

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

    # Post-OCR: Run AI classification and validation agent
    classification = classify_and_validate(
        db,
        invoice_id=invoice.id,
        extracted_data=extracted,
        ocr_confidence=result["confidence"],
    )

    return {
        "message": "OCR extraction and classification complete",
        "data": result,
        "classification": classification,
    }


@router.post("/{invoice_id}/match")
def match_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run matching for an invoice against PO (and optionally GRN) data.

    Automatically selects 3-way matching when GRN data exists for the
    referenced PO lines, otherwise falls back to 2-way matching.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Determine match type based on GRN availability
    po_line_ids = [
        li.po_line_id
        for li in invoice.line_items
        if li.po_line_id
    ]

    use_three_way = False
    if po_line_ids:
        grn_count = (
            db.query(func.count(GRNLineItem.id))
            .filter(GRNLineItem.po_line_id.in_(po_line_ids))
            .scalar()
        ) or 0
        use_three_way = grn_count > 0

    try:
        if use_three_way:
            result = match_service.run_three_way_match(db, invoice_id)
        else:
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
        changes={
            "match_type": result.match_type.value,
            "match_status": result.match_status.value,
            "score": result.overall_score,
        },
    )
    db.commit()

    return {
        "match_id": str(result.id),
        "match_type": result.match_type,
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


@router.post("/batch-process")
def batch_process_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process all draft/extracted invoices through the matching pipeline.

    Returns a summary of results: touchless, exceptions, escalated.
    """
    # Find invoices ready for matching (extracted status)
    invoices = (
        db.query(Invoice)
        .filter(Invoice.status.in_([InvoiceStatus.extracted, InvoiceStatus.draft]))
        .all()
    )

    results = {
        "total_processed": 0,
        "touchless": 0,
        "exceptions": 0,
        "pending_approval": 0,
        "errors": 0,
        "details": [],
    }

    for inv in invoices:
        try:
            # Determine match type
            po_line_ids = [li.po_line_id for li in inv.line_items if li.po_line_id]
            use_three_way = False
            if po_line_ids:
                grn_count = (
                    db.query(func.count(GRNLineItem.id))
                    .filter(GRNLineItem.po_line_id.in_(po_line_ids))
                    .scalar()
                ) or 0
                use_three_way = grn_count > 0

            if use_three_way:
                match_result = match_service.run_three_way_match(db, inv.id)
            else:
                match_result = match_service.run_two_way_match(db, inv.id)

            results["total_processed"] += 1

            if match_result.match_status.value in ("matched", "tolerance_passed"):
                results["touchless"] += 1
                status_label = "touchless"
            elif inv.status == InvoiceStatus.exception:
                results["exceptions"] += 1
                status_label = "exception"
            else:
                results["pending_approval"] += 1
                status_label = "pending_approval"

            results["details"].append({
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "status": status_label,
                "match_score": match_result.overall_score,
            })

            audit_service.log_action(
                db,
                entity_type="invoice",
                entity_id=inv.id,
                action="batch_matched",
                actor_type=ActorType.system,
                actor_name="Batch Processor",
                changes={
                    "match_type": match_result.match_type.value,
                    "match_status": match_result.match_status.value,
                },
            )
            db.commit()
        except Exception as e:
            results["errors"] += 1
            results["details"].append({
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "status": "error",
                "error": str(e),
            })
            db.rollback()

    return results
