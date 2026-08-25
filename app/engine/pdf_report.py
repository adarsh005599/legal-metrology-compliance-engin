import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.units import inch
from app.models import ComplianceReport, MANDATORY_DISCLAIMER

def generate_pdf_report(report: ComplianceReport) -> bytes:
    """
    Generates a formal, downloadable PDF compliance-assist screening report using ReportLab.
    Strictly follows statutory framing and non-enforcement language requirements.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),  # Navy/Government Blue
        alignment=1, # Center
        spaceAfter=4
    )

    ministry_style = ParagraphStyle(
        'MinistryHeader',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
        spaceAfter=6
    )

    subheader_style = ParagraphStyle(
        'ReportSubheader',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#742A2A"),  # Alert reddish-brown
        alignment=1,
        fontName="Helvetica-Bold",
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=10,
        spaceAfter=6,
        fontName="Helvetica-Bold"
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2D3748")
    )

    disclaimer_box_style = ParagraphStyle(
        'DisclaimerBox',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
        fontName="Helvetica-Oblique"
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2D3748")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1A202C")
    )

    story = []

    # 1. Main Header & Ministry Branding
    story.append(Paragraph("Ministry of Consumer Affairs, Food & Public Distribution", ministry_style))
    story.append(Paragraph("<b>MetraSetu</b>: Legal Metrology Compliance Assistant", title_style))
    story.append(Paragraph("Pre-inspection screening report — not a statutory notice under the Legal Metrology Act, 2009", subheader_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E0"), spaceAfter=10))

    # 2. Metadata Table
    status_color = "#27AE60" if report.overall_status == "COMPLIANT" else ("#2B6CB0" if report.overall_status == "EXEMPT" else ("#D97706" if report.overall_status == "UNCERTAIN" else "#E53E3E"))
    status_display = f"<font color='{status_color}'><b>{report.overall_status}</b></font>"
    
    meta_data = [
        [
            Paragraph("<b>Scan Reference ID:</b>", table_cell_style),
            Paragraph(report.scan_id, table_cell_style),
            Paragraph("<b>Date & Time:</b>", table_cell_style),
            Paragraph(report.timestamp, table_cell_style)
        ],
        [
            Paragraph("<b>Analyzed File:</b>", table_cell_style),
            Paragraph(report.filename or "Uploaded Label Image", table_cell_style),
            Paragraph("<b>Screening Status:</b>", table_cell_style),
            Paragraph(status_display, table_cell_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[120, 140, 110, 150])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#EDF2F7")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Exemption Section (if exempt)
    if report.is_exempt and report.exemption_details:
        story.append(Paragraph("Exemption Screening Result", section_heading))
        ex_data = [
            [
                Paragraph("<b>Exemption Status:</b>", table_cell_style),
                Paragraph("<font color='#2B6CB0'><b>EXEMPT FROM PACKAGED COMMODITY RULES</b></font>", table_cell_style)
            ],
            [
                Paragraph("<b>Exemption Reason:</b>", table_cell_style),
                Paragraph(report.exemption_details.reason or "Package meets statutory exemption criteria.", table_cell_style)
            ],
            [
                Paragraph("<b>Statutory Reference:</b>", table_cell_style),
                Paragraph(report.exemption_details.rule_reference or "Rule 3 & Rule 26, Legal Metrology (Packaged Commodities) Rules, 2011", table_cell_style)
            ]
        ]
        ex_table = Table(ex_data, colWidths=[130, 390])
        ex_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#3182CE")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#BEE3F8")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(ex_table)
        story.append(Spacer(1, 10))
        story.append(Paragraph("<i>Note: As this commodity falls under statutory exemption criteria, standard packaged commodity declaration checks are waived.</i>", body_style))
        story.append(Spacer(1, 12))
    else:
        # 4. Mandatory Declarations Table (Rule 6 checks)
        story.append(Paragraph("Mandatory Declaration Screening Results (Rule 6)", section_heading))
        
        table_rows = [
            [
                Paragraph("Mandatory Field", table_header_style),
                Paragraph("Rule Ref.", table_header_style),
                Paragraph("Status", table_header_style),
                Paragraph("Detected Text / Finding", table_header_style),
                Paragraph("Remarks / Flags", table_header_style)
            ]
        ]

        for field in report.fields:
            if field.status == "PASS":
                status_html = "<font color='#27AE60'><b>PASS</b></font>"
            elif field.status in {"WARNING", "FLAGGED"}:
                status_html = "<font color='#D69E2E'><b>FLAGGED</b></font>"
            elif field.status == "UNCERTAIN":
                status_html = "<font color='#D97706'><b>UNCERTAIN</b></font>"
            else:
                status_html = "<font color='#E53E3E'><b>FAIL</b></font>"

            matched = field.matched_text if field.matched_text else "<i>Not detected</i>"
            remarks = field.flag or field.details

            table_rows.append([
                Paragraph(field.field_name, table_cell_bold),
                Paragraph(field.rule_reference.split(',')[0], table_cell_style),
                Paragraph(status_html, table_cell_style),
                Paragraph(matched, table_cell_style),
                Paragraph(remarks, table_cell_style)
            ])

        rule_table = Table(table_rows, colWidths=[110, 65, 55, 140, 150])
        rule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(rule_table)
        story.append(Spacer(1, 14))

    # 5. Extracted OCR Lines Section (first 10 lines or summary)
    if report.extracted_lines:
        story.append(Paragraph("Extracted Label Text Snippets (OCR Summary)", section_heading))
        ocr_preview = " | ".join([f"[{line.text}]" for line in report.extracted_lines[:15]])
        if len(report.extracted_lines) > 15:
            ocr_preview += f" ... (+{len(report.extracted_lines) - 15} more lines)"
        
        ocr_table = Table([[Paragraph(f"<font color='#4A5568'>{ocr_preview}</font>", table_cell_style)]], colWidths=[520])
        ocr_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(ocr_table)
        story.append(Spacer(1, 14))

    # 6. Statutory Disclaimer Box (Mandatory Framing Requirement)
    disclaimer_html = (
        "<b>STATUTORY DISCLAIMER:</b><br/>"
        f"{report.disclaimer}<br/>"
        "Under Section 15 of the Legal Metrology Act, 2009, only an authorized Legal Metrology Officer (LMO) "
        "is empowered to initiate statutory inspection, seize commodities, or issue enforcement proceedings. "
        "This automated pre-inspection report is generated solely to assist packaging compliance screening."
    )
    
    disclaimer_table = Table([[Paragraph(disclaimer_html, disclaimer_box_style)]], colWidths=[520])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFF5F5")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#FEB2B2")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(KeepTogether([disclaimer_table]))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
