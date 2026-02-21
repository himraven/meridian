#!/usr/bin/env python3
"""
Trend Filter — 20-Day Moving Average

检查股票是否在 20 日均线上方:
- 上方 → actionable (📈)
- 下方 → downgraded, 标记 ⚠️

使用 yfinance 获取价格数据。
结果会缓存到 data/trend_cache.json (按日),避免重复请求。
"""

import json
import time
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Optional, Tuple

import yfinance as yf


import os as _os
# trend_cache lives in writable /app/db/ (not read-only /app/data/)
_CACHE_DIR = Path(_os.getenv("DB_DIR", str(Path(__file__).parent.parent.parent / "db")))
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = _CACHE_DIR / "trend_cache.json"


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_cache(cache: dict):
    CACHE_FILE.parent.mkdir(exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def get_trend_info(ticker: str) -> Dict:
    """
    获取单只股票的趋势信息。

    Returns:
        {
            "ticker": "AAPL",
            "price": 198.5,
            "ma20": 192.3,
            "above_ma20": True,
            "pct_from_ma20": 3.22,   # +3.22% 表示在20日线上方
            "trend_label": "📈 趋势: 20日线上方+3.2%",
            "ok": True
        }
    """
    today_str = date.today().isoformat()
    cache = _load_cache()

    # Check cache (keyed by date + ticker)
    cache_key = f"{today_str}:{ticker}"
    if cache_key in cache:
        return cache[cache_key]

    result = {
        "ticker": ticker,
        "price": None,
        "ma20": None,
        "above_ma20": None,
        "pct_from_ma20": None,
        "trend_label": "",
        "ok": False,
    }

    try:
        # Download 40 days of data (enough for 20 trading days)
        data = yf.download(ticker, period="2mo", progress=False, timeout=15)
        if data is None or data.empty or len(data) < 20:
            result["trend_label"] = "❓ 趋势: 数据不足"
            return result

        # Current price = last close
        close = data["Close"]
        # Handle multi-level columns from yfinance
        if hasattr(close, 'columns'):
            close = close.iloc[:, 0]
        
        current_price = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])

        pct = ((current_price - ma20) / ma20) * 100
        above = current_price >= ma20

        result["price"] = round(current_price, 2)
        result["ma20"] = round(ma20, 2)
        result["above_ma20"] = above
        result["pct_from_ma20"] = round(pct, 1)
        result["ok"] = True

        if above:
            result["trend_label"] = f"📈 趋势: 20日线上方+{pct:.1f}%"
        else:
            result["trend_label"] = f"⚠️ 趋势: 20日线下方{pct:.1f}%"

        # Cache it
        cache[cache_key] = result
        _save_cache(cache)

    except Exception as e:
        result["trend_label"] = f"❓ 趋势: 查询失败({e})"

    return result


def get_batch_trend_info(tickers: list, delay: float = 0.3) -> Dict[str, Dict]:
    """
    批量获取多只股票的趋势信息。
    为了避免 rate-limiting，在请求间添加延迟。
    """
    results = {}
    # Deduplicate and filter None
    unique = sorted(set(t for t in tickers if t))

    for i, ticker in enumerate(unique):
        results[ticker] = get_trend_info(ticker)
        # Rate limiting — yfinance can be throttled
        if i < len(unique) - 1:
            time.sleep(delay)

    return results


if __name__ == "__main__":
    # Test
    test_tickers = ["AAPL", "TSLA", "NVDA", "GOOG", "COIN"]
    print("Testing trend filter...")
    results = get_batch_trend_info(test_tickers)
    for ticker, info in results.items():
        print(f"  {ticker}: {info['trend_label']}  (price={info.get('price')}, ma20={info.get('ma20')})")
