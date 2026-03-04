"""Learning engine — feedback loops, threshold tuning, and rule suggestions.

Analyzes historical resolution patterns, user feedback, and operational
metrics to recommend tolerance adjustments, new rules, and process
improvements.  This is ACT 6 of the 6-ACT framework: AI Improves Itself.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.exception import Exception_, ExceptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.matching import MatchResult, MatchStatus
from app.models.vendor import Vendor, VendorStatus

logger = logging.getLogger(__name__)


# ── Resolution Pattern Analysis ──────────────────────────────────────


def analyze_resolution_patterns(db: Session) -> dict[str, Any]:
    """Analyze how exceptions have been resolved to find optimization patterns."""
    resolved = db.query(Exception_).filter(Exception_.status == ExceptionStatus.resolved).all()

    all_exceptions = db.query(Exception_).all()

    if not all_exceptions:
        return {
            "total_exceptions": 0,
            "resolved_count": 0,
            "patterns": [],
            "auto_resolve_rate": 0,
        }

    # Group by exception type
    by_type: dict[str, list] = defaultdict(list)
    for exc in all_exceptions:
        by_type[exc.exception_type].append(exc)

    patterns = []
    for exc_type, exceptions in by_type.items():
        resolved_in_type = [e for e in exceptions if e.status == ExceptionStatus.resolved]
        auto_resolved = [e for e in resolved_in_type if e.resolution_type and "auto" in str(e.resolution_type)]
        tolerance_applied = [e for e in resolved_in_type if e.resolution_type and "tolerance" in str(e.resolution_type)]

        patterns.append(
            {
                "exception_type": exc_type,
                "total_count": len(exceptions),
                "resolved_count": len(resolved_in_type),
                "auto_resolved_count": len(auto_resolved),
                "tolerance_applied_count": len(tolerance_applied),
                "resolution_rate": round(len(resolved_in_type) / len(exceptions) * 100, 1) if exceptions else 0,
                "auto_resolve_rate": round(len(auto_resolved) / len(exceptions) * 100, 1) if exceptions else 0,
            }
        )

    total_auto = sum(p["auto_resolved_count"] for p in patterns)
    return {
        "total_exceptions": len(all_exceptions),
        "resolved_count": len(resolved),
        "auto_resolve_rate": round(total_auto / len(all_exceptions) * 100, 1) if all_exceptions else 0,
        "patterns": sorted(patterns, key=lambda p: p["total_count"], reverse=True),
    }


# ── Threshold Tuning Recommendations ─────────────────────────────────


def recommend_threshold_adjustments(db: Session) -> list[dict[str, Any]]:
    """Analyze variance patterns to recommend tolerance threshold changes."""
    recommendations = []

    # Get amount variance exceptions
    amount_exceptions = db.query(Exception_).filter(Exception_.exception_type == "amount_variance").all()

    if amount_exceptions:
        # Since we don't store variance details on exceptions, analyze the count and resolution patterns
        total_amt_exc = len(amount_exceptions)
        resolved_amount = [e for e in amount_exceptions if e.status == ExceptionStatus.resolved]

        if total_amt_exc >= 2:
            recommendations.append(
                {
                    "id": "THR-001",
                    "type": "threshold_adjustment",
                    "title": "Increase Amount Tolerance to 5%",
                    "description": f"{total_amt_exc} amount variance exceptions detected. "
                    f"Increasing tolerance from 2% to 5% would likely auto-resolve many of these.",
                    "current_value": "2%",
                    "recommended_value": "5%",
                    "impact": f"Could auto-resolve up to {total_amt_exc} exceptions",
                    "confidence": 0.75,
                    "category": "tolerance",
                }
            )

        if len(resolved_amount) > total_amt_exc * 0.5:
            recommendations.append(
                {
                    "id": "THR-002",
                    "type": "threshold_adjustment",
                    "title": "Amount Variance Auto-Resolution Pattern Detected",
                    "description": f"{len(resolved_amount)}/{total_amt_exc} amount variance exceptions were eventually resolved. "
                    "Consider pre-approving these within tolerance to reduce manual workload.",
                    "current_value": "Manual review",
                    "recommended_value": "Auto-resolve within 5% tolerance",
                    "impact": "Reduce exception review time by ~70%",
                    "confidence": round(len(resolved_amount) / total_amt_exc, 2) if total_amt_exc else 0,
                    "category": "auto_resolution",
                }
            )

    # Quantity variance analysis
    qty_exceptions = db.query(Exception_).filter(Exception_.exception_type == "quantity_variance").all()

    if qty_exceptions:
        resolved_qty = [e for e in qty_exceptions if e.status == ExceptionStatus.resolved]
        if len(resolved_qty) > len(qty_exceptions) * 0.5:
            recommendations.append(
                {
                    "id": "THR-003",
                    "type": "threshold_adjustment",
                    "title": "Enable Partial Delivery Tolerance",
                    "description": f"{len(qty_exceptions)} quantity variance exceptions detected. "
                    f"{len(resolved_qty)} were resolved, suggesting a tolerance for partial deliveries (e.g., 10%) would reduce workload.",
                    "current_value": "0% (exact match required)",
                    "recommended_value": "10% partial delivery tolerance",
                    "impact": f"Auto-resolve up to {len(resolved_qty)} quantity exceptions",
                    "confidence": 0.75,
                    "category": "tolerance",
                }
            )

    # Vendor-specific tolerance recommendation
    vendor_exceptions = (
        db.query(
            Invoice.vendor_id,
            func.count(Exception_.id).label("exc_count"),
        )
        .join(Exception_, Exception_.invoice_id == Invoice.id)
        .group_by(Invoice.vendor_id)
        .having(func.count(Exception_.id) >= 3)
        .all()
    )

    for vendor_id, exc_count in vendor_exceptions:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if vendor:
            recommendations.append(
                {
                    "id": f"THR-V-{str(vendor.id)[:8]}",
                    "type": "vendor_specific",
                    "title": f"Vendor-Specific Tolerance for {vendor.name}",
                    "description": f"{vendor.name} has {exc_count} exceptions. Consider setting a vendor-specific tolerance "
                    "to account for their typical invoice variances.",
                    "current_value": "Global tolerance",
                    "recommended_value": "Vendor-specific 3% tolerance",
                    "impact": f"Reduce {vendor.name} exceptions by up to 50%",
                    "confidence": 0.65,
                    "category": "vendor_config",
                }
            )

    return recommendations


# ── Rule Suggestions ─────────────────────────────────────────────────


def suggest_new_rules(db: Session) -> list[dict[str, Any]]:
    """Analyze system data to suggest new business rules or rule modifications."""
    suggestions = []

    # Suggestion 1: Vendor-on-hold blocking rule
    on_hold_invoices = (
        db.query(func.count(Invoice.id))
        .join(Vendor, Vendor.id == Invoice.vendor_id)
        .filter(Vendor.status == VendorStatus.on_hold)
        .filter(Invoice.status.notin_([InvoiceStatus.draft, InvoiceStatus.rejected]))
        .scalar()
        or 0
    )

    if on_hold_invoices > 0:
        suggestions.append(
            {
                "id": "RULE-001",
                "type": "new_rule",
                "title": "Block Invoices from On-Hold Vendors at Ingestion",
                "description": f"Currently {on_hold_invoices} invoices from on-hold vendors were processed. "
                "Add a pre-processing check to block these at the ingestion stage.",
                "rule_text": "IF vendor.status = 'on_hold' THEN reject invoice at ingestion with reason 'Vendor on hold'",
                "impact": "Prevent processing of unauthorized vendor invoices",
                "confidence": 0.95,
                "category": "validation",
            }
        )

    # Suggestion 2: Duplicate invoice pattern
    dupes = (
        db.query(Invoice.invoice_number, Invoice.vendor_id, func.count(Invoice.id))
        .group_by(Invoice.invoice_number, Invoice.vendor_id)
        .having(func.count(Invoice.id) > 1)
        .all()
    )

    if dupes:
        suggestions.append(
            {
                "id": "RULE-002",
                "type": "rule_enhancement",
                "title": "Strengthen Duplicate Detection with Fuzzy Matching",
                "description": f"{len(dupes)} duplicate invoice groups found. Enhance duplicate detection "
                "to include fuzzy matching on amount + date + vendor for near-duplicates.",
                "rule_text": "IF (vendor_match AND amount_within_1% AND date_within_7_days) THEN flag as potential duplicate",
                "impact": "Catch additional duplicates before processing",
                "confidence": 0.80,
                "category": "duplicate_prevention",
            }
        )

    # Suggestion 3: Approval routing optimization
    db.query(AuditLog).filter(AuditLog.action == "status_change").all()
    pending_count = (
        db.query(func.count(Invoice.id)).filter(Invoice.status == InvoiceStatus.pending_approval).scalar() or 0
    )

    if pending_count > 3:
        suggestions.append(
            {
                "id": "RULE-003",
                "type": "process_improvement",
                "title": "Implement Tiered Auto-Approval",
                "description": f"{pending_count} invoices pending approval. For invoices under $1,000 with "
                "a successful 3-way match, consider auto-approval to improve throughput.",
                "rule_text": "IF invoice.amount < $1000 AND match_status = 'matched' THEN auto_approve",
                "impact": "Increase touchless processing rate by estimated 15-20%",
                "confidence": 0.70,
                "category": "approval",
            }
        )

    # Suggestion 4: Exception SLA enforcement
    sla_breached = (
        db.query(func.count(Exception_.id))
        .filter(Exception_.status.in_([ExceptionStatus.open, ExceptionStatus.assigned]))
        .filter(Exception_.created_at < datetime.utcnow() - timedelta(hours=48))
        .scalar()
        or 0
    )

    if sla_breached > 0:
        suggestions.append(
            {
                "id": "RULE-004",
                "type": "escalation_rule",
                "title": "Implement Auto-Escalation for SLA Breaches",
                "description": f"{sla_breached} exceptions have breached the 48-hour SLA. "
                "Add automated escalation to management when exceptions approach the SLA deadline.",
                "rule_text": "IF exception.age > 36h AND status IN ('open','assigned') THEN escalate_to_manager AND send_alert",
                "impact": "Ensure 100% SLA compliance on exception resolution",
                "confidence": 0.90,
                "category": "escalation",
            }
        )

    return suggestions


# ── Performance Benchmarking ─────────────────────────────────────────


def get_performance_benchmarks(db: Session) -> dict[str, Any]:
    """Calculate operational performance benchmarks and trends."""
    total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
    total_exceptions = db.query(func.count(Exception_.id)).scalar() or 0
    resolved_exceptions = (
        db.query(func.count(Exception_.id)).filter(Exception_.status == ExceptionStatus.resolved).scalar() or 0
    )

    # Match performance
    total_matched = db.query(func.count(MatchResult.id)).scalar() or 0
    perfect_matches = (
        db.query(func.count(MatchResult.id)).filter(MatchResult.match_status == MatchStatus.matched).scalar() or 0
    )
    tolerance_matches = (
        db.query(func.count(MatchResult.id)).filter(MatchResult.tolerance_applied.is_(True)).scalar() or 0
    )

    # Touchless rate
    posted = db.query(func.count(Invoice.id)).filter(Invoice.status == InvoiceStatus.posted).scalar() or 0
    touchless_rate = (posted / total_invoices * 100) if total_invoices > 0 else 0

    # Exception rate
    exception_rate = (total_exceptions / total_invoices * 100) if total_invoices > 0 else 0

    # Status distribution
    statuses = db.query(Invoice.status, func.count(Invoice.id)).group_by(Invoice.status).all()

    # Industry benchmark comparisons (typical AP automation benchmarks)
    benchmarks = {
        "touchless_rate": {
            "current": round(touchless_rate, 1),
            "industry_avg": 30.0,
            "best_in_class": 80.0,
            "rating": "above_average"
            if touchless_rate > 30
            else "below_average"
            if touchless_rate > 15
            else "needs_improvement",
        },
        "exception_rate": {
            "current": round(exception_rate, 1),
            "industry_avg": 25.0,
            "best_in_class": 5.0,
            "rating": "best_in_class"
            if exception_rate < 5
            else "above_average"
            if exception_rate < 25
            else "needs_improvement",
        },
        "first_time_match_rate": {
            "current": round(perfect_matches / total_matched * 100, 1) if total_matched > 0 else 0,
            "industry_avg": 60.0,
            "best_in_class": 90.0,
            "rating": "above_average",
        },
        "exception_resolution_rate": {
            "current": round(resolved_exceptions / total_exceptions * 100, 1) if total_exceptions > 0 else 0,
            "industry_avg": 70.0,
            "best_in_class": 95.0,
            "rating": "above_average",
        },
    }

    return {
        "total_invoices": total_invoices,
        "total_exceptions": total_exceptions,
        "touchless_rate": round(touchless_rate, 1),
        "exception_rate": round(exception_rate, 1),
        "match_performance": {
            "total_matched": total_matched,
            "perfect_matches": perfect_matches,
            "tolerance_matches": tolerance_matches,
        },
        "status_distribution": {s.value if hasattr(s, "value") else str(s): c for s, c in statuses},
        "benchmarks": benchmarks,
    }


# ── Comprehensive Learning Summary ──────────────────────────────────


def get_learning_summary(db: Session) -> dict[str, Any]:
    """Generate a comprehensive learning and improvement summary.

    Combines resolution patterns, threshold recommendations, rule suggestions,
    and performance benchmarks into a single view.
    """
    patterns = analyze_resolution_patterns(db)
    threshold_recs = recommend_threshold_adjustments(db)
    rule_suggestions = suggest_new_rules(db)
    benchmarks = get_performance_benchmarks(db)

    # Compute improvement score (0-100)
    improvement_areas = 0
    total_areas = 4

    if benchmarks["touchless_rate"] > 30:
        improvement_areas += 1
    if benchmarks["exception_rate"] < 25:
        improvement_areas += 1
    if patterns["auto_resolve_rate"] > 20:
        improvement_areas += 1
    if len(threshold_recs) <= 2:
        improvement_areas += 1

    maturity_score = round(improvement_areas / total_areas * 100)

    return {
        "maturity_score": maturity_score,
        "maturity_level": (
            "Optimized"
            if maturity_score >= 75
            else "Managed"
            if maturity_score >= 50
            else "Developing"
            if maturity_score >= 25
            else "Initial"
        ),
        "resolution_patterns": patterns,
        "threshold_recommendations": threshold_recs,
        "rule_suggestions": rule_suggestions,
        "benchmarks": benchmarks,
        "total_recommendations": len(threshold_recs) + len(rule_suggestions),
        "generated_at": datetime.utcnow().isoformat(),
    }
