"""
HK market routes
"""
from fastapi import APIRouter

from api.shared import (
    HK_STATE_FILE, HK_ENTRY_EXIT_FILE, HK_MONTHLY_PICKS_FILE,
    read_json, file_mtime
)

router = APIRouter()

# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/hk/signals")
def api_hk_signals():
    """Current HK Top 7 picks with entry/exit data."""
    state = read_json(HK_STATE_FILE)
    entry_exit = read_json(HK_ENTRY_EXIT_FILE)

    picks = []
    if state and "picks" in state:
        picks = state["picks"]
    elif entry_exit and "signals" in entry_exit:
        picks = entry_exit["signals"]

    ee_map = {}
    if entry_exit and "signals" in entry_exit:
        for s in entry_exit["signals"]:
            ee_map[s.get("ticker")] = s

    merged = []
    for p in picks[:7]:
        ticker = p.get("ticker")
        ee = ee_map.get(ticker, {})
        item = {**p}
        if "entry_score" not in item and "entry_score" in ee:
            item["entry_score"] = ee["entry_score"]
        if "entry_label" not in item and "score_label" in ee:
            item["entry_label"] = ee["score_label"]
        if "exit_levels" not in item and "exit_levels" in ee:
            item["exit_levels"] = ee["exit_levels"]
        if "entry_zone" not in item and "entry_zone" in ee:
            item["entry_zone"] = ee["entry_zone"]
        if "indicators" not in item and "indicators" in ee:
            item["indicators"] = ee["indicators"]
        if "entry_description" not in item and "score_description" in ee:
            item["entry_description"] = ee["score_description"]
        merged.append(item)

    return {
        "date": state.get("date") if state else None,
        "generated_at": (state or entry_exit or {}).get("generated_at"),
        "picks": merged,
        "updated_at": file_mtime(HK_STATE_FILE),
    }

@router.get("/api/hk/history")
def api_hk_history():
    """Monthly picks + full ranking for historical context."""
    monthly = read_json(HK_MONTHLY_PICKS_FILE)
    if not monthly:
        return {"picks": [], "updated_at": None}
    return {
        "strategy": monthly.get("strategy"),
        "universe": monthly.get("universe"),
        "top_n": monthly.get("top_n"),
        "warnings": monthly.get("warnings", []),
        "picks": monthly.get("picks", [])[:30],
        "updated_at": file_mtime(HK_MONTHLY_PICKS_FILE),
    }

