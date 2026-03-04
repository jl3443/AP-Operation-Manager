"""Vendor-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.vendor import VendorRiskLevel, VendorStatus


class VendorCreate(BaseModel):
    vendor_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = "US"
    payment_terms_code: str | None = None
    bank_account_info: dict[str, Any] | None = None
    status: VendorStatus = VendorStatus.active
    risk_level: VendorRiskLevel = VendorRiskLevel.low


class VendorUpdate(BaseModel):
    name: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    payment_terms_code: str | None = None
    bank_account_info: dict[str, Any] | None = None
    status: VendorStatus | None = None
    risk_level: VendorRiskLevel | None = None


class VendorResponse(BaseModel):
    id: uuid.UUID
    vendor_code: str
    name: str
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    payment_terms_code: str | None = None
    bank_account_info: dict[str, Any] | None = None
    status: VendorStatus
    risk_level: VendorRiskLevel
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
