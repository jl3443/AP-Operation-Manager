"""Analytics / dashboard Pydantic schemas."""

from __future__ import annotations

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
    stages: list[FunnelStage] = []


class TrendPoint(BaseModel):
    date: str
    value: float
    label: str | None = None


class TrendData(BaseModel):
    series_name: str
    data_points: list[TrendPoint] = []


class VendorSummary(BaseModel):
    vendor_id: str
    vendor_name: str
    invoice_count: int = 0
    total_amount: float = 0.0
    exception_count: int = 0
    avg_processing_days: float = 0.0


class AgingBucket(BaseModel):
    bucket: str
    count: int
    amount: float


class AgingData(BaseModel):
    buckets: list[AgingBucket]


class ExceptionBreakdown(BaseModel):
    exception_type: str
    count: int
    percentage: float


class VendorRiskDistribution(BaseModel):
    risk_level: str
    count: int
    percentage: float


class MonthlyComparison(BaseModel):
    month: str
    invoice_count: int
    total_amount: float


class ApprovalTurnaround(BaseModel):
    level: int
    avg_hours: float
    total_tasks: int


class TouchlessRate(BaseModel):
    rate: float
    total_invoices: int
    touchless_count: int
    cycle_time_avg_hours: float


class RootCauseItem(BaseModel):
    category: str
    issue: str
    occurrence_count: int
    affected_invoices: int
    impact_amount: float
    suggested_fix: str


class OptimizationProposal(BaseModel):
    id: str
    title: str
    description: str
    category: str  # matching_rule | tolerance | supplier_config | policy
    priority: str  # high | medium | low
    projected_impact: str
    effort: str  # low | medium | high
    status: str  # proposed | approved | implemented
