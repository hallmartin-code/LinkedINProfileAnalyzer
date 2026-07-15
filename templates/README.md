# LinkedIn Analysis — Document Structure Template

Reusable, company-agnostic template for the TEN Capital
**"&lt;Company&gt; – LinkedIn Analysis"** document. Derived from the document
*structure* only — all company-specific data has been stripped out. Use these
files as the general template the Python app fills in for any company.

## Files

| File | Purpose |
|---|---|
| `linkedin_analysis_structure.json` | The **data model** — every field the app must populate, as empty placeholders. Feed this schema to the AI/analysis layer; consume the filled result in the PDF/DOCX generator. |
| `linkedin_analysis_layout.md` | The **visual layout** — section order, headings, tables, and repeatable blocks with `{{placeholders}}`. |

## Document architecture (fixed section order)

1. **Cover** — company logo + title `{company_name} – LinkedIn Analysis`
2. **Executive Summary** — two paragraphs (positioning + investor-readiness)
3. **Investor Appeal Score** — `X / 10` plus the 7-category scoring table + overall
4. **1. Strengths – What Builds Investor Confidence** — repeatable strength blocks (heading + narrative + optional signal bullets)
5. **2. Weaknesses or Gaps – Potential Investor Concerns** — repeatable weakness blocks + the Traction Visibility checklist table
6. **3. Specific Recommendations – How to Improve Investor Appeal** — lettered items (A, B, C…), each using any mix of: current-vs-recommended, grouped bullets, simple bullets, before/after examples, a table, an example line
7. **Final Assessment** — two paragraphs (foundational strengths + primary weakness)

## Scoring rubric (fixed framework — retained by design)

The seven scored categories are part of the TEN Capital analysis framework, not
company data, so their names are kept in the template. Scores are placeholders.

| Category | What it measures |
|---|---|
| Credibility | Legitimacy signals: real operations, funding, recognition |
| Leadership Visibility | Founder/executive public presence and articulation |
| Technology Differentiation | Proprietary tech, IP, defensibility signals |
| Commercial Proof | Traction, customers, revenue, deployments shown |
| Investor Storytelling | Whether the investment narrative is clearly told |
| Thought Leadership | Market/industry content and authority |
| Social Proof | Followers, engagement, stakeholder amplification |
| **Overall Investor Appeal** | Weighted/blended headline score (`X / 10`) |

## Repeatable / variable blocks

- **Strengths / Weaknesses items** — 0..N each; count varies per company.
- **Traction Visibility checklist rows** — the investor-question list (e.g.
  "Revenue growth", "Customers served", "Patent portfolio"…) with a ✓ / ❌
  visibility flag per row; questions may be added or removed per analysis.
- **Recommendations** — lettered A..N; each item only renders the components it
  needs, so the generator must treat every recommendation sub-field as optional.

## Formatting standards

- **Footer (every page, centered, Open Sans 7pt):**
  `{footer_title}   {page#}   Compiled on {date} by TEN Capital Network   [TEN Capital logo]`
- **Header:** empty.
- See the root `CLAUDE.md` → *TEN Capital Footer* for the exact footer spec.

## Usage in the app

```text
company LinkedIn data
   │  analysis layer   →  fill linkedin_analysis_structure.json (all placeholders)
   ▼
populated structure (dict)
   │  generator        →  render sections per linkedin_analysis_layout.md
   ▼
<company_name> - LinkedIn Analysis.pdf   (TEN Capital branded, footered)
```
