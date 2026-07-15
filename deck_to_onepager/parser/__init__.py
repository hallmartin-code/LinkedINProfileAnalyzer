"""Deck parsers: detect input type and extract structured slide data."""

import os

from .pdf_parser import parse_pdf
from .pptx_parser import parse_pptx


def parse_deck(path):
    """Auto-detect file type from extension and dispatch to the right parser.

    Returns a list of slide dicts. Raises ValueError for unsupported formats
    and FileNotFoundError if the file is missing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return parse_pdf(path)
    if ext in (".pptx", ".ppt"):
        # python-pptx cannot read the legacy binary .ppt format, but we accept
        # the extension and let the parser raise a clear error if it fails.
        return parse_pptx(path)

    raise ValueError(
        f"Unsupported file format '{ext}'. Supported formats: .pdf, .pptx"
    )


__all__ = ["parse_deck", "parse_pdf", "parse_pptx"]
