"""Invoice extraction service with 3-tier OCR pipeline.

Tier 1: pdfplumber — extract text from digital/text-based PDFs (fast, free)
Tier 2: pdf2image + pytesseract — OCR for scanned PDFs (when pdfplumber finds no text)
Tier 3: Claude Vision — structured extraction from images or as fallback

All tiers ultimately pass through Claude for structured JSON extraction when
the AI service is available.
"""

from __future__ import annotations

import io
import logging
import tempfile
from typing import Any

from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """\
You are an expert accounts-payable document processor. Given invoice text or an \
invoice image/PDF, extract all structured data and return ONLY a JSON object \
(no markdown, no explanation) with exactly this schema:

{
  "invoice_number": "string",
  "vendor_name": "string",
  "vendor_tax_id": "string or null",
  "vendor_address": "string or null",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "currency": "3-letter ISO code",
  "po_number": "string or null",
  "subtotal": number,
  "tax_amount": number,
  "freight_amount": number,
  "discount_amount": number,
  "total_amount": number,
  "line_items": [
    {
      "line_number": integer,
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "line_total": number,
      "tax_amount": number,
      "gl_account_code": "predicted GL code or null",
      "gl_confidence": number between 0 and 1
    }
  ]
}

Rules:
- Use 0 for any missing numeric fields.
- If a PO number or reference is mentioned anywhere in the document, extract it.
- Predict the most likely GL account code for each line item based on the \
description (e.g., office supplies → 6100-00, IT equipment → 1500-00, \
raw materials → 5200-00, packaging → 5300-00, services → 6200-00, \
fabrication/manufacturing → 5100-00, metal work → 5200-00).
- gl_confidence is your confidence in the GL prediction (0.0 – 1.0).
- Return ONLY valid JSON, no extra text."""

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def _media_type_for(filename: str) -> str | None:
    """Determine MIME type from filename extension."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return MEDIA_TYPES.get(ext)


def _compute_confidence(extracted: dict[str, Any]) -> float:
    """Compute OCR confidence score based on extraction completeness."""
    required_fields = [
        "invoice_number", "vendor_name", "invoice_date",
        "due_date", "currency", "total_amount",
    ]
    filled = sum(1 for f in required_fields if extracted.get(f))
    field_score = filled / len(required_fields)

    line_items = extracted.get("line_items", [])
    has_lines = 1.0 if line_items else 0.0

    line_quality = 0.0
    if line_items:
        good_lines = sum(
            1 for li in line_items
            if li.get("description") and li.get("line_total", 0) > 0
        )
        line_quality = good_lines / len(line_items)

    score = field_score * 0.5 + has_lines * 0.2 + line_quality * 0.3
    return round(min(max(score, 0.0), 1.0), 2)


# ── Tier 1: pdfplumber (digital/text-based PDFs) ─────────────────────────


def _extract_text_pdfplumber(file_content: bytes) -> str:
    """Extract text from a PDF using pdfplumber (works for text-based PDFs)."""
    try:
        import pdfplumber

        text_parts = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

                # Also extract tables if present
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            cells = [str(c).strip() for c in row if c]
                            if cells:
                                text_parts.append(" | ".join(cells))

        combined = "\n".join(text_parts).strip()
        logger.info(
            "pdfplumber extracted %d characters from PDF", len(combined)
        )
        return combined
    except Exception as e:
        logger.warning("pdfplumber extraction failed: %s", e)
        return ""


# ── Tier 2: pdf2image + pytesseract (scanned PDFs) ──────────────────────


def _extract_text_tesseract(file_content: bytes) -> str:
    """Extract text from a scanned PDF using Tesseract OCR."""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract

        logger.info("Converting PDF to images for Tesseract OCR...")
        images = convert_from_bytes(file_content, dpi=300)

        text_parts = []
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img, lang="eng")
            if page_text.strip():
                text_parts.append(page_text.strip())
            logger.info("Tesseract page %d: extracted %d chars", i + 1, len(page_text))

        combined = "\n".join(text_parts).strip()
        logger.info("Tesseract OCR extracted %d total characters", len(combined))
        return combined
    except ImportError as e:
        logger.warning("Tesseract OCR dependencies not installed: %s", e)
        return ""
    except Exception as e:
        logger.warning("Tesseract OCR failed: %s", e)
        return ""


def _extract_text_tesseract_image(file_content: bytes) -> str:
    """Extract text from a raster image (PNG/JPG) using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(img, lang="eng")
        logger.info("Tesseract image OCR extracted %d characters", len(text))
        return text.strip()
    except ImportError as e:
        logger.warning("Tesseract/PIL not installed: %s", e)
        return ""
    except Exception as e:
        logger.warning("Tesseract image OCR failed: %s", e)
        return ""


# ── Tier 3: Claude Vision (structured extraction) ────────────────────────


def _extract_via_claude_vision(
    file_content: bytes, media_type: str
) -> dict[str, Any] | None:
    """Send file directly to Claude Vision for extraction."""
    if not ai_service.available:
        return None

    logger.info("Sending to Claude Vision (media_type=%s)", media_type)
    raw = ai_service.call_claude_vision(
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        image_data=file_content,
        media_type=media_type,
        user_message="Extract all data from this invoice document.",
        max_tokens=4096,
    )

    parsed = ai_service.extract_json(raw) if raw else None
    if parsed:
        logger.info("Claude Vision extraction successful")
    else:
        logger.warning("Claude Vision returned no parseable JSON")
    return parsed


def _structure_via_claude_text(raw_text: str) -> dict[str, Any] | None:
    """Send raw OCR text to Claude for structured extraction."""
    if not ai_service.available:
        return None

    logger.info("Sending %d chars of OCR text to Claude for structuring", len(raw_text))
    raw = ai_service.call_claude_with_text(
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        text_content=raw_text,
        user_message=(
            "The following is raw text extracted from an invoice document via OCR. "
            "Parse it carefully and return the structured JSON."
        ),
        max_tokens=4096,
    )

    parsed = ai_service.extract_json(raw) if raw else None
    if parsed:
        logger.info("Claude text structuring successful")
    else:
        logger.warning("Claude text structuring returned no parseable JSON")
    return parsed


# ── Normalise parsed data ────────────────────────────────────────────────


def _normalise_extraction(parsed: dict[str, Any]) -> dict[str, Any]:
    """Convert parsed JSON into the standard shape the rest of the app expects."""
    line_items = []
    for li in parsed.get("line_items", []):
        line_items.append(
            {
                "line_number": li.get("line_number", 1),
                "description": li.get("description", ""),
                "quantity": li.get("quantity", 1),
                "unit_price": li.get("unit_price", 0),
                "line_total": li.get("line_total", 0),
                "tax_amount": li.get("tax_amount", 0),
                "ai_gl_prediction": li.get("gl_account_code"),
                "ai_confidence": li.get("gl_confidence", 0),
            }
        )

    return {
        "invoice_number": parsed.get("invoice_number", ""),
        "vendor_name": parsed.get("vendor_name", ""),
        "vendor_tax_id": parsed.get("vendor_tax_id"),
        "vendor_address": parsed.get("vendor_address"),
        "po_number": parsed.get("po_number"),
        "invoice_date": parsed.get("invoice_date", ""),
        "due_date": parsed.get("due_date", ""),
        "currency": parsed.get("currency", "USD"),
        "subtotal": parsed.get("subtotal", 0),
        "tax_amount": parsed.get("tax_amount", 0),
        "freight_amount": parsed.get("freight_amount", 0),
        "discount_amount": parsed.get("discount_amount", 0),
        "total_amount": parsed.get("total_amount", 0),
        "line_items": line_items,
    }


# ── Main extraction entry point ──────────────────────────────────────────


def extract_invoice(
    file_content: bytes,
    filename: str = "invoice.pdf",
) -> dict[str, Any]:
    """Extract invoice data from an image/PDF using a 3-tier OCR pipeline.

    Tier 1: pdfplumber (digital PDFs — fast, free)
    Tier 2: pdf2image + pytesseract (scanned PDFs)
    Tier 3: Claude Vision (direct image/PDF processing)

    When text is extracted (Tier 1 or 2), it's sent to Claude for structured
    JSON extraction. For images, Claude Vision processes them directly.
    """
    media_type = _media_type_for(filename)
    is_pdf = media_type == "application/pdf"
    is_image = media_type and media_type.startswith("image/")

    extraction_method = "unknown"
    raw_text = ""
    parsed: dict[str, Any] | None = None

    if is_pdf:
        # ── Tier 1: Try pdfplumber for text-based PDFs ────────────────
        raw_text = _extract_text_pdfplumber(file_content)

        if len(raw_text) > 50:
            extraction_method = "pdfplumber"
            logger.info("Tier 1 (pdfplumber) extracted sufficient text (%d chars)", len(raw_text))
        else:
            # ── Tier 2: Scanned PDF → images → Tesseract ─────────────
            logger.info("Tier 1 insufficient (%d chars), trying Tier 2 (Tesseract)...", len(raw_text))
            raw_text = _extract_text_tesseract(file_content)

            if len(raw_text) > 50:
                extraction_method = "tesseract"
                logger.info("Tier 2 (Tesseract) extracted sufficient text (%d chars)", len(raw_text))

        # If we got text from Tier 1 or 2, send to Claude for structuring
        if len(raw_text) > 50 and ai_service.available:
            parsed = _structure_via_claude_text(raw_text)

        # If text-based structuring failed, try Claude Vision directly
        if not parsed and media_type:
            logger.info("Text extraction didn't yield structured data, trying Claude Vision directly...")
            parsed = _extract_via_claude_vision(file_content, media_type)
            if parsed:
                extraction_method = "claude_vision"

    elif is_image:
        # ── Images: Try Tesseract first, then Claude Vision ──────────
        raw_text = _extract_text_tesseract_image(file_content)
        if len(raw_text) > 50 and ai_service.available:
            extraction_method = "tesseract_image"
            parsed = _structure_via_claude_text(raw_text)

        # Fallback to Claude Vision for images
        if not parsed and media_type:
            parsed = _extract_via_claude_vision(file_content, media_type)
            if parsed:
                extraction_method = "claude_vision"

    else:
        logger.warning("Unsupported file type: %s (media_type=%s)", filename, media_type)

    # ── Build result ──────────────────────────────────────────────────
    if parsed:
        extracted = _normalise_extraction(parsed)
        confidence = _compute_confidence(extracted)
        logger.info(
            "Extraction complete: method=%s, confidence=%.2f, invoice=%s, total=%s",
            extraction_method,
            confidence,
            extracted.get("invoice_number", "?"),
            extracted.get("total_amount", "?"),
        )
        return {
            "confidence": confidence,
            "extracted_data": extracted,
            "raw_text": raw_text or "(extracted via vision)",
            "pages_processed": 1,
            "extraction_method": extraction_method,
        }

    # ── All tiers failed — return raw text if we have any ─────────────
    if raw_text:
        logger.warning(
            "AI structuring unavailable but raw text extracted (%d chars). "
            "Returning raw text without structured extraction.",
            len(raw_text),
        )
        return {
            "confidence": 0.1,
            "extracted_data": {
                "invoice_number": "",
                "vendor_name": "",
                "vendor_tax_id": None,
                "vendor_address": None,
                "po_number": None,
                "invoice_date": "",
                "due_date": "",
                "currency": "USD",
                "subtotal": 0,
                "tax_amount": 0,
                "freight_amount": 0,
                "discount_amount": 0,
                "total_amount": 0,
                "line_items": [],
            },
            "raw_text": raw_text,
            "pages_processed": 1,
            "extraction_method": f"{extraction_method}_text_only",
            "error": "AI service unavailable — raw text extracted but not structured",
        }

    # ── Nothing worked ────────────────────────────────────────────────
    logger.error("All OCR tiers failed for file: %s", filename)
    return {
        "confidence": 0.0,
        "extracted_data": {
            "invoice_number": "",
            "vendor_name": "",
            "vendor_tax_id": None,
            "vendor_address": None,
            "po_number": None,
            "invoice_date": "",
            "due_date": "",
            "currency": "USD",
            "subtotal": 0,
            "tax_amount": 0,
            "freight_amount": 0,
            "discount_amount": 0,
            "total_amount": 0,
            "line_items": [],
        },
        "raw_text": "",
        "pages_processed": 0,
        "extraction_method": "failed",
        "error": "All OCR extraction methods failed",
    }
