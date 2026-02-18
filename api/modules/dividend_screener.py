"""
Dividend Screener - High Quality Dividend Stock Analyzer
Analyzes US/HK/CN markets for stable, high-dividend, quality stocks.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import warnings

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings('ignore')

# ── Universe Definitions ──────────────────────────────────────────────────
US_UNIVERSE = [
    # Dividend Aristocrats / Kings (25+ years of dividend growth)
    'JNJ', 'PG', 'KO', 'PEP', 'MCD', 'MMM', 'ABT', 'ABBV', 'T', 'VZ',
    'XOM', 'CVX', 'IBM', 'WMT', 'HD', 'LOW', 'CL', 'SYY', 'GPC', 'EMR',
    'AFL', 'APD', 'BDX', 'CLX', 'DOV', 'ED', 'GD', 'ITW', 'SWK', 'TGT',
    # High Yield Blue Chips
    'O', 'MAIN', 'MO', 'PM', 'BMY', 'AMGN', 'GILD',
    'UPS', 'CAT', 'DE', 'LMT', 'RTX', 'BA', 'CSCO', 'INTC', 'TXN', 'AVGO',
    # REITs
    'AMT', 'PLD', 'CCI', 'SPG', 'PSA', 'WELL', 'DLR', 'EQR', 'AVB',
    # Utilities
    'NEE', 'DUK', 'SO', 'D', 'AEP', 'SRE', 'EXC', 'WEC',
    # Banks with good dividends
    'JPM', 'BAC', 'WFC', 'USB', 'PNC', 'BK', 'STT',
    # Consumer staples
    'COST', 'KR', 'GIS', 'K', 'HSY', 'HRL', 'SJM', 'MKC',
    # Healthcare
    'PFE', 'MRK', 'LLY', 'UNH', 'MDT',
    # Industrials
    'HON', 'GE', 'UNP', 'NSC',
]

HK_UNIVERSE = [
    # Banks
    '0005.HK', '0011.HK', '0939.HK', '1398.HK', '3988.HK',
    # Utilities
    '0002.HK', '0003.HK', '0006.HK',
    # Telco
    '0941.HK', '0762.HK',
    # Insurance
    '2318.HK', '2628.HK',
    # REITs
    '0435.HK', '0808.HK',
    # Blue chips
    '0001.HK', '0016.HK', '0388.HK', '0688.HK', '0700.HK',
    '1113.HK', '1299.HK', '1928.HK', '2318.HK', '2388.HK',
]

CN_UNIVERSE = [
    # 银行
    '601398.SS', '601288.SS', '601328.SS', '601939.SS', '600036.SS',
    '601166.SS', '600016.SS', '601818.SS', '600000.SS', '601229.SS',
    # 能源
    '601857.SS', '600028.SS', '601088.SS', '600900.SS',
    # 公用事业
    '600886.SS', '600674.SS',
    # 消费
    '600519.SS', '000858.SZ', '000568.SZ', '603369.SS',
    # 保险
    '601318.SS', '601628.SS', '601601.SS',
    # 基建
    '601668.SS', '601390.SS', '601186.SS',
    # 通信
    '600941.SS', '601728.SS',
    # 交通
    '601006.SS', '600009.SS',
    # 其他蓝筹
    '601888.SS', '000651.SZ', '600585.SS', '002415.SZ',
]

# ── Cache ─────────────────────────────────────────────────────────────────
from api.config import DATA_DIR as _CFG_DATA_DIR
CACHE_DIR = _CFG_DATA_DIR
CACHE_FILE = CACHE_DIR / "dividend_screener_cache.json"
CACHE_EXPIRY_HOURS = 168  # 7 days — dividend data is weekly, no need for aggressive expiry


def load_cache() -> dict[str, Any]:
    """Load cache from disk."""
    if not CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(CACHE_FILE.read_text())
        cache_time = datetime.fromisoformat(data.get("updated_at", "2020-01-01"))
        if datetime.now(timezone.utc) - cache_time < timedelta(hours=CACHE_EXPIRY_HOURS):
            return data
    except Exception:
        pass
    return {}


def save_cache(data: dict):
    """Save cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


# ── Data Fetching ─────────────────────────────────────────────────────────
def fetch_stock_data(ticker: str, period: str = "5y") -> dict | None:
    """Fetch stock data from yfinance with error handling."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period=period)
        
        if hist.empty or len(hist) < 100:
            return None
            
        # Get dividends
        divs = stock.dividends
        if len(divs) > 0:
            # Remove timezone from index for comparison
            divs_copy = divs.copy()
            if hasattr(divs_copy.index, 'tz') and divs_copy.index.tz is not None:
                divs_copy.index = divs_copy.index.tz_localize(None)
            cutoff_date = datetime.now() - timedelta(days=365*5)
            divs_5y = divs_copy[divs_copy.index > cutoff_date]
        else:
            divs_5y = pd.Series(dtype=float)
        
        return {
            "ticker": ticker,
            "info": info,
            "history": hist,
            "dividends": divs_5y,
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def calculate_quality_score(data: dict) -> dict:
    """Calculate company quality metrics (30% weight)."""
    info = data["info"]
    
    roe = info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0
    gross_margin = info.get("grossMargins", 0) * 100 if info.get("grossMargins") else 0
    operating_margin = info.get("operatingMargins", 0) * 100 if info.get("operatingMargins") else 0
    debt_equity = info.get("debtToEquity", 0) if info.get("debtToEquity") else 0
    
    # Score components (0-100)
    roe_score = min(100, max(0, roe * 4))  # 25% ROE = 100 points
    margin_score = min(100, max(0, (gross_margin + operating_margin) / 2))
    debt_score = max(0, 100 - debt_equity / 2)  # Lower debt = higher score
    
    # Earnings stability (stddev of quarterly earnings)
    hist = data["history"]
    if len(hist) > 20:
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        stability_score = max(0, 100 - volatility * 2)
    else:
        stability_score = 50
    
    total = (roe_score + margin_score + debt_score + stability_score) / 4
    
    return {
        "quality_score": round(total, 1),
        "roe": round(roe, 1),
        "gross_margin": round(gross_margin, 1),
        "operating_margin": round(operating_margin, 1),
        "debt_equity": round(debt_equity, 1),
        "earnings_stability": round(stability_score, 1),
    }


def calculate_dividend_score(data: dict) -> dict:
    """Calculate dividend quality metrics (30% weight)."""
    info = data["info"]
    divs = data["dividends"]
    
    div_yield = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
    payout_ratio = info.get("payoutRatio", 0) * 100 if info.get("payoutRatio") else 0
    
    # Score dividend yield (3-7% is optimal)
    if 3 <= div_yield <= 7:
        yield_score = 100
    elif div_yield > 7:
        yield_score = max(50, 100 - (div_yield - 7) * 5)  # Too high might be risky
    else:
        yield_score = min(100, div_yield * 25)
    
    # Score payout ratio (30-60% is optimal)
    if 30 <= payout_ratio <= 60:
        payout_score = 100
    elif payout_ratio > 60:
        payout_score = max(0, 100 - (payout_ratio - 60) * 2)
    else:
        payout_score = min(100, payout_ratio * 2)
    
    # Calculate consecutive dividend years
    consecutive_years = 0
    if len(divs) > 0:
        years = divs.resample('YE').sum()
        consecutive_years = 0
        for val in reversed(list(years)):
            if val > 0:
                consecutive_years += 1
            else:
                break
    
    years_score = min(100, consecutive_years * 10)  # 10 years = 100 points
    
    # Calculate 5-year dividend growth
    if len(divs) >= 2:
        annual_divs = divs.resample('YE').sum()
        if len(annual_divs) >= 2:
            first_year = annual_divs.iloc[0]
            last_year = annual_divs.iloc[-1]
            if first_year > 0:
                years_count = len(annual_divs)
                growth_rate = ((last_year / first_year) ** (1 / max(1, years_count - 1)) - 1) * 100
                growth_score = min(100, max(0, 50 + growth_rate * 5))  # 10% growth = 100
            else:
                growth_score = 0
                growth_rate = 0
        else:
            growth_score = 0
            growth_rate = 0
    else:
        growth_score = 0
        growth_rate = 0
    
    total = (yield_score + payout_score + years_score + growth_score) / 4
    
    return {
        "dividend_score": round(total, 1),
        "dividend_yield": round(div_yield, 2),
        "payout_ratio": round(payout_ratio, 1),
        "consecutive_years": consecutive_years,
        "div_growth_5y": round(growth_rate, 2),
    }


def calculate_dca_score(data: dict) -> dict:
    """Calculate DCA (Dollar Cost Averaging) returns (20% weight)."""
    hist = data["history"]
    
    if len(hist) < 60:  # Need at least 5 months of data
        return {
            "dca_score": 0,
            "dca_5y_return": 0,
            "dca_annual_return": 0,
        }
    
    # Simulate monthly DCA
    monthly_investment = 1000
    total_invested = 0
    total_shares = 0
    
    # Resample to monthly
    monthly_prices = hist['Close'].resample('ME').last()
    
    for price in monthly_prices:
        if pd.notna(price) and price > 0:
            shares = monthly_investment / price
            total_shares += shares
            total_invested += monthly_investment
    
    if total_invested == 0:
        return {"dca_score": 0, "dca_5y_return": 0, "dca_annual_return": 0}
    
    current_value = total_shares * hist['Close'].iloc[-1]
    total_return = ((current_value - total_invested) / total_invested) * 100
    
    # Calculate annualized return
    years = len(monthly_prices) / 12
    if years > 0 and total_return > -100:
        annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100
    else:
        annual_return = 0
    
    # Score: 8% annual = 100 points
    dca_score = min(100, max(0, 50 + annual_return * 5))
    
    return {
        "dca_score": round(dca_score, 1),
        "dca_5y_return": round(total_return, 2),
        "dca_annual_return": round(annual_return, 2),
    }


def calculate_stability_score(data: dict) -> dict:
    """Calculate volatility and drawdown metrics (20% weight)."""
    hist = data["history"]
    
    if len(hist) < 20:
        return {
            "stability_score": 0,
            "volatility_annual": 0,
            "max_drawdown": 0,
            "max_dd_days": 0,
            "sharpe": 0,
        }
    
    # Calculate annualized volatility
    returns = hist['Close'].pct_change().dropna()
    volatility = returns.std() * np.sqrt(252) * 100
    
    # Calculate maximum drawdown
    prices = hist['Close']
    cummax = prices.cummax()
    drawdown = (prices - cummax) / cummax * 100
    max_dd = drawdown.min()
    
    # Find max drawdown recovery days
    max_dd_idx = drawdown.idxmin()
    recovery_idx = prices[prices.index > max_dd_idx].where(prices >= cummax.loc[max_dd_idx]).first_valid_index()
    if recovery_idx:
        max_dd_days = (recovery_idx - max_dd_idx).days
    else:
        max_dd_days = (hist.index[-1] - max_dd_idx).days
    
    # Calculate Sharpe ratio (assume risk-free rate = 2%)
    risk_free_rate = 0.02
    mean_return = returns.mean() * 252
    if returns.std() > 0:
        sharpe = (mean_return - risk_free_rate) / (returns.std() * np.sqrt(252))
    else:
        sharpe = 0
    
    # Scoring
    vol_score = max(0, 100 - volatility * 2)  # Lower vol = better
    dd_score = max(0, 100 + max_dd)  # -50% DD = 50 points
    sharpe_score = min(100, max(0, sharpe * 50))  # Sharpe 2.0 = 100
    
    total = (vol_score + dd_score + sharpe_score) / 3
    
    return {
        "stability_score": round(total, 1),
        "volatility_annual": round(volatility, 2),
        "max_drawdown": round(max_dd, 2),
        "max_dd_days": max_dd_days,
        "sharpe": round(sharpe, 3),
    }


def calculate_total_score(metrics: dict) -> float:
    """Calculate weighted total score."""
    weights = {
        "quality_score": 0.30,
        "dividend_score": 0.30,
        "dca_score": 0.20,
        "stability_score": 0.20,
    }
    
    total = sum(metrics.get(k, 0) * w for k, w in weights.items())
    return round(total, 1)


def analyze_stock(ticker: str) -> dict | None:
    """Full analysis pipeline for a single stock."""
    print(f"Analyzing {ticker}...")
    
    data = fetch_stock_data(ticker)
    if not data:
        return None
    
    info = data["info"]
    
    # Calculate all metrics
    quality = calculate_quality_score(data)
    dividend = calculate_dividend_score(data)
    dca = calculate_dca_score(data)
    stability = calculate_stability_score(data)
    
    # Combine all metrics
    metrics = {
        **quality,
        **dividend,
        **dca,
        **stability,
    }
    
    metrics["total_score"] = calculate_total_score(metrics)
    
    # Add basic info
    metrics["ticker"] = ticker
    metrics["name"] = info.get("longName", info.get("shortName", ticker))
    metrics["sector"] = info.get("sector", "Unknown")
    metrics["industry"] = info.get("industry", "Unknown")
    metrics["market_cap"] = info.get("marketCap", 0)
    metrics["pe_ratio"] = round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else 0
    metrics["price"] = round(data["history"]["Close"].iloc[-1], 2)
    
    return metrics


def screen_market(universe: list[str], batch_delay: int = 2) -> list[dict]:
    """Screen a market universe and return ranked stocks."""
    results = []
    
    for i, ticker in enumerate(universe):
        try:
            result = analyze_stock(ticker)
            if result and result["total_score"] > 0:
                results.append(result)
            
            # Rate limiting
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{len(universe)}")
                time.sleep(batch_delay)
            else:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            continue
    
    # Sort by total score
    results.sort(key=lambda x: x["total_score"], reverse=True)
    
    # Add rank
    for i, stock in enumerate(results):
        stock["rank"] = i + 1
    
    return results[:20]  # Top 20


def get_screener_data(market: str | None = None, force_refresh: bool = False) -> dict:
    """Main entry point - get screener data for market(s)."""
    
    # Try to load from cache
    if not force_refresh:
        cached = load_cache()
        if cached:
            if market:
                return {
                    "market": market,
                    "updated_at": cached.get("updated_at"),
                    "stocks": cached.get(market, []),
                }
            return cached
    
    # Generate fresh data
    print("Generating fresh dividend screener data...")
    
    data = {}
    
    if not market or market == "us":
        print("\n=== Screening US Market ===")
        data["us"] = screen_market(US_UNIVERSE)
    
    if not market or market == "hk":
        print("\n=== Screening HK Market ===")
        data["hk"] = screen_market(HK_UNIVERSE)
    
    if not market or market == "cn":
        print("\n=== Screening CN Market ===")
        data["cn"] = screen_market(CN_UNIVERSE)
    
    # Save to cache
    save_cache(data)
    
    if market:
        return {
            "market": market,
            "updated_at": data.get("updated_at"),
            "stocks": data.get(market, []),
        }
    
    return data


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    market = sys.argv[1] if len(sys.argv) > 1 else None
    force = "--force" in sys.argv
    
    result = get_screener_data(market, force_refresh=force)
    print(json.dumps(result, indent=2, ensure_ascii=False))
