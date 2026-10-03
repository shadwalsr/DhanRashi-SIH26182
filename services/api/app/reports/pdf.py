"""PDF Generator using ReportLab with all required sections, epistemic labels, and SHA-256 checksum (FR-RPT-01..03)."""

import hashlib
import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_investigation_pdf(report_data: dict[str, Any]) -> tuple[bytes, str]:
    """Generates an investigator-grade PDF report from structured investigation data.
    Returns (pdf_bytes, sha256_hex_hash).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    meta_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#64748b"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#991b1b"),
        fontName="Helvetica-Bold",
    )

    elements: list[Any] = []

    # 1. Header Banner & Title
    elements.append(
        Paragraph("<b>VASP-TRACE LAWFUL DISCLOSURE &amp; ATTRIBUTION REPORT</b>", title_style)
    )
    elements.append(
        Paragraph(
            "SIH-26182 · Automated Cryptocurrency Wallet Attribution Platform",
            meta_style,
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=12))

    # Case Metadata Box
    case_meta = [
        [
            Paragraph("<b>Case Reference:</b>", body_style),
            Paragraph(str(report_data.get("case_reference", "N/A")), body_style),
            Paragraph("<b>Generated At:</b>", body_style),
            Paragraph(f"{report_data.get('created_at', 'N/A')} UTC", body_style),
        ],
        [
            Paragraph("<b>Case Title:</b>", body_style),
            Paragraph(str(report_data.get("case_title", "N/A")), body_style),
            Paragraph("<b>Author / Role:</b>", body_style),
            Paragraph(f"{report_data.get('author_email', 'INV')} ({report_data.get('author_role', 'INV')})", body_style),
        ],
        [
            Paragraph("<b>Target Wallet:</b>", body_style),
            Paragraph(f"<font name='Courier'>{report_data.get('target_wallet', 'N/A')}</font>", body_style),
            Paragraph("<b>Blockchain:</b>", body_style),
            Paragraph(str(report_data.get("blockchain", "N/A")).upper(), body_style),
        ],
    ]
    t_meta = Table(case_meta, colWidths=[1.3 * inch, 2.3 * inch, 1.2 * inch, 2.4 * inch])
    t_meta.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(t_meta)
    elements.append(Spacer(1, 10))

    # 2. Mandatory Disclaimer & Limitations (FR-RPT-03)
    disclaimer_text = (
        "<b>MANDATORY LEGAL &amp; INVESTIGATIVE DISCLAIMER (FR-RPT-03 — CANNOT BE DISABLED):</b><br/>"
        "Attribution scores represent algorithmic correlation over public blockchain transaction graphs "
        "and intelligence registries. They are investigative leads and do NOT constitute conclusive legal proof "
        "of wallet ownership or culpability. Scores below 0.40 must not be used as the sole basis for statutory disclosure requests."
    )
    t_disc = Table([[Paragraph(disclaimer_text, disclaimer_style)]], colWidths=[7.2 * inch])
    t_disc.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f87171")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    elements.append(t_disc)
    elements.append(Spacer(1, 10))

    # 3. Top Candidate VASP & Score Summary
    elements.append(Paragraph("1. Primary Entity Attribution Summary (FR-ATT-01..09)", h2_style))
    top_cand = report_data.get("top_candidate", {})
    score_summary = [
        [
            Paragraph("<b>Attributed VASP Entity:</b>", body_style),
            Paragraph(f"<b>{top_cand.get('vasp_name', 'Unknown VASP')}</b> ({top_cand.get('vasp_id', 'N/A')})", body_style),
            Paragraph("<b>Confidence Tier:</b>", body_style),
            Paragraph(f"<b>{top_cand.get('tier', 'INSUFFICIENT')}</b>", body_style),
        ],
        [
            Paragraph("<b>Raw Score (Mathematical):</b>", body_style),
            Paragraph(f"{top_cand.get('raw_score', 0.0):.4f}", body_style),
            Paragraph("<b>Final Score (Post-Caps):</b>", body_style),
            Paragraph(f"<b>{top_cand.get('final_score', 0.0):.1%}</b>", body_style),
        ],
    ]
    t_score = Table(score_summary, colWidths=[1.6 * inch, 2.0 * inch, 1.6 * inch, 2.0 * inch])
    t_score.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf5ff")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8b4fe")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ede9fe")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(t_score)
    elements.append(Spacer(1, 10))

    # 4. 10-Feature Contribution Decomposition (Table)
    elements.append(Paragraph("2. 10-Feature Attribution Decomposition (FR-ATT-02, G2 Invariant)", h2_style))
    factors = top_cand.get("factors", [])
    factors_data = [
        [
            Paragraph("<b>Feature</b>", meta_style),
            Paragraph("<b>Observed Raw Value</b>", meta_style),
            Paragraph("<b>Normalized</b>", meta_style),
            Paragraph("<b>Weight</b>", meta_style),
            Paragraph("<b>Contribution</b>", meta_style),
            Paragraph("<b>Status</b>", meta_style),
        ]
    ]
    for f in factors:
        factors_data.append([
            Paragraph(f.get("name", "").replace("_", " "), body_style),
            Paragraph(str(f.get("raw_value", "")), body_style),
            Paragraph(f"{f.get('normalized_score', 0.0):.3f}", body_style),
            Paragraph(f"{f.get('weight', 0.0):.1%}", body_style),
            Paragraph(f"<b>+{f.get('contribution', 0.0):.4f}</b>", body_style),
            Paragraph("Active" if f.get("applicable") else "Inactive", meta_style),
        ])
    t_factors = Table(factors_data, colWidths=[1.8 * inch, 1.8 * inch, 0.9 * inch, 0.8 * inch, 1.0 * inch, 0.9 * inch])
    t_factors.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    elements.append(t_factors)
    elements.append(Spacer(1, 10))

    # 5. Independent Transit Laundering Risk Assessment (FR-RISK-01..04)
    elements.append(Paragraph("3. Independent Transit Laundering Risk Assessment (FR-RISK-01..04)", h2_style))
    risk_data = report_data.get("risk_assessment", {})
    signals = risk_data.get("signals", [])
    triggered_signals = [s for s in signals if s.get("triggered")]

    risk_summary = [
        [
            Paragraph("<b>Transit Risk Score:</b>", body_style),
            Paragraph(f"<b>{risk_data.get('risk_score', 0)} / 100</b>", body_style),
            Paragraph("<b>Risk Tier:</b>", body_style),
            Paragraph(f"<b>{risk_data.get('risk_tier', 'LOW')}</b>", body_style),
        ],
        [
            Paragraph("<b>Flagged Laundering Signals:</b>", body_style),
            Paragraph(f"{len(triggered_signals)} signals detected", body_style),
            Paragraph("<b>VASP Node Neutrality:</b>", body_style),
            Paragraph("Zero risk assigned to VASP (FR-RISK-04)", meta_style),
        ],
    ]
    t_risk = Table(risk_summary, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    t_risk.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff1f2")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#fecdd3")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ffe4e6")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(t_risk)
    elements.append(Spacer(1, 10))

    # 6. Immutable Evidence Facts Table (FR-RPT-02: Every row labeled)
    elements.append(Paragraph("4. Immutable Cryptographic Evidence Ledger (FR-RPT-02)", h2_style))
    elements.append(
        Paragraph(
            "Every assertion below is strictly labeled with its epistemic provenance class (FR-RPT-02).",
            meta_style,
        )
    )
    evidence_facts = report_data.get("evidence_facts", [])
    ev_table_data = [
        [
            Paragraph("<b>Seq</b>", meta_style),
            Paragraph("<b>Epistemic Class (FR-RPT-02)</b>", meta_style),
            Paragraph("<b>Fact Type &amp; Description</b>", meta_style),
            Paragraph("<b>Source Proof</b>", meta_style),
            Paragraph("<b>Evidence Hash (SHA-256)</b>", meta_style),
        ]
    ]
    for ef in evidence_facts:
        ev_table_data.append([
            Paragraph(f"#{ef.get('sequence_num', '')}", meta_style),
            Paragraph(f"<b>{ef.get('provenance_class', 'UNKNOWN')}</b>", body_style),
            Paragraph(str(ef.get("description", ef.get("evidence_type", ""))), body_style),
            Paragraph(str(ef.get("source", "ledger")), meta_style),
            Paragraph(f"<font name='Courier'>{str(ef.get('evidence_hash', ''))[:16]}...</font>", meta_style),
        ])
    t_ev = Table(ev_table_data, colWidths=[0.5 * inch, 2.0 * inch, 2.3 * inch, 1.2 * inch, 1.2 * inch])
    t_ev.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    elements.append(t_ev)
    elements.append(Spacer(1, 14))

    # 7. Supervisory Approvals & Signatures (FR-RPT-04)
    elements.append(Paragraph("5. Author Sign-Off & Supervisory Approval (FR-RPT-04)", h2_style))
    sig_data = [
        [
            Paragraph("<b>Investigator (Report Author):</b>", body_style),
            Paragraph(str(report_data.get("author_email", "Lead Investigator")), body_style),
            Paragraph("<b>Date / Status:</b>", body_style),
            Paragraph(f"{report_data.get('created_at', 'N/A')} · GENERATED", body_style),
        ],
        [
            Paragraph("<b>Supervisor (Approver):</b>", body_style),
            Paragraph(str(report_data.get("approved_by_email", "Pending Supervisor Review")), body_style),
            Paragraph("<b>Approval Status:</b>", body_style),
            Paragraph(f"<b>{report_data.get('status', 'PENDING_APPROVAL')}</b>", body_style),
        ],
    ]
    t_sig = Table(sig_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
    t_sig.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    elements.append(t_sig)

    # Build document
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Compute SHA-256 digest
    sha256_hash = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, sha256_hash
