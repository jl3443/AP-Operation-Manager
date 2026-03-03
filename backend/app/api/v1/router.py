"""Main API v1 router that aggregates all endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_chat,
    analytics,
    approvals,
    audit,
    auth,
    compliance,
    config,
    exceptions,
    import_data,
    invoices,
    knowledge,
    learning,
    operations,
    system_design,
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
api_router.include_router(ai_chat.router)
api_router.include_router(audit.router)
api_router.include_router(config.router)
api_router.include_router(compliance.router)
api_router.include_router(operations.router)
api_router.include_router(knowledge.router)
api_router.include_router(learning.router)
api_router.include_router(system_design.router)
