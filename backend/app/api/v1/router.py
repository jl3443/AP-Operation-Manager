"""Main API v1 router that aggregates all endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    approvals,
    auth,
    exceptions,
    import_data,
    invoices,
    vendors,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(invoices.router)
api_router.include_router(exceptions.router)
api_router.include_router(approvals.router)
api_router.include_router(import_data.router)
api_router.include_router(analytics.router)
api_router.include_router(vendors.router)
