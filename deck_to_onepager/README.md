# deck_to_onepager

`deck_to_onepager` reads an investor pitch deck (PDF or PPTX), extracts the key
information from each slide, uses the Claude API to structure it into a clean
JSON schema, and renders a single-page, branded one-pager PDF summary — problem,
solution, market, traction, team, the ask, and contact — ready to share.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # then edit .env and add your ANTHROPIC_API_KEY
```

On Windows PowerShell, use `Copy-Item .env.example .env`.

## Usage

```bash
python main.py --input path/to/deck.pdf
```

Options:

| Option     | Description                                   | Default     |
|------------|-----------------------------------------------|-------------|
| `--input`  | Path to the PDF or PPTX pitch deck (required) | —           |
| `--output` | Output directory for the generated PDF        | `./output/` |
| `--debug`  | Print the extracted JSON before generating    | off         |

The generated file lands at `output/<company_name>_onepager.pdf`.

## Supported input formats

- **PDF** (`.pdf`) — text and embedded images are extracted per page.
- **PowerPoint** (`.pptx`) — text frames, titles, tables, chart titles, and
  speaker notes are extracted per slide.

> Legacy binary PowerPoint (`.ppt`) is **not** supported — re-save as `.pptx`.

## Optional branding

Drop a `logo.png` into `assets/` and it will be rendered in the header bar of
the one-pager. If it's absent, the header renders cleanly without it.

## How it works

```
deck (PDF/PPTX)
   │  parser/            extract raw slide text (+ images)
   ▼
raw slide data
   │  extractor/         Claude structures it into the one-pager JSON schema
   ▼
structured JSON
   │  generator/         ReportLab renders the branded single-page PDF
   ▼
output/<company>_onepager.pdf
```
