"""Email template rendering service."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EmailTemplate:
    """Email template definitions and rendering."""

    TEMPLATES = {
        "credit_approval": {
            "subject": "Credit Request Approved - Invoice {invoice_id}",
            "body": """Dear {supplier_name},

Thank you for your invoice.

We are pleased to inform you that your credit request for Invoice {invoice_id} has been approved.

**Invoice Details:**
- Invoice Amount: {currency} {amount}
- Credit Approved: {currency} {credit_amount}
- Invoice Date: {invoice_date}

This credit will be processed within the standard payment terms.

If you have any questions, please contact our accounts payable department.

Best regards,
AP Operations Team""",
        },
        "po_request": {
            "subject": "Purchase Order Request - {supplier_name}",
            "body": """Dear {supplier_name},

We hope this message finds you well.

We are requesting a Purchase Order (PO) to proceed with your current invoice processing.

**Request Details:**
- Invoice ID: {invoice_id}
- Total Amount: {currency} {amount}
- PO Deadline: {deadline}

Please provide the PO at your earliest convenience to expedite the payment process.

Thank you for your prompt attention to this matter.

Best regards,
AP Operations Team""",
        },
        "credit_rejection": {
            "subject": "Credit Request Status - Invoice {invoice_id}",
            "body": """Dear {supplier_name},

Thank you for your invoice.

Regarding Invoice {invoice_id}, we are unable to approve the credit request at this time.

**Invoice Details:**
- Invoice Amount: {currency} {amount}
- Reason: {reason}

Please review the details and resubmit if needed. Contact our team if you have questions.

Best regards,
AP Operations Team""",
        },
    }

    @classmethod
    def render(
        cls,
        template_name: str,
        context: dict[str, Any],
    ) -> dict[str, str]:
        """
        Render an email template with context variables.

        Args:
            template_name: Name of the template (e.g., 'credit_approval')
            context: Dictionary of variables to replace in template

        Returns:
            Dictionary with 'subject' and 'body' keys
        """
        if template_name not in cls.TEMPLATES:
            raise ValueError(f"Template '{template_name}' not found")

        template = cls.TEMPLATES[template_name]
        subject = template["subject"]
        body = template["body"]

        # Replace all placeholders
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))

        logger.info(f"Rendered email template: {template_name}")
        return {
            "subject": subject,
            "body": body,
        }

    @classmethod
    def get_credit_approval_email(
        cls,
        supplier_name: str,
        invoice_id: str,
        amount: float,
        credit_amount: float,
        currency: str = "USD",
        invoice_date: str = "",
    ) -> dict[str, str]:
        """Get rendered credit approval email."""
        return cls.render(
            "credit_approval",
            {
                "supplier_name": supplier_name,
                "invoice_id": invoice_id,
                "amount": f"{amount:,.2f}",
                "credit_amount": f"{credit_amount:,.2f}",
                "currency": currency,
                "invoice_date": invoice_date,
            },
        )

    @classmethod
    def get_po_request_email(
        cls,
        supplier_name: str,
        invoice_id: str,
        amount: float,
        currency: str = "USD",
        deadline: str = "48 hours",
    ) -> dict[str, str]:
        """Get rendered PO request email."""
        return cls.render(
            "po_request",
            {
                "supplier_name": supplier_name,
                "invoice_id": invoice_id,
                "amount": f"{amount:,.2f}",
                "currency": currency,
                "deadline": deadline,
            },
        )

    @classmethod
    def get_credit_rejection_email(
        cls,
        supplier_name: str,
        invoice_id: str,
        amount: float,
        currency: str = "USD",
        reason: str = "Policy requirement",
    ) -> dict[str, str]:
        """Get rendered credit rejection email."""
        return cls.render(
            "credit_rejection",
            {
                "supplier_name": supplier_name,
                "invoice_id": invoice_id,
                "amount": f"{amount:,.2f}",
                "currency": currency,
                "reason": reason,
            },
        )
