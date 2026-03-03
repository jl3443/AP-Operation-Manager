"""Knowledge base endpoints — document parsing, rule management, and search."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class ParseRequest(BaseModel):
    ap_inputs_dir: str = "/Users/kyle/Desktop/AP-Digital-Ops-Manager/AP_Inputs"
    use_ai: bool = True


class RuleReviewRequest(BaseModel):
    notes: Optional[str] = None


@router.get("/summary")
def get_knowledge_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a summary of the knowledge base — document counts, rule counts, breakdowns."""
    from app.services.knowledge_base import get_knowledge_summary

    return get_knowledge_summary(db)


@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all parsed policy documents."""
    from app.services.knowledge_base import get_all_documents

    return get_all_documents(db)


@router.get("/rules")
def list_rules(
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    status: Optional[str] = Query(None, description="Filter by status (pending/approved/rejected)"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List policy rules with optional filters."""
    from app.services.knowledge_base import get_all_rules

    return get_all_rules(db, rule_type=rule_type, status=status, document_id=document_id, min_confidence=min_confidence)


@router.get("/search")
def search_rules(
    q: str = Query(..., min_length=1, description="Search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search the knowledge base by rule text or type."""
    from app.services.knowledge_base import search_rules

    return search_rules(db, q)


@router.post("/parse")
def parse_documents(
    payload: ParseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Parse all AP_Inputs documents and extract rules into the knowledge base.

    This will parse AP_Policy.docx, Audit_Findings_2024.pdf, and all supplier contracts.
    """
    from app.services.document_parser import parse_all_ap_inputs

    result = parse_all_ap_inputs(db, payload.ap_inputs_dir, use_ai=payload.use_ai)
    return result


@router.post("/rules/{rule_id}/approve")
def approve_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a pending policy rule."""
    from app.services.knowledge_base import approve_rule

    return approve_rule(db, rule_id, reviewer_id=str(current_user.id))


@router.post("/rules/{rule_id}/reject")
def reject_rule(
    rule_id: str,
    payload: RuleReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a policy rule."""
    from app.services.knowledge_base import reject_rule

    return reject_rule(db, rule_id, reviewer_id=str(current_user.id), notes=payload.notes)
