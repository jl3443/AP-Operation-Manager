"""Vendor-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.vendor import VendorRiskLevel, VendorStatus


class VendorCreate(BaseModel):
    vendor_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "US"
    payment_terms_code: Optional[str] = None
    bank_account_info: Optional[dict[str, Any]] = None
    status: VendorStatus = VendorStatus.active
    risk_level: VendorRiskLevel = VendorRiskLevel.low


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    payment_terms_code: Optional[str] = None
    bank_account_info: Optional[dict[str, Any]] = None
    status: Optional[VendorStatus] = None
    risk_level: Optional[VendorRiskLevel] = None


class VendorResponse(BaseModel):
    id: uuid.UUID
    vendor_code: str
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    payment_terms_code: Optional[str] = None
    bank_account_info: Optional[dict[str, Any]] = None
    status: VendorStatus
    risk_level: VendorRiskLevel
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
