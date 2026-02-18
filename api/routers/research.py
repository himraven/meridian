"""
Research report routes — serves AI-generated stock research reports.
Reports are stored as JSON files in the research data directory.
"""

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# ── Data directory ─────────────────────────────────────────────────────
RESEARCH_DIR = Path(os.getenv("RESEARCH_DIR", "./data/research"))


def _read_report(ticker: str) -> dict[str, Any] | None:
    """Read a research report JSON file by ticker."""
    file_path = RESEARCH_DIR / f"{ticker}.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _list_reports() -> list[dict[str, Any]]:
    """List all available research reports (summary only)."""
    reports = []
    if not RESEARCH_DIR.exists():
        return reports

    for file_path in sorted(RESEARCH_DIR.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            overview = data.get("overview", {})
            rating = data.get("rating", {})
            reports.append({
                "ticker": overview.get("ticker", file_path.stem),
                "name": overview.get("name", ""),
                "market": overview.get("market", ""),
                "signal": rating.get("signal", ""),
                "updatedAt": rating.get("updatedAt", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue

    return reports


# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/research")
def api_research_list():
    """List all available research reports."""
    reports = _list_reports()
    return {"reports": reports, "count": len(reports)}


@router.get("/api/research/{ticker}")
def api_research_detail(ticker: str):
    """Get full research report for a specific ticker."""
    report = _read_report(ticker)

    if report is None:
        # Try uppercase/lowercase variants
        report = _read_report(ticker.upper()) or _read_report(ticker.lower())

    if report is None:
        raise HTTPException(
            status_code=404,
            detail=f"No research report found for ticker '{ticker}'"
        )

    return report
