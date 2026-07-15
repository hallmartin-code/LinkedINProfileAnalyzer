# LinkedIn Investor Appeal Analyzer (Web App)

A Flask web app that turns a company's **pasted LinkedIn page content** into a
**branded TEN Capital "LinkedIn Analysis" PDF**. It calls the Claude API to score
the page against the TEN Capital investor-appeal rubric and generates the
multi-page document (executive summary, scoring table, strengths, weaknesses +
traction-visibility checklist, lettered recommendations, final assessment).

## How it works

```
Paste LinkedIn page text  →  Claude API (fills the analysis structure)  →  ReportLab  →  branded PDF download
```

- **Input:** company name + pasted LinkedIn page content (About, posts, headline,
  followers, funding/recognition mentions…).
- **Analysis:** Claude (`claude-sonnet-5` by default) returns the structured
  analysis; grounded only in what you paste (absence is reported, not invented).
- **Output:** `<Company> - LinkedIn Analysis.pdf`, TEN Capital footer + logo.

## Local development

```bash
cd linkedin_analyzer_web
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env        # then edit .env and add ANTHROPIC_API_KEY
python app.py               # serves http://localhost:8000
```

(On PowerShell: `Copy-Item .env.example .env`, and activate with
`.venv\Scripts\Activate.ps1`.)

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | Your Claude Console API key. |
| `ANTHROPIC_MODEL` | No | Model override (default `claude-sonnet-5`). |
| `PORT` | No | Port for local dev (Railway sets this automatically). |
| `FLASK_DEBUG` | No | Set to `1` for local debug reloader. |

## Deploy to Railway

You have two easy paths.

### Option A — Deploy from GitHub (recommended)

1. Push this project to a GitHub repo. If the repo root is the parent
   `LinkedIN Profile Analyzer` folder (which also contains other apps), set
   Railway's **Root Directory** to `linkedin_analyzer_web` so it builds just this
   app. If this folder is the repo root, skip that.
2. In Railway: **New Project → Deploy from GitHub repo** → pick the repo.
3. **Variables** tab → add `ANTHROPIC_API_KEY` = your Claude key.
4. Railway auto-detects Python (Nixpacks), installs `requirements.txt`, and
   starts the app via `railway.json` / `Procfile`
   (`gunicorn app:app`). A public URL is generated under **Settings → Networking →
   Generate Domain**.

### Option B — Deploy with the Railway CLI

```bash
npm i -g @railway/cli
railway login
cd linkedin_analyzer_web
railway init                       # create a new project
railway variables --set ANTHROPIC_API_KEY=sk-ant-...   # add your key
railway up                         # build & deploy this directory
railway domain                     # generate a public URL
```

### Deploy notes

- **Start command / health check** come from `railway.json`
  (`/healthz` returns 200). A `Procfile` is included as a fallback.
- **Python version** is pinned to 3.12 via `.python-version` for reliable wheels.
- **gunicorn timeout** is 180s to accommodate longer Claude responses.
- The **TEN Capital footer logo** ships in `assets/`. To render the footer in
  Open Sans (the brand standard) instead of the Helvetica fallback, drop
  `OpenSans-Regular.ttf` into `assets/fonts/`.

## Project layout

```
linkedin_analyzer_web/
├── app.py                     # Flask: form (GET /) + analyze (POST /analyze) + /healthz
├── analyzer/claude_analyzer.py# Claude call → filled analysis structure
├── generator/pdf_builder.py   # ReportLab Platypus → branded multi-page PDF
├── webtemplates/index.html    # paste-text form UI
├── static/style.css
├── assets/TEN_Capital_logo_footer.png
├── requirements.txt
├── Procfile
├── railway.json
├── .python-version
└── .env.example
```

## Security notes

- The API key is read server-side from the environment and is **never** sent to
  the browser or embedded in the PDF.
- Pasted content is used only to build the analysis for that request; the app
  does not persist submissions.
```
