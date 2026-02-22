"""
Crypto Market Intelligence — CoinGlass Data
Reads from /app/data/coinglass/*.json (bind mount from rsnest)

Endpoints:
  GET /api/crypto/overview    — Dashboard summary (OI table, F&G current)
  GET /api/crypto/derivatives — Full derivatives detail (OI + funding + options)
  GET /api/crypto/etf         — Convenience alias → /api/us/etf-flows?category=crypto
  GET /api/crypto/fear-greed  — F&G time series (last 90 entries + BTC prices)
"""
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Data path ────────────────────────────────────────────────────────────────
COINGLASS_DIR = Path("/app/data/coinglass")

# ── In-memory TTL cache (5 minutes) ─────────────────────────────────────────
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 300  # seconds


def _cached(key: str) -> Any | None:
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None


def _set_cache(key: str, val: Any) -> None:
    _cache[key] = (time.time(), val)


# ── JSON loaders ─────────────────────────────────────────────────────────────

def _load_json(filename: str) -> dict | None:
    """Load a JSON file from the coinglass data directory. Returns None on error."""
    path = COINGLASS_DIR / filename
    try:
        import orjson
        return orjson.loads(path.read_bytes())
    except FileNotFoundError:
        logger.warning(f"[crypto] Missing data file: {path}")
        return None
    except Exception as e:
        logger.error(f"[crypto] Error loading {filename}: {e}")
        return None


# ── Data builders ─────────────────────────────────────────────────────────────

def _build_overview() -> dict:
    """
    Dashboard summary:
    - Top coins OI table (from oi_overview.json)
    - Total OI
    - BTC/ETH highlights
    - Fear & Greed current value (last entry from fear_greed.json)
    """
    cached = _cached("overview_v1")
    if cached:
        return cached

    # ── OI Overview ──────────────────────────────────────────────────────────
    oi_data = _load_json("oi_overview.json")
    coins: list[dict] = []
    total_oi: float | None = None
    oi_collected_at: str | None = None
    btc_highlight: dict = {}
    eth_highlight: dict = {}

    if oi_data:
        coins = oi_data.get("coins", [])
        total_oi = oi_data.get("total_oi")
        oi_collected_at = oi_data.get("collected_at")

        # BTC / ETH highlights
        for coin in coins:
            sym = (coin.get("symbol") or "").upper()
            highlight = {
                "symbol": sym,
                "openInterest": coin.get("openInterest"),
                "avgFundingRate": coin.get("avgFundingRate"),
                "h1OIChange": coin.get("h1OIChange"),
                "h4OIChange": coin.get("h4OIChange"),
                "h24OIChange": coin.get("h24OIChange"),
                "oiChange7d": coin.get("oiChange7d"),
                "oiChange30d": coin.get("oiChange30d"),
                "oiVolRatio": coin.get("oiVolRatio"),
                "volUsd": coin.get("volUsd"),
            }
            if sym == "BTC":
                btc_highlight = highlight
            elif sym == "ETH":
                eth_highlight = highlight

    # ── Fear & Greed (last entry only) ───────────────────────────────────────
    fg_current: dict = {}
    fg_collected_at: str | None = None
    fg_data = _load_json("fear_greed.json")
    if fg_data:
        fg_collected_at = fg_data.get("collected_at")
        dl = fg_data.get("data_list", [])
        tl = fg_data.get("time_list", [])
        pl = fg_data.get("price_list", [])
        if dl:
            fg_current = {
                "value": dl[-1],
                "timestamp_ms": tl[-1] if tl else None,
                "btc_price": pl[-1] if pl else None,
                "label": _fg_label(dl[-1]),
            }

    result = {
        "total_oi": total_oi,
        "coins": coins,
        "btc": btc_highlight,
        "eth": eth_highlight,
        "fear_greed": fg_current,
        "metadata": {
            "oi_collected_at": oi_collected_at,
            "fear_greed_collected_at": fg_collected_at,
            "coin_count": len(coins),
        },
    }

    _set_cache("overview_v1", result)
    return result


def _build_derivatives() -> dict:
    """
    Full derivatives detail:
    - OI by coin (oi_overview.json)
    - Funding rates — current only, deduplicated per exchange (funding_rates.json)
    - Options data (options_overview.json)
    """
    cached = _cached("derivatives_v1")
    if cached:
        return cached

    # ── OI ───────────────────────────────────────────────────────────────────
    oi_data = _load_json("oi_overview.json")
    coins: list[dict] = []
    total_oi: float | None = None
    oi_collected_at: str | None = None
    if oi_data:
        coins = oi_data.get("coins", [])
        total_oi = oi_data.get("total_oi")
        oi_collected_at = oi_data.get("collected_at")

    # ── Funding Rates ────────────────────────────────────────────────────────
    # New format: each coin key maps to a list of exchange entries (already deduped).
    # Old format: each coin key maps to {"exchanges": [...]} (with historical data).
    funding_rates: dict[str, list[dict]] = {}
    fr_collected_at: str | None = None
    fr_data = _load_json("funding_rates.json")
    if fr_data:
        fr_collected_at = fr_data.get("collected_at")
        for coin_sym, coin_obj in fr_data.items():
            if coin_sym == "collected_at":
                continue
            if isinstance(coin_obj, list):
                # New format: already a clean list of exchange entries
                funding_rates[coin_sym] = coin_obj
            elif isinstance(coin_obj, dict):
                # Old format: {"exchanges": [...]} — dedup by last-write-wins
                exchanges_raw = coin_obj.get("exchanges", [])
                latest_per_exchange: dict[str, dict] = {}
                for entry in exchanges_raw:
                    name = entry.get("name")
                    if name:
                        latest_per_exchange[name] = entry
                funding_rates[coin_sym] = list(latest_per_exchange.values())

    # ── Options ──────────────────────────────────────────────────────────────
    options: dict[str, dict] = {}
    opt_collected_at: str | None = None
    opt_data = _load_json("options_overview.json")
    if opt_data:
        opt_collected_at = opt_data.get("collected_at")
        for coin_sym, coin_obj in opt_data.items():
            if coin_sym == "collected_at":
                continue
            if isinstance(coin_obj, dict):
                options[coin_sym] = {
                    "exchanges": coin_obj.get("exchanges", []),
                    "totals": coin_obj.get("totals", {}),
                }

    result = {
        "total_oi": total_oi,
        "coins": coins,
        "funding_rates": funding_rates,
        "options": options,
        "metadata": {
            "oi_collected_at": oi_collected_at,
            "funding_rates_collected_at": fr_collected_at,
            "options_collected_at": opt_collected_at,
            "coin_count": len(coins),
            "funding_coins": list(funding_rates.keys()),
            "options_coins": list(options.keys()),
        },
    }

    _set_cache("derivatives_v1", result)
    return result


def _build_fear_greed(limit: int = 90) -> dict:
    """
    Fear & Greed time series — last `limit` entries with timestamps + BTC prices.
    """
    cache_key = f"fear_greed_v1_{limit}"
    cached = _cached(cache_key)
    if cached:
        return cached

    fg_data = _load_json("fear_greed.json")
    if not fg_data:
        result = {
            "entries": [],
            "current": None,
            "metadata": {"error": "fear_greed.json not found", "collected_at": None},
        }
        _set_cache(cache_key, result)
        return result

    dl = fg_data.get("data_list", [])
    tl = fg_data.get("time_list", [])
    pl = fg_data.get("price_list", [])
    collected_at = fg_data.get("collected_at")

    # Align all three lists to the shortest length
    n = min(len(dl), len(tl), len(pl))
    dl, tl, pl = dl[:n], tl[:n], pl[:n]

    # Slice last `limit` entries
    entries_raw = list(zip(tl[-limit:], dl[-limit:], pl[-limit:]))
    entries = [
        {
            "timestamp_ms": int(ts),
            "date": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d"),
            "value": fg,
            "label": _fg_label(fg),
            "btc_price": btc,
        }
        for ts, fg, btc in entries_raw
    ]

    current = entries[-1] if entries else None

    result = {
        "entries": entries,
        "current": current,
        "metadata": {
            "total_history_days": n,
            "returned_entries": len(entries),
            "collected_at": collected_at,
        },
    }

    _set_cache(cache_key, result)
    return result


def _fg_label(value: float | None) -> str:
    """Map a fear & greed numeric value to its label."""
    if value is None:
        return "Unknown"
    if value <= 20:
        return "Extreme Fear"
    if value <= 40:
        return "Fear"
    if value <= 60:
        return "Neutral"
    if value <= 80:
        return "Greed"
    return "Extreme Greed"


# ── FastAPI Router ────────────────────────────────────────────────────────────

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/api/crypto")


@router.get("/overview")
def api_crypto_overview():
    """
    Crypto Dashboard Summary.
    Returns top coins OI table, total OI, BTC/ETH highlights, and current
    Fear & Greed value.
    Sources: oi_overview.json + fear_greed.json  |  Cache: 5 minutes.
    """
    try:
        return _build_overview()
    except Exception as e:
        logger.error(f"[crypto/overview] {e}", exc_info=True)
        return {
            "error": str(e),
            "total_oi": None,
            "coins": [],
            "btc": {},
            "eth": {},
            "fear_greed": {},
            "metadata": {"collected_at": None},
        }


@router.get("/derivatives")
def api_crypto_derivatives():
    """
    Full Derivatives Detail.
    Returns OI by coin, current funding rates (latest per exchange, no history),
    and options data (OI + volume per exchange).
    Sources: oi_overview.json + funding_rates.json + options_overview.json  |  Cache: 5 minutes.
    """
    try:
        return _build_derivatives()
    except Exception as e:
        logger.error(f"[crypto/derivatives] {e}", exc_info=True)
        return {
            "error": str(e),
            "total_oi": None,
            "coins": [],
            "funding_rates": {},
            "options": {},
            "metadata": {},
        }


@router.get("/etf")
def api_crypto_etf():
    """
    Convenience alias → /api/us/etf-flows?category=crypto
    Redirects to the existing ETF flows endpoint filtered for crypto.
    """
    return RedirectResponse(url="/api/us/etf-flows?category=crypto", status_code=302)


@router.get("/fear-greed")
def api_crypto_fear_greed(limit: int = 90):
    """
    Fear & Greed Time Series.
    Returns the last `limit` entries (default 90) with ISO dates, numeric values,
    label strings, and corresponding BTC prices.
    Source: fear_greed.json  |  Cache: 5 minutes.
    """
    try:
        limit = max(1, min(limit, 365))  # clamp to sane range
        return _build_fear_greed(limit=limit)
    except Exception as e:
        logger.error(f"[crypto/fear-greed] {e}", exc_info=True)
        return {
            "error": str(e),
            "entries": [],
            "current": None,
            "metadata": {"collected_at": None},
        }
