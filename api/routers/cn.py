"""
CN market routes - Trend signal and 12x30 strategy
Supports both legacy 8x30 and current 12x30 endpoints.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.shared import CN_TREND_FILE, CN_8X30_DIR, read_json, file_mtime
import os

router = APIRouter()

# ── 12x30 data directory ──────────────────────────────────────────────
SIGNALS_DIR = os.getenv("SIGNALS_DIR", "./data/signals")
CN_12X30_DIR = f"{SIGNALS_DIR}/cn-12x30"

# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/cn/trend")
def api_cn_trend():
    """China market trend signal."""
    data = read_json(CN_TREND_FILE)
    if not data:
        return {"error": "CN trend data not available"}
    return {
        "signal": data.get("signal"),
        "date": data.get("date"),
        "price": data.get("price"),
        "ma200": data.get("ma200"),
        "ma_distance_pct": data.get("ma_distance_pct"),
        "rsi14": data.get("rsi14"),
        "volume_ratio": data.get("volume_ratio"),
        "last_signal_change": data.get("last_signal_change"),
        "previous_signal": data.get("previous_signal"),
        "updated_at": data.get("updated_at") or file_mtime(CN_TREND_FILE),
    }


# ── 12x30 Strategy (CURRENT) ──────────────────────────────────────────

@router.get("/api/cn/12x30/portfolio")
@router.get("/api/cn/8x30/portfolio")  # backward compat
def api_cn_12x30_portfolio():
    """CN 12x30 Factor Strategy current portfolio holdings."""
    # Try 12x30 first, fallback to 8x30
    data = read_json(f"{CN_12X30_DIR}/paper_portfolio_12x30.json")
    if data:
        # Normalize to expected format
        return {
            "strategy": data.get("strategy", "12x30"),
            "date": data.get("as_of", ""),
            "generated": data.get("generated", ""),
            "top_n": data.get("config", {}).get("top_n", 30),
            "n_factors": data.get("config", {}).get("factors", []),
            "factor_names": data.get("config", {}).get("factors", []),
            "config": data.get("config", {}),
            "backtest": data.get("backtest", {}),
            "initial_capital": 1_000_000,
            "per_stock": round(1_000_000 / data.get("config", {}).get("top_n", 30)),
            "holdings": data.get("holdings", []),
        }
    # Fallback
    data = read_json(f"{CN_8X30_DIR}/paper_portfolio_8x30.json")
    if not data:
        return JSONResponse({"error": "CN portfolio not available"}, status_code=500)
    return data


@router.get("/api/cn/12x30/nav")
@router.get("/api/cn/8x30/nav")  # backward compat
def api_cn_12x30_nav():
    """CN 12x30 Factor Strategy NAV curve."""
    # 12x30 NAV is monthly: [{date, nav, daily_ret}]
    nav_data = read_json(f"{CN_12X30_DIR}/nav_curve_12x30.json")
    metrics = read_json(f"{CN_12X30_DIR}/strategy_metrics_12x30.json")

    if nav_data and isinstance(nav_data, list) and len(nav_data) > 0:
        dates = [p["date"] for p in nav_data]
        strategy_nav = [p["nav"] for p in nav_data]

        # Compute benchmark NAV from metrics
        bench_return = metrics.get("benchmark_return", 0) if metrics else 0
        n = len(nav_data)
        benchmark_nav = []
        for i in range(n):
            # Linear interpolation for benchmark
            frac = i / max(n - 1, 1)
            benchmark_nav.append(round(1.0 + (bench_return / 100) * frac, 4))

        return {
            "dates": dates,
            "strategy_nav": strategy_nav,
            "benchmark_nav": benchmark_nav,
            "strategy_name": f"12-Factor Contrarian ({metrics.get('factors', 12)}F, 10d rebal)" if metrics else "12-Factor Contrarian",
            "benchmark_name": "A-Share Equal Weight",
            "total_return_pct": round((strategy_nav[-1] - 1) * 100, 2) if strategy_nav else 0,
            "benchmark_return_pct": bench_return,
        }

    # Fallback to 8x30
    data = read_json(f"{CN_8X30_DIR}/nav_curve_8x30.json")
    if not data:
        return JSONResponse({"error": "CN NAV data not available"}, status_code=500)
    return data


@router.get("/api/cn/12x30/metrics")
@router.get("/api/cn/8x30/metrics")  # backward compat
def api_cn_12x30_metrics():
    """CN 12x30 Factor Strategy key metrics."""
    data = read_json(f"{CN_12X30_DIR}/strategy_metrics_12x30.json")
    if data:
        return {
            "strategy": data.get("strategy", "12x30"),
            "total_return": data.get("total_return", 0),
            "max_drawdown": data.get("max_drawdown", 0),
            "sharpe": data.get("sharpe", 0),
            "benchmark_return": data.get("benchmark_return", 0),
            "excess_return": data.get("excess_return", 0),
            "factors": data.get("factors", 12),
            "months": data.get("months", 0),
            "evolution": data.get("evolution", ""),
            "oos_sharpe_2025": data.get("oos_sharpe_2025", None),
            "trading_days": data.get("months", 0) * 22,  # approx
            "updated_at": file_mtime(f"{CN_12X30_DIR}/strategy_metrics_12x30.json"),
        }
    # Fallback
    data = read_json(f"{CN_8X30_DIR}/strategy_metrics_8x30.json")
    if not data:
        return JSONResponse({"error": "CN metrics not available"}, status_code=500)
    return data


@router.get("/api/cn/8x30/sensitivity")
def api_cn_8x30_sensitivity():
    """CN 8x30 Factor Strategy sensitivity analysis (legacy, no 12x30 equivalent yet)."""
    data = read_json(f"{CN_8X30_DIR}/sensitivity_results.json")
    if not data:
        return JSONResponse({"error": "CN sensitivity not available"}, status_code=500)
    return data


@router.get("/api/portfolio-cn")
def api_portfolio_cn():
    """CN 12×30 paper portfolio in unified format (same shape as /api/portfolio)."""
    raw = read_json(f"{CN_12X30_DIR}/paper_portfolio_12x30.json")
    metrics_raw = read_json(f"{CN_12X30_DIR}/strategy_metrics_12x30.json")
    nav_raw = read_json(f"{CN_12X30_DIR}/nav_curve_12x30.json")

    # Fallback to 8x30 if 12x30 not available
    if not raw:
        raw = read_json(f"{CN_8X30_DIR}/paper_portfolio_8x30.json")
        metrics_raw = read_json(f"{CN_8X30_DIR}/strategy_metrics_8x30.json")
        nav_raw = read_json(f"{CN_8X30_DIR}/nav_curve_8x30.json")

    positions = []
    if raw and "holdings" in raw:
        for h in raw["holdings"]:
            code = h.get("ts_code", "")
            close = h.get("close", 0)
            ret5 = h.get("ret_5d_pct", 0)
            entry = round(close / (1 + ret5 / 100), 2) if ret5 else close
            positions.append({
                "ticker": code,
                "code": code,
                "name": h.get("name", code),
                "market": "CN",
                "status": "open",
                "entry_price": entry,
                "current_price": close,
                "pnl_pct": ret5,
                "score": h.get("score", 0),
                "weight": h.get("weight", 0),
                "industry": h.get("industry", ""),
                "rank": h.get("rank", 0),
                "entry_date": raw.get("as_of", raw.get("date", "")),
                "days_held": 0,
            })

    daily_returns = []
    if nav_raw and isinstance(nav_raw, list):
        cap = raw.get("initial_capital", 1_000_000) if raw and isinstance(raw, dict) else 1_000_000
        for point in nav_raw:
            nav_val = point.get("nav", 1) if isinstance(point, dict) else 1
            daily_returns.append({
                "date": point.get("date", "") if isinstance(point, dict) else "",
                "portfolio_value": nav_val * cap,
                "daily_return_pct": point.get("daily_ret", 0) if isinstance(point, dict) else 0,
            })

    metrics = {}
    if positions:
        pnls = [p.get("pnl_pct", 0) for p in positions]
        winners = [x for x in pnls if x > 0]
        metrics = {
            "total_return": round(sum(pnls) / len(pnls), 2) if pnls else 0,
            "open_positions": len(positions),
            "win_rate": round(len(winners) / len(pnls) * 100, 1) if pnls else 0,
        }
    if metrics_raw:
        metrics["backtest_total_return"] = metrics_raw.get("total_return", 0)
        metrics["backtest_sharpe"] = metrics_raw.get("sharpe", 0)
        metrics["backtest_max_drawdown"] = metrics_raw.get("max_drawdown", 0)

    return {
        "created": raw.get("as_of", raw.get("date", "")) if raw else None,
        "last_updated": file_mtime(f"{CN_12X30_DIR}/paper_portfolio_12x30.json") or file_mtime(f"{CN_8X30_DIR}/paper_portfolio_8x30.json"),
        "initial_capital": 1_000_000,
        "positions": positions,
        "closed_positions": [],
        "metrics": metrics,
        "daily_returns": daily_returns,
        "actions_log": [],
    }
