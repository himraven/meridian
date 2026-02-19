"""
Data Health — monitors freshness of all data sources.

Each source has an expected update frequency. If a file's mtime
exceeds the staleness threshold, it's flagged as stale.

GET /api/data-health → full report
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

router = APIRouter()

# ── Data Source Definitions ────────────────────────────────────────────────
# max_age_hours: how old before we flag it as stale
# schedule: human-readable cron description
# critical: True = core data, affects user experience directly

SOURCES = [
    # US Smart Money (rsnest crons → /app/data/)
    # ── US Smart Money (rsnest crons → /app/data/) ──
    {
        "name": "Congress Trades",
        "path": "/app/data/congress.json",
        "max_age_hours": 14,    # 3x daily: 13:00, 18:00, 23:00 UTC → max gap ~11h
        "schedule": "3x/day (13:00, 18:00, 23:00 UTC)",
        "critical": True,
    },
    {
        "name": "Congress Trades (processed)",
        "path": "/app/data/congress_trades.json",
        "max_age_hours": 14,
        "schedule": "3x/day (with congress collector)",
        "critical": False,
    },
    {
        "name": "ARK Trades (JSON)",
        "path": "/app/data/ark_trades.json",
        "max_age_hours": 72,    # Mon-Fri only; weekend gap = ~62h
        "schedule": "4x/day Mon-Fri (14:30-20:30 UTC)",
        "critical": True,
        "weekday_only": True,
    },
    {
        "name": "ARK Holdings (JSON)",
        "path": "/app/data/ark_holdings.json",
        "max_age_hours": 72,
        "schedule": "4x/day Mon-Fri",
        "critical": False,
        "weekday_only": True,
    },
    {
        "name": "ARK Changes (JSONL)",
        "path": "/app/ark-data/ark_changes.jsonl",
        "max_age_hours": 96,    # Only updates when ARK trades; can skip days + weekends
        "schedule": "On ARK trade activity (cathiesark.com)",
        "critical": True,
        "weekday_only": True,
    },
    {
        "name": "ARK Trend Cache",
        "path": "/app/ark-data/trend_cache.json",
        "max_age_hours": 96,
        "schedule": "With ARK collector",
        "critical": False,
        "weekday_only": True,
    },
    {
        "name": "Dark Pool Analytics",
        "path": "/app/data/darkpool.json",
        "max_age_hours": 72,    # Daily Tue-Sat; weekend gap ~62h
        "schedule": "Daily Tue-Sat (00:15 UTC, after FINRA publish)",
        "critical": True,
        "weekday_only": True,
    },
    {
        "name": "Confluence Ranking",
        "path": "/app/data/ranking.json",
        "max_age_hours": 16,    # 2x daily: 01:00, 14:00 UTC
        "schedule": "2x/day (01:00, 14:00 UTC)",
        "critical": True,
    },
    {
        "name": "Institution 13F Filings",
        "path": "/app/data/institutions.json",
        "max_age_hours": 192,   # Weekly Monday
        "schedule": "Weekly (Monday 12:00 UTC)",
        "critical": False,
    },
    {
        "name": "Insider Trading (SEC Form 4)",
        "path": "/app/data/insiders.json",
        "max_age_hours": 28,    # 2x daily expected
        "schedule": "2x/day (with insider collector)",
        "critical": True,
    },

    # ── CN Market (signals crons → /app/signals/) ──
    {
        "name": "CN 12x30 Portfolio",
        "path": "/app/signals/cn-12x30/paper_portfolio_12x30.json",
        "max_age_hours": 72,    # A-share trading days only; weekend gap
        "schedule": "Daily (A-share trading days)",
        "critical": True,
        "weekday_only": True,
    },
    {
        "name": "CN 12x30 NAV Curve",
        "path": "/app/signals/cn-12x30/nav_curve_12x30.json",
        "max_age_hours": 72,
        "schedule": "Daily (A-share trading days)",
        "critical": False,
        "weekday_only": True,
    },
    {
        "name": "CN Trend State",
        "path": "/app/signals/cn_trend_state.json",
        "max_age_hours": 72,
        "schedule": "Daily (A-share trading days)",
        "critical": True,
        "weekday_only": True,
    },

    # ── HK Market ──
    {
        "name": "HK Daily Signals",
        "path": "/app/signals/hk_daily_state.json",
        "max_age_hours": 72,    # HK trading days; weekend gap
        "schedule": "Daily (HK trading days)",
        "critical": True,
        "weekday_only": True,
    },
    {
        "name": "HK Entry/Exit",
        "path": "/app/signals/hk_entry_exit.json",
        "max_age_hours": 72,
        "schedule": "Daily (HK trading days)",
        "critical": False,
        "weekday_only": True,
    },

    # Research (Nova deep-research → /app/research/)
    {
        "name": "Research Reports",
        "path": "/app/research",
        "is_directory": True,
        "max_age_hours": 168,  # Weekly-ish, manual
        "schedule": "On-demand (Nova deep research)",
        "critical": False,
    },

    # SQLite
    {
        "name": "SQLite Database",
        "path": "/app/db/smartmoney.db",
        "max_age_hours": 24,
        "schedule": "Updated by meridian cron collectors",
        "critical": False,
    },
]


def _weekend_adjusted_max_age(base_hours: float, weekday_only: bool) -> float:
    """Add extra tolerance on weekends/Monday for market-data sources."""
    if not weekday_only:
        return base_hours
    now = datetime.now(timezone.utc)
    # Saturday=5, Sunday=6, Monday=0 (data from Friday may be 48-72h old)
    if now.weekday() in (5, 6, 0):
        return base_hours + 48  # +2 days tolerance for weekend gap
    return base_hours


def _check_source(source: dict) -> dict:
    """Check a single data source and return status."""
    path = source["path"]
    is_dir = source.get("is_directory", False)
    weekday_only = source.get("weekday_only", False)
    max_age_hours = _weekend_adjusted_max_age(source["max_age_hours"], weekday_only)

    result = {
        "name": source["name"],
        "path": path,
        "schedule": source["schedule"],
        "critical": source["critical"],
        "max_age_hours": max_age_hours,
    }

    if not os.path.exists(path):
        result.update({
            "status": "missing",
            "icon": "🔴",
            "age_hours": None,
            "last_updated": None,
            "message": "File not found",
        })
        return result

    if is_dir:
        # For directories, check the most recent file
        files = list(Path(path).glob("*.json"))
        if not files:
            result.update({
                "status": "empty",
                "icon": "🔴",
                "age_hours": None,
                "last_updated": None,
                "file_count": 0,
                "message": "Directory empty",
            })
            return result

        latest_mtime = max(f.stat().st_mtime for f in files)
        result["file_count"] = len(files)
    else:
        latest_mtime = os.path.getmtime(path)
        # Add file size
        result["size_bytes"] = os.path.getsize(path)

    age_seconds = time.time() - latest_mtime
    age_hours = round(age_seconds / 3600, 1)
    last_updated = datetime.fromtimestamp(latest_mtime, tz=timezone.utc).isoformat()

    # Determine status
    if age_hours <= max_age_hours:
        status = "fresh"
        icon = "🟢"
        message = "Up to date"
    elif age_hours <= max_age_hours * 1.5:
        status = "stale"
        icon = "🟡"
        message = f"Approaching staleness ({age_hours}h old, threshold: {max_age_hours}h)"
    else:
        status = "stale"
        icon = "🔴"
        message = f"Stale ({age_hours}h old, threshold: {max_age_hours}h)"

    result.update({
        "status": status,
        "icon": icon,
        "age_hours": age_hours,
        "last_updated": last_updated,
        "message": message,
    })
    return result


@router.get("/api/data-health")
def api_data_health():
    """
    Comprehensive data freshness report.
    
    Status levels:
      🟢 fresh  — within expected update window
      🟡 stale  — approaching threshold (1.0x - 1.5x max age)
      🔴 stale  — beyond threshold (>1.5x max age) or missing
    """
    results = [_check_source(s) for s in SOURCES]

    # Summary
    fresh = sum(1 for r in results if r["status"] == "fresh")
    stale = sum(1 for r in results if r["status"] == "stale")
    missing = sum(1 for r in results if r["status"] in ("missing", "empty"))
    critical_issues = [
        r for r in results
        if r["critical"] and r["status"] in ("stale", "missing", "empty")
        and r.get("icon") == "🔴"
    ]

    # Overall health
    if critical_issues:
        overall = "degraded"
        overall_icon = "🔴"
    elif stale > 0:
        overall = "warning"
        overall_icon = "🟡"
    else:
        overall = "healthy"
        overall_icon = "🟢"

    return {
        "overall": {
            "status": overall,
            "icon": overall_icon,
            "fresh": fresh,
            "stale": stale,
            "missing": missing,
            "total": len(results),
            "critical_issues": len(critical_issues),
        },
        "sources": results,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
