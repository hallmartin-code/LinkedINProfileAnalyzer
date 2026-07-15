# LinkedIn Analysis — Document Layout Template

> Generic structural template for a TEN Capital **"<Company> – LinkedIn Analysis"**
> document. Placeholders are written as `{{field}}`. Repeatable blocks are marked
> `(repeat per …)`. This file defines **layout and order only** — no company data.

---

## Page Furniture (applies to every page)

- **Footer (single line, centered):**
  `{{footer_title}}   {{page_number}}   Compiled on {{analysis_date}} by TEN Capital Network   [TEN Capital logo]`
  - Font: Open Sans, 7pt, centered (per TEN Capital footer standard).
- **Header:** empty.

---

## COVER

- `[{{company_logo}}]`  — company logo, centered near top
- **Title (H1, centered):** `{{company_name}} – LinkedIn Analysis`

---

## EXECUTIVE SUMMARY

**Heading (H2):** `Executive Summary`

- Paragraph 1 — `{{executive_summary.positioning_paragraph}}`
  *(what the profile signals about the company from an investor's perspective)*
- Paragraph 2 — `{{executive_summary.investor_readiness_paragraph}}`
  *(who the profile is currently optimized for and what investment factors it under-communicates)*

**Investor Appeal Score: `{{investor_appeal_score.overall_score}}` / `{{scale_max}}`**

| Category | Score |
|---|---|
| Credibility | `{{score}}` |
| Leadership Visibility | `{{score}}` |
| Technology Differentiation | `{{score}}` |
| Commercial Proof | `{{score}}` |
| Investor Storytelling | `{{score}}` |
| Thought Leadership | `{{score}}` |
| Social Proof | `{{score}}` |
| **Overall Investor Appeal** | **`{{overall_score}}`** |

---

## 1. Strengths – What Builds Investor Confidence

**(repeat per strength item):**

- **Sub-heading (H3):** `{{strengths.items[].heading}}`
- Paragraph — `{{strengths.items[].narrative}}`
- *(optional)* labeled bullet list, e.g. **Positive Signals**:
  - `{{signal}}` *(repeat)*

---

## 2. Weaknesses or Gaps – Potential Investor Concerns

**(repeat per weakness item):**

- **Sub-heading (H3):** `{{weaknesses.items[].heading}}`
- Paragraph — `{{weaknesses.items[].narrative}}`
- *(optional)* bullet list of specifics / investor takeaways:
  - `{{point}}` *(repeat)*

**Traction Visibility checklist (table):**

| Investor Question | Visible? |
|---|---|
| `{{investor_question}}` | `{{✓ / ❌}}` *(repeat per row)* |

---

## 3. Specific Recommendations – How to Improve Investor Appeal

**(repeat per lettered recommendation A, B, C, …):**

- **Sub-heading (H3):** `{{id}}. {{title}}`
- *(optional)* intro line — `{{intro}}`

Each recommendation uses **one or more** of the following optional components,
depending on its type:

- **Current vs. Recommended pair:**
  - *Current:* `{{current}}`
  - *Recommended / Investor-Optimized Example:* `{{recommended}}`
  - *(optional)* "This version communicates:" → bullets `{{communicates[]}}`
- **Grouped bullet lists:** *(repeat per group)*
  - **`{{subheading}}`**
    - `{{bullet}}` *(repeat)*
- **Simple bullet list:**
  - `{{bullet}}` *(repeat)*
- **Before/After examples:** *(repeat)*
  - *Instead of:* `{{instead_of}}`
  - *Use:* `{{use}}`
- **Table:**

  | `{{column}}` | `{{column}}` |
  |---|---|
  | `{{cell}}` | `{{cell}}` *(repeat per row)* |
- **Example line:** `{{example_line}}`

---

## FINAL ASSESSMENT

**Heading (H2):** `Final Assessment`

- Paragraph 1 — `{{final_assessment.foundational_strengths_paragraph}}`
  *(recap of the foundational strengths that attract investor interest)*
- Paragraph 2 — `{{final_assessment.primary_weakness_paragraph}}`
  *(the primary weakness and the path to improve investor appeal)*
