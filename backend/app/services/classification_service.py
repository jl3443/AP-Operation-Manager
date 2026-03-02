"""Post-OCR AI classification and validation agent.

After OCR extraction, this agent:
1. Classifies the document type (invoice / credit_memo / debit_memo)
2. Validates extracted data for consistency
3. Cross-checks vendor information
4. Flags low-confidence or suspicious fields
5. Returns a quality assessment with recommendations
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.vendor import Vendor
from app.models.audit import AuditLog
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """You are an AP (Accounts Payable) document classification and validation agent.

Given extracted invoice data, perform:

1. DOCUMENT CLASSIFICATION
   - Classify as: "invoice", "credit_memo", or "debit_memo"
   - Reasoning: explain why (e.g. negative totals = credit memo, "Credit Note" in text)

2. DATA QUALITY VALIDATION
   Check for:
   - Missing critical fields (invoice_number, vendor_name, total_amount)
   - Line item totals vs header total consistency
   - Quantity * unit_price = line_total for each line
   - Date reasonableness (not future-dated beyond 30 days, not older than 2 years)
   - Currency code validity
   - Duplicate invoice number patterns

3. VENDOR CROSS-CHECK
   If vendor info is provided, verify:
   - Vendor name similarity
   - Tax ID match

4. FIELD CONFIDENCE ASSESSMENT
   For each field, rate confidence: high / medium / low
   Flag any fields that need human review.

Return ONLY valid JSON:
{
  "document_type": "invoice" | "credit_memo" | "debit_memo",
  "classification_confidence": 0.0-1.0,
  "classification_reasoning": "string",
  "validation_passed": true/false,
  "validation_issues": [
    {"field": "field_name", "issue": "description", "severity": "error" | "warning" | "info"}
  ],
  "field_confidence": {
    "invoice_number": "high" | "medium" | "low",
    "invoice_date": "high" | "medium" | "low",
    "total_amount": "high" | "medium" | "low",
    "vendor_name": "high" | "medium" | "low",
    "line_items": "high" | "medium" | "low"
  },
  "needs_human_review": true/false,
  "review_reasons": ["string"],
  "quality_score": 0.0-1.0,
  "recommendations": ["string"]
}"""


def _rule_based_validation(
    extracted_data: dict[str, Any],
    vendor: Vendor | None = None,
) -> list[dict[str, str]]:
    """Run deterministic validation rules on extracted data."""
    issues: list[dict[str, str]] = []

    # Required fields
    required = ["invoice_number", "total_amount"]
    for field in required:
        val = extracted_data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            issues.append({
                "field": field,
                "issue": f"Missing required field: {field}",
                "severity": "error",
            })

    # Total amount sanity
    total = extracted_data.get("total_amount")
    if total is not None:
        try:
            total_f = float(total)
            if total_f == 0:
                issues.append({
                    "field": "total_amount",
                    "issue": "Total amount is zero",
                    "severity": "warning",
                })
        except (ValueError, TypeError):
            issues.append({
                "field": "total_amount",
                "issue": "Total amount is not a valid number",
                "severity": "error",
            })

    # Line item math checks
    line_items = extracted_data.get("line_items", [])
    if line_items:
        computed_total = 0.0
        for i, li in enumerate(line_items):
            qty = float(li.get("quantity", 0) or 0)
            price = float(li.get("unit_price", 0) or 0)
            line_total = float(li.get("line_total", 0) or 0)

            expected = round(qty * price, 2)
            if expected > 0 and abs(expected - line_total) > 0.02:
                issues.append({
                    "field": f"line_items[{i}].line_total",
                    "issue": f"qty({qty}) * price({price}) = {expected}, but line_total = {line_total}",
                    "severity": "warning",
                })
            computed_total += line_total

        # Compare line total sum vs header total
        header_total = float(extracted_data.get("total_amount", 0) or 0)
        subtotal = float(extracted_data.get("subtotal", 0) or 0)
        tax = float(extracted_data.get("tax_amount", 0) or 0)

        # Allow small rounding difference
        compare_to = subtotal if subtotal > 0 else header_total
        if compare_to > 0 and abs(computed_total - compare_to) > 1.0:
            issues.append({
                "field": "line_items_total",
                "issue": f"Sum of line totals ({computed_total:.2f}) differs from header ({compare_to:.2f})",
                "severity": "warning",
            })

    # Date validation
    for date_field in ["invoice_date", "due_date"]:
        date_str = extracted_data.get(date_field)
        if date_str:
            try:
                parsed = datetime.strptime(str(date_str), "%Y-%m-%d").date()
                today = date.today()
                if parsed > today + timedelta(days=30):
                    issues.append({
                        "field": date_field,
                        "issue": f"{date_field} is more than 30 days in the future",
                        "severity": "warning",
                    })
                if parsed < today - timedelta(days=730):
                    issues.append({
                        "field": date_field,
                        "issue": f"{date_field} is more than 2 years old",
                        "severity": "warning",
                    })
            except ValueError:
                issues.append({
                    "field": date_field,
                    "issue": f"Invalid date format: {date_str}",
                    "severity": "error",
                })

    # Vendor cross-check
    if vendor:
        vendor_name_extracted = extracted_data.get("vendor_name", "")
        if vendor_name_extracted and vendor.name:
            # Simple containment check
            ext_lower = vendor_name_extracted.lower()
            db_lower = vendor.name.lower()
            if ext_lower not in db_lower and db_lower not in ext_lower:
                # Check for partial word overlap
                ext_words = set(ext_lower.split())
                db_words = set(db_lower.split())
                overlap = ext_words & db_words
                if len(overlap) < 1:
                    issues.append({
                        "field": "vendor_name",
                        "issue": f"Extracted vendor '{vendor_name_extracted}' does not match DB vendor '{vendor.name}'",
                        "severity": "warning",
                    })

    return issues


def classify_and_validate(
    db: Session,
    invoice_id: uuid.UUID,
    extracted_data: dict[str, Any],
    ocr_confidence: float,
) -> dict[str, Any]:
    """Run post-OCR classification and validation on an invoice.

    Returns a classification result dict with quality assessment.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise ValueError(f"Invoice {invoice_id} not found")

    vendor: Vendor | None = None
    if invoice.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == invoice.vendor_id).first()

    # Step 1: Rule-based validation (always runs, no AI needed)
    rule_issues = _rule_based_validation(extracted_data, vendor)

    # Step 2: AI classification (if available)
    ai_result = _run_ai_classification(extracted_data, vendor, ocr_confidence)

    # Step 3: Merge results
    if ai_result:
        # Merge rule-based issues into AI issues (avoid duplicates)
        existing_fields = {i["field"] for i in ai_result.get("validation_issues", [])}
        for issue in rule_issues:
            if issue["field"] not in existing_fields:
                ai_result["validation_issues"].append(issue)
        result = ai_result
    else:
        # Fallback: rule-based only
        has_errors = any(i["severity"] == "error" for i in rule_issues)
        result = _build_fallback_result(extracted_data, rule_issues, has_errors, ocr_confidence)

    # Step 4: Update invoice with classification
    doc_type = result.get("document_type", "invoice")
    if doc_type == "credit_memo":
        invoice.document_type = "credit_memo"
    elif doc_type == "debit_memo":
        invoice.document_type = "debit_memo"
    else:
        invoice.document_type = "invoice"

    # Store classification metadata in a dedicated audit log
    db.add(AuditLog(
        entity_type="invoice",
        entity_id=invoice.id,
        action="ai_classification",
        actor_type="ai_agent",
        actor_name="Classification Agent",
        changes={
            "document_type": doc_type,
            "quality_score": result.get("quality_score", 0),
        },
        evidence={
            "classification_confidence": result.get("classification_confidence", 0),
            "validation_passed": result.get("validation_passed", False),
            "needs_human_review": result.get("needs_human_review", False),
            "issue_count": len(result.get("validation_issues", [])),
            "ocr_confidence": ocr_confidence,
        },
    ))

    db.commit()

    return result


def _run_ai_classification(
    extracted_data: dict[str, Any],
    vendor: Vendor | None,
    ocr_confidence: float,
) -> dict[str, Any] | None:
    """Call Claude to classify and validate extracted data."""
    if not ai_service or not ai_service.client:
        logger.info("AI service unavailable, using rule-based classification only")
        return None

    vendor_context = ""
    if vendor:
        vendor_context = f"\nKnown vendor in system: name='{vendor.name}', code='{vendor.vendor_code}'"
        if vendor.tax_id:
            vendor_context += f", tax_id='{vendor.tax_id}'"

    user_msg = (
        f"Classify and validate this extracted invoice data.\n"
        f"OCR confidence score: {ocr_confidence:.2f}\n"
        f"{vendor_context}\n\n"
        f"Extracted data:\n{_safe_json_str(extracted_data)}"
    )

    try:
        response = ai_service.call_claude(
            system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
            user_message=user_msg,
            max_tokens=2048,
        )
        if not response:
            return None

        parsed = ai_service.extract_json(response)
        if not parsed:
            logger.warning("Failed to parse AI classification response")
            return None

        # Ensure required fields exist
        parsed.setdefault("validation_issues", [])
        parsed.setdefault("review_reasons", [])
        parsed.setdefault("recommendations", [])
        return parsed

    except Exception:
        logger.exception("AI classification failed")
        return None


def _build_fallback_result(
    extracted_data: dict[str, Any],
    issues: list[dict[str, str]],
    has_errors: bool,
    ocr_confidence: float,
) -> dict[str, Any]:
    """Build a classification result without AI, using rules only."""
    # Simple document type heuristic
    total = float(extracted_data.get("total_amount", 0) or 0)
    inv_num = str(extracted_data.get("invoice_number", "")).lower()

    if total < 0 or "credit" in inv_num or "cn" in inv_num:
        doc_type = "credit_memo"
    elif "debit" in inv_num or "dn" in inv_num:
        doc_type = "debit_memo"
    else:
        doc_type = "invoice"

    # Quality score based on OCR confidence and issues
    error_count = sum(1 for i in issues if i["severity"] == "error")
    warning_count = sum(1 for i in issues if i["severity"] == "warning")
    quality = ocr_confidence * 0.6 + max(0, 1.0 - error_count * 0.2 - warning_count * 0.05) * 0.4

    needs_review = has_errors or ocr_confidence < 0.7 or error_count > 0

    return {
        "document_type": doc_type,
        "classification_confidence": 0.7 if doc_type != "invoice" else 0.9,
        "classification_reasoning": "Rule-based classification (AI unavailable)",
        "validation_passed": not has_errors,
        "validation_issues": issues,
        "field_confidence": {
            "invoice_number": "high" if extracted_data.get("invoice_number") else "low",
            "invoice_date": "high" if extracted_data.get("invoice_date") else "low",
            "total_amount": "high" if extracted_data.get("total_amount") else "low",
            "vendor_name": "medium" if extracted_data.get("vendor_name") else "low",
            "line_items": "high" if extracted_data.get("line_items") else "low",
        },
        "needs_human_review": needs_review,
        "review_reasons": (
            [f"{error_count} validation error(s) found"] if error_count else []
        ) + (
            ["Low OCR confidence"] if ocr_confidence < 0.7 else []
        ),
        "quality_score": round(quality, 2),
        "recommendations": (
            ["Review flagged validation errors before processing"] if error_count else []
        ),
    }


def _safe_json_str(data: Any) -> str:
    """Serialize data to JSON string, handling non-serializable types."""
    import json

    def default(obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return str(obj)

    return json.dumps(data, indent=2, default=default)
