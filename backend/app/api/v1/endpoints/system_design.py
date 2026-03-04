"""System design showcase endpoints — architecture, data flow, and design decisions."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/system-design", tags=["system-design"])


@router.get("/architecture")
def get_architecture(
    current_user: User = Depends(get_current_user),
):
    """Return system architecture metadata."""
    return {
        "name": "AP Operation Manager",
        "version": "2.0",
        "framework": "6-ACT AP Automation",
        "layers": [
            {
                "name": "Presentation Layer",
                "tech": "Next.js 15 + React 19 + TailwindCSS + shadcn/ui",
                "components": [
                    "Dashboard with KPIs & trends",
                    "Invoice processing pipeline",
                    "Exception management",
                    "Approval workflow",
                    "Compliance & audit pack",
                    "Knowledge base",
                    "AI improvements",
                    "Vendor management",
                    "Analytics & reporting",
                ],
            },
            {
                "name": "API Layer",
                "tech": "FastAPI + Pydantic + SQLAlchemy 2.0",
                "components": [
                    "RESTful API with JWT auth",
                    "14 endpoint modules",
                    "Background tasks (Celery)",
                    "AI chat integration",
                ],
            },
            {
                "name": "Business Logic",
                "tech": "Python services",
                "components": [
                    "3-way matching engine",
                    "Auto-resolution engine",
                    "Duplicate detection",
                    "Document parser (docx/pdf)",
                    "Knowledge base extraction",
                    "Compliance engine",
                    "Learning engine",
                ],
            },
            {
                "name": "AI Layer",
                "tech": "Claude API (Anthropic)",
                "components": [
                    "Invoice data extraction (OCR)",
                    "Exception analysis & severity",
                    "Policy rule extraction",
                    "Chat assistant (context-aware)",
                    "Threshold tuning suggestions",
                ],
            },
            {
                "name": "Data Layer",
                "tech": "PostgreSQL + Redis + MinIO",
                "components": [
                    "Relational database (invoices, POs, GRNs, vendors)",
                    "Object storage (PDF/image files)",
                    "Task queue (Celery/Redis)",
                    "Audit trail logging",
                ],
            },
        ],
        "six_acts": [
            {
                "act": 1,
                "name": "AI Understands Business",
                "status": "complete",
                "description": "Parse AP policies, contracts, and audit findings into structured knowledge base",
                "features": [
                    "AP_Policy.docx parsing with section extraction",
                    "Supplier contract analysis (5 contracts)",
                    "Audit findings ingestion from PDF",
                    "40 business rules extracted with confidence scores",
                    "Rule approval workflow (pending/approved/rejected)",
                ],
            },
            {
                "act": 2,
                "name": "AI Designs System",
                "status": "complete",
                "description": "Architecture documentation and system design showcase",
                "features": [
                    "Layered architecture visualization",
                    "Data flow diagrams",
                    "API contract documentation",
                    "6-ACT framework mapping",
                ],
            },
            {
                "act": 3,
                "name": "AI Builds App",
                "status": "complete",
                "description": "Full-stack application with invoice processing pipeline",
                "features": [
                    "Invoice upload with OCR extraction",
                    "3-way matching (Invoice-PO-GRN)",
                    "Exception flagging and routing",
                    "Approval workflow with matrix enforcement",
                    "Dashboard with real-time KPIs",
                    "Vendor management",
                    "Audit trail logging",
                ],
            },
            {
                "act": 4,
                "name": "AI Runs Operations",
                "status": "complete",
                "description": "Automated operations including duplicate detection and auto-resolution",
                "features": [
                    "Duplicate invoice detection (exact + fuzzy)",
                    "Auto-resolution for minor discrepancies",
                    "Batch matching engine",
                    "Background task scheduling (Celery)",
                    "Daily operations reporting",
                    "AI-powered chat assistant",
                ],
            },
            {
                "act": 5,
                "name": "Audit & Compliance",
                "status": "complete",
                "description": "Comprehensive compliance engine with audit pack generation",
                "features": [
                    "10 AP controls mapped to policy sections",
                    "7 automated control tests",
                    "Per-invoice compliance scoring (6 checks)",
                    "Gap analysis from operational data",
                    "Full audit pack generation",
                    "Policy linkage for every decision",
                ],
            },
            {
                "act": 6,
                "name": "AI Improves Itself",
                "status": "complete",
                "description": "Learning engine that recommends improvements from operational data",
                "features": [
                    "Resolution pattern analysis",
                    "AI threshold tuning recommendations",
                    "New rule suggestions",
                    "Performance benchmarking vs industry",
                    "Maturity scoring",
                    "Root cause analysis",
                ],
            },
        ],
    }


@router.get("/data-flow")
def get_data_flow(
    current_user: User = Depends(get_current_user),
):
    """Return the invoice processing data flow."""
    return {
        "pipeline": [
            {
                "step": 1,
                "name": "Ingestion",
                "description": "Invoice received via PDF upload, email, or API",
                "ai_role": "OCR extracts structured data from PDF images",
                "outputs": ["Invoice record created", "PDF stored in MinIO"],
            },
            {
                "step": 2,
                "name": "Validation",
                "description": "Duplicate check and vendor validation",
                "ai_role": "Fuzzy matching detects near-duplicate invoices",
                "outputs": ["Duplicate flag", "Vendor status verified"],
            },
            {
                "step": 3,
                "name": "Matching",
                "description": "3-way match: Invoice vs PO vs GRN",
                "ai_role": "Tolerance-based matching with configurable thresholds",
                "outputs": ["Match score", "Line-level comparison", "Exception flags"],
            },
            {
                "step": 4,
                "name": "Exception Handling",
                "description": "Mismatches flagged as exceptions with severity assessment",
                "ai_role": "AI suggests resolution and assesses severity",
                "outputs": ["Exception record", "AI suggestion", "Severity rating"],
            },
            {
                "step": 5,
                "name": "Auto-Resolution",
                "description": "Minor discrepancies auto-resolved within tolerance",
                "ai_role": "Learned thresholds applied from resolution patterns",
                "outputs": ["Auto-resolved exceptions", "Tolerance audit trail"],
            },
            {
                "step": 6,
                "name": "Approval",
                "description": "Routed to appropriate approver based on amount thresholds",
                "ai_role": "Approval matrix enforcement per policy rules",
                "outputs": ["Approval/rejection decision", "Audit log entry"],
            },
            {
                "step": 7,
                "name": "Posting",
                "description": "Approved invoices posted for payment",
                "ai_role": "Compliance scoring and policy linkage recorded",
                "outputs": ["Posted invoice", "Compliance score", "Audit pack data"],
            },
            {
                "step": 8,
                "name": "Learning",
                "description": "Outcomes fed back into learning engine",
                "ai_role": "Threshold tuning, rule suggestions, benchmarking",
                "outputs": ["Updated recommendations", "Performance metrics"],
            },
        ],
    }


@router.get("/api-contracts")
def get_api_contracts(
    current_user: User = Depends(get_current_user),
):
    """Return API endpoint documentation."""
    return {
        "base_url": "/api/v1",
        "auth": "JWT Bearer token",
        "modules": [
            {
                "name": "Authentication",
                "prefix": "/auth",
                "endpoints": [
                    {"method": "POST", "path": "/login", "description": "Login with email/password"},
                    {"method": "POST", "path": "/register", "description": "Register new user"},
                    {"method": "GET", "path": "/me", "description": "Get current user profile"},
                ],
            },
            {
                "name": "Invoices",
                "prefix": "/invoices",
                "endpoints": [
                    {"method": "GET", "path": "/", "description": "List all invoices with pagination"},
                    {"method": "GET", "path": "/{id}", "description": "Get invoice details"},
                    {"method": "POST", "path": "/upload", "description": "Upload PDF invoice"},
                    {"method": "POST", "path": "/{id}/extract", "description": "Run OCR extraction"},
                    {"method": "POST", "path": "/{id}/match", "description": "Run 3-way matching"},
                ],
            },
            {
                "name": "Exceptions",
                "prefix": "/exceptions",
                "endpoints": [
                    {"method": "GET", "path": "/", "description": "List exceptions with filters"},
                    {"method": "PATCH", "path": "/{id}", "description": "Update exception status"},
                    {"method": "POST", "path": "/{id}/comments", "description": "Add comment"},
                ],
            },
            {
                "name": "Compliance",
                "prefix": "/compliance",
                "endpoints": [
                    {"method": "GET", "path": "/control-map", "description": "AP control-to-policy mapping"},
                    {"method": "GET", "path": "/gaps", "description": "Gap analysis"},
                    {"method": "GET", "path": "/control-tests", "description": "Automated control tests"},
                    {"method": "GET", "path": "/scoring", "description": "Compliance scoring"},
                    {"method": "GET", "path": "/audit-pack", "description": "Full audit pack"},
                ],
            },
            {
                "name": "Knowledge Base",
                "prefix": "/knowledge",
                "endpoints": [
                    {"method": "GET", "path": "/summary", "description": "Knowledge base stats"},
                    {"method": "GET", "path": "/rules", "description": "List extracted rules"},
                    {"method": "POST", "path": "/parse", "description": "Parse AP_Inputs documents"},
                    {"method": "POST", "path": "/rules/{id}/approve", "description": "Approve a rule"},
                ],
            },
            {
                "name": "Learning",
                "prefix": "/learning",
                "endpoints": [
                    {"method": "GET", "path": "/summary", "description": "Learning summary"},
                    {"method": "GET", "path": "/threshold-recommendations", "description": "AI threshold tuning"},
                    {"method": "GET", "path": "/rule-suggestions", "description": "AI rule suggestions"},
                    {"method": "GET", "path": "/benchmarks", "description": "Performance benchmarks"},
                ],
            },
            {
                "name": "Operations",
                "prefix": "/operations",
                "endpoints": [
                    {"method": "POST", "path": "/check-duplicate", "description": "Duplicate detection"},
                    {"method": "POST", "path": "/auto-resolve", "description": "Auto-resolve exceptions"},
                    {"method": "POST", "path": "/batch-match", "description": "Batch matching"},
                    {"method": "GET", "path": "/daily-report", "description": "Daily ops report"},
                ],
            },
            {
                "name": "Analytics",
                "prefix": "/analytics",
                "endpoints": [
                    {"method": "GET", "path": "/dashboard", "description": "Dashboard KPIs"},
                    {"method": "GET", "path": "/trends", "description": "Invoice volume trends"},
                    {"method": "GET", "path": "/root-causes", "description": "Root cause analysis"},
                    {"method": "GET", "path": "/optimization-proposals", "description": "AI optimization ideas"},
                ],
            },
        ],
    }


@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return system-level statistics for the design showcase."""
    from sqlalchemy import func

    from app.models.audit import AuditLog
    from app.models.config import PolicyDocument, PolicyRule
    from app.models.exception import Exception_
    from app.models.invoice import Invoice
    from app.models.matching import MatchResult
    from app.models.vendor import Vendor

    return {
        "database": {
            "invoices": db.query(func.count(Invoice.id)).scalar() or 0,
            "exceptions": db.query(func.count(Exception_.id)).scalar() or 0,
            "match_results": db.query(func.count(MatchResult.id)).scalar() or 0,
            "audit_entries": db.query(func.count(AuditLog.id)).scalar() or 0,
            "vendors": db.query(func.count(Vendor.id)).scalar() or 0,
            "policy_documents": db.query(func.count(PolicyDocument.id)).scalar() or 0,
            "policy_rules": db.query(func.count(PolicyRule.id)).scalar() or 0,
        },
        "api": {
            "total_endpoints": 45,
            "modules": 14,
            "auth_method": "JWT",
        },
        "tech_stack": {
            "frontend": ["Next.js 15", "React 19", "TailwindCSS", "shadcn/ui", "React Query"],
            "backend": ["FastAPI", "SQLAlchemy 2.0", "Celery", "Pydantic"],
            "ai": ["Claude API (Anthropic)", "OCR Pipeline", "NLP Rule Extraction"],
            "infrastructure": ["PostgreSQL", "Redis", "MinIO (S3-compatible)"],
        },
    }
