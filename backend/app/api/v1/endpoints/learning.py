"""Learning engine endpoints — feedback loops, threshold tuning, and self-improvement."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/summary")
def get_learning_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a comprehensive learning and improvement summary."""
    from app.services.learning_engine import get_learning_summary

    return get_learning_summary(db)


@router.get("/resolution-patterns")
def get_resolution_patterns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze exception resolution patterns."""
    from app.services.learning_engine import analyze_resolution_patterns

    return analyze_resolution_patterns(db)


@router.get("/threshold-recommendations")
def get_threshold_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-recommended threshold adjustments."""
    from app.services.learning_engine import recommend_threshold_adjustments

    return recommend_threshold_adjustments(db)


@router.get("/rule-suggestions")
def get_rule_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-suggested new business rules."""
    from app.services.learning_engine import suggest_new_rules

    return suggest_new_rules(db)


@router.get("/benchmarks")
def get_benchmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get performance benchmarks with industry comparisons."""
    from app.services.learning_engine import get_performance_benchmarks

    return get_performance_benchmarks(db)
