"""Tolerance configuration CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.config import ToleranceConfig
from app.models.user import User
from app.schemas.config import (
    ToleranceConfigCreate,
    ToleranceConfigResponse,
    ToleranceConfigUpdate,
)

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/tolerances", response_model=list[ToleranceConfigResponse])
def list_tolerances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tolerance configurations."""
    return (
        db.query(ToleranceConfig)
        .order_by(ToleranceConfig.scope, ToleranceConfig.name)
        .all()
    )


@router.get("/tolerances/{tolerance_id}", response_model=ToleranceConfigResponse)
def get_tolerance(
    tolerance_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single tolerance configuration."""
    tol = db.query(ToleranceConfig).filter(ToleranceConfig.id == tolerance_id).first()
    if not tol:
        raise HTTPException(status_code=404, detail="Tolerance config not found")
    return tol


@router.post("/tolerances", response_model=ToleranceConfigResponse, status_code=status.HTTP_201_CREATED)
def create_tolerance(
    payload: ToleranceConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new tolerance configuration."""
    tol = ToleranceConfig(**payload.model_dump())
    db.add(tol)
    db.commit()
    db.refresh(tol)
    return tol


@router.patch("/tolerances/{tolerance_id}", response_model=ToleranceConfigResponse)
def update_tolerance(
    tolerance_id: uuid.UUID,
    payload: ToleranceConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a tolerance configuration."""
    tol = db.query(ToleranceConfig).filter(ToleranceConfig.id == tolerance_id).first()
    if not tol:
        raise HTTPException(status_code=404, detail="Tolerance config not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tol, key, value)

    db.commit()
    db.refresh(tol)
    return tol
