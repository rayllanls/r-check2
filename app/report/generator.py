"""Geração do relatório HTML com Jinja2. Abre no browser local."""
from __future__ import annotations

import base64
import dataclasses
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.core.models import ScanResult

TEMPLATE_DIR = Path(__file__).parent / "templates"
STATIC_DIR   = Path(__file__).parent / "static"
PROJECT_ROOT = Path(__file__).parent.parent.parent  # raksaas/

# Severity sort order for pre-sorting before template render
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _load_chartjs() -> str:
    """Read bundled Chart.js from static dir. Returns empty string on failure."""
    path = STATIC_DIR / "chart.min.js"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_favicon_svg() -> str:
    """Read favicon.svg and return as base64 data URI for use in <img> and <link>."""
    svg_path = PROJECT_ROOT / "app" / "favicon.svg"
    try:
        data = svg_path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/svg+xml;base64,{b64}"
    except OSError:
        return ""


def generate_report(result: ScanResult, open_browser: bool = True) -> Path:
    """Gera relatório HTML e (opcionalmente) abre no browser. Retorna path do arquivo.

    Injeta Chart.js inline (offline-safe, D-10), logo como base64 (D-09),
    findings pré-ordenados Critical-first (D-02), e timestamp de geração.
    """
    # Pre-sort findings Critical-first (template sort is secondary safety net only)
    sorted_findings = sorted(
        result.findings,
        key=lambda f: _SEVERITY_ORDER.get(f.severity.value, 99)
    )
    # Build a ScanResult-like namespace with sorted findings for template
    # We pass individual vars so template does not need to re-sort
    sorted_result = dataclasses.replace(result, findings=sorted_findings)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,  # HTML template, not user input
    )
    template = env.get_template("report.html")
    favicon_b64 = _load_favicon_svg()
    html = template.render(
        result=sorted_result,
        favicon_b64=favicon_b64,
        chartjs=_load_chartjs(),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    output = Path(tempfile.gettempdir()) / "r-check_report.html"
    output.write_text(html, encoding="utf-8")

    if open_browser:
        # Use absolute URI to handle spaces and special characters in various OSs
        report_uri = output.resolve().as_uri()
        webbrowser.open(report_uri)

    return output
