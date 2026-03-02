"""Analytics / dashboard Pydantic schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DashboardKPI(BaseModel):
    total_invoices: int = 0
    pending_approval: int = 0
    open_exceptions: int = 0
    total_amount_pending: float = 0.0
    avg_processing_time_hours: float = 0.0
    match_rate_pct: float = 0.0
    straight_through_rate_pct: float = 0.0
    overdue_invoices: int = 0


class FunnelStage(BaseModel):
    stage: str
    count: int
    amount: float = 0.0


class FunnelData(BaseModel):
    stages: List[FunnelStage] = []


class TrendPoint(BaseModel):
    date: str
    value: float
    label: Optional[str] = None


class TrendData(BaseModel):
    series_name: str
    data_points: List[TrendPoint] = []


class VendorSummary(BaseModel):
    vendor_id: str
    vendor_name: str
    invoice_count: int = 0
    total_amount: float = 0.0
    exception_count: int = 0
    avg_processing_days: float = 0.0
