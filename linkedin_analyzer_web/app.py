"""Flask web app: paste LinkedIn page text -> Claude analysis -> branded PDF.

Deployed on Railway. The Claude API key is read from the ANTHROPIC_API_KEY
environment variable (set it in Railway → Variables).
"""

import datetime
import io
import os
import re

from dotenv import load_dotenv
from flask import (
    Flask,
    make_response,
    render_template,
    request,
)

from analyzer import analyze_linkedin, AnalyzerError
from generator import build_analysis_pdf

load_dotenv()

app = Flask(__name__, template_folder="webtemplates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB cap on form posts


def _safe_filename(name):
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "").strip()).strip("_")
    return stem or "Company"


def _today():
    # Local date in M/D/YYYY to match the TEN Capital footer style.
    d = datetime.date.today()
    return f"{d.month}/{d.day}/{d.year}"


@app.route("/", methods=["GET"])
def index():
    key_configured = bool(os.getenv("ANTHROPIC_API_KEY"))
    return render_template("index.html", key_configured=key_configured, error=None)


@app.route("/healthz", methods=["GET"])
def healthz():
    return {"status": "ok"}, 200


@app.route("/analyze", methods=["POST"])
def analyze():
    company_name = (request.form.get("company_name") or "").strip()
    linkedin_content = (request.form.get("linkedin_content") or "").strip()
    key_configured = bool(os.getenv("ANTHROPIC_API_KEY"))

    def _fail(message, status=400):
        resp = make_response(
            render_template(
                "index.html",
                key_configured=key_configured,
                error=message,
                company_name=company_name,
                linkedin_content=linkedin_content,
            ),
            status,
        )
        return resp

    if not company_name:
        return _fail("Please enter a company name.")
    if not linkedin_content:
        return _fail("Please paste the LinkedIn page content to analyze.")

    analysis_date = _today()

    try:
        data = analyze_linkedin(
            company_name=company_name,
            linkedin_content=linkedin_content,
            analysis_date=analysis_date,
        )
    except AnalyzerError as exc:
        return _fail(str(exc), status=502 if "API" in str(exc) else 400)
    except Exception as exc:  # noqa: BLE001 - never leak a stack trace to the user
        return _fail(f"Unexpected error during analysis: {exc}", status=500)

    try:
        pdf_bytes = build_analysis_pdf(data)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Analysis succeeded but PDF generation failed: {exc}", status=500)

    filename = f"{_safe_filename(company_name)} - LinkedIn Analysis.pdf"
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


if __name__ == "__main__":
    # Local dev server. In production, gunicorn serves `app` (see Procfile).
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=bool(os.getenv("FLASK_DEBUG")))
