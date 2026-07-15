"""Call the Claude API to turn raw slide text into a structured JSON object."""

import copy
import json
import os

from dotenv import load_dotenv

# Load .env once at import time so ANTHROPIC_API_KEY is available.
load_dotenv()

# Model choice: use the latest available Sonnet. The prompt spec asked for
# "claude-sonnet-4-6 (or latest available)"; claude-sonnet-5 is the current
# latest Sonnet-tier model, so we default to it and allow an env override.
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

# The exact schema the model must return. Also doubles as the fallback template
# (with every string set to "Not disclosed") when extraction fails.
EMPTY_TEMPLATE = {
    "company_name": "Not disclosed",
    "tagline": "Not disclosed",
    "one_line_pitch": "Not disclosed",
    "problem": "Not disclosed",
    "solution": "Not disclosed",
    "market_size": {
        "tam": "Not disclosed",
        "sam": "Not disclosed",
        "som": "Not disclosed",
    },
    "business_model": "Not disclosed",
    "traction": {
        "key_metrics": [],
        "notable_customers": [],
        "growth_rate": "Not disclosed",
    },
    "team": [],
    "competitive_advantage": "Not disclosed",
    "funding_ask": {
        "amount": "Not disclosed",
        "use_of_funds": [],
        "stage": "Not disclosed",
    },
    "contact": {
        "email": "Not disclosed",
        "website": "Not disclosed",
        "linkedin": "Not disclosed",
    },
}

_SCHEMA_STR = json.dumps(
    {
        "company_name": "",
        "tagline": "",
        "one_line_pitch": "",
        "problem": "",
        "solution": "",
        "market_size": {"tam": "", "sam": "", "som": ""},
        "business_model": "",
        "traction": {
            "key_metrics": [],
            "notable_customers": [],
            "growth_rate": "",
        },
        "team": [{"name": "", "title": "", "background": ""}],
        "competitive_advantage": "",
        "funding_ask": {"amount": "", "use_of_funds": [], "stage": ""},
        "contact": {"email": "", "website": "", "linkedin": ""},
    },
    indent=2,
)

SYSTEM_PROMPT = (
    "You are an expert venture-capital analyst. You extract clean, structured "
    "data from raw pitch-deck slide content. You never invent facts: if a field "
    "is not supported by the deck text, you set it to the string \"Not disclosed\" "
    "(or an empty list for list fields). You respond with valid JSON only — no "
    "markdown fences, no commentary."
)


def _build_user_prompt(slides):
    """Concatenate all slide text into a single prompt block."""
    lines = []
    for s in slides:
        header = f"--- SLIDE {s.get('slide', '?')} ---"
        lines.append(header)
        if s.get("title"):
            lines.append(f"Title: {s['title']}")
        if s.get("text"):
            lines.append(s["text"])
        if s.get("notes"):
            lines.append(f"[Speaker notes] {s['notes']}")
        lines.append("")

    deck_text = "\n".join(lines).strip()

    return (
        "Below is the full text extracted from an investor pitch deck, slide by "
        "slide. Extract the information into EXACTLY this JSON schema. Return only "
        "the JSON object, matching keys and structure precisely.\n\n"
        f"SCHEMA:\n{_SCHEMA_STR}\n\n"
        "Rules:\n"
        "- Use \"Not disclosed\" for any string field not supported by the deck.\n"
        "- Use empty arrays for list fields with no data.\n"
        "- Keep values concise; do not pad with filler.\n"
        "- Do not wrap the JSON in markdown code fences.\n\n"
        f"PITCH DECK CONTENT:\n{deck_text}"
    )


def extract_structured_data(slides, model=None):
    """Send slide data to Claude and return the parsed structured dict.

    On any API error or malformed JSON (after one retry), returns a copy of
    EMPTY_TEMPLATE so the pipeline can still produce a one-pager rather than
    crashing. Raises RuntimeError only if the API key is missing.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.strip() in ("", "your_key_here"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add "
            "your key."
        )

    # Imported here so that a missing key raises the friendly error above before
    # we ever touch the SDK.
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    model = model or DEFAULT_MODEL
    user_prompt = _build_user_prompt(slides)

    # Try up to twice: the first attempt, plus one retry on malformed JSON.
    last_error = None
    for attempt in range(2):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = _response_text(resp)
            data = _parse_json(raw)
            return _merge_with_template(data)
        except Exception as exc:  # noqa: BLE001 - retry once, then fall back
            last_error = exc
            continue

    # Both attempts failed — return the safe fallback template.
    print(
        f"[ai_extractor] Warning: extraction failed ({last_error}). "
        "Falling back to a 'Not disclosed' template."
    )
    return copy.deepcopy(EMPTY_TEMPLATE)


def _response_text(resp):
    """Flatten the Anthropic message response content blocks into a string."""
    parts = []
    for block in resp.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()


def _parse_json(raw):
    """Parse model output as JSON, tolerating stray markdown fences."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Strip a leading ```json / ``` fence and trailing ```
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    # As a last resort, isolate the outermost JSON object.
    if not cleaned.lstrip().startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _merge_with_template(data):
    """Overlay model output onto EMPTY_TEMPLATE so every expected key exists.

    This guarantees the PDF generator always sees the full schema even if the
    model omitted a field.
    """
    result = copy.deepcopy(EMPTY_TEMPLATE)
    if not isinstance(data, dict):
        return result

    for key, default_val in result.items():
        if key not in data or data[key] in (None, ""):
            continue
        incoming = data[key]
        if isinstance(default_val, dict) and isinstance(incoming, dict):
            merged = copy.deepcopy(default_val)
            for sub_key in merged:
                if sub_key in incoming and incoming[sub_key] not in (None, ""):
                    merged[sub_key] = incoming[sub_key]
            result[key] = merged
        else:
            result[key] = incoming

    return result
