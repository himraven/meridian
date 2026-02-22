"""
Macro / Market Regime routes — Regime Detector, Crisis Dashboard, Cross-Asset Signals
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ── In-memory TTL cache (avoid hammering yfinance/FRED) ─────────────────────
_cache: dict[str, tuple[float, Any]] = {}

def _cached(key: str, ttl_seconds: int):
    """Return cached value if fresh, else None."""
    if key in _cache:
        ts, val = _cache[key]
        if time.time() - ts < ttl_seconds:
            return val
    return None

def _set_cache(key: str, val: Any):
    _cache[key] = (time.time(), val)


# ── Data fetchers ────────────────────────────────────────────────────────────

def _fetch_yf(ticker: str, period: str = "1y", interval: str = "1d") -> list[dict]:
    """Fetch OHLCV from Yahoo Finance via yfinance."""
    try:
        import yfinance as yf
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df is None or df.empty:
            return []
        df = df.reset_index()
        # Flatten MultiIndex columns if any
        if hasattr(df.columns, 'levels'):
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        rows = []
        for _, row in df.iterrows():
            try:
                date_val = row.get("Date") or row.get("Datetime")
                close_val = row.get("Close")
                if date_val is None or close_val is None:
                    continue
                rows.append({
                    "date": str(date_val)[:10],
                    "close": float(close_val),
                })
            except Exception:
                continue
        return rows
    except Exception as e:
        logger.warning(f"[yfinance] {ticker} fetch error: {e}")
        return []


def _fetch_yf_latest(ticker: str) -> float | None:
    """Get latest close price for a ticker."""
    rows = _fetch_yf(ticker, period="5d", interval="1d")
    if not rows:
        return None
    # Return most recent non-null close
    for row in reversed(rows):
        v = row.get("close")
        if v and v > 0:
            return float(v)
    return None


def _fetch_fred_series(series_id: str) -> list[dict]:
    """Fetch a FRED data series as list of {date, value}."""
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "meridian/1.0"})
        resp.raise_for_status()
        rows = []
        for line in resp.text.splitlines()[1:]:  # skip header
            parts = line.split(",")
            if len(parts) >= 2:
                date_str, val_str = parts[0].strip(), parts[1].strip()
                try:
                    val = float(val_str)
                    rows.append({"date": date_str, "value": val})
                except ValueError:
                    continue
        return rows
    except Exception as e:
        logger.warning(f"[FRED] {series_id} fetch error: {e}")
        return []


def _fred_latest(series_id: str) -> float | None:
    """Get the most recent value from a FRED series."""
    rows = _fetch_fred_series(series_id)
    for row in reversed(rows):
        v = row.get("value")
        if v is not None and str(v) not in (".", ""):
            return float(v)
    return None


# ── Regime helpers ───────────────────────────────────────────────────────────

def _compute_ma(prices: list[float], window: int) -> float | None:
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window


def _get_regime_data() -> dict:
    """Compute market regime. Cached 1 hour."""
    CACHE_KEY = "regime_v1"
    cached = _cached(CACHE_KEY, 3600)
    if cached:
        return cached

    # --- VIX ---
    vix_val = _fetch_yf_latest("^VIX")
    if vix_val is None:
        vix_val = 20.0  # fallback neutral
    if vix_val < 20:
        vix_status, vix_label = "green", "Normal"
    elif vix_val < 30:
        vix_status, vix_label = "yellow", "Elevated"
    else:
        vix_status, vix_label = "red", "Crisis"

    # --- SPY vs MA200 ---
    spy_rows = _fetch_yf("SPY", period="2y", interval="1d")
    spy_closes = [r["close"] for r in spy_rows if r.get("close")]
    spy_current = spy_closes[-1] if spy_closes else None
    ma200 = _compute_ma(spy_closes, 200)
    if spy_current and ma200:
        pct_above = (spy_current - ma200) / ma200 * 100
        spy_status = "bullish" if spy_current > ma200 else "bearish"
    else:
        pct_above = 0.0
        spy_status = "neutral"

    # --- Credit Spread (BAMLH0A0HYM2 from FRED) ---
    spread_val = _fred_latest("BAMLH0A0HYM2")
    if spread_val is None:
        spread_val = 4.0  # fallback neutral
    if spread_val < 4:
        spread_status, spread_label = "green", "Normal"
    elif spread_val < 6:
        spread_status, spread_label = "yellow", "Elevated"
    else:
        spread_status, spread_label = "red", "Crisis"

    # --- Overall regime ---
    statuses = [vix_status, "green" if spy_status == "bullish" else "yellow", spread_status]
    red_count = statuses.count("red")
    yellow_count = statuses.count("yellow")
    if red_count >= 1:
        overall = "red"
    elif yellow_count >= 2:
        overall = "yellow"
    elif yellow_count >= 1:
        overall = "yellow"
    else:
        overall = "green"

    # Summary text
    summaries = {
        "green": "All indicators normal — risk-on environment",
        "yellow": "Mixed signals — exercise caution",
        "red": "Multiple risk indicators elevated — defensive posture warranted",
    }

    result = {
        "regime": overall,
        "summary": summaries[overall],
        "components": {
            "vix": {
                "value": round(vix_val, 2),
                "status": vix_status,
                "label": vix_label,
                "thresholds": {"green": "<20", "yellow": "20-30", "red": ">30"},
            },
            "spy_ma200": {
                "spy_price": round(spy_current, 2) if spy_current else None,
                "ma200": round(ma200, 2) if ma200 else None,
                "pct_above": round(pct_above, 2),
                "status": spy_status,
                "label": "Above MA200" if spy_status == "bullish" else "Below MA200",
            },
            "credit_spread": {
                "value": round(spread_val, 2),
                "status": spread_status,
                "label": spread_label,
                "thresholds": {"green": "<4%", "yellow": "4-6%", "red": ">6%"},
                "series": "BAMLH0A0HYM2",
                "description": "ICE BofA High Yield OAS",
            },
        },
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    _set_cache(CACHE_KEY, result)
    return result


# ── Crisis data ───────────────────────────────────────────────────────────────

def _get_vix_stats() -> dict:
    """VIX historical stats — current, 1Y avg, 5Y avg."""
    rows = _fetch_yf("^VIX", period="5y", interval="1d")
    if not rows:
        return {"current": None, "avg_1y": None, "avg_5y": None}
    closes = [r["close"] for r in rows if r.get("close") and r["close"] > 0]
    current = closes[-1] if closes else None
    avg_1y = sum(closes[-252:]) / len(closes[-252:]) if len(closes) >= 252 else (sum(closes) / len(closes) if closes else None)
    avg_5y = sum(closes) / len(closes) if closes else None

    # Categorize
    if current is None:
        regime = "unknown"
    elif current < 20:
        regime = "calm"
    elif current < 25:
        regime = "elevated"
    elif current < 35:
        regime = "fearful"
    else:
        regime = "crisis"

    return {
        "current": round(current, 2) if current else None,
        "avg_1y": round(avg_1y, 2) if avg_1y else None,
        "avg_5y": round(avg_5y, 2) if avg_5y else None,
        "regime": regime,
        "is_elevated": current is not None and current >= 25,
    }


def _get_crisis_data() -> dict:
    """Compute crisis dashboard data. Cached 30 minutes."""
    CACHE_KEY = "crisis_v1"
    cached = _cached(CACHE_KEY, 1800)
    if cached:
        return cached

    # VIX stats
    vix = _get_vix_stats()

    # Smart money signals from existing JSON files
    from api.shared import smart_money_cache

    smart_money = []

    # Congress
    congress_data = smart_money_cache.read("congress.json")
    if congress_data and "trades" in congress_data:
        trades = congress_data["trades"]
        cutoff = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
        recent = [t for t in trades if (t.get("transaction_date") or "") >= cutoff]
        buys = sum(1 for t in recent if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
        sells = sum(1 for t in recent if (t.get("trade_type") or "").lower() in ("sell", "sale"))
        net_buying = buys > sells
        smart_money.append({
            "source": "congress",
            "label": "Congress",
            "buy_count": buys,
            "sell_count": sells,
            "net_buying": net_buying,
            "sentiment": "bullish" if net_buying else "bearish",
            "weight": 25,
        })

    # Insiders
    insider_data = smart_money_cache.read("insiders.json")
    if insider_data and "trades" in insider_data:
        trades = insider_data["trades"]
        cutoff = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
        recent = [t for t in trades if (t.get("trade_date") or t.get("filing_date", "")) >= cutoff]
        buys = sum(1 for t in recent if (t.get("transaction_type") or "").lower() == "buy")
        sells = sum(1 for t in recent if (t.get("transaction_type") or "").lower() in ("sale", "sell"))
        net_buying = buys > sells
        smart_money.append({
            "source": "insider",
            "label": "Insiders",
            "buy_count": buys,
            "sell_count": sells,
            "net_buying": net_buying,
            "sentiment": "bullish" if net_buying else "bearish",
            "weight": 25,
        })

    # ARK
    ark_data = smart_money_cache.read("ark_trades.json")
    if ark_data and "trades" in ark_data:
        trades = ark_data["trades"]
        cutoff = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        recent = [t for t in trades if (t.get("date") or "") >= cutoff]
        buys = sum(1 for t in recent if (t.get("trade_type") or "").lower() == "buy")
        sells = sum(1 for t in recent if (t.get("trade_type") or "").lower() == "sell")
        net_buying = buys > sells
        smart_money.append({
            "source": "ark",
            "label": "ARK Invest",
            "buy_count": buys,
            "sell_count": sells,
            "net_buying": net_buying,
            "sentiment": "bullish" if net_buying else "bearish",
            "weight": 15,
        })

    # 13F (use institutions.json if available, else ark_data 13f)
    inst_data = smart_money_cache.read("institutions.json")
    if inst_data and "filings" in inst_data:
        # 13F: use total value comparison as proxy for buying
        filings = inst_data["filings"]
        total_holdings = sum(f.get("total_holdings", 0) for f in filings)
        # We'll treat as bullish if any major institution has recent filing
        recent_filings = [f for f in filings if (f.get("filing_date") or "") >= (datetime.utcnow() - timedelta(days=120)).strftime("%Y-%m-%d")]
        smart_money.append({
            "source": "institution",
            "label": "Institutions (13F)",
            "buy_count": len(recent_filings),
            "sell_count": 0,
            "net_buying": len(recent_filings) > 0,
            "sentiment": "bullish" if recent_filings else "neutral",
            "weight": 20,
        })

    # Dark Pool
    dp_data = smart_money_cache.read("darkpool.json")
    if dp_data and "tickers" in dp_data:
        tickers = dp_data["tickers"]
        cutoff = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent = [t for t in tickers if (t.get("date") or "") >= cutoff]
        # High DPI (>0.5) with high z-score indicates unusual buying
        anomalies = [t for t in recent if (t.get("z_score") or 0) >= 2.0]
        smart_money.append({
            "source": "darkpool",
            "label": "Dark Pool",
            "buy_count": len(anomalies),
            "sell_count": 0,
            "net_buying": len(anomalies) > 5,
            "sentiment": "bullish" if len(anomalies) > 5 else "neutral",
            "weight": 15,
        })

    # Crisis Conviction Score
    weights = {"congress": 25, "insider": 25, "ark": 15, "institution": 20, "darkpool": 15}
    score = 0
    for sm in smart_money:
        if sm["net_buying"]:
            score += sm["weight"]

    # Historical crisis playbook (static data)
    historical_playbook = [
        {
            "event": "COVID Crash",
            "date": "2020-03",
            "vix_peak": 82.7,
            "spy_drawdown": -34.0,
            "return_6m": 51.5,
            "return_12m": 75.2,
            "lesson": "Largest VIX spike in history. Unprecedented fiscal stimulus drove fastest recovery ever.",
        },
        {
            "event": "2022 Rate Shock",
            "date": "2022-06",
            "vix_peak": 36.4,
            "spy_drawdown": -24.5,
            "return_6m": 12.5,
            "return_12m": 26.3,
            "lesson": "Fed's fastest rate hike cycle in 40 years. Growth/tech sold hard; value outperformed.",
        },
        {
            "event": "Aug 2024 Vol Spike",
            "date": "2024-08",
            "vix_peak": 65.7,
            "spy_drawdown": -8.5,
            "return_6m": 18.2,
            "return_12m": None,
            "lesson": "Yen carry trade unwind. Spike was fast and sharp — VIX mean-reverted in days.",
        },
        {
            "event": "GFC Bottom",
            "date": "2009-03",
            "vix_peak": 80.7,
            "spy_drawdown": -57.0,
            "return_6m": 49.7,
            "return_12m": 68.6,
            "lesson": "Greatest buying opportunity of the century. Insider and Congress buying clustered at lows.",
        },
        {
            "event": "2018 Q4 Selloff",
            "date": "2018-12",
            "vix_peak": 36.2,
            "spy_drawdown": -20.2,
            "return_6m": 24.0,
            "return_12m": 31.5,
            "lesson": "Fed pivot concerns. Powell reversed course → immediate recovery in Q1 2019.",
        },
    ]

    result = {
        "vix": vix,
        "conviction_score": score,
        "conviction_label": "Strong Buy" if score >= 75 else "Buy" if score >= 50 else "Mixed" if score >= 25 else "Defensive",
        "smart_money_signals": smart_money,
        "is_crisis": vix.get("is_elevated", False),
        "historical_playbook": historical_playbook,
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    _set_cache(CACHE_KEY, result)
    return result


# ── Cross-asset data ─────────────────────────────────────────────────────────

def _compute_rolling_correlation(series_a: list[float], series_b: list[float], window: int) -> float | None:
    """Compute rolling correlation for the last `window` periods."""
    if len(series_a) < window or len(series_b) < window:
        return None
    try:
        import numpy as np
        a = np.array(series_a[-window:])
        b = np.array(series_b[-window:])
        corr = np.corrcoef(a, b)[0, 1]
        return round(float(corr), 4) if not (corr != corr) else None  # NaN check
    except Exception:
        return None


def _align_series(rows_a: list[dict], rows_b: list[dict]) -> tuple[list[float], list[float]]:
    """Align two price series by date, returning (closes_a, closes_b)."""
    dates_a = {r["date"]: r["close"] for r in rows_a if r.get("date") and r.get("close")}
    dates_b = {r["date"]: r["close"] for r in rows_b if r.get("date") and r.get("close")}
    common_dates = sorted(set(dates_a) & set(dates_b))
    a = [dates_a[d] for d in common_dates]
    b = [dates_b[d] for d in common_dates]
    return a, b


def _get_cross_asset_data() -> dict:
    """Compute cross-asset signals. Cached 1 hour."""
    CACHE_KEY = "cross_asset_v1"
    cached = _cached(CACHE_KEY, 3600)
    if cached:
        return cached

    # --- Gold vs BTC correlation ---
    gld_rows = _fetch_yf("GLD", period="1y", interval="1d")
    btc_rows = _fetch_yf("BTC-USD", period="1y", interval="1d")

    gld_closes, btc_closes = _align_series(gld_rows, btc_rows)
    corr_30 = _compute_rolling_correlation(gld_closes, btc_closes, 30)
    corr_90 = _compute_rolling_correlation(gld_closes, btc_closes, 90)
    corr_180 = _compute_rolling_correlation(gld_closes, btc_closes, 180)

    # Mini-chart data for BTC and Gold (last 90 days)
    gld_chart = [{"date": r["date"], "value": round(r["close"], 2)} for r in gld_rows[-90:] if r.get("close")]
    btc_chart = [{"date": r["date"], "value": round(r["close"], 0)} for r in btc_rows[-90:] if r.get("close")]

    # --- M2 Money Supply ---
    m2_rows = _fetch_fred_series("M2SL")
    m2_current = None
    m2_yoy = None
    m2_chart = []
    if m2_rows:
        # M2 is monthly — last value
        valid_m2 = [r for r in m2_rows if r.get("value") is not None and str(r.get("value", "")) not in (".", "")]
        if valid_m2:
            m2_current = valid_m2[-1]["value"]
            # YoY growth: compare to ~12 rows back
            if len(valid_m2) >= 13:
                m2_1y_ago = valid_m2[-13]["value"]
                if m2_1y_ago and m2_1y_ago > 0:
                    m2_yoy = round((m2_current - m2_1y_ago) / m2_1y_ago * 100, 2)
            # Chart: last 36 months
            m2_chart = [{"date": r["date"], "value": round(r["value"], 1)}
                        for r in valid_m2[-36:] if r.get("value")]

    # --- Treasury Yields (GS2 and GS10 from FRED) ---
    gs2_rows = _fetch_fred_series("GS2")
    gs10_rows = _fetch_fred_series("GS10")

    def _fred_latest_from_rows(rows: list[dict]) -> float | None:
        valid = [r for r in rows if r.get("value") is not None and str(r.get("value", "")) not in (".", "")]
        return valid[-1]["value"] if valid else None

    yield_2y = _fred_latest_from_rows(gs2_rows)
    yield_10y = _fred_latest_from_rows(gs10_rows)
    spread = round(yield_10y - yield_2y, 2) if (yield_10y and yield_2y) else None
    yield_status = "inverted" if (spread is not None and spread < 0) else "normal"

    # Yield curve chart: last 24 months of 10Y-2Y spread
    gs2_dict = {r["date"]: r["value"] for r in gs2_rows if r.get("value") is not None and str(r.get("value")) not in (".", "")}
    gs10_dict = {r["date"]: r["value"] for r in gs10_rows if r.get("value") is not None and str(r.get("value")) not in (".", "")}
    common_yield_dates = sorted(set(gs2_dict) & set(gs10_dict))[-24:]
    yield_chart = [
        {
            "date": d,
            "yield_2y": round(gs2_dict[d], 2),
            "yield_10y": round(gs10_dict[d], 2),
            "spread": round(gs10_dict[d] - gs2_dict[d], 2),
        }
        for d in common_yield_dates
    ]

    # --- Fear & Greed proxy (VIX-based) ---
    vix_val = _fetch_yf_latest("^VIX")
    if vix_val is None:
        vix_val = 20.0
    if vix_val < 12:
        fg_label, fg_score = "Extreme Greed", min(95, 100 - int(vix_val * 3))
    elif vix_val < 20:
        fg_label, fg_score = "Greed", min(75, 100 - int(vix_val * 3))
    elif vix_val < 25:
        fg_label, fg_score = "Neutral", 50
    elif vix_val < 30:
        fg_label, fg_score = "Fear", max(30, 50 - int((vix_val - 25) * 4))
    else:
        fg_label, fg_score = "Extreme Fear", max(5, 30 - int((vix_val - 30) * 2))

    # BTC latest price
    btc_latest = _fetch_yf_latest("BTC-USD")
    gld_latest = _fetch_yf_latest("GLD")

    result = {
        "gold_btc_correlation": {
            "30d": corr_30,
            "90d": corr_90,
            "180d": corr_180,
            "gld_price": round(gld_latest, 2) if gld_latest else None,
            "btc_price": round(btc_latest, 0) if btc_latest else None,
            "gld_chart": gld_chart,
            "btc_chart": btc_chart,
        },
        "m2": {
            "current": round(m2_current, 1) if m2_current else None,
            "unit": "billions USD",
            "yoy_growth_pct": m2_yoy,
            "chart": m2_chart,
            "series": "M2SL",
        },
        "treasury_yields": {
            "yield_2y": round(yield_2y, 2) if yield_2y else None,
            "yield_10y": round(yield_10y, 2) if yield_10y else None,
            "spread": spread,
            "status": yield_status,
            "label": "Inverted Yield Curve" if yield_status == "inverted" else "Normal Yield Curve",
            "chart": yield_chart,
        },
        "fear_greed": {
            "vix": round(vix_val, 2),
            "label": fg_label,
            "score": fg_score,
            "narrative": _fear_greed_narrative(fg_label, vix_val),
        },
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    _set_cache(CACHE_KEY, result)
    return result


def _fear_greed_narrative(label: str, vix: float) -> str:
    narratives = {
        "Extreme Greed": f"VIX at {vix:.1f} — markets pricing near-zero fear. Historically precedes volatility spikes.",
        "Greed": f"VIX at {vix:.1f} — complacent environment. Risk assets typically well-bid.",
        "Neutral": f"VIX at {vix:.1f} — balanced fear/greed. Market participants in wait-and-see mode.",
        "Fear": f"VIX at {vix:.1f} — elevated anxiety. Smart money historically uses dips to accumulate.",
        "Extreme Fear": f"VIX at {vix:.1f} — panic conditions. Historically strong medium-term buy signal.",
    }
    return narratives.get(label, f"VIX at {vix:.1f}")


# ── Crypto Signals data ──────────────────────────────────────────────────────

# Crypto stocks: companies whose core business IS crypto
CRYPTO_STOCKS = {
    "COIN",  # Coinbase — crypto exchange
    "MSTR",  # MicroStrategy — BTC treasury company
    "MARA",  # Marathon Digital — BTC miner
    "RIOT",  # Riot Platforms — BTC miner
    "CLSK",  # CleanSpark — BTC miner
    "HUT",   # Hut 8 — BTC miner
    "BTBT",  # Bit Digital — BTC miner
    "CIFR",  # Cipher Mining — BTC miner
    "CORZ",  # Core Scientific — BTC miner / AI HPC
    "IREN",  # Iris Energy — BTC miner / AI
    "WULF",  # TeraWulf — BTC miner
}

# Hardcoded company names for crypto stocks (fallback when data sources lack them)
CRYPTO_STOCK_NAMES = {
    "COIN": "Coinbase Global Inc",
    "MSTR": "MicroStrategy Inc.",
    "MARA": "Marathon Digital Holdings",
    "RIOT": "Riot Platforms Inc.",
    "CLSK": "CleanSpark Inc.",
    "HUT": "Hut 8 Corp.",
    "BTBT": "Bit Digital Inc.",
    "CIFR": "Cipher Mining Inc.",
    "CORZ": "Core Scientific Inc.",
    "IREN": "Iris Energy Ltd.",
    "WULF": "TeraWulf Inc.",
}

# Crypto ETFs: pass-through vehicles tracking crypto assets
CRYPTO_ETFS = {
    "IBIT",  # iShares Bitcoin Trust (BlackRock)
    "GBTC",  # Grayscale Bitcoin Trust
    "FBTC",  # Fidelity Wise Origin Bitcoin Fund
    "ARKB",  # ARK 21Shares Bitcoin ETF
    "BITO",  # ProShares Bitcoin Strategy ETF
    "BITB",  # Bitwise Bitcoin ETF
    "ETHE",  # Grayscale Ethereum Trust
    "ETHU",  # ProShares Ultra Ether ETF
    "BITX",  # 2x Bitcoin Strategy ETF
    "MSTU",  # T-Rex 2X Long MSTR Daily Target ETF
    "MSTZ",  # T-Rex 2X Inverse MSTR Daily Target ETF
    "CONL",  # GraniteShares 2X Long COIN Daily ETF
}

CRYPTO_TICKERS = CRYPTO_STOCKS | CRYPTO_ETFS


def _get_crypto_prices() -> dict:
    """Fetch BTC and ETH current prices + 90d charts."""
    btc_rows = _fetch_yf("BTC-USD", period="3mo", interval="1d")
    eth_rows = _fetch_yf("ETH-USD", period="3mo", interval="1d")

    def _extract(rows: list[dict]) -> dict:
        if not rows:
            return {"price": None, "change_24h_pct": None, "chart_90d": []}
        valid = [r for r in rows if r.get("close") and r["close"] > 0]
        price = valid[-1]["close"] if valid else None
        prev = valid[-2]["close"] if len(valid) >= 2 else None
        change = round((price - prev) / prev * 100, 2) if (price and prev) else None
        chart = [{"date": r["date"], "value": round(r["close"], 2)} for r in valid]
        return {
            "price": round(price, 2) if price else None,
            "change_24h_pct": change,
            "chart_90d": chart,
        }

    return {
        "btc": _extract(btc_rows),
        "eth": _extract(eth_rows),
    }


def _get_crypto_signals_data() -> dict:
    """Aggregate all crypto-relevant data from existing sources. Cached 30 minutes."""
    CACHE_KEY = "crypto_signals_v1"
    cached = _cached(CACHE_KEY, 1800)
    if cached:
        return cached

    from api.shared import smart_money_cache

    # --- BTC / ETH Prices ---
    crypto_prices = _get_crypto_prices()

    # --- ARK Trades (crypto stocks + ETFs, but tag them) ---
    ark_trades = []
    ark_data = smart_money_cache.read("ark_trades.json")
    if ark_data and "trades" in ark_data:
        for t in ark_data["trades"]:
            tk = (t.get("ticker") or "").upper()
            if tk not in CRYPTO_TICKERS:
                continue
            # Skip ARK rebalancing its own ETF (ARKB in ARKW/ARKF = internal move)
            if tk == "ARKB":
                continue
            trade = {**t, "category": "stock" if tk in CRYPTO_STOCKS else "etf"}
            ark_trades.append(trade)
        ark_trades.sort(key=lambda t: t.get("date", ""), reverse=True)
        ark_trades = ark_trades[:50]

    # --- Insider Trades (crypto STOCKS only) ---
    insider_trades = []
    insider_data = smart_money_cache.read("insiders.json")
    if insider_data and "trades" in insider_data:
        insider_trades = [
            t for t in insider_data["trades"]
            if (t.get("ticker") or "").upper() in CRYPTO_STOCKS
        ]
        insider_trades.sort(key=lambda t: t.get("trade_date") or t.get("filing_date", ""), reverse=True)
        insider_trades = insider_trades[:30]

    # --- Dark Pool (crypto STOCKS only) ---
    darkpool = []
    dp_data = smart_money_cache.read("darkpool.json")
    if dp_data and "tickers" in dp_data:
        darkpool = [
            t for t in dp_data["tickers"]
            if (t.get("ticker") or "").upper() in CRYPTO_STOCKS
        ]
        darkpool.sort(key=lambda t: t.get("dpi", 0), reverse=True)

    # --- Short Interest (crypto STOCKS only — ETF short interest is different dynamic) ---
    short_interest = []
    si_data = smart_money_cache.read("short_interest.json")
    if si_data and "tickers" in si_data:
        short_interest = [
            t for t in si_data["tickers"]
            if (t.get("ticker") or "").upper() in CRYPTO_STOCKS
        ]
        short_interest.sort(key=lambda t: t.get("short_interest", 0) or 0, reverse=True)

    # --- Smart Money Signals (crypto STOCKS only — ETFs are noise here) ---
    smart_money_signals = []
    sig_data = smart_money_cache.read("signals_v2.json")
    if sig_data and "signals" in sig_data:
        smart_money_signals = [
            s for s in sig_data["signals"]
            if (s.get("ticker") or "").upper() in CRYPTO_STOCKS
        ]
        smart_money_signals.sort(key=lambda s: s.get("score", 0) or 0, reverse=True)

    # Enrich missing company names
    for sig in smart_money_signals:
        if not sig.get("company"):
            sig["company"] = CRYPTO_STOCK_NAMES.get((sig.get("ticker") or "").upper(), "")

    # --- Congress Trades (crypto tickers) ---
    congress_trades = []
    congress_data = smart_money_cache.read("congress.json")
    if congress_data and "trades" in congress_data:
        congress_trades = [
            t for t in congress_data["trades"]
            if (t.get("ticker") or "").upper() in CRYPTO_TICKERS
        ]
        congress_trades.sort(key=lambda t: t.get("transaction_date", ""), reverse=True)
        congress_trades = congress_trades[:20]

    # --- Institution Holdings (crypto tickers) ---
    institution_holdings = []
    inst_data = smart_money_cache.read("institutions.json")
    if inst_data and "filings" in inst_data:
        for filing in inst_data["filings"]:
            for holding in filing.get("holdings", []):
                if (holding.get("ticker") or "").upper() in CRYPTO_TICKERS:
                    institution_holdings.append({
                        **holding,
                        "institution": filing.get("fund_name") or filing.get("company_name", ""),
                        "filing_date": filing.get("filing_date", ""),
                        "quarter": filing.get("quarter", ""),
                    })
        institution_holdings.sort(key=lambda h: h.get("value", 0) or 0, reverse=True)
        institution_holdings = institution_holdings[:30]

    # --- Summary ---
    bullish_signals = sum(
        1 for s in smart_money_signals
        if (s.get("direction") or "").lower() == "bullish"
    )
    bearish_signals = sum(
        1 for s in smart_money_signals
        if (s.get("direction") or "").lower() == "bearish"
    )

    # Most active ticker (by ARK trades + insider + darkpool mentions combined)
    ticker_counts: dict[str, int] = {}
    for t in ark_trades:
        tk = (t.get("ticker") or "").upper()
        if tk:
            ticker_counts[tk] = ticker_counts.get(tk, 0) + 1
    for t in insider_trades:
        tk = (t.get("ticker") or "").upper()
        if tk:
            ticker_counts[tk] = ticker_counts.get(tk, 0) + 1
    for t in darkpool:
        tk = (t.get("ticker") or "").upper()
        if tk:
            ticker_counts[tk] = ticker_counts.get(tk, 0) + 2
    most_active = max(ticker_counts, key=lambda k: ticker_counts[k]) if ticker_counts else ""

    # Build narrative
    narrative_parts = []
    ark_30d = [
        t for t in ark_trades
        if (t.get("date") or "") >= (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    ]
    if ark_30d:
        # Count actual buy vs sell for accurate narrative
        ark_buys = sum(1 for t in ark_30d if t.get("trade_type") == "Buy"
                       or t.get("change_type") in ("INCREASED", "NEW_POSITION"))
        ark_sells = sum(1 for t in ark_30d if t.get("trade_type") == "Sell"
                        or t.get("change_type") in ("DECREASED", "SOLD_OUT"))
        tickers_30d = set(t.get("ticker") for t in ark_30d)
        tickers_str = ", ".join(sorted(tickers_30d))
        if ark_sells > ark_buys:
            narrative_parts.append(f"ARK net selling crypto stocks ({ark_sells} sells vs {ark_buys} buys in 30d: {tickers_str})")
        elif ark_buys > ark_sells:
            narrative_parts.append(f"ARK net buying crypto stocks ({ark_buys} buys vs {ark_sells} sells in 30d: {tickers_str})")
        else:
            narrative_parts.append(f"ARK actively trading crypto stocks ({len(ark_30d)} trades in 30d: {tickers_str})")

    high_si = [t for t in short_interest if (t.get("short_pct_float") or 0) >= 15]
    if high_si:
        tickers_str = ", ".join(t["ticker"] for t in high_si[:4])
        narrative_parts.append(f"Elevated short interest in miners ({tickers_str})")

    if bullish_signals > bearish_signals:
        narrative_parts.append(f"{bullish_signals} bullish smart money signals across crypto-adjacent equities")
    elif bearish_signals > bullish_signals:
        narrative_parts.append(f"{bearish_signals} bearish signals — caution warranted")

    if not narrative_parts:
        narrative_parts.append("No strong crypto-adjacent signals detected across smart money sources")

    narrative = ". ".join(narrative_parts) + "."

    # --- ARK Sentiment (actual buy/sell ratio, more accurate than signal score) ---
    ark_sentiment = {"buys": 0, "sells": 0, "net": "neutral", "period": "30d"}
    if ark_30d:
        ark_sentiment["buys"] = sum(1 for t in ark_30d if t.get("trade_type") == "Buy"
                                    or t.get("change_type") in ("INCREASED", "NEW_POSITION"))
        ark_sentiment["sells"] = sum(1 for t in ark_30d if t.get("trade_type") == "Sell"
                                     or t.get("change_type") in ("DECREASED", "SOLD_OUT"))
        if ark_sentiment["sells"] > ark_sentiment["buys"] * 1.5:
            ark_sentiment["net"] = "bearish"
        elif ark_sentiment["buys"] > ark_sentiment["sells"] * 1.5:
            ark_sentiment["net"] = "bullish"
        else:
            ark_sentiment["net"] = "mixed"

    result = {
        "crypto_prices": crypto_prices,
        "ark_sentiment": ark_sentiment,
        "ark_trades": ark_trades,
        "insider_trades": insider_trades,
        "darkpool": darkpool,
        "short_interest": short_interest,
        "smart_money_signals": smart_money_signals,
        "congress_trades": congress_trades,
        "institution_holdings": institution_holdings,
        "summary": {
            "total_signals": len(smart_money_signals),
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "most_active_ticker": most_active,
            "narrative": narrative,
        },
        "cached_at": datetime.now(timezone.utc).isoformat(),
    }

    _set_cache(CACHE_KEY, result)
    return result


# ── FastAPI routes ───────────────────────────────────────────────────────────

from fastapi import APIRouter
router = APIRouter()


@router.get("/api/us/regime")
def api_us_regime():
    """
    Market Regime Detector — Green/Yellow/Red status.
    Components: VIX, SPY vs MA200, Credit Spread (FRED).
    Cached 1 hour.
    """
    try:
        return _get_regime_data()
    except Exception as e:
        logger.error(f"[regime] Error: {e}", exc_info=True)
        return {
            "regime": "unknown",
            "summary": "Unable to fetch regime data",
            "error": str(e),
            "components": {},
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/api/us/crisis")
def api_us_crisis():
    """
    Crisis Dashboard — VIX regime, Smart Money crisis behavior,
    Conviction Score (0-100), Historical Playbook.
    Cached 30 minutes.
    """
    try:
        return _get_crisis_data()
    except Exception as e:
        logger.error(f"[crisis] Error: {e}", exc_info=True)
        return {
            "error": str(e),
            "vix": {},
            "conviction_score": 0,
            "smart_money_signals": [],
            "historical_playbook": [],
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/api/us/crypto-signals")
def api_us_crypto_signals():
    """
    Crypto Signals — aggregated crypto-related data from all smart money sources.
    Includes BTC/ETH prices, ARK trades, insider activity, dark pool, short interest,
    smart money signals, Congress trades, and 13F holdings filtered for crypto tickers.
    Cached 30 minutes.
    """
    try:
        return _get_crypto_signals_data()
    except Exception as e:
        logger.error(f"[crypto-signals] Error: {e}", exc_info=True)
        return {
            "error": str(e),
            "crypto_prices": {},
            "ark_trades": [],
            "insider_trades": [],
            "darkpool": [],
            "short_interest": [],
            "smart_money_signals": [],
            "congress_trades": [],
            "institution_holdings": [],
            "summary": {"total_signals": 0, "bullish_signals": 0, "bearish_signals": 0, "most_active_ticker": "", "narrative": ""},
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/api/us/cross-asset")
def api_us_cross_asset():
    """
    Cross-Asset Signal Dashboard — Gold/BTC correlation, M2 supply,
    Treasury yield curve, Fear & Greed proxy.
    Cached 1 hour.
    """
    try:
        return _get_cross_asset_data()
    except Exception as e:
        logger.error(f"[cross-asset] Error: {e}", exc_info=True)
        return {
            "error": str(e),
            "gold_btc_correlation": {},
            "m2": {},
            "treasury_yields": {},
            "fear_greed": {},
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
