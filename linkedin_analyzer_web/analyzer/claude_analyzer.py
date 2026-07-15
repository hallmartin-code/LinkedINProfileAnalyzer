"""Call the Claude API to produce a TEN Capital LinkedIn Analysis structure.

Given a company name and pasted LinkedIn page content, this asks Claude to fill
the analysis data model defined in
`templates/linkedin_analysis_structure.json` (kept in sync below as
EMPTY_STRUCTURE). The returned dict feeds the PDF generator.
"""

import copy
import json
import os

# The fixed TEN Capital scoring rubric (framework, not company data).
SCORING_CATEGORIES = [
    "Credibility",
    "Leadership Visibility",
    "Technology Differentiation",
    "Commercial Proof",
    "Investor Storytelling",
    "Thought Leadership",
    "Social Proof",
]

# Empty data model — mirrors templates/linkedin_analysis_structure.json. Used as
# the merge base so the generator always receives every expected key.
EMPTY_STRUCTURE = {
    "company_name": "",
    "analysis_date": "",
    "compiled_by": "TEN Capital Network",
    "executive_summary": {
        "positioning_paragraph": "",
        "investor_readiness_paragraph": "",
    },
    "investor_appeal_score": {
        "scale_max": 10,
        "overall_score": None,
        "categories": [{"category": c, "score": None} for c in SCORING_CATEGORIES],
    },
    "strengths": {
        "section_title": "Strengths – What Builds Investor Confidence",
        "items": [],
    },
    "weaknesses": {
        "section_title": "Weaknesses or Gaps – Potential Investor Concerns",
        "items": [],
        "traction_visibility_checklist": {
            "table_title": "Traction Visibility",
            "columns": ["Investor Question", "Visible?"],
            "rows": [],
        },
    },
    "recommendations": {
        "section_title": "Specific Recommendations – How to Improve Investor Appeal",
        "items": [],
    },
    "final_assessment": {
        "section_title": "Final Assessment",
        "foundational_strengths_paragraph": "",
        "primary_weakness_paragraph": "",
    },
}

# Model default: strong reasoning for nuanced investor analysis. Override with
# the ANTHROPIC_MODEL env var.
DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

MAX_CONTENT_CHARS = 60_000  # guard against pathologically large pastes


class AnalyzerError(Exception):
    """Raised for user-facing analyzer failures (bad key, API error, etc.)."""


SYSTEM_PROMPT = """You are a senior venture-capital analyst at TEN Capital. You \
evaluate a company's LinkedIn presence strictly from an INVESTOR's perspective \
and produce a structured "LinkedIn Analysis" that follows TEN Capital's fixed \
format.

You assess how well the LinkedIn presence communicates the factors that drive \
investment decisions: credibility, leadership visibility, technology \
differentiation, commercial proof/traction, investor storytelling, thought \
leadership, and social proof.

Ground every observation in the provided LinkedIn content. Do not invent \
specific facts (funding amounts, customer names, metrics) that are not present \
in the content. When something an investor would want is absent, say so — \
absence is itself a finding. Write in the measured, professional voice of an \
investment analyst.

You respond with a single valid JSON object and nothing else — no markdown \
fences, no commentary before or after."""

# Human-readable schema shown to the model. Kept verbose so the model fills the
# variable recommendation blocks correctly.
SCHEMA_GUIDE = """Return EXACTLY this JSON shape:

{
  "company_name": "string",
  "analysis_date": "string (use the date provided in the request)",
  "compiled_by": "TEN Capital Network",

  "executive_summary": {
    "positioning_paragraph": "1 paragraph: what the profile signals about the company to an investor",
    "investor_readiness_paragraph": "1 paragraph: who the profile is optimized for and which investment factors it under-communicates"
  },

  "investor_appeal_score": {
    "scale_max": 10,
    "overall_score": 0.0,
    "categories": [
      {"category": "Credibility", "score": 0.0},
      {"category": "Leadership Visibility", "score": 0.0},
      {"category": "Technology Differentiation", "score": 0.0},
      {"category": "Commercial Proof", "score": 0.0},
      {"category": "Investor Storytelling", "score": 0.0},
      {"category": "Thought Leadership", "score": 0.0},
      {"category": "Social Proof", "score": 0.0}
    ]
  },

  "strengths": {
    "section_title": "Strengths – What Builds Investor Confidence",
    "items": [
      {"heading": "short title", "narrative": "1-2 paragraphs", "signals": ["optional short bullet", "..."]}
    ]
  },

  "weaknesses": {
    "section_title": "Weaknesses or Gaps – Potential Investor Concerns",
    "items": [
      {"heading": "short title", "narrative": "1-2 paragraphs", "points": ["optional short bullet", "..."]}
    ],
    "traction_visibility_checklist": {
      "table_title": "Traction Visibility",
      "columns": ["Investor Question", "Visible?"],
      "rows": [
        {"investor_question": "e.g. Revenue growth", "visible": false}
      ]
    }
  },

  "recommendations": {
    "section_title": "Specific Recommendations – How to Improve Investor Appeal",
    "items": [
      {
        "id": "A",
        "title": "short title",
        "intro": "optional one-line intro (\"\" if none)",
        "current": "optional current-state text (\"\" if not applicable)",
        "recommended": "optional recommended/optimized text (\"\" if not applicable)",
        "communicates": ["optional bullets describing what the recommended version communicates"],
        "bullet_groups": [{"subheading": "optional group label", "bullets": ["..."]}],
        "bullets": ["optional flat bullet list"],
        "before_after_examples": [{"context": "optional label", "instead_of": "...", "use": "..."}],
        "table": {"columns": ["optional", "columns"], "rows": [["cell", "cell"]]},
        "example_line": "optional single example line (\"\" if none)"
      }
    ]
  },

  "final_assessment": {
    "section_title": "Final Assessment",
    "foundational_strengths_paragraph": "1 paragraph recapping foundational strengths",
    "primary_weakness_paragraph": "1 paragraph naming the primary weakness and the path to improve investor appeal"
  }
}

Rules:
- Scores are numbers 0.0–10.0 with one decimal. overall_score reflects the blended picture (roughly the weighted average of the categories).
- Provide 4–6 strengths items and 4–6 weaknesses items when the content supports them.
- The traction_visibility_checklist should list the concrete investor questions (e.g. Revenue growth, Customers served, Enterprise deployments, Strategic partnerships, Units shipped, Patent portfolio, Channel partners, Market penetration) with visible=true only if the content actually shows it.
- Provide 6–8 recommendations (ids A, B, C, …). For each recommendation, include ONLY the components that fit it; set unused string fields to "" and unused list/table fields to empty. Do not force every component into every recommendation.
- Output ONLY the JSON object."""


def _build_user_prompt(company_name, linkedin_content, analysis_date):
    content = linkedin_content.strip()
    if len(content) > MAX_CONTENT_CHARS:
        content = content[:MAX_CONTENT_CHARS] + "\n...[content truncated]..."
    return (
        f"Company name: {company_name}\n"
        f"Analysis date: {analysis_date}\n\n"
        f"{SCHEMA_GUIDE}\n\n"
        "LINKEDIN PAGE CONTENT (verbatim, pasted by the user):\n"
        "-----------------------------------------------------\n"
        f"{content}\n"
        "-----------------------------------------------------"
    )


def analyze_linkedin(company_name, linkedin_content, analysis_date,
                     api_key=None, model=None):
    """Run the analysis and return the populated structure dict.

    Raises AnalyzerError with a user-friendly message on failure.
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key.strip() in ("", "your_key_here"):
        raise AnalyzerError(
            "No Claude API key configured. Set ANTHROPIC_API_KEY in the "
            "environment (Railway → Variables)."
        )
    if not company_name.strip():
        raise AnalyzerError("Company name is required.")
    if not linkedin_content.strip():
        raise AnalyzerError("LinkedIn page content is required.")

    try:
        from anthropic import Anthropic
    except ImportError as exc:  # pragma: no cover
        raise AnalyzerError("The 'anthropic' package is not installed.") from exc

    client = Anthropic(api_key=api_key)
    model = model or DEFAULT_MODEL
    user_prompt = _build_user_prompt(company_name, linkedin_content, analysis_date)

    last_error = None
    for attempt in range(2):  # one retry on malformed JSON / transient error
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=8000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:  # noqa: BLE001 - surface a clean message
            # Auth / rate / network errors from the SDK.
            raise AnalyzerError(f"Claude API request failed: {exc}") from exc

        raw = _response_text(resp)
        try:
            data = _parse_json(raw)
            merged = _merge(data, company_name, analysis_date)
            return merged
        except (ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            continue

    raise AnalyzerError(
        "Claude returned a response that could not be parsed as the expected "
        f"analysis format. Please try again. ({last_error})"
    )


def _response_text(resp):
    parts = []
    for block in resp.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()


def _parse_json(raw):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    if not cleaned.lstrip().startswith("{"):
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _merge(data, company_name, analysis_date):
    """Overlay model output on EMPTY_STRUCTURE so all keys exist and are typed."""
    result = copy.deepcopy(EMPTY_STRUCTURE)
    if not isinstance(data, dict):
        raise ValueError("Top-level analysis result is not a JSON object.")

    result["company_name"] = data.get("company_name") or company_name
    result["analysis_date"] = data.get("analysis_date") or analysis_date
    result["compiled_by"] = data.get("compiled_by") or "TEN Capital Network"

    es = data.get("executive_summary") or {}
    result["executive_summary"]["positioning_paragraph"] = es.get(
        "positioning_paragraph", ""
    )
    result["executive_summary"]["investor_readiness_paragraph"] = es.get(
        "investor_readiness_paragraph", ""
    )

    ias = data.get("investor_appeal_score") or {}
    result["investor_appeal_score"]["overall_score"] = ias.get("overall_score")
    incoming_cats = {
        (c.get("category") or "").strip().lower(): c.get("score")
        for c in (ias.get("categories") or [])
        if isinstance(c, dict)
    }
    for cat in result["investor_appeal_score"]["categories"]:
        cat["score"] = incoming_cats.get(cat["category"].lower(), None)

    strengths = data.get("strengths") or {}
    result["strengths"]["items"] = [
        {
            "heading": (it or {}).get("heading", ""),
            "narrative": (it or {}).get("narrative", ""),
            "signals": list((it or {}).get("signals", []) or []),
        }
        for it in (strengths.get("items") or [])
        if isinstance(it, dict)
    ]

    weaknesses = data.get("weaknesses") or {}
    result["weaknesses"]["items"] = [
        {
            "heading": (it or {}).get("heading", ""),
            "narrative": (it or {}).get("narrative", ""),
            "points": list((it or {}).get("points", []) or []),
        }
        for it in (weaknesses.get("items") or [])
        if isinstance(it, dict)
    ]
    checklist = (weaknesses.get("traction_visibility_checklist") or {})
    rows = []
    for r in (checklist.get("rows") or []):
        if isinstance(r, dict):
            rows.append(
                {
                    "investor_question": r.get("investor_question", ""),
                    "visible": bool(r.get("visible", False)),
                }
            )
    result["weaknesses"]["traction_visibility_checklist"]["rows"] = rows

    recs = data.get("recommendations") or {}
    result["recommendations"]["items"] = [
        _clean_recommendation(it)
        for it in (recs.get("items") or [])
        if isinstance(it, dict)
    ]

    fa = data.get("final_assessment") or {}
    result["final_assessment"]["foundational_strengths_paragraph"] = fa.get(
        "foundational_strengths_paragraph", ""
    )
    result["final_assessment"]["primary_weakness_paragraph"] = fa.get(
        "primary_weakness_paragraph", ""
    )

    return result


def _clean_recommendation(it):
    table = it.get("table") or {}
    cols = list(table.get("columns", []) or [])
    raw_rows = table.get("rows", []) or []
    norm_rows = []
    for row in raw_rows:
        if isinstance(row, list):
            norm_rows.append([str(c) for c in row])
        elif isinstance(row, dict):
            norm_rows.append([str(v) for v in row.values()])
    return {
        "id": str(it.get("id", "") or ""),
        "title": it.get("title", "") or "",
        "intro": it.get("intro", "") or "",
        "current": it.get("current", "") or "",
        "recommended": it.get("recommended", "") or "",
        "communicates": list(it.get("communicates", []) or []),
        "bullet_groups": [
            {
                "subheading": (g or {}).get("subheading", "") or "",
                "bullets": list((g or {}).get("bullets", []) or []),
            }
            for g in (it.get("bullet_groups", []) or [])
            if isinstance(g, dict)
        ],
        "bullets": list(it.get("bullets", []) or []),
        "before_after_examples": [
            {
                "context": (e or {}).get("context", "") or "",
                "instead_of": (e or {}).get("instead_of", "") or "",
                "use": (e or {}).get("use", "") or "",
            }
            for e in (it.get("before_after_examples", []) or [])
            if isinstance(e, dict)
        ],
        "table": {"columns": cols, "rows": norm_rows},
        "example_line": it.get("example_line", "") or "",
    }
