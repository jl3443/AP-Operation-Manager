"""AI-generated executive summary service for analytics and dashboard pages.

Provides a cached AI summary of AP operations data, refreshed every 5 minutes.
Reuses the system stats builder from chat_service for comprehensive context.
"""

from __future__ import annotations

import logging
import time

from sqlalchemy.orm import Session

from app.services.ai_service import ai_service
from app.services.chat_service import _get_system_stats

logger = logging.getLogger(__name__)

# In-memory cache: { page_name: (summary_text, timestamp) }
_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

SUMMARY_PROMPTS: dict[str, str] = {
    "analytics": (
        "Write 2 sentences max (under 30 words total) summarizing AP analytics. "
        "Mention one key risk and one metric. Use numbers. "
        "No markdown, no bullets, no headers. Be extremely brief."
    ),
    "dashboard": (
        "Write 2 sentences max (under 30 words total) as an AP dashboard summary. "
        "Mention processing health and one urgent item. Use numbers. "
        "No markdown, no bullets, no headers. Be extremely brief."
    ),
}

FALLBACK_SUMMARIES: dict[str, str] = {
    "analytics": (
        "Analytics data is being compiled. AI-powered insights will appear here "
        "once the system processes current invoice and exception data."
    ),
    "dashboard": (
        "Dashboard data is being compiled. AI-powered insights will appear here "
        "once the system processes current operational metrics."
    ),
}


def get_ai_summary(db: Session, page: str) -> str:
    """Generate or retrieve a cached AI summary for the given page.

    Args:
        db: Database session for querying current state.
        page: One of 'analytics' or 'dashboard'.

    Returns:
        A 2-3 sentence plain-text executive summary.
    """
    now = time.time()

    # Check cache
    if page in _cache:
        cached_text, cached_at = _cache[page]
        if now - cached_at < CACHE_TTL_SECONDS:
            logger.debug("AI summary cache hit for page=%s (age=%.0fs)", page, now - cached_at)
            return cached_text

    # Generate fresh summary
    if not ai_service.available:
        logger.warning("AI service unavailable, returning fallback summary for page=%s", page)
        return FALLBACK_SUMMARIES.get(page, "AI summary unavailable.")

    try:
        system_stats = _get_system_stats(db)
        prompt = SUMMARY_PROMPTS.get(page, SUMMARY_PROMPTS["dashboard"])

        summary = ai_service.call_claude(
            system_prompt=prompt,
            user_message=f"Here is the current AP system data:\n\n{system_stats}",
            max_tokens=150,
        )

        if summary and summary.strip():
            clean_summary = summary.strip()
            _cache[page] = (clean_summary, now)
            logger.info("AI summary generated for page=%s (%d chars)", page, len(clean_summary))
            return clean_summary
        else:
            logger.warning("AI returned empty summary for page=%s", page)
            return FALLBACK_SUMMARIES.get(page, "AI summary unavailable.")

    except Exception as e:
        logger.error("AI summary generation failed for page=%s: %s", page, e)
        return FALLBACK_SUMMARIES.get(page, "AI summary unavailable.")
