"""PDF analytics report generation using ReportLab."""

from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.exception import Exception_, ExceptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.matching import MatchResult, MatchStatus
from app.models.vendor import Vendor

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
HEADER_BG = colors.HexColor("#1e293b")
HEADER_FG = colors.white
ROW_ALT = colors.HexColor("#f1f5f9")
ROW_NORMAL = colors.white
BORDER_COLOR = colors.HexColor("#cbd5e1")


def _build_table(
    data: List[List[str]],
    col_widths: List[float] | None = None,
) -> Table:
    """Build a styled Table with dark header and alternating rows."""
    table = Table(data, colWidths=col_widths, repeatRows=1)

    style_commands: list = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    # Alternating row colours
    for i in range(1, len(data)):
        bg = ROW_ALT if i % 2 == 0 else ROW_NORMAL
        style_commands.append(("BACKGROUND", (0, i), (-1, i), bg))

    table.setStyle(TableStyle(style_commands))
    return table


def generate_analytics_pdf(
    db: Session,
    date_from: date,
    date_to: date,
) -> bytes:
    """Generate a multi-page PDF analytics report and return raw bytes."""

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=4,
        textColor=HEADER_BG,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=20,
        textColor=colors.HexColor("#64748b"),
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=18,
        spaceAfter=8,
        textColor=HEADER_BG,
    )

    elements: list = []

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    elements.append(Paragraph("AP Operations Analytics Report", title_style))
    elements.append(
        Paragraph(
            f"Period: {date_from.isoformat()} to {date_to.isoformat()}",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 12))

    # ------------------------------------------------------------------
    # KPI Summary
    # ------------------------------------------------------------------
    total_invoices = (
        db.query(func.count(Invoice.id))
        .filter(
            func.date(Invoice.created_at) >= date_from,
            func.date(Invoice.created_at) <= date_to,
        )
        .scalar()
        or 0
    )
    pending_approval = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.status == InvoiceStatus.pending_approval)
        .scalar()
        or 0
    )
    open_exceptions = (
        db.query(func.count(Exception_.id))
        .filter(
            Exception_.status.in_(
                [ExceptionStatus.open, ExceptionStatus.assigned, ExceptionStatus.in_progress]
            )
        )
        .scalar()
        or 0
    )
    total_matched = db.query(func.count(MatchResult.id)).scalar() or 0
    fully_matched = (
        db.query(func.count(MatchResult.id))
        .filter(
            MatchResult.match_status.in_(
                [MatchStatus.matched, MatchStatus.tolerance_passed]
            )
        )
        .scalar()
        or 0
    )
    match_rate = round((fully_matched / total_matched * 100) if total_matched else 0.0, 1)

    elements.append(Paragraph("KPI Summary", section_style))
    kpi_data = [
        ["Metric", "Value"],
        ["Total Invoices (period)", str(total_invoices)],
        ["Pending Approval", str(pending_approval)],
        ["Open Exceptions", str(open_exceptions)],
        ["Match Rate", f"{match_rate}%"],
    ]
    elements.append(_build_table(kpi_data, col_widths=[3.5 * inch, 3 * inch]))
    elements.append(Spacer(1, 16))

    # ------------------------------------------------------------------
    # Invoice Processing Funnel
    # ------------------------------------------------------------------
    elements.append(Paragraph("Invoice Processing Funnel", section_style))
    funnel_data: list = [["Status", "Count", "Amount"]]
    for s in InvoiceStatus:
        cnt = db.query(func.count(Invoice.id)).filter(Invoice.status == s).scalar() or 0
        amt = (
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0))
            .filter(Invoice.status == s)
            .scalar()
        )
        funnel_data.append([s.value, str(cnt), f"${float(amt):,.2f}"])
    elements.append(
        _build_table(funnel_data, col_widths=[2.5 * inch, 2 * inch, 2 * inch])
    )
    elements.append(Spacer(1, 16))

    # ------------------------------------------------------------------
    # Exception Breakdown
    # ------------------------------------------------------------------
    elements.append(Paragraph("Exception Breakdown", section_style))
    exc_rows = (
        db.query(
            Exception_.exception_type,
            func.count(Exception_.id).label("cnt"),
        )
        .group_by(Exception_.exception_type)
        .all()
    )
    exc_total = sum(r.cnt for r in exc_rows) or 1
    exc_data: list = [["Exception Type", "Count", "Percentage"]]
    for r in exc_rows:
        etype = r.exception_type.value if hasattr(r.exception_type, "value") else str(r.exception_type)
        pct = round(r.cnt / exc_total * 100, 1)
        exc_data.append([etype, str(r.cnt), f"{pct}%"])
    elements.append(
        _build_table(exc_data, col_widths=[2.5 * inch, 2 * inch, 2 * inch])
    )
    elements.append(Spacer(1, 16))

    # ------------------------------------------------------------------
    # Top Vendors
    # ------------------------------------------------------------------
    elements.append(Paragraph("Top Vendors", section_style))
    vendor_rows = (
        db.query(
            Vendor.name,
            func.count(Invoice.id).label("invoice_count"),
            func.coalesce(func.sum(Invoice.total_amount), 0).label("total_amount"),
        )
        .join(Invoice, Invoice.vendor_id == Vendor.id)
        .group_by(Vendor.name)
        .order_by(func.count(Invoice.id).desc())
        .limit(10)
        .all()
    )
    vendor_data: list = [["Vendor Name", "Invoice Count", "Total Amount"]]
    for r in vendor_rows:
        vendor_data.append([r.name, str(r.invoice_count), f"${float(r.total_amount):,.2f}"])
    elements.append(
        _build_table(vendor_data, col_widths=[2.5 * inch, 2 * inch, 2 * inch])
    )
    elements.append(Spacer(1, 24))

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#94a3b8"),
        alignment=1,  # center
    )
    elements.append(
        Paragraph(
            f"Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            footer_style,
        )
    )

    doc.build(elements)
    return buffer.getvalue()
