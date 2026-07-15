"""Extract text and embedded images from a PDF pitch deck using pypdf + Pillow."""

import io
import os
import tempfile

from pypdf import PdfReader

# Images are written to the system temp dir so the AI/vision layer can read them
# later if needed. We namespace them under a dedicated subfolder for easy cleanup.
_IMAGE_TMP_DIR = os.path.join(tempfile.gettempdir(), "deck_to_onepager_images")


def parse_pdf(path):
    """Parse a PDF deck.

    Returns a list of dicts, one per page:
        [{"slide": 1, "text": "...", "images": [".../img.png", ...]}]

    Image extraction failures are swallowed per-page so a malformed image never
    blocks text extraction (which is what the AI layer actually needs).
    """
    try:
        reader = PdfReader(path)
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the CLI
        raise RuntimeError(f"Failed to open PDF '{path}': {exc}") from exc

    os.makedirs(_IMAGE_TMP_DIR, exist_ok=True)

    slides = []
    for page_index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001 - a bad page shouldn't kill the run
            text = ""

        images = _extract_page_images(page, page_index)

        slides.append(
            {
                "slide": page_index,
                "text": text.strip(),
                "images": images,
            }
        )

    return slides


def _extract_page_images(page, page_index):
    """Extract embedded raster images from a single PDF page.

    Uses pypdf's built-in image iterator. Pillow is used indirectly by pypdf to
    decode images; we re-save through Pillow to normalize to PNG when possible.
    """
    saved = []
    try:
        page_images = list(getattr(page, "images", []) or [])
    except Exception:  # noqa: BLE001
        return saved

    for img_index, image_file in enumerate(page_images, start=1):
        try:
            out_path = os.path.join(
                _IMAGE_TMP_DIR, f"page{page_index}_img{img_index}.png"
            )
            _save_image_as_png(image_file.data, out_path)
            saved.append(out_path)
        except Exception:  # noqa: BLE001 - skip any image we can't decode/save
            continue

    return saved


def _save_image_as_png(raw_bytes, out_path):
    """Normalize arbitrary image bytes to a PNG on disk via Pillow."""
    from PIL import Image  # imported lazily so text-only runs don't need PIL

    with Image.open(io.BytesIO(raw_bytes)) as im:
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        im.save(out_path, format="PNG")
