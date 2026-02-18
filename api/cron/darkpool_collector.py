#!/usr/bin/env python3
"""
Dark Pool (Off-Exchange) Data Collector

Fetches OTC volume data, calculates DPI (Dark Pool Index) and Z-scores,
flags anomalies per PRD specifications:
  - DPI = OTC_Short / OTC_Total
  - Z-score = (DPI_today - Mean_DPI_30d) / StdDev_DPI_30d
  - Anomaly: Z ≥ 2.0 AND DPI ≥ 0.4 AND volume ≥ 500K

Output: data/darkpool.json matching DarkPoolTicker model schema.

Schedule: Daily 19:00 ET (after market close)
"""

import json
import logging
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import (
    DATA_DIR,
    DARKPOOL,
)
from api.modules.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class DarkPoolCollector:
    """
    Collects dark pool data and computes DPI anomalies.
    
    Algorithm:
    1. Load raw OTC data (from Quiver API or provided data)
    2. Group by ticker, sort by date
    3. For each ticker with ≥30 days of data:
       a. Calculate DPI = otc_short / otc_total for each day
       b. Compute 30-day rolling mean and stddev of DPI
       c. Calculate Z-score for latest day
       d. Flag as anomaly if Z ≥ 2.0 AND DPI ≥ 0.4 AND volume ≥ 500K
    4. Write results to cache
    """

    def __init__(self, cache_dir: str = str(DATA_DIR)):
        self.cache = CacheManager(cache_dir)
        self.z_threshold = DARKPOOL.z_score_threshold
        self.min_dpi = DARKPOOL.min_dpi
        self.min_volume = DARKPOOL.min_volume
        self.rolling_window = DARKPOOL.rolling_window_days
        self.min_history = DARKPOOL.rolling_window_days  # Need at least this many days

    def calculate_dpi(self, otc_short: int, otc_total: int) -> float:
        """
        Calculate Dark Pool Index.
        DPI = OTC_Short / OTC_Total
        
        Returns 0.0 if otc_total is 0 (avoid division by zero).
        """
        if otc_total <= 0:
            return 0.0
        return otc_short / otc_total

    def compute_z_score(self, dpi_values: List[float], current_dpi: float) -> Tuple[float, float, float]:
        """
        Compute Z-score for current DPI against rolling window.
        
        Args:
            dpi_values: List of historical DPI values (rolling window)
            current_dpi: Current day's DPI
            
        Returns:
            (z_score, mean, stddev) tuple
        """
        if len(dpi_values) < 2:
            return 0.0, current_dpi, 0.0

        mean_dpi = statistics.mean(dpi_values)
        stddev_dpi = statistics.stdev(dpi_values)

        if stddev_dpi == 0:
            return 0.0, mean_dpi, 0.0

        z_score = (current_dpi - mean_dpi) / stddev_dpi
        return z_score, mean_dpi, stddev_dpi

    def is_anomaly(self, z_score: float, dpi: float, total_volume: int) -> bool:
        """
        Check if a ticker meets anomaly criteria per PRD:
        - Z-score ≥ 2.0 (95% confidence)
        - DPI ≥ 0.4
        - Total volume ≥ 500K shares/day
        """
        return (
            z_score >= self.z_threshold
            and dpi >= self.min_dpi
            and total_volume >= self.min_volume
        )

    def process_raw_data(self, raw_records: List[Dict]) -> List[Dict]:
        """
        Process raw OTC records into analyzed dark pool data.
        
        Args:
            raw_records: List of dicts with keys:
                ticker, date, otc_short, otc_total, price (optional)
                
        Returns:
            List of analyzed ticker dicts matching DarkPoolTicker model.
        """
        # Group by ticker
        by_ticker: Dict[str, List[Dict]] = {}
        for record in raw_records:
            ticker = record.get("ticker", "").upper().strip()
            if not ticker:
                continue
            if ticker not in by_ticker:
                by_ticker[ticker] = []
            by_ticker[ticker].append(record)

        results = []

        for ticker, records in by_ticker.items():
            # Sort by date ascending
            records.sort(key=lambda r: r.get("date", ""))

            # Need minimum history for Z-score
            if len(records) < self.min_history:
                logger.debug(f"{ticker}: only {len(records)} days, need {self.min_history}")
                continue

            # Calculate DPI for each day
            dpi_series = []
            for r in records:
                otc_short = int(r.get("otc_short", 0))
                otc_total = int(r.get("otc_total", 0))
                dpi = self.calculate_dpi(otc_short, otc_total)
                dpi_series.append(dpi)

            # Take last 30 days for rolling statistics (excluding today)
            window_dpis = dpi_series[-(self.rolling_window + 1):-1] if len(dpi_series) > self.rolling_window else dpi_series[:-1]
            current_dpi = dpi_series[-1]

            if len(window_dpis) < 2:
                continue

            # Compute Z-score
            z_score, mean_dpi, stddev_dpi = self.compute_z_score(window_dpis, current_dpi)

            # Latest record data
            latest = records[-1]
            otc_short = int(latest.get("otc_short", 0))
            otc_total = int(latest.get("otc_total", 0))
            total_volume = otc_total  # Total off-exchange volume

            # Check anomaly
            anomaly = self.is_anomaly(z_score, current_dpi, total_volume)

            results.append({
                "ticker": ticker,
                "date": latest.get("date", ""),
                "otc_short": otc_short,
                "otc_total": otc_total,
                "dpi": round(current_dpi, 4),
                "dpi_30d_mean": round(mean_dpi, 4),
                "dpi_30d_stddev": round(stddev_dpi, 4),
                "z_score": round(z_score, 2),
                "is_anomaly": anomaly,
                "total_volume": total_volume,
                "price": latest.get("price"),
                "price_change_pct": latest.get("price_change_pct"),
            })

        # Sort: anomalies first (by Z-score desc), then non-anomalies
        results.sort(key=lambda x: (-int(x["is_anomaly"]), -x["z_score"]))

        logger.info(
            f"Processed {len(results)} tickers, "
            f"{sum(1 for r in results if r['is_anomaly'])} anomalies"
        )
        return results

    def save_results(self, results: List[Dict]) -> bool:
        """Save results to cache as darkpool.json."""
        output = {
            "last_updated": datetime.now().isoformat(),
            "tickers": results,
            "metadata": {
                "total_count": len(results),
                "anomaly_count": sum(1 for r in results if r["is_anomaly"]),
                "avg_dpi": round(
                    statistics.mean(r["dpi"] for r in results), 4
                ) if results else 0,
                "highest_dpi": max((r["dpi"] for r in results), default=0),
                "z_score_threshold": self.z_threshold,
                "min_dpi": self.min_dpi,
                "min_volume": self.min_volume,
            }
        }
        ok = self.cache.write("darkpool.json", output)
        # Dual-write to SQLite
        try:
            from api.database import SessionLocal
            from api.crud import upsert_darkpool_data, log_refresh
            import time
            db = SessionLocal()
            t0 = time.time()
            anomaly_set = {r["ticker"] for r in results if r.get("is_anomaly")}
            count = upsert_darkpool_data(db, results, anomaly_set)
            ms = int((time.time() - t0) * 1000)
            log_refresh(db, "darkpool", "success", count, ms)
            db.close()
            logger.info(f"SQLite: {count} darkpool records written ({ms}ms)")
        except Exception as e:
            logger.warning(f"SQLite write failed (JSON still saved): {e}")
        return ok

    def run(self, raw_data: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Main entry point.
        
        Args:
            raw_data: If provided, use this data instead of fetching.
                      Useful for testing or when data is pre-fetched.
                      
        Returns:
            List of analyzed dark pool results.
        """
        if raw_data is None:
            # In production, fetch from Quiver API
            from api.modules.quiver_client import QuiverClient
            client = QuiverClient()
            if not client.is_configured:
                logger.error("Quiver API key not configured")
                return []
            
            # Fetch popular tickers (fetching all is too expensive)
            # In practice, we'd fetch specific tickers from a watchlist
            raw_data = client.get_darkpool_data(days=DARKPOOL.history_days)

        results = self.process_raw_data(raw_data)
        self.save_results(results)
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = DarkPoolCollector()
    results = collector.run()
    
    anomalies = [r for r in results if r["is_anomaly"]]
    print(f"\n{'='*60}")
    print(f"Dark Pool Analysis Complete")
    print(f"Total tickers: {len(results)}")
    print(f"Anomalies: {len(anomalies)}")
    
    if anomalies:
        print(f"\n🌑 Dark Pool Anomalies:")
        for a in anomalies[:10]:
            print(f"  {a['ticker']:6s} | DPI: {a['dpi']:.4f} | Z: {a['z_score']:+.2f}σ | Vol: {a['total_volume']:,}")
