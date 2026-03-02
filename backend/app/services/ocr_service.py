"""Mock OCR extraction service.

In production this would call an external OCR/AI service.  For now it
returns a pre-defined JSON payload with confidence scores.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any


def mock_extract_invoice(file_path: str | None = None) -> dict[str, Any]:
    """Simulate OCR extraction and return structured invoice data.

    Returns a realistic-looking extraction result that the API layer
    can use to populate / update an Invoice record.
    """
    return {
        "confidence": 0.92,
        "extracted_data": {
            "invoice_number": "INV-2025-00142",
            "vendor_name": "Acme Supplies Co.",
            "vendor_tax_id": "12-3456789",
            "invoice_date": str(date(2025, 6, 15)),
            "due_date": str(date(2025, 7, 15)),
            "currency": "USD",
            "subtotal": 4250.00,
            "tax_amount": 340.00,
            "freight_amount": 75.00,
            "discount_amount": 0.00,
            "total_amount": 4665.00,
            "line_items": [
                {
                    "line_number": 1,
                    "description": "Industrial Widget A",
                    "quantity": 50,
                    "unit_price": 45.00,
                    "line_total": 2250.00,
                    "tax_amount": 180.00,
                    "ai_gl_prediction": "5200-00",
                    "ai_confidence": 0.88,
                },
                {
                    "line_number": 2,
                    "description": "Packing Material B",
                    "quantity": 100,
                    "unit_price": 20.00,
                    "line_total": 2000.00,
                    "tax_amount": 160.00,
                    "ai_gl_prediction": "5300-00",
                    "ai_confidence": 0.81,
                },
            ],
        },
        "raw_text": (
            "INVOICE\n"
            "Invoice No: INV-2025-00142\n"
            "Date: 2025-06-15\n"
            "Due: 2025-07-15\n"
            "...\n"
        ),
        "pages_processed": 1,
    }
