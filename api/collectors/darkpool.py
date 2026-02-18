#!/usr/bin/env python3
"""
Dark Pool Collector — FINRA RegSHO short volume data + Z-score anomaly detection.

Data source: FINRA RegSHO daily short volume files (FREE, daily updates)
  URL: https://cdn.finra.org/equity/regsho/daily/CNMSshvol{YYYYMMDD}.txt

DPI = ShortVolume / TotalVolume (Dark Pool Index)
Z-Score = (DPI_today - mean_30d) / std_30d
Anomaly = Z ≥ 2σ AND DPI ≥ 0.4 AND TotalVolume ≥ 500K

Output: data/darkpool.json (canonical SCHEMA.md format)
Schedule: Daily 19:00 ET (weekdays)
"""

import csv
import io
import json
import logging
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import DATA_DIR

logger = logging.getLogger(__name__)

FINRA_URL_TEMPLATE = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{date}.txt"
Z_SCORE_WINDOW = 30
MIN_HISTORY_DAYS = 20
HISTORY_DAYS = 45  # Fetch 45 days to have 30-day window + current


def get_signal_universe() -> set:
    """Get tickers from Congress + ARK data (our signal universe)."""
    tickers = set()
    
    for filename in ("congress.json", "ark_trades.json", "ark_holdings.json"):
        path = DATA_DIR / filename
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            for item in data.get("trades", data.get("holdings", [])):
                t = (item.get("ticker") or "").upper().strip()
                if t and t.isalpha() and 1 <= len(t) <= 5:
                    tickers.add(t)
    
    return tickers


def fetch_finra_day(date_str: str) -> Dict[str, Dict]:
    """
    Fetch one day of FINRA RegSHO data.
    
    Returns: {ticker: {short_volume, total_volume, dpi}}
    """
    url = FINRA_URL_TEMPLATE.format(date=date_str)
    
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return {}
        
        result = {}
        reader = csv.reader(io.StringIO(resp.text), delimiter="|")
        next(reader)  # Skip header: Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market
        
        for row in reader:
            if len(row) < 5:
                continue
            ticker = row[1].strip()
            try:
                short_vol = int(row[2])
                total_vol = int(row[4])
            except (ValueError, IndexError):
                continue
            
            if total_vol == 0:
                continue
            
            dpi = short_vol / total_vol
            
            result[ticker] = {
                "short_volume": short_vol,
                "total_volume": total_vol,
                "dpi": dpi,
            }
        
        return result
    except Exception as e:
        logger.warning(f"Failed to fetch {date_str}: {e}")
        return {}


def fetch_history(days: int = HISTORY_DAYS) -> List[tuple]:
    """
    Fetch multiple days of FINRA data.
    
    Returns: [(date_str, {ticker: {short_volume, total_volume, dpi}}), ...]
    """
    history = []
    today = datetime.now()
    
    fetched = 0
    for offset in range(1, days + 15):  # Extra days to account for weekends/holidays
        if fetched >= days:
            break
        
        d = today - timedelta(days=offset)
        if d.weekday() >= 5:  # Skip weekends
            continue
        
        date_str = d.strftime("%Y%m%d")
        data = fetch_finra_day(date_str)
        
        if data:
            iso_date = d.strftime("%Y-%m-%d")
            history.append((iso_date, data))
            fetched += 1
            logger.info(f"  Fetched {iso_date}: {len(data)} tickers")
        else:
            logger.debug(f"  No data for {date_str}")
    
    # Sort oldest first
    history.sort(key=lambda x: x[0])
    return history


def compute_anomalies(
    history: List[tuple],
    universe: Optional[set] = None,
) -> tuple:
    """
    Compute Z-scores and flag anomalies for signal universe tickers.
    
    Returns: (all_latest, anomalies)
    """
    if len(history) < MIN_HISTORY_DAYS:
        logger.warning(f"Only {len(history)} days of history, need {MIN_HISTORY_DAYS}")
        return [], []
    
    # Build per-ticker DPI history
    ticker_history: Dict[str, List[tuple]] = {}  # ticker → [(date, dpi, short_vol, total_vol)]
    
    for date, day_data in history:
        for ticker, values in day_data.items():
            if universe and ticker not in universe:
                continue
            if ticker not in ticker_history:
                ticker_history[ticker] = []
            ticker_history[ticker].append((
                date,
                values["dpi"],
                values["short_volume"],
                values["total_volume"],
            ))
    
    all_latest = []
    anomalies = []
    cutoff_7d = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    for ticker, records in ticker_history.items():
        if len(records) < MIN_HISTORY_DAYS:
            continue
        
        # Records are sorted by date (oldest first)
        dpis = [r[1] for r in records]
        
        # Use last Z_SCORE_WINDOW values for stats, last value for current
        if len(dpis) >= Z_SCORE_WINDOW + 1:
            window_dpis = dpis[-(Z_SCORE_WINDOW + 1):-1]
            current_dpi = dpis[-1]
        else:
            window_dpis = dpis[:-1]
            current_dpi = dpis[-1]
        
        if len(window_dpis) < MIN_HISTORY_DAYS:
            continue
        
        mean_dpi = statistics.mean(window_dpis)
        std_dpi = statistics.stdev(window_dpis) if len(window_dpis) > 1 else 0.001
        if std_dpi < 0.001:
            std_dpi = 0.001
        
        z_score = (current_dpi - mean_dpi) / std_dpi
        
        latest_date = records[-1][0]
        short_vol = records[-1][2]
        total_vol = records[-1][3]
        
        entry = {
            "ticker": ticker,
            "date": latest_date,
            "off_exchange_volume": short_vol,
            "short_volume": short_vol,  # FINRA ShortVolume = short sale volume
            "total_volume": total_vol,
            "dpi": round(current_dpi, 4),
            "off_exchange_pct": round(current_dpi * 100, 2),
            "short_pct": round(current_dpi * 100, 2),  # Same as off_exchange_pct for FINRA
            "z_score": round(z_score, 2),
            "z_score_window": Z_SCORE_WINDOW,
            "source": "finra_regsho",
        }
        
        all_latest.append(entry)
        
        # Anomaly check
        if (z_score >= 2.0 
            and current_dpi >= 0.4 
            and total_vol >= 500_000
            and latest_date >= cutoff_7d):
            anomalies.append(entry)
    
    all_latest.sort(key=lambda x: x["z_score"], reverse=True)
    anomalies.sort(key=lambda x: x["z_score"], reverse=True)
    
    return all_latest, anomalies


class DarkPoolCollector:
    """
    FINRA-based dark pool collector.
    
    One HTTP request per day of data (~45 requests for full history).
    Each request returns ALL tickers, so no per-ticker API calls needed.
    """

    def __init__(self, cache_dir: str = str(DATA_DIR)):
        self.cache_dir = Path(cache_dir)

    def run(self, days: int = HISTORY_DAYS, universe_only: bool = True) -> dict:
        """
        Main entry point.
        
        Args:
            days: Number of trading days of history to fetch.
            universe_only: If True, only process tickers in our signal universe.
        """
        universe = get_signal_universe() if universe_only else None
        
        logger.info(f"Fetching {days} days of FINRA RegSHO data...")
        if universe:
            logger.info(f"Signal universe: {len(universe)} tickers")
        
        history = fetch_history(days=days)
        logger.info(f"Fetched {len(history)} trading days")
        
        all_latest, anomalies = compute_anomalies(history, universe=universe)
        
        output = {
            "tickers": all_latest,
            "anomalies": anomalies,
            "metadata": {
                "schema_version": "1.0.0",
                "total_tickers": len(all_latest),
                "anomaly_count": len(anomalies),
                "avg_dpi": round(
                    sum(t["dpi"] for t in all_latest) / len(all_latest), 4
                ) if all_latest else 0,
                "highest_z": anomalies[0]["z_score"] if anomalies else 0,
                "trading_days": len(history),
                "date_range": f"{history[0][0]} to {history[-1][0]}" if history else "",
                "last_updated": datetime.now().isoformat(),
            },
        }
        
        out_path = self.cache_dir / "darkpool.json"
        with open(out_path, "w") as f:
            json.dump(output, f)
        
        logger.info(
            f"Dark Pool: {len(all_latest)} tickers processed, "
            f"{len(anomalies)} anomalies flagged"
        )
        
        return output


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    collector = DarkPoolCollector()
    result = collector.run()
    
    print(f"\n{'='*50}")
    print(f"Dark Pool Collection Complete:")
    print(f"  Tickers processed: {result['metadata']['total_tickers']}")
    print(f"  Anomalies: {result['metadata']['anomaly_count']}")
    print(f"  Avg DPI: {result['metadata']['avg_dpi']}")
    print(f"  Date range: {result['metadata']['date_range']}")
    
    if result['anomalies']:
        print(f"\n🌑 Anomalies (Z ≥ 2σ, DPI ≥ 0.4, Vol ≥ 500K):")
        for a in result['anomalies'][:15]:
            print(f"  {a['ticker']:6s} | DPI={a['dpi']:.3f} | Z={a['z_score']:+.1f}σ | vol={a['total_volume']:>12,} | {a['date']}")
    else:
        print("\nNo anomalies detected in last 7 days.")
