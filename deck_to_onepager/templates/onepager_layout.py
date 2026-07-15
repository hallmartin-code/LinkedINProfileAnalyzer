"""Layout constants, fonts, colors, and section order for the one-pager."""

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter

# --- Colors (from the spec) ---
COLOR_HEADER_BG = HexColor("#1A1A2E")       # dark navy header background
COLOR_SECTION_HEADER = HexColor("#0F3460")  # deep blue section headers
COLOR_BODY_TEXT = HexColor("#2D2D2D")       # near-black body text
COLOR_ACCENT = HexColor("#E94560")          # red accent / divider lines
COLOR_WHITE = HexColor("#FFFFFF")
COLOR_PLACEHOLDER = HexColor("#B0B0B0")     # greyed-out "no data" placeholder

# --- Fonts (ReportLab built-ins, no external files needed) ---
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# --- Sizes (points) ---
SECTION_HEADER_SIZE = 8
BODY_SIZE = 8
COMPANY_NAME_SIZE = 20
TAGLINE_SIZE = 10
STAGE_BADGE_SIZE = 8

# --- Page geometry ---
PAGE_SIZE = letter          # (612, 792) points = 8.5" x 11"
MARGIN = 36                 # 0.5 inch margins
