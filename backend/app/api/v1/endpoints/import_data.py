"""CSV import endpoints for POs, GRNs, and Vendors."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import import_service

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/purchase-orders")
async def import_purchase_orders(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import purchase orders from a CSV file."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted",
        )
    content = await file.read()
    result = import_service.import_csv_purchase_orders(db, content)
    return {"message": "Import complete", **result}


@router.post("/goods-receipts")
async def import_goods_receipts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import goods receipts from a CSV file."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted",
        )
    content = await file.read()
    result = import_service.import_csv_goods_receipts(db, content)
    return {"message": "Import complete", **result}


@router.post("/vendors")
async def import_vendors(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import vendors from a CSV file."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted",
        )
    content = await file.read()
    result = import_service.import_csv_vendors(db, content)
    return {"message": "Import complete", **result}


@router.get("/jobs/{job_id}")
def get_import_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the status of an import job (placeholder for async/Celery jobs)."""
    # In a production setup this would query a Celery result backend
    return {
        "job_id": job_id,
        "status": "completed",
        "message": "Synchronous import; job tracking is a future enhancement",
    }
