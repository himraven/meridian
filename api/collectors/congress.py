#!/usr/bin/env python3
"""
Congress Trading Collector — Migrated to new platform format.

Reads from Quiver API (with free API fallback), normalizes to 
CongressTrade model, writes to data/congress.json.

Output format:
{
    "trades": [CongressTrade, ...],
    "metadata": {
        "total_count": int,
        "buy_count": int, 
        "sell_count": int,
        "avg_position": float,
        "last_updated": str
    }
}

Schedule: Daily 18:00 ET (weekdays)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import DATA_DIR, CONGRESS
from api.modules.cache_manager import CacheManager
from api.modules.quiver_client import QuiverClient, fetch_free_congress_trades
from api.utils import (
    parse_amount_range,
    normalize_party,
    normalize_chamber,
    normalize_trade_type,
)

logger = logging.getLogger(__name__)

# Politicians worth highlighting
TRACKED_POLITICIANS = [
    "Pelosi", "Crenshaw", "Gottheimer", "Tuberville",
    "Greene", "McCaul", "Fallon", "Mast", "Ossoff",
    "Kelly", "Hickenlooper", "Mullin", "Hagerty",
]


class CongressCollector:
    """
    Collects Congress trading data and writes normalized JSON.
    
    Data flow:
    1. Fetch from Quiver API (or free fallback)
    2. Normalize fields to CongressTrade model shape
    3. Calculate excess returns (from Quiver data)
    4. Write to data/congress.json
    """

    def __init__(self, cache_dir: str = str(DATA_DIR)):
        self.cache = CacheManager(cache_dir)
        self.quiver = QuiverClient()

    def fetch_raw_trades(self, days: int = 365) -> List[Dict]:
        """Fetch raw trades from Quiver API with free fallback."""
        if self.quiver.is_configured:
            try:
                return self.quiver.get_congress_trades(days=days)
            except Exception as e:
                logger.warning(f"Quiver API failed, falling back to free API: {e}")
        
        return fetch_free_congress_trades(days=days)

    def normalize_trade(self, raw: Dict) -> Optional[Dict]:
        """
        Normalize a raw trade dict to CongressTrade model shape.
        
        Returns None if trade should be filtered out.
        """
        ticker = raw.get("ticker", "").upper().strip()
        if not ticker or ticker == "--":
            return None

        # Parse amount range
        amount_raw = raw.get("amount_range", raw.get("amount", ""))
        amount_min, amount_max = parse_amount_range(amount_raw)

        # Normalize fields
        party = normalize_party(raw.get("party", ""))
        chamber = normalize_chamber(raw.get("chamber", ""))
        trade_type = normalize_trade_type(
            raw.get("trade_type", raw.get("Transaction", ""))
        )

        # Dates
        trade_date = raw.get("transaction_date", raw.get("trade_date", ""))
        filing_date = raw.get("filing_date", raw.get("disclosed_date"))

        # Returns (from Quiver)
        excess_return = raw.get("excess_return")
        stock_return = raw.get("price_change")
        spy_return = raw.get("spy_change")

        return {
            "ticker": ticker,
            "representative": raw.get("representative", raw.get("politician", "")),
            "bio_guide_id": raw.get("bio_guide_id", raw.get("BioGuideID")),
            "party": party,
            "chamber": chamber,
            "trade_type": trade_type,
            "amount_range": amount_raw,
            "amount_min": amount_min,
            "amount_max": amount_max,
            "transaction_date": trade_date,
            "filing_date": filing_date,
            "price_at_trade": raw.get("price_at_trade"),
            "price_current": raw.get("price_current"),
            "stock_return_pct": round(stock_return, 2) if stock_return is not None else None,
            "spy_return_pct": round(spy_return, 2) if spy_return is not None else None,
            "excess_return_pct": round(excess_return, 2) if excess_return is not None else None,
        }

    def process_trades(self, raw_trades: List[Dict]) -> List[Dict]:
        """Normalize all raw trades, filter invalids."""
        normalized = []
        for raw in raw_trades:
            trade = self.normalize_trade(raw)
            if trade:
                normalized.append(trade)
        
        # Sort by transaction date descending
        normalized.sort(key=lambda t: t.get("transaction_date", ""), reverse=True)
        return normalized

    def build_metadata(self, trades: List[Dict]) -> Dict:
        """Compute summary metadata for the API response."""
        buy_count = sum(1 for t in trades if t["trade_type"] == "Buy")
        sell_count = sum(1 for t in trades if t["trade_type"] == "Sell")
        
        positions = [(t["amount_min"] + t["amount_max"]) / 2 for t in trades if t["amount_max"] > 0]
        avg_position = sum(positions) / len(positions) if positions else 0

        excess_returns = [t["excess_return_pct"] for t in trades if t.get("excess_return_pct") is not None]
        avg_excess = sum(excess_returns) / len(excess_returns) if excess_returns else 0

        return {
            "schema_version": "1.0.0",
            "total_count": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "avg_position": round(avg_position, 2),
            "avg_excess_return_30d": round(avg_excess, 2),
            "last_updated": datetime.now().isoformat(),
        }

    def save(self, trades: List[Dict]) -> bool:
        """Save normalized trades to cache."""
        output = {
            "trades": trades,
            "metadata": self.build_metadata(trades),
        }
        return self.cache.write("congress.json", output)

    def run(self, raw_data: Optional[List[Dict]] = None, days: int = 365) -> List[Dict]:
        """
        Main entry point.
        
        Args:
            raw_data: If provided, use instead of API fetch.
            days: How many days of trades to fetch.
            
        Returns:
            List of normalized trades.
        """
        if raw_data is None:
            raw_data = self.fetch_raw_trades(days=days)
        
        trades = self.process_trades(raw_data)
        self.save(trades)
        
        logger.info(
            f"Congress: {len(trades)} trades saved "
            f"({sum(1 for t in trades if t['trade_type']=='Buy')} buy, "
            f"{sum(1 for t in trades if t['trade_type']=='Sell')} sell)"
        )
        return trades


def load_legacy_data(path: str) -> List[Dict]:
    """
    Load data from the old-format congress_trades.json.
    
    Maps old field names to the format expected by normalize_trade():
    - politician → representative
    - trade_type → trade_type  
    - amount → amount_range
    - trade_date → transaction_date
    - disclosed_date → filing_date
    """
    import json
    with open(path) as f:
        old_data = json.load(f)
    
    mapped = []
    for t in old_data:
        mapped.append({
            "ticker": t.get("ticker", ""),
            "representative": t.get("politician", ""),
            "party": t.get("party", ""),
            "chamber": t.get("chamber", ""),
            "trade_type": t.get("trade_type", ""),
            "amount_range": t.get("amount", ""),
            "transaction_date": t.get("trade_date", ""),
            "filing_date": t.get("disclosed_date"),
            "excess_return": t.get("excess_return"),
            "price_change": t.get("price_change"),
            "spy_change": t.get("spy_change"),
        })
    return mapped


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Try loading legacy data for migration
    legacy_path = "./data/ark/congress_trades.json"
    
    collector = CongressCollector()
    
    try:
        legacy = load_legacy_data(legacy_path)
        trades = collector.run(raw_data=legacy)
        print(f"\n✅ Migrated {len(trades)} trades from legacy format")
    except FileNotFoundError:
        trades = collector.run()
        print(f"\n✅ Fetched {len(trades)} trades from API")
