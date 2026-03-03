"""Knowledge base service — manage structured policy rules, contract terms, and audit findings.

Provides CRUD operations, search, and aggregation of the knowledge base
built from parsed documents.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.config import (
    ExtractionStatus,
    PolicyDocument,
    PolicyRule,
    PolicyRuleStatus,
)

logger = logging.getLogger(__name__)


# ── Query helpers ────────────────────────────────────────────────────────


def get_all_documents(db: Session) -> list[dict[str, Any]]:
    """Return all parsed policy documents with rule counts."""
    docs = db.query(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc()).all()
    return [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "document_type": doc.document_type,
            "extraction_status": doc.extraction_status.value,
            "rules_count": doc.extracted_rules_count,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        }
        for doc in docs
    ]


def get_all_rules(
    db: Session,
    rule_type: Optional[str] = None,
    status: Optional[str] = None,
    document_id: Optional[str] = None,
    min_confidence: float = 0.0,
) -> list[dict[str, Any]]:
    """Return policy rules with optional filters."""
    query = db.query(PolicyRule).join(PolicyDocument)

    if rule_type:
        query = query.filter(PolicyRule.rule_type == rule_type)
    if status:
        query = query.filter(PolicyRule.status == PolicyRuleStatus(status))
    if document_id:
        query = query.filter(PolicyRule.policy_document_id == document_id)
    if min_confidence > 0:
        query = query.filter(PolicyRule.confidence >= min_confidence)

    rules = query.order_by(PolicyRule.confidence.desc()).all()

    return [
        {
            "id": str(r.id),
            "rule_type": r.rule_type,
            "source_text": r.source_text,
            "conditions": r.conditions,
            "action": r.action,
            "confidence": r.confidence,
            "status": r.status.value,
            "document": r.policy_document.filename if r.policy_document else None,
            "document_type": r.policy_document.document_type if r.policy_document else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rules
    ]


def get_knowledge_summary(db: Session) -> dict[str, Any]:
    """Return a summary of the knowledge base."""
    total_docs = db.query(func.count(PolicyDocument.id)).scalar() or 0
    total_rules = db.query(func.count(PolicyRule.id)).scalar() or 0
    pending_rules = (
        db.query(func.count(PolicyRule.id))
        .filter(PolicyRule.status == PolicyRuleStatus.pending)
        .scalar() or 0
    )
    approved_rules = (
        db.query(func.count(PolicyRule.id))
        .filter(PolicyRule.status == PolicyRuleStatus.approved)
        .scalar() or 0
    )

    # Rule types breakdown
    type_counts = (
        db.query(PolicyRule.rule_type, func.count(PolicyRule.id))
        .group_by(PolicyRule.rule_type)
        .all()
    )

    # Document types breakdown
    doc_type_counts = (
        db.query(PolicyDocument.document_type, func.count(PolicyDocument.id))
        .filter(PolicyDocument.extraction_status == ExtractionStatus.completed)
        .group_by(PolicyDocument.document_type)
        .all()
    )

    # Avg confidence
    avg_confidence = db.query(func.avg(PolicyRule.confidence)).scalar() or 0.0

    return {
        "total_documents": total_docs,
        "total_rules": total_rules,
        "pending_review": pending_rules,
        "approved_rules": approved_rules,
        "rejected_rules": total_rules - pending_rules - approved_rules,
        "avg_confidence": round(float(avg_confidence), 2),
        "rules_by_type": {t: c for t, c in type_counts},
        "documents_by_type": {t: c for t, c in doc_type_counts},
    }


def search_rules(db: Session, query: str) -> list[dict[str, Any]]:
    """Search rules by source text or rule type."""
    results = (
        db.query(PolicyRule)
        .join(PolicyDocument)
        .filter(
            PolicyRule.source_text.ilike(f"%{query}%")
            | PolicyRule.rule_type.ilike(f"%{query}%")
        )
        .order_by(PolicyRule.confidence.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "id": str(r.id),
            "rule_type": r.rule_type,
            "source_text": r.source_text,
            "conditions": r.conditions,
            "action": r.action,
            "confidence": r.confidence,
            "status": r.status.value,
            "document": r.policy_document.filename,
            "document_type": r.policy_document.document_type,
        }
        for r in results
    ]


def approve_rule(db: Session, rule_id: str, reviewer_id: Optional[str] = None) -> dict[str, Any]:
    """Approve a pending policy rule."""
    rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
    if not rule:
        return {"error": "Rule not found"}

    rule.status = PolicyRuleStatus.approved
    if reviewer_id:
        rule.reviewed_by = reviewer_id
    db.commit()

    return {"id": str(rule.id), "status": "approved"}


def reject_rule(
    db: Session, rule_id: str, reviewer_id: Optional[str] = None, notes: Optional[str] = None
) -> dict[str, Any]:
    """Reject a policy rule."""
    rule = db.query(PolicyRule).filter(PolicyRule.id == rule_id).first()
    if not rule:
        return {"error": "Rule not found"}

    rule.status = PolicyRuleStatus.rejected
    if reviewer_id:
        rule.reviewed_by = reviewer_id
    if notes:
        rule.review_notes = notes
    db.commit()

    return {"id": str(rule.id), "status": "rejected"}


def get_rules_for_context(db: Session) -> str:
    """Build a text summary of all approved rules for AI chat context injection."""
    rules = (
        db.query(PolicyRule)
        .join(PolicyDocument)
        .filter(PolicyRule.status.in_([PolicyRuleStatus.approved, PolicyRuleStatus.pending]))
        .filter(PolicyRule.confidence >= 0.7)
        .order_by(PolicyRule.rule_type, PolicyRule.confidence.desc())
        .all()
    )

    if not rules:
        return ""

    lines = ["\n=== KNOWLEDGE BASE: POLICY RULES & CONTRACT TERMS ===\n"]
    current_type = None

    for r in rules:
        if r.rule_type != current_type:
            current_type = r.rule_type
            lines.append(f"\n## {current_type.upper().replace('_', ' ')}")

        source = f"[{r.policy_document.filename}]" if r.policy_document else ""
        lines.append(f"  - {r.source_text} {source}")
        if r.conditions:
            lines.append(f"    Conditions: {r.conditions}")
        if r.action:
            lines.append(f"    Action: {r.action}")

    return "\n".join(lines)
