"""
Dividend screener routes
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.modules.dividend_screener import get_screener_data
from api.shared import wants_markdown, markdown_response
from api.markdown_format import MARKDOWN_FORMATTERS

router = APIRouter()

# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/dividend-screener")
def api_dividend_screener_all():
    """Get dividend screener data for all markets. Returns cached data only (no live fetch)."""
    try:
        from api.modules.dividend_screener import load_cache
        cached = load_cache()
        if cached:
            return cached
        return {
            "status": "no_data",
            "message": "Dividend screener cache is empty. Run the screener cron job first.",
            "us": [], "hk": [], "cn": [],
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/api/dividend-screener/{market}")
def api_dividend_screener_market(market: str):
    """Get dividend screener data for specific market (us/hk/cn). Returns cached data only."""
    if market not in ["us", "hk", "cn"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Market must be us, hk, or cn"}
        )
    
    try:
        from api.modules.dividend_screener import load_cache
        cached = load_cache()
        if cached and cached.get(market):
            return {
                "market": market,
                "updated_at": cached.get("updated_at"),
                "stocks": cached.get(market, []),
            }
        return {
            "market": market,
            "status": "no_data",
            "message": f"No cached data for {market}. Run the screener cron job first.",
            "stocks": [],
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

