"""Render the TEN Capital LinkedIn Analysis structure into a branded PDF.

Uses ReportLab Platypus (flowables) so prose-heavy content paginates naturally,
matching the multi-page format of the reference document. Each page carries the
standard TEN Capital footer (single centered line + logo).
"""

import io
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    ListFlowable,
    ListItem,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_FOOTER_LOGO = os.path.abspath(os.path.join(_ASSETS_DIR, "TEN_Capital_logo_footer.png"))

# Brand palette
NAVY = colors.HexColor("#1A1A2E")
DEEP_BLUE = colors.HexColor("#0F3460")
ACCENT = colors.HexColor("#E94560")
BODY = colors.HexColor("#2D2D2D")
GREEN = colors.HexColor("#1B7F4B")
MUTED = colors.HexColor("#6B7280")

PAGE_W, PAGE_H = letter
LEFT_MARGIN = RIGHT_MARGIN = 0.9 * inch
TOP_MARGIN = 0.85 * inch
BOTTOM_MARGIN = 0.85 * inch

# --- Footer font: prefer Open Sans (TEN Capital standard) if a TTF is bundled;
# otherwise fall back to Helvetica so the app never crashes on a missing font. ---
FOOTER_FONT = "Helvetica"
_opensans = os.path.join(_ASSETS_DIR, "fonts", "OpenSans-Regular.ttf")
if os.path.exists(_opensans):
    try:
        pdfmetrics.registerFont(TTFont("OpenSans", _opensans))
        FOOTER_FONT = "OpenSans"
    except Exception:  # noqa: BLE001
        FOOTER_FONT = "Helvetica"


def _styles():
    ss = getSampleStyleSheet()
    styles = {}
    styles["Title"] = ParagraphStyle(
        "DocTitle", parent=ss["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=24, textColor=NAVY, alignment=TA_CENTER,
        spaceAfter=18, spaceBefore=6,
    )
    styles["H2"] = ParagraphStyle(
        "H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
        fontSize=14, leading=18, textColor=NAVY, spaceBefore=16, spaceAfter=8,
    )
    styles["H3"] = ParagraphStyle(
        "H3", parent=ss["Heading3"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=DEEP_BLUE, spaceBefore=10, spaceAfter=4,
    )
    styles["H4"] = ParagraphStyle(
        "H4", parent=ss["Heading4"], fontName="Helvetica-Bold",
        fontSize=9.5, leading=12, textColor=BODY, spaceBefore=6, spaceAfter=2,
    )
    styles["Body"] = ParagraphStyle(
        "Body", parent=ss["BodyText"], fontName="Helvetica",
        fontSize=10, leading=14, textColor=BODY, spaceAfter=6, alignment=TA_LEFT,
    )
    styles["ScoreLine"] = ParagraphStyle(
        "ScoreLine", parent=styles["Body"], fontName="Helvetica-Bold",
        fontSize=11, textColor=NAVY, spaceBefore=6, spaceAfter=6,
    )
    styles["Bullet"] = ParagraphStyle(
        "Bullet", parent=styles["Body"], fontSize=10, leading=13, spaceAfter=1,
    )
    styles["Label"] = ParagraphStyle(
        "Label", parent=styles["Body"], fontName="Helvetica-Oblique",
        textColor=MUTED, fontSize=9.5, spaceAfter=1,
    )
    styles["Example"] = ParagraphStyle(
        "Example", parent=styles["Body"], fontName="Helvetica-Oblique",
        textColor=DEEP_BLUE, leftIndent=10, spaceAfter=6,
    )
    return styles


def _esc(text):
    """Escape XML special chars for ReportLab Paragraph markup."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _fmt_score(val):
    if val is None:
        return "—"
    try:
        return f"{float(val):.1f}"
    except (TypeError, ValueError):
        return _esc(val)


def build_analysis_pdf(data, company_logo_path=None):
    """Build the PDF and return raw bytes."""
    styles = _styles()
    buf = io.BytesIO()

    footer_title = f"{data.get('company_name', 'Company')} – LinkedIn page Analysis"
    footer_meta = (
        f"Compiled on {data.get('analysis_date', '')} by "
        f"{data.get('compiled_by', 'TEN Capital Network')}"
    )

    def _draw_footer(canvas, doc):
        canvas.saveState()
        y = 0.45 * inch
        page_str = str(doc.page)
        # Assemble a single centered line: title    page#    meta   [logo]
        gap = "        "
        line = f"{footer_title}{gap}{page_str}{gap}{footer_meta}"
        canvas.setFont(FOOTER_FONT, 7)
        canvas.setFillColor(MUTED)
        text_w = canvas.stringWidth(line, FOOTER_FONT, 7)
        logo_w, logo_h = 0.55 * inch, 0.205 * inch
        total_w = text_w + 6 + logo_w
        start_x = (PAGE_W - total_w) / 2.0
        canvas.drawString(start_x, y, line)
        if os.path.exists(_FOOTER_LOGO):
            try:
                canvas.drawImage(
                    _FOOTER_LOGO, start_x + text_w + 6, y - 0.055 * inch,
                    width=logo_w, height=logo_h,
                    preserveAspectRatio=True, mask="auto",
                )
            except Exception:  # noqa: BLE001 - footer must never crash the render
                pass
        canvas.restoreState()

    doc = BaseDocTemplate(
        buf, pagesize=letter,
        leftMargin=LEFT_MARGIN, rightMargin=RIGHT_MARGIN,
        topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN,
        title=f"{data.get('company_name', 'Company')} - LinkedIn Analysis",
        author="TEN Capital Network",
    )
    frame = Frame(
        LEFT_MARGIN, BOTTOM_MARGIN,
        PAGE_W - LEFT_MARGIN - RIGHT_MARGIN,
        PAGE_H - TOP_MARGIN - BOTTOM_MARGIN,
        id="main",
    )
    doc.addPageTemplates([
        PageTemplate(id="all", frames=[frame], onPage=_draw_footer)
    ])

    story = []
    _add_cover(story, styles, data, company_logo_path)
    _add_executive_summary(story, styles, data)
    _add_strengths(story, styles, data)
    _add_weaknesses(story, styles, data)
    _add_recommendations(story, styles, data)
    _add_final_assessment(story, styles, data)

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _add_cover(story, styles, data, company_logo_path):
    if company_logo_path and os.path.exists(company_logo_path):
        try:
            img = Image(company_logo_path)
            max_w, max_h = 2.6 * inch, 1.1 * inch
            iw, ih = img.drawWidth, img.drawHeight
            scale = min(max_w / iw, max_h / ih, 1.0)
            img.drawWidth, img.drawHeight = iw * scale, ih * scale
            img.hAlign = "CENTER"
            story.append(Spacer(1, 6))
            story.append(img)
            story.append(Spacer(1, 10))
        except Exception:  # noqa: BLE001
            pass
    title = f"{_esc(data.get('company_name', 'Company'))} – LinkedIn Analysis"
    story.append(Paragraph(title, styles["Title"]))


def _add_executive_summary(story, styles, data):
    story.append(Paragraph("Executive Summary", styles["H2"]))
    es = data.get("executive_summary", {})
    for key in ("positioning_paragraph", "investor_readiness_paragraph"):
        txt = es.get(key, "")
        if txt:
            story.append(Paragraph(_esc(txt), styles["Body"]))

    ias = data.get("investor_appeal_score", {})
    overall = _fmt_score(ias.get("overall_score"))
    scale = ias.get("scale_max", 10)
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(f"Investor Appeal Score: {overall} / {scale}", styles["ScoreLine"])
    )
    story.append(_scoring_table(styles, ias))
    story.append(Spacer(1, 6))


def _scoring_table(styles, ias):
    header = [
        Paragraph("<b>Category</b>", styles["Body"]),
        Paragraph("<b>Score</b>", styles["Body"]),
    ]
    rows = [header]
    for c in ias.get("categories", []):
        rows.append([
            Paragraph(_esc(c.get("category", "")), styles["Body"]),
            Paragraph(_fmt_score(c.get("score")), styles["Body"]),
        ])
    rows.append([
        Paragraph("<b>Overall Investor Appeal</b>", styles["Body"]),
        Paragraph(f"<b>{_fmt_score(ias.get('overall_score'))}</b>", styles["Body"]),
    ])
    tbl = Table(rows, colWidths=[3.4 * inch, 1.1 * inch], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C0CC")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F7EAED")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _add_strengths(story, styles, data):
    s = data.get("strengths", {})
    story.append(Paragraph(f"1. {_esc(s.get('section_title', 'Strengths'))}", styles["H2"]))
    for item in s.get("items", []):
        if item.get("heading"):
            story.append(Paragraph(_esc(item["heading"]), styles["H3"]))
        if item.get("narrative"):
            story.append(Paragraph(_esc(item["narrative"]), styles["Body"]))
        _add_bullets(story, styles, item.get("signals", []))


def _add_weaknesses(story, styles, data):
    w = data.get("weaknesses", {})
    story.append(
        Paragraph(f"2. {_esc(w.get('section_title', 'Weaknesses or Gaps'))}", styles["H2"])
    )
    for item in w.get("items", []):
        if item.get("heading"):
            story.append(Paragraph(_esc(item["heading"]), styles["H3"]))
        if item.get("narrative"):
            story.append(Paragraph(_esc(item["narrative"]), styles["Body"]))
        _add_bullets(story, styles, item.get("points", []))

    checklist = w.get("traction_visibility_checklist", {})
    rows_data = checklist.get("rows", [])
    if rows_data:
        story.append(Paragraph(_esc(checklist.get("table_title", "Traction Visibility")), styles["H3"]))
        story.append(_visibility_table(styles, checklist))


def _visibility_table(styles, checklist):
    cols = checklist.get("columns", ["Investor Question", "Visible?"])
    rows = [[
        Paragraph(f"<b>{_esc(cols[0])}</b>", styles["Body"]),
        Paragraph(f"<b>{_esc(cols[1]) if len(cols) > 1 else 'Visible?'}</b>", styles["Body"]),
    ]]
    for r in checklist.get("rows", []):
        visible = r.get("visible", False)
        mark = "Yes" if visible else "No"
        color_hex = "#1B7F4B" if visible else "#E94560"
        cell = Paragraph(
            f'<font color="{color_hex}"><b>{mark}</b></font>', styles["Body"]
        )
        rows.append([Paragraph(_esc(r.get("investor_question", "")), styles["Body"]), cell])
    tbl = Table(rows, colWidths=[3.8 * inch, 1.1 * inch], hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C0CC")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _add_recommendations(story, styles, data):
    rec = data.get("recommendations", {})
    story.append(
        Paragraph(f"3. {_esc(rec.get('section_title', 'Specific Recommendations'))}", styles["H2"])
    )
    for item in rec.get("items", []):
        rid = item.get("id", "")
        title = item.get("title", "")
        heading = f"{_esc(rid)}. {_esc(title)}" if rid else _esc(title)
        story.append(Paragraph(heading, styles["H3"]))

        if item.get("intro"):
            story.append(Paragraph(_esc(item["intro"]), styles["Body"]))

        if item.get("current"):
            story.append(Paragraph("Current", styles["H4"]))
            story.append(Paragraph(_esc(item["current"]), styles["Body"]))
        if item.get("recommended"):
            story.append(Paragraph("Recommended", styles["H4"]))
            story.append(Paragraph(_esc(item["recommended"]), styles["Body"]))
        _add_bullets(story, styles, item.get("communicates", []),
                     lead="This version communicates:")

        for group in item.get("bullet_groups", []):
            if group.get("subheading"):
                story.append(Paragraph(_esc(group["subheading"]), styles["H4"]))
            _add_bullets(story, styles, group.get("bullets", []))

        _add_bullets(story, styles, item.get("bullets", []))

        for ex in item.get("before_after_examples", []):
            if ex.get("context"):
                story.append(Paragraph(_esc(ex["context"]), styles["H4"]))
            if ex.get("instead_of"):
                story.append(Paragraph("Instead of:", styles["Label"]))
                story.append(Paragraph(_esc(ex["instead_of"]), styles["Example"]))
            if ex.get("use"):
                story.append(Paragraph("Use:", styles["Label"]))
                story.append(Paragraph(_esc(ex["use"]), styles["Example"]))

        table = item.get("table", {})
        if table.get("rows"):
            story.append(_generic_table(styles, table))

        if item.get("example_line"):
            story.append(Paragraph(_esc(item["example_line"]), styles["Example"]))


def _generic_table(styles, table):
    cols = table.get("columns", [])
    data_rows = table.get("rows", [])
    ncols = len(cols) if cols else (len(data_rows[0]) if data_rows else 2)
    rows = []
    if cols:
        rows.append([Paragraph(f"<b>{_esc(c)}</b>", styles["Body"]) for c in cols])
    for r in data_rows:
        cells = [Paragraph(_esc(c), styles["Body"]) for c in r]
        # pad/truncate to ncols
        cells = (cells + [Paragraph("", styles["Body"])] * ncols)[:ncols]
        rows.append(cells)
    avail = PAGE_W - LEFT_MARGIN - RIGHT_MARGIN
    col_w = min(2.4 * inch, avail / ncols)
    tbl = Table(rows, colWidths=[col_w] * ncols, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C0CC")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2F7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _add_final_assessment(story, styles, data):
    fa = data.get("final_assessment", {})
    story.append(Paragraph(_esc(fa.get("section_title", "Final Assessment")), styles["H2"]))
    for key in ("foundational_strengths_paragraph", "primary_weakness_paragraph"):
        txt = fa.get(key, "")
        if txt:
            story.append(Paragraph(_esc(txt), styles["Body"]))


def _add_bullets(story, styles, items, lead=None):
    items = [i for i in (items or []) if str(i).strip()]
    if not items:
        return
    if lead:
        story.append(Paragraph(lead, styles["Body"]))
    flow = ListFlowable(
        [ListItem(Paragraph(_esc(i), styles["Bullet"]), leftIndent=12) for i in items],
        bulletType="bullet", start="•", bulletColor=ACCENT,
        leftIndent=14, bulletFontSize=8,
    )
    story.append(flow)
    story.append(Spacer(1, 4))
