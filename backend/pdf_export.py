"""PDF export for coding results using reportlab.

Renders a de-identified, audit-safe PDF summary of a coding session.
No PHI is included (results contain only codes + guideline refs).
"""
from __future__ import annotations
import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


NAVY = colors.HexColor("#003F87")
BLUE = colors.HexColor("#0073CF")
MIST = colors.HexColor("#F4F8FC")
BORDER = colors.HexColor("#E2E8F0")
INK = colors.HexColor("#0F172A")
SLATE = colors.HexColor("#64748B")


def _styles():
    s = getSampleStyleSheet()
    base = s["BodyText"]
    base.fontName = "Helvetica"
    base.fontSize = 9
    base.textColor = INK
    return {
        "title": ParagraphStyle("t", parent=s["Title"], fontName="Helvetica-Bold", fontSize=20, textColor=NAVY, leading=24, spaceAfter=4),
        "sub": ParagraphStyle("s", parent=base, fontSize=9, textColor=SLATE, leading=12, spaceAfter=12),
        "h2": ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=12, textColor=NAVY, leading=16, spaceBefore=14, spaceAfter=6),
        "small": ParagraphStyle("sm", parent=base, fontSize=8, textColor=SLATE, leading=10),
        "body": base,
        "mono": ParagraphStyle("mono", parent=base, fontName="Courier", fontSize=8, textColor=INK, leading=10),
        "badge_ok": ParagraphStyle("ok", parent=base, fontSize=8, textColor=colors.HexColor("#059669")),
        "badge_warn": ParagraphStyle("wn", parent=base, fontSize=8, textColor=colors.HexColor("#D97706")),
    }


def _table(code_rows: list[dict], st: dict) -> Table | None:
    if not code_rows:
        return None
    data: list[list[Any]] = [["Code", "Type", "Description", "Guideline Ref.", "Status"]]
    for c in code_rows:
        status = "Verified" if c.get("status") == "verified" else "Review"
        data.append([
            Paragraph(f"<font face='Courier'><b>{c.get('code','')}</b></font>", st["body"]),
            Paragraph(c.get("code_type", ""), st["small"]),
            Paragraph(c.get("description", ""), st["body"]),
            Paragraph(c.get("guideline_ref", ""), st["small"]),
            Paragraph(status, st["badge_ok"] if status == "Verified" else st["badge_warn"]),
        ])
    t = Table(data, colWidths=[0.9 * inch, 0.8 * inch, 2.8 * inch, 2.0 * inch, 0.7 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), MIST),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def build_pdf(session: dict) -> bytes:
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"CHC Pro AI — Session {session['id'][:8]}",
    )
    story: list[Any] = []

    story.append(Paragraph("CHC Pro AI · Coding Results", st["title"]))
    meta = f"Session <font face='Courier'>{session['id'][:8]}</font> · {session.get('claim_type','')} · {session.get('payer','')}"
    if session.get("state"):
        meta += f" ({session['state']})"
    meta += f" · Specialty: {', '.join(session.get('specialty') or []) or '—'}"
    meta += f" · Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
    story.append(Paragraph(meta, st["sub"]))

    phi = session.get("phi_report") or {}
    total = sum((phi.get("redactions") or {}).values())
    cats = " · ".join(phi.get("categories_found") or []) or "none detected"
    story.append(Paragraph(
        f"<b>PHI minimization:</b> {total} identifier(s) redacted across categories — {cats}. "
        f"OCR pages: {session.get('ocr_pages', '—')}.",
        st["small"],
    ))

    r = session.get("coding_result") or {}
    codes_all: dict[str, list[dict]] = {
        "Principal diagnosis (ICD-10-CM)": [r["principal_diagnosis"]] if r.get("principal_diagnosis") else [],
        "Secondary diagnoses": r.get("secondary_diagnoses") or [],
        "Principal procedure": [r["principal_procedure"]] if r.get("principal_procedure") else [],
        "Additional procedures": r.get("additional_procedures") or [],
        "MS-DRG assignment": [r["ms_drg"]] if r.get("ms_drg") else [],
        "Revenue codes (UB-04)": r.get("revenue_codes") or [],
        "Condition codes (UB-04)": r.get("condition_codes") or [],
        "Occurrence codes (UB-04)": r.get("occurrence_codes") or [],
        "Value codes (UB-04)": r.get("value_codes") or [],
        "Modifiers": r.get("modifiers") or [],
    }

    for section, rows in codes_all.items():
        tbl = _table(rows, st)
        if tbl is None:
            continue
        story.append(Paragraph(section, st["h2"]))
        story.append(tbl)

    # Edits
    story.append(PageBreak())
    story.append(Paragraph("Edit checks", st["h2"]))
    for block_name, items in (("MUE edits", r.get("mue_checks") or []), ("NCCI edits", r.get("ncci_checks") or [])):
        story.append(Paragraph(f"<b>{block_name}</b>", st["body"]))
        for m in items:
            story.append(Paragraph(f"• {m}", st["mono"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Processing log", st["h2"]))
    for line in r.get("processing_log") or []:
        story.append(Paragraph(f"• {line}", st["mono"]))

    # Footer note
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "This report is generated from de-identified records. No Protected Health Information is contained herein. "
        "Generated by CHC Pro AI — in-process OCR, PHI redaction and rule-based coding. No external AI services used.",
        st["small"],
    ))

    doc.build(story)
    return buf.getvalue()
