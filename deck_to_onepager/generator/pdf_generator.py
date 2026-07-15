"""Render the branded one-pager PDF from structured deck data using ReportLab."""

import os
import re

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from templates.onepager_layout import (
    BODY_SIZE,
    COLOR_ACCENT,
    COLOR_BODY_TEXT,
    COLOR_HEADER_BG,
    COLOR_PLACEHOLDER,
    COLOR_SECTION_HEADER,
    COLOR_WHITE,
    COMPANY_NAME_SIZE,
    FONT_BOLD,
    FONT_REGULAR,
    MARGIN,
    PAGE_SIZE,
    SECTION_HEADER_SIZE,
    STAGE_BADGE_SIZE,
    TAGLINE_SIZE,
)

PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE
CONTENT_LEFT = MARGIN
CONTENT_RIGHT = PAGE_WIDTH - MARGIN
CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT

PLACEHOLDER_TEXT = "Not disclosed"


def generate_onepager(data, output_dir="output", logo_path=None):
    """Generate the one-pager PDF and return the output file path.

    `data` is the structured dict produced by the extractor. `logo_path` is an
    optional path to a logo image; if missing, the header renders without it.
    """
    os.makedirs(output_dir, exist_ok=True)

    company = _clean(data.get("company_name")) or "Company"
    filename = _safe_filename(company) + "_onepager.pdf"
    out_path = os.path.join(output_dir, filename)

    try:
        c = canvas.Canvas(out_path, pagesize=PAGE_SIZE)
        _draw_page(c, data, logo_path)
        c.showPage()
        c.save()
    except Exception as exc:  # noqa: BLE001 - report cleanly to the CLI
        raise RuntimeError(f"Failed to generate PDF at '{out_path}': {exc}") from exc

    return out_path


# ---------------------------------------------------------------------------
# Page drawing
# ---------------------------------------------------------------------------

def _draw_page(c, data, logo_path):
    """Draw the full one-pager top-to-bottom.

    We lay the page out from the top down, tracking a running `y` cursor. Section
    heights are fixed so the whole thing fits on one letter page; body text is
    wrapped and truncated to the space available in each section.
    """
    y = PAGE_HEIGHT

    # --- Header bar ---
    y = _draw_header(c, data, logo_path, y)

    gap = 10
    y -= gap

    # --- Problem / Solution (two columns) ---
    y = _draw_two_col(
        c, y,
        left_title="The Problem", left_body=_clean(data.get("problem")),
        right_title="The Solution", right_body=_clean(data.get("solution")),
        height=118,
    )
    y -= gap

    # --- Market Opportunity (full width, single row of TAM/SAM/SOM) ---
    y = _draw_market(c, data, y)
    y -= gap

    # --- Traction / Business Model / Competitive Edge (three columns) ---
    y = _draw_three_col(c, data, y)
    y -= gap

    # --- Team (full width) ---
    y = _draw_team(c, data, y)
    y -= gap

    # --- The Ask / Contact (two columns) ---
    _draw_ask_and_contact(c, data, y)


def _draw_header(c, data, logo_path, y):
    """Dark navy header bar with logo, company name, stage badge, tagline."""
    header_h = 74
    top = y
    bottom = y - header_h

    c.setFillColor(COLOR_HEADER_BG)
    c.rect(0, bottom, PAGE_WIDTH, header_h, stroke=0, fill=1)

    text_left = CONTENT_LEFT

    # Optional logo on the left
    if logo_path and os.path.exists(logo_path):
        try:
            from reportlab.lib.utils import ImageReader

            img = ImageReader(logo_path)
            logo_size = 46
            c.drawImage(
                img,
                CONTENT_LEFT,
                bottom + (header_h - logo_size) / 2,
                width=logo_size,
                height=logo_size,
                preserveAspectRatio=True,
                mask="auto",
            )
            text_left = CONTENT_LEFT + logo_size + 12
        except Exception:  # noqa: BLE001 - a bad logo shouldn't break the header
            text_left = CONTENT_LEFT

    # Stage badge on the right (accent pill)
    stage = _clean((data.get("funding_ask") or {}).get("stage"))
    name_right_limit = CONTENT_RIGHT
    if stage and stage != PLACEHOLDER_TEXT:
        badge = stage.upper()
        pad = 6
        badge_w = stringWidth(badge, FONT_BOLD, STAGE_BADGE_SIZE) + pad * 2
        badge_h = 16
        badge_x = CONTENT_RIGHT - badge_w
        badge_y = top - 12 - badge_h
        c.setFillColor(COLOR_ACCENT)
        c.roundRect(badge_x, badge_y, badge_w, badge_h, 3, stroke=0, fill=1)
        c.setFillColor(COLOR_WHITE)
        c.setFont(FONT_BOLD, STAGE_BADGE_SIZE)
        c.drawString(badge_x + pad, badge_y + 5, badge)
        name_right_limit = badge_x - 10

    # Company name
    name = _clean(data.get("company_name")) or "Company"
    name = _truncate_to_width(
        name, FONT_BOLD, COMPANY_NAME_SIZE, name_right_limit - text_left
    )
    c.setFillColor(COLOR_WHITE)
    c.setFont(FONT_BOLD, COMPANY_NAME_SIZE)
    c.drawString(text_left, top - 30, name)

    # Tagline / one-line pitch
    tagline = _clean(data.get("tagline"))
    if not tagline or tagline == PLACEHOLDER_TEXT:
        tagline = _clean(data.get("one_line_pitch"))
    if tagline and tagline != PLACEHOLDER_TEXT:
        tagline = _truncate_to_width(
            tagline, FONT_REGULAR, TAGLINE_SIZE, CONTENT_RIGHT - text_left
        )
        c.setFillColor(COLOR_WHITE)
        c.setFont(FONT_REGULAR, TAGLINE_SIZE)
        c.drawString(text_left, top - 48, tagline)

    return bottom


def _draw_two_col(c, y, left_title, left_body, right_title, right_body, height):
    """Two equal columns side by side, each a titled text box."""
    col_gap = 14
    col_w = (CONTENT_WIDTH - col_gap) / 2
    top = y

    _draw_section_box(
        c, CONTENT_LEFT, top, col_w, height, left_title, left_body
    )
    _draw_section_box(
        c, CONTENT_LEFT + col_w + col_gap, top, col_w, height,
        right_title, right_body,
    )
    return top - height


def _draw_market(c, data, y):
    """Full-width Market Opportunity section with TAM / SAM / SOM."""
    height = 52
    top = y
    _draw_section_header(c, CONTENT_LEFT, top, CONTENT_WIDTH, "Market Opportunity")

    market = data.get("market_size") or {}
    tam = _clean(market.get("tam"))
    sam = _clean(market.get("sam"))
    som = _clean(market.get("som"))

    body_top = top - 16
    third = CONTENT_WIDTH / 3
    labels = [("TAM", tam), ("SAM", sam), ("SOM", som)]
    for i, (label, value) in enumerate(labels):
        x = CONTENT_LEFT + i * third
        has_data = value and value != PLACEHOLDER_TEXT
        # Label in accent color
        c.setFillColor(COLOR_ACCENT)
        c.setFont(FONT_BOLD, BODY_SIZE + 1)
        c.drawString(x, body_top - 12, label)
        # Value
        val_text = value if has_data else PLACEHOLDER_TEXT
        c.setFillColor(COLOR_BODY_TEXT if has_data else COLOR_PLACEHOLDER)
        c.setFont(FONT_REGULAR if has_data else FONT_REGULAR, BODY_SIZE + 1)
        val_text = _truncate_to_width(
            val_text, FONT_REGULAR, BODY_SIZE + 1, third - 30
        )
        c.drawString(x + 28, body_top - 12, val_text)

    _draw_divider(c, top - height + 4)
    return top - height


def _draw_three_col(c, data, y):
    """Traction | Business Model | Competitive Edge."""
    height = 96
    top = y
    col_gap = 12
    col_w = (CONTENT_WIDTH - 2 * col_gap) / 3

    # Traction: assemble metrics, customers, growth into lines
    traction = data.get("traction") or {}
    t_lines = []
    for m in traction.get("key_metrics") or []:
        t_lines.append(f"- {m}")
    growth = _clean(traction.get("growth_rate"))
    if growth and growth != PLACEHOLDER_TEXT:
        t_lines.append(f"- Growth: {growth}")
    customers = traction.get("notable_customers") or []
    if customers:
        t_lines.append("- Customers: " + ", ".join(str(x) for x in customers))
    traction_body = "\n".join(t_lines)

    x0 = CONTENT_LEFT
    _draw_section_box(c, x0, top, col_w, height, "Traction", traction_body)
    _draw_section_box(
        c, x0 + col_w + col_gap, top, col_w, height,
        "Business Model", _clean(data.get("business_model")),
    )
    _draw_section_box(
        c, x0 + 2 * (col_w + col_gap), top, col_w, height,
        "Competitive Edge", _clean(data.get("competitive_advantage")),
    )
    return top - height


def _draw_team(c, data, y):
    """Full-width team section: 'Name · Title · Background' per member."""
    height = 74
    top = y
    _draw_section_header(c, CONTENT_LEFT, top, CONTENT_WIDTH, "Team")

    team = data.get("team") or []
    body_top = top - 16
    line_h = 11
    max_lines = int((height - 20) / line_h)

    if not team:
        c.setFillColor(COLOR_PLACEHOLDER)
        c.setFont(FONT_REGULAR, BODY_SIZE)
        c.drawString(CONTENT_LEFT, body_top - 8, PLACEHOLDER_TEXT)
    else:
        line_y = body_top - 8
        for member in team[:max_lines]:
            name = _clean(member.get("name"))
            title = _clean(member.get("title"))
            background = _clean(member.get("background"))
            parts = [p for p in (name, title, background) if p and p != PLACEHOLDER_TEXT]
            line = "  ·  ".join(parts) if parts else PLACEHOLDER_TEXT
            line = _truncate_to_width(line, FONT_REGULAR, BODY_SIZE, CONTENT_WIDTH)
            # Bold the name segment by drawing it separately.
            c.setFillColor(COLOR_BODY_TEXT)
            if name and name != PLACEHOLDER_TEXT:
                c.setFont(FONT_BOLD, BODY_SIZE)
                c.drawString(CONTENT_LEFT, line_y, name)
                offset = stringWidth(name, FONT_BOLD, BODY_SIZE)
                rest = line[len(name):]
                c.setFont(FONT_REGULAR, BODY_SIZE)
                c.drawString(CONTENT_LEFT + offset, line_y, rest)
            else:
                c.setFont(FONT_REGULAR, BODY_SIZE)
                c.drawString(CONTENT_LEFT, line_y, line)
            line_y -= line_h

    _draw_divider(c, top - height + 4)
    return top - height


def _draw_ask_and_contact(c, data, y):
    """The Ask | Contact, two columns at the bottom."""
    height = 96
    top = y
    col_gap = 14
    col_w = (CONTENT_WIDTH - col_gap) / 2

    ask = data.get("funding_ask") or {}
    amount = _clean(ask.get("amount"))
    use = ask.get("use_of_funds") or []
    ask_lines = []
    if amount and amount != PLACEHOLDER_TEXT:
        ask_lines.append(f"Raising: {amount}")
    if use:
        ask_lines.append("Use of funds:")
        for u in use:
            ask_lines.append(f"- {u}")
    ask_body = "\n".join(ask_lines)

    contact = data.get("contact") or {}
    c_lines = []
    for label, key in (("Email", "email"), ("Web", "website"), ("LinkedIn", "linkedin")):
        val = _clean(contact.get(key))
        if val and val != PLACEHOLDER_TEXT:
            c_lines.append(f"{label}: {val}")
    contact_body = "\n".join(c_lines)

    _draw_section_box(c, CONTENT_LEFT, top, col_w, height, "The Ask", ask_body)
    _draw_section_box(
        c, CONTENT_LEFT + col_w + col_gap, top, col_w, height,
        "Contact", contact_body,
    )


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def _draw_section_box(c, x, top, width, height, title, body):
    """A titled section: header label, then wrapped/truncated body text.

    Renders a greyed-out placeholder when `body` is empty or 'Not disclosed'.
    """
    _draw_section_header(c, x, top, width, title)

    body = (body or "").strip()
    body_top = top - 16
    line_h = 9.5
    max_lines = max(1, int((height - 18) / line_h))

    if not body or body == PLACEHOLDER_TEXT:
        c.setFillColor(COLOR_PLACEHOLDER)
        c.setFont(FONT_REGULAR, BODY_SIZE)
        c.drawString(x, body_top - 7, PLACEHOLDER_TEXT)
        return

    lines = _wrap_text(body, FONT_REGULAR, BODY_SIZE, width)
    lines = _clip_lines(lines, max_lines)

    c.setFillColor(COLOR_BODY_TEXT)
    c.setFont(FONT_REGULAR, BODY_SIZE)
    line_y = body_top - 7
    for line in lines:
        c.drawString(x, line_y, line)
        line_y -= line_h


def _draw_section_header(c, x, top, width, title):
    """Uppercase deep-blue section header with a short accent underline."""
    c.setFillColor(COLOR_SECTION_HEADER)
    c.setFont(FONT_BOLD, SECTION_HEADER_SIZE)
    c.drawString(x, top - 9, title.upper())
    # Short accent underline beneath the header
    c.setStrokeColor(COLOR_ACCENT)
    c.setLineWidth(1.2)
    c.line(x, top - 13, x + min(28, width), top - 13)


def _draw_divider(c, y):
    """Full-width thin accent divider line."""
    c.setStrokeColor(COLOR_ACCENT)
    c.setLineWidth(0.5)
    c.line(CONTENT_LEFT, y, CONTENT_RIGHT, y)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _wrap_text(text, font, size, max_width):
    """Word-wrap text (honoring explicit newlines) to fit `max_width` points."""
    out_lines = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        words = paragraph.split()
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if stringWidth(trial, font, size) <= max_width:
                current = trial
            else:
                if current:
                    out_lines.append(current)
                # A single word longer than the line: hard-break it.
                if stringWidth(word, font, size) > max_width:
                    out_lines.extend(_hard_break(word, font, size, max_width))
                    current = ""
                else:
                    current = word
        if current:
            out_lines.append(current)
    return out_lines


def _hard_break(word, font, size, max_width):
    """Break a too-long word character by character."""
    pieces = []
    current = ""
    for ch in word:
        if stringWidth(current + ch, font, size) <= max_width:
            current += ch
        else:
            if current:
                pieces.append(current)
            current = ch
    if current:
        pieces.append(current)
    return pieces


def _clip_lines(lines, max_lines):
    """Truncate a list of lines to `max_lines`, adding an ellipsis if clipped."""
    if len(lines) <= max_lines:
        return lines
    kept = lines[:max_lines]
    last = kept[-1]
    if not last.endswith("..."):
        kept[-1] = (last[:-3] + "...") if len(last) > 3 else last + "..."
    return kept


def _truncate_to_width(text, font, size, max_width):
    """Single-line truncation with a trailing ellipsis to fit `max_width`."""
    if stringWidth(text, font, size) <= max_width:
        return text
    ellipsis = "..."
    while text and stringWidth(text + ellipsis, font, size) > max_width:
        text = text[:-1]
    return (text + ellipsis) if text else ellipsis


def _clean(value):
    """Normalize a field to a trimmed string (empty string if None)."""
    if value is None:
        return ""
    return str(value).strip()


def _safe_filename(name):
    """Turn a company name into a filesystem-safe filename stem."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return stem or "company"
