"""Invoice endpoints: CRUD, OCR extract, file upload, match, audit trail."""

from __future__ import annotations

import contextlib
import json
import time
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from datetime import date as _date

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
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
from app.services.approval_service import _get_ai_recommendation, create_approval_tasks
from app.services.classification_service import classify_and_validate
from app.services.ocr_service import extract_invoice

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
    vendor_id: uuid.UUID | None = Query(None, description="Vendor ID for the invoice (optional — AI will auto-match)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an invoice PDF/image, store in S3, and create a draft invoice record."""
    if vendor_id:
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
    status: str | None = Query(None),
    vendor_id: str | None = Query(None),
    search: str | None = Query(None),
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
    file: UploadFile | None = File(None),
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
        raise HTTPException(
            status_code=400,
            detail="No file available for extraction. Upload a file first.",
        )

    # Update invoice fields from extraction
    extracted = result.get("extracted_data", {})
    invoice.ocr_confidence_score = result["confidence"]
    if extracted.get("invoice_number"):
        invoice.invoice_number = extracted["invoice_number"]
    if extracted.get("invoice_date"):
        with contextlib.suppress(ValueError):
            invoice.invoice_date = _date.fromisoformat(extracted["invoice_date"])
    if extracted.get("due_date"):
        with contextlib.suppress(ValueError):
            invoice.due_date = _date.fromisoformat(extracted["due_date"])
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
        db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice.id).delete()
        for li in extracted_lines:
            db.add(
                InvoiceLineItem(
                    invoice_id=invoice.id,
                    line_number=li.get("line_number", 1),
                    description=li.get("description"),
                    quantity=li.get("quantity", 1),
                    unit_price=li.get("unit_price", 0),
                    line_total=li.get("line_total", 0),
                    tax_amount=li.get("tax_amount", 0),
                    ai_gl_prediction=li.get("ai_gl_prediction"),
                    ai_confidence=li.get("ai_confidence"),
                )
            )

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

    Automatically discovers and links PO lines when not already set (e.g. after OCR).
    Selects 3-way matching when GRN data exists, otherwise 2-way.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Auto-link PO lines if not already set (critical for OCR-extracted invoices)
    link_result = match_service.auto_link_po_lines(db, invoice_id)

    # Re-read invoice after potential linking
    db.refresh(invoice)
    for li in invoice.line_items:
        db.refresh(li)

    # Determine match type based on GRN availability
    po_line_ids = [li.po_line_id for li in invoice.line_items if li.po_line_id]

    use_three_way = False
    if po_line_ids:
        grn_count = (db.query(func.count(GRNLineItem.id)).filter(GRNLineItem.po_line_id.in_(po_line_ids)).scalar()) or 0
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
            "po_link": link_result,
        },
    )
    db.commit()

    return {
        "match_id": str(result.id),
        "match_type": result.match_type,
        "match_status": result.match_status,
        "overall_score": result.overall_score,
        "details": result.details,
        "po_link": link_result,
    }


@router.post("/{invoice_id}/approve")
def approve_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve an invoice directly. Updates status and resolves any pending approval tasks."""
    from app.models.approval import ApprovalStatus, ApprovalTask

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.status = InvoiceStatus.approved

    # Resolve any pending approval tasks for this invoice
    pending_tasks = (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.invoice_id == invoice_id,
            ApprovalTask.status == ApprovalStatus.pending,
        )
        .all()
    )
    for task in pending_tasks:
        task.status = ApprovalStatus.approved
        task.comments = f"Approved by {current_user.name}"

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="approved",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
    )

    # Auto-post: transition approved → posted immediately
    from datetime import datetime

    invoice.status = InvoiceStatus.posted
    invoice.posted_at = datetime.now(UTC)

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="posted",
        actor_type=ActorType.system,
        actor_id=current_user.id,
        actor_name="Auto-Post",
    )
    db.commit()

    return {
        "message": "Invoice approved and posted to ledger",
        "status": "posted",
        "invoice_id": str(invoice_id),
        "posted_at": invoice.posted_at.isoformat(),
    }


@router.post("/{invoice_id}/reject")
def reject_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject an invoice directly. Updates status and resolves any pending approval tasks."""
    from app.models.approval import ApprovalStatus, ApprovalTask

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.status = InvoiceStatus.rejected

    pending_tasks = (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.invoice_id == invoice_id,
            ApprovalTask.status == ApprovalStatus.pending,
        )
        .all()
    )
    for task in pending_tasks:
        task.status = ApprovalStatus.rejected
        task.comments = f"Rejected by {current_user.name}"

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="rejected",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
    )
    db.commit()

    return {"message": "Invoice rejected", "status": "rejected", "invoice_id": str(invoice_id)}


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
    invoices = db.query(Invoice).filter(Invoice.status.in_([InvoiceStatus.extracted, InvoiceStatus.draft])).all()

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
                    db.query(func.count(GRNLineItem.id)).filter(GRNLineItem.po_line_id.in_(po_line_ids)).scalar()
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

            results["details"].append(
                {
                    "invoice_id": str(inv.id),
                    "invoice_number": inv.invoice_number,
                    "status": status_label,
                    "match_score": match_result.overall_score,
                }
            )

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
            results["details"].append(
                {
                    "invoice_id": str(inv.id),
                    "invoice_number": inv.invoice_number,
                    "status": "error",
                    "error": str(e),
                }
            )
            db.rollback()

    return results


def _ndjson_line(data: dict) -> str:
    """Encode a dict as a single NDJSON line (JSON + newline)."""
    return json.dumps(data, default=str) + "\n"


def _pipeline_generator(
    invoice_id: uuid.UUID,
    db: Session,
    current_user: User,
) -> Generator[str, None, None]:
    """Generator that yields NDJSON lines as each pipeline step completes."""
    from app.models.config import ToleranceConfig
    from app.models.exception import Exception_
    from app.models.purchase_order import PurchaseOrder
    from app.services.vendor_matcher import auto_match_vendor

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        yield _ndjson_line({"event": "error", "message": "Invoice not found"})
        return

    pipeline_start = time.time()
    extracted = {}

    # ── Cleanup: resolve any stale open exceptions from a previous pipeline run ──
    from app.models.exception import ExceptionStatus

    stale = (
        db.query(Exception_)
        .filter(
            Exception_.invoice_id == invoice.id,
            Exception_.status.in_(
                [
                    ExceptionStatus.open,
                    ExceptionStatus.assigned,
                    ExceptionStatus.in_progress,
                ]
            ),
        )
        .all()
    )
    if stale:
        from app.models.exception import ResolutionType

        for s in stale:
            s.status = ExceptionStatus.resolved
            s.resolution_type = ResolutionType.auto_resolved
            s.resolution_notes = "Auto-resolved on pipeline rerun"
            s.resolved_at = datetime.now(UTC)
        db.commit()

    # ── Step 1: OCR Extraction ────────────────────────────────────────────────
    yield _ndjson_line({"event": "step_start", "step": "ocr_extraction", "label": "OCR Extraction"})
    step_start = time.time()
    try:
        if not invoice.file_storage_path:
            raise ValueError("No file available for extraction. Upload a file first.")

        file_content = s3_service.download_file(invoice.file_storage_path)
        filename = invoice.file_storage_path.rsplit("/", 1)[-1] if "/" in invoice.file_storage_path else "invoice.pdf"
        ocr_result = extract_invoice(file_content, filename=filename)

        extracted = ocr_result.get("extracted_data", {})

        # Persist extracted fields
        invoice.ocr_confidence_score = ocr_result["confidence"]
        if extracted.get("invoice_number"):
            invoice.invoice_number = extracted["invoice_number"]
        if extracted.get("invoice_date"):
            with contextlib.suppress(ValueError):
                invoice.invoice_date = _date.fromisoformat(extracted["invoice_date"])
        if extracted.get("due_date"):
            with contextlib.suppress(ValueError):
                invoice.due_date = _date.fromisoformat(extracted["due_date"])
        if extracted.get("total_amount"):
            invoice.total_amount = extracted["total_amount"]
        if extracted.get("tax_amount") is not None:
            invoice.tax_amount = extracted["tax_amount"]
        if extracted.get("currency"):
            invoice.currency = extracted["currency"]

        extracted_lines = extracted.get("line_items", [])
        if extracted_lines:
            db.query(InvoiceLineItem).filter(InvoiceLineItem.invoice_id == invoice.id).delete()
            for li in extracted_lines:
                db.add(
                    InvoiceLineItem(
                        invoice_id=invoice.id,
                        line_number=li.get("line_number", 1),
                        description=li.get("description"),
                        quantity=li.get("quantity", 1),
                        unit_price=li.get("unit_price", 0),
                        line_total=li.get("line_total", 0),
                        tax_amount=li.get("tax_amount", 0),
                        ai_gl_prediction=li.get("ai_gl_prediction"),
                        ai_confidence=li.get("ai_confidence"),
                    )
                )

        invoice.status = InvoiceStatus.extracted
        db.commit()
        db.refresh(invoice)

        extraction_method = ocr_result.get("extraction_method", "unknown")
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "ocr_extraction",
                "label": "OCR Extraction",
                "agent": f"3-Tier OCR Pipeline ({extraction_method})",
                "status": "complete",
                "duration_ms": int((time.time() - step_start) * 1000),
                "output": {
                    "confidence": ocr_result["confidence"],
                    "pages_processed": ocr_result.get("pages_processed", 1),
                    "extraction_method": extraction_method,
                    "extracted_data": extracted,
                    "raw_text_preview": (ocr_result.get("raw_text", "") or "")[:500],
                },
            }
        )
    except Exception as exc:
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "ocr_extraction",
                "label": "OCR Extraction",
                "agent": "Claude Vision",
                "status": "error",
                "duration_ms": int((time.time() - step_start) * 1000),
                "error": str(exc),
                "output": {},
            }
        )
        yield _ndjson_line(
            {
                "event": "pipeline_done",
                "invoice_id": str(invoice_id),
                "invoice_number": invoice.invoice_number,
                "total_duration_ms": int((time.time() - pipeline_start) * 1000),
                "final_status": invoice.status.value,
                "recommendation": None,
            }
        )
        return

    # ── Step 2: Vendor Match ──────────────────────────────────────────────────
    yield _ndjson_line({"event": "step_start", "step": "vendor_match", "label": "Vendor Match"})
    step_start = time.time()
    try:
        vendor_name = extracted.get("vendor_name") or extracted.get("supplier_name")
        vendor_tax_id = extracted.get("vendor_tax_id") or extracted.get("tax_id")

        if invoice.vendor_id:
            # Already has a vendor (e.g. passed during upload)
            from app.models.vendor import Vendor as VendorModel

            existing_vendor = db.query(VendorModel).filter(VendorModel.id == invoice.vendor_id).first()
            yield _ndjson_line(
                {
                    "event": "step_complete",
                    "step": "vendor_match",
                    "label": "Vendor Match",
                    "agent": "Pre-assigned",
                    "status": "complete",
                    "duration_ms": int((time.time() - step_start) * 1000),
                    "output": {
                        "method": "pre_assigned",
                        "vendor_id": str(invoice.vendor_id),
                        "vendor_name": existing_vendor.name if existing_vendor else "Unknown",
                        "confidence": 1.0,
                    },
                }
            )
        elif vendor_name or vendor_tax_id:
            matched_vendor = auto_match_vendor(db, vendor_name=vendor_name, vendor_tax_id=vendor_tax_id)
            if matched_vendor:
                invoice.vendor_id = matched_vendor.id
                db.commit()
                yield _ndjson_line(
                    {
                        "event": "step_complete",
                        "step": "vendor_match",
                        "label": "Vendor Match",
                        "agent": "AI Vendor Matcher (fuzzy + tax_id)",
                        "status": "complete",
                        "duration_ms": int((time.time() - step_start) * 1000),
                        "output": {
                            "method": "tax_id_exact" if vendor_tax_id else "fuzzy_name",
                            "vendor_id": str(matched_vendor.id),
                            "vendor_name": matched_vendor.name,
                            "vendor_code": matched_vendor.vendor_code,
                            "ocr_vendor_name": vendor_name,
                            "ocr_tax_id": vendor_tax_id,
                            "confidence": 0.95 if vendor_tax_id else 0.85,
                        },
                    }
                )
            else:
                yield _ndjson_line(
                    {
                        "event": "step_complete",
                        "step": "vendor_match",
                        "label": "Vendor Match",
                        "agent": "AI Vendor Matcher (fuzzy + tax_id)",
                        "status": "complete",
                        "duration_ms": int((time.time() - step_start) * 1000),
                        "output": {
                            "method": "no_match",
                            "ocr_vendor_name": vendor_name,
                            "ocr_tax_id": vendor_tax_id,
                            "message": "No vendor match found — manual assignment may be needed",
                            "confidence": 0.0,
                        },
                    }
                )
        else:
            yield _ndjson_line(
                {
                    "event": "step_complete",
                    "step": "vendor_match",
                    "label": "Vendor Match",
                    "agent": "AI Vendor Matcher",
                    "status": "complete",
                    "duration_ms": int((time.time() - step_start) * 1000),
                    "output": {
                        "method": "no_ocr_data",
                        "message": "No vendor information extracted from document",
                        "confidence": 0.0,
                    },
                }
            )
    except Exception as exc:
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "vendor_match",
                "label": "Vendor Match",
                "agent": "AI Vendor Matcher",
                "status": "error",
                "duration_ms": int((time.time() - step_start) * 1000),
                "error": str(exc),
                "output": {},
            }
        )

    # ── Step 3: Document Classification ──────────────────────────────────────
    yield _ndjson_line({"event": "step_start", "step": "classification", "label": "Document Classification"})
    step_start = time.time()
    try:
        classification = classify_and_validate(
            db,
            invoice_id=invoice.id,
            extracted_data=extracted,
            ocr_confidence=ocr_result["confidence"],
        )
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "classification",
                "label": "Document Classification",
                "agent": "Claude (claude-haiku-4-5-20251001)",
                "status": "complete",
                "duration_ms": int((time.time() - step_start) * 1000),
                "output": classification,
            }
        )
    except Exception as exc:
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "classification",
                "label": "Document Classification",
                "agent": "Claude (claude-haiku-4-5-20251001)",
                "status": "error",
                "duration_ms": int((time.time() - step_start) * 1000),
                "error": str(exc),
                "output": {},
            }
        )

    # ── Step 4: 3-Way / 2-Way Matching ───────────────────────────────────────
    yield _ndjson_line({"event": "step_start", "step": "three_way_match", "label": "3-Way Match"})
    step_start = time.time()
    match_result = None
    exc_count = 0
    try:
        match_service.auto_link_po_lines(db, invoice.id)
        db.refresh(invoice)
        for li in invoice.line_items:
            db.refresh(li)

        po_line_ids = [li.po_line_id for li in invoice.line_items if li.po_line_id]
        use_three_way = False
        if po_line_ids:
            grn_count = (
                db.query(func.count(GRNLineItem.id)).filter(GRNLineItem.po_line_id.in_(po_line_ids)).scalar()
            ) or 0
            use_three_way = grn_count > 0

        if use_three_way:
            match_result = match_service.run_three_way_match(db, invoice.id)
        else:
            match_result = match_service.run_two_way_match(db, invoice.id)

        db.commit()

        exc_count = db.query(Exception_).filter(Exception_.invoice_id == invoice.id).count()

        header_match = {}
        matched_po = None
        if match_result.matched_po_id:
            matched_po = db.query(PurchaseOrder).filter(PurchaseOrder.id == match_result.matched_po_id).first()
        if matched_po:
            vendor_match_flag = (
                str(invoice.vendor_id) == str(matched_po.vendor_id)
                if invoice.vendor_id and matched_po.vendor_id
                else False
            )
            header_match = {
                "vendor": {"match": vendor_match_flag},
                "po_number": {"match": True, "value": matched_po.po_number},
                "currency": {"match": (invoice.currency or "USD") == (matched_po.currency or "USD")},
                "invoice_total": float(invoice.total_amount) if invoice.total_amount else 0,
                "po_total": float(matched_po.total_amount) if matched_po.total_amount else 0,
            }

        tol_summary = None
        if match_result.tolerance_config_id:
            tol_cfg = db.query(ToleranceConfig).filter(ToleranceConfig.id == match_result.tolerance_config_id).first()
            if tol_cfg:
                tol_summary = {
                    "scope": tol_cfg.scope,
                    "amount_pct": tol_cfg.amount_tolerance_pct,
                    "amount_abs": float(tol_cfg.amount_tolerance_abs) if tol_cfg.amount_tolerance_abs else 0,
                    "quantity_pct": tol_cfg.quantity_tolerance_pct,
                }

        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "three_way_match",
                "label": "3-Way Match" if use_three_way else "2-Way Match",
                "agent": "AP Match Engine (rule-based, PO + GRN data)",
                "status": "complete",
                "duration_ms": int((time.time() - step_start) * 1000),
                "output": {
                    "match_type": match_result.match_type.value,
                    "match_status": match_result.match_status.value,
                    "overall_score": match_result.overall_score,
                    "matched_po_id": str(match_result.matched_po_id) if match_result.matched_po_id else None,
                    "matched_grn_ids": [str(g) for g in (match_result.matched_grn_ids or [])],
                    "tolerance_applied": match_result.tolerance_applied,
                    "tolerance_config": tol_summary,
                    "exceptions_created": exc_count,
                    "header_match": header_match,
                    "details": match_result.details,
                },
            }
        )
    except Exception as exc:
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "three_way_match",
                "label": "3-Way Match",
                "agent": "AP Match Engine",
                "status": "error",
                "duration_ms": int((time.time() - step_start) * 1000),
                "error": str(exc),
                "output": {},
            }
        )

    # ── Clean match → auto-approve + auto-post (skip Steps 5 & 6) ────────────
    match_status_val = match_result.match_status.value if match_result else None
    if exc_count == 0 and match_status_val in ("matched", "tolerance_passed"):
        # Auto-approve & auto-post the invoice
        invoice.status = InvoiceStatus.posted
        invoice.posted_at = datetime.now(UTC)
        db.commit()

        audit_service.log_action(
            db,
            entity_type="invoice",
            entity_id=invoice.id,
            action="auto_approved_posted",
            actor_type=ActorType.ai_agent,
            actor_name="AP Pipeline Agent",
            evidence={"match_status": match_status_val, "overall_score": match_result.overall_score},
        )
        db.commit()

        # Emit recommendation step as auto-approved
        yield _ndjson_line(
            {"event": "step_start", "step": "approval_recommendation", "label": "Approval Recommendation"}
        )
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "approval_recommendation",
                "label": "Approval Recommendation",
                "agent": "AP Pipeline Agent (auto)",
                "status": "complete",
                "duration_ms": 0,
                "output": {
                    "recommendation": "approve",
                    "reasoning": f"Clean {match_status_val} with score {match_result.overall_score}%. No exceptions. Auto-approved and posted.",
                    "risk_factors": [],
                    "auto_approved": True,
                    "auto_posted": True,
                    "posted_at": invoice.posted_at.isoformat(),
                },
            }
        )

        # Pipeline done
        audit_service.log_action(
            db,
            entity_type="invoice",
            entity_id=invoice.id,
            action="pipeline_executed",
            actor_type=ActorType.ai_agent,
            actor_name="AP Pipeline Agent",
            evidence={"total_ms": int((time.time() - pipeline_start) * 1000)},
        )
        db.commit()

        yield _ndjson_line(
            {
                "event": "pipeline_done",
                "invoice_id": str(invoice_id),
                "invoice_number": invoice.invoice_number,
                "total_duration_ms": int((time.time() - pipeline_start) * 1000),
                "final_status": "posted",
                "recommendation": "approve",
                "auto_approved": True,
                "auto_posted": True,
            }
        )
        return

    # ── Step 5: Exception Resolution (if exceptions exist) ───────────────────
    if exc_count > 0:
        yield _ndjson_line({"event": "step_start", "step": "exception_resolution", "label": "AI Exception Resolution"})
        step_start = time.time()
        try:
            from app.models.resolution import PlanStatus
            from app.services import resolution_orchestrator
            from app.services.ai_exception_resolver import generate_resolution_plan

            total_exc_count = (
                db.query(Exception_)
                .filter(
                    Exception_.invoice_id == invoice.id,
                    Exception_.status == "open",
                )
                .count()
            )
            exceptions = (
                db.query(Exception_)
                .filter(
                    Exception_.invoice_id == invoice.id,
                    Exception_.status == "open",
                )
                .order_by(Exception_.created_at.asc())
                .limit(5)
                .all()
            )

            plans_data = []
            for exc_obj in exceptions:
                try:
                    plan = generate_resolution_plan(db, exc_obj.id)
                    # Auto-approve and execute
                    plan.status = PlanStatus.approved
                    db.commit()
                    resolution_orchestrator.execute(db, plan.id)

                    # Build serializable plan data
                    db.refresh(plan)
                    actions_data = []
                    for action in sorted(plan.actions, key=lambda a: a.step_id):
                        actions_data.append(
                            {
                                "id": str(action.id),
                                "step_id": action.step_id,
                                "action_type": action.action_type,
                                "status": action.status.value
                                if hasattr(action.status, "value")
                                else str(action.status),
                                "requires_human_approval": action.requires_human_approval,
                                "params_json": action.params_json,
                                "result_json": action.result_json,
                                "expected_result": action.expected_result,
                                "error_message": action.error_message,
                            }
                        )

                    plans_data.append(
                        {
                            "exception_id": str(exc_obj.id),
                            "exception_type": exc_obj.exception_type.value
                            if hasattr(exc_obj.exception_type, "value")
                            else str(exc_obj.exception_type),
                            "plan_id": str(plan.id),
                            "plan_status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
                            "diagnosis": plan.diagnosis,
                            "confidence": plan.confidence,
                            "automation_level": plan.automation_level.value
                            if hasattr(plan.automation_level, "value")
                            else str(plan.automation_level),
                            "actions": actions_data,
                        }
                    )
                except Exception as plan_exc:
                    plans_data.append(
                        {
                            "exception_id": str(exc_obj.id),
                            "exception_type": exc_obj.exception_type.value
                            if hasattr(exc_obj.exception_type, "value")
                            else str(exc_obj.exception_type),
                            "error": str(plan_exc),
                        }
                    )

            yield _ndjson_line(
                {
                    "event": "step_complete",
                    "step": "exception_resolution",
                    "label": "AI Exception Resolution",
                    "agent": "Claude Resolution Engine",
                    "status": "complete",
                    "duration_ms": int((time.time() - step_start) * 1000),
                    "output": {
                        "exceptions_count": len(exceptions),
                        "total_exceptions": total_exc_count,
                        "truncated": total_exc_count > 5,
                        "plans": plans_data,
                    },
                }
            )
        except Exception as exc:
            yield _ndjson_line(
                {
                    "event": "step_complete",
                    "step": "exception_resolution",
                    "label": "AI Exception Resolution",
                    "agent": "Claude Resolution Engine",
                    "status": "error",
                    "duration_ms": int((time.time() - step_start) * 1000),
                    "error": str(exc),
                    "output": {},
                }
            )

    # ── Step 6: Approval Recommendation ──────────────────────────────────────
    yield _ndjson_line({"event": "step_start", "step": "approval_recommendation", "label": "Approval Recommendation"})
    step_start = time.time()
    db.refresh(invoice)
    recommendation_value = None
    try:
        try:
            create_approval_tasks(db, invoice.id)
            db.commit()
        except Exception:
            db.rollback()

        ai_rec, ai_reason = _get_ai_recommendation(db, invoice)
        recommendation_value = ai_rec.value

        risk_factors: list = []
        reasoning = ai_reason
        if " Risk factors: " in ai_reason:
            parts = ai_reason.split(" Risk factors: ", 1)
            reasoning = parts[0]
            risk_factors = [r.strip() for r in parts[1].rstrip(".").split(",") if r.strip()]

        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "approval_recommendation",
                "label": "Approval Recommendation",
                "agent": "Claude (claude-haiku-4-5-20251001)",
                "status": "complete",
                "duration_ms": int((time.time() - step_start) * 1000),
                "output": {
                    "recommendation": ai_rec.value,
                    "reasoning": reasoning,
                    "risk_factors": risk_factors,
                },
            }
        )
    except Exception as exc:
        yield _ndjson_line(
            {
                "event": "step_complete",
                "step": "approval_recommendation",
                "label": "Approval Recommendation",
                "agent": "Claude (claude-haiku-4-5-20251001)",
                "status": "error",
                "duration_ms": int((time.time() - step_start) * 1000),
                "error": str(exc),
                "output": {},
            }
        )

    # ── Pipeline done ────────────────────────────────────────────────────────
    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="pipeline_executed",
        actor_type=ActorType.ai_agent,
        actor_name="AP Pipeline Agent",
        evidence={"total_ms": int((time.time() - pipeline_start) * 1000)},
    )
    db.commit()

    yield _ndjson_line(
        {
            "event": "pipeline_done",
            "invoice_id": str(invoice_id),
            "invoice_number": invoice.invoice_number,
            "total_duration_ms": int((time.time() - pipeline_start) * 1000),
            "final_status": invoice.status.value,
            "recommendation": recommendation_value,
        }
    )


@router.post("/{invoice_id}/simulate-send-email")
def simulate_send_email(
    invoice_id: uuid.UUID,
    body: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Simulate sending a vendor email. Sets invoice status to pending_approval (awaiting vendor)."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.status = InvoiceStatus.pending_approval
    db.commit()

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="email_sent_simulated",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        evidence={"action_id": body.get("action_id"), "simulated": True},
    )
    db.commit()

    return {
        "message": "Email sent (simulated)",
        "invoice_status": "pending_approval",
        "invoice_id": str(invoice_id),
        "simulated": True,
    }


@router.post("/{invoice_id}/apply-corrections")
def apply_corrections_endpoint(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recalculate all line totals from qty*unit_price and update invoice total."""
    from sqlalchemy.orm import joinedload as _jl

    invoice = db.query(Invoice).options(_jl(Invoice.line_items)).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    corrections = []
    old_total = float(invoice.total_amount)

    for li in invoice.line_items:
        computed = round(float(li.quantity) * float(li.unit_price), 2)
        current = float(li.line_total)
        if abs(computed - current) >= 0.01:
            corrections.append(
                {
                    "line_number": li.line_number,
                    "description": li.description,
                    "old_total": current,
                    "new_total": computed,
                    "difference": round(computed - current, 2),
                }
            )
            li.line_total = computed

    new_subtotal = sum(float(li.line_total) for li in invoice.line_items)
    new_total = round(
        new_subtotal + float(invoice.tax_amount) + float(invoice.freight_amount) - float(invoice.discount_amount), 2
    )
    invoice.total_amount = new_total
    db.commit()

    audit_service.log_action(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="corrections_applied",
        actor_type=ActorType.user,
        actor_id=current_user.id,
        actor_name=current_user.name,
        evidence={"corrections": len(corrections), "old_total": old_total, "new_total": new_total},
    )
    db.commit()

    return {
        "corrections": corrections,
        "old_total": old_total,
        "new_total": new_total,
        "difference": round(new_total - old_total, 2),
    }


@router.post("/{invoice_id}/run-pipeline")
def run_invoice_pipeline(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the full AP agent pipeline as a streaming NDJSON response.

    Steps: OCR → Vendor Match → Classification → 3-Way Match → Exception Resolution → Approval Recommendation.
    Each step emits events as it starts and completes for real-time frontend visualization.
    """
    # Validate invoice exists before starting the stream
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return StreamingResponse(
        _pipeline_generator(invoice_id, db, current_user),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
