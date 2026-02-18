"""
Shared utilities and constants for the API.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import PlainTextResponse

# ── Data source paths (configured via environment variables) ───────────────
SIGNALS_DIR = os.getenv("SIGNALS_DIR", "./data/signals")
ARK_DATA_DIR = os.getenv("ARK_DATA_DIR", "./data/ark")
BACKTEST_DIR = os.getenv("BACKTEST_DIR", "./data/backtest")

HK_STATE_FILE = f"{SIGNALS_DIR}/hk_daily_state.json"
HK_ENTRY_EXIT_FILE = f"{SIGNALS_DIR}/hk_entry_exit.json"
HK_MONTHLY_PICKS_FILE = f"{SIGNALS_DIR}/hk_monthly_picks.json"
CN_TREND_FILE = f"{SIGNALS_DIR}/cn_trend_state.json"
CN_8X30_DIR = f"{SIGNALS_DIR}/cn-8x30"
SECTOR_BT_FILE = f"{BACKTEST_DIR}/sector_neutral_backtest.json"
SIGNAL_LOG = f"{SIGNALS_DIR}/signal_log.jsonl"

from api.config import DATA_DIR
STATIC_DIR = Path(__file__).parent.parent / "frontend" / "static"


# ── Helper Functions ───────────────────────────────────────────────────────
def read_json(path: str) -> Any:
    """Read a JSON file, return None on error."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def read_jsonl(path: str, limit: int = 100) -> list:
    """Read last N lines of a JSONL file."""
    try:
        lines = Path(path).read_text().strip().splitlines()
        result = []
        for line in lines[-limit:]:
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return result
    except Exception:
        return []


def file_mtime(path: str) -> str | None:
    """Get file modification time as ISO string."""
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return None


def markdown_response(data: dict, formatter) -> PlainTextResponse:
    """Convert JSON dict to Markdown response using the given formatter.

    Inspired by Cloudflare's Markdown for Agents.
    Usage in endpoints:
        if "text/markdown" in request.headers.get("accept", ""):
            return markdown_response(result, format_congress_trades)
        return result
    """
    markdown_text = formatter(data)
    token_estimate = int(len(markdown_text.split()) * 0.75)
    return PlainTextResponse(
        content=markdown_text,
        media_type="text/markdown; charset=utf-8",
        headers={
            "x-markdown-tokens": str(token_estimate),
            "x-source-format": "json",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        }
    )


def wants_markdown(request: Request) -> bool:
    """Check if client sent Accept: text/markdown."""
    return "text/markdown" in request.headers.get("accept", "")


# ── Global Instances ───────────────────────────────────────────────────────
from api.config import DATA_DIR as SMART_MONEY_DATA_DIR
from api.modules.cache_manager import CacheManager
from api.ticker_lookup import TickerNameLookup

smart_money_cache = CacheManager(str(SMART_MONEY_DATA_DIR))
ticker_names = TickerNameLookup(smart_money_cache)
