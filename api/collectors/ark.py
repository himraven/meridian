#!/usr/bin/env python3
"""
ARK Invest Collector — Migrated to new platform format.

Reads ARK changes (JSONL) and holdings (per-ETF JSON),
normalizes to ArkTrade/ArkHolding models,
writes to data/ark_trades.json and data/ark_holdings.json.

Schedule: Daily 22:00 ET (weekdays)
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import DATA_DIR, ARK_ETFS
from api.modules.cache_manager import CacheManager
from api.utils import ark_change_to_trade_type

logger = logging.getLogger(__name__)


class ARKCollector:
    """
    Normalizes ARK trade changes and holdings data.
    
    Data flow:
    1. Read ARK changes (JSONL) — buy/sell/increase/decrease events
    2. Read ARK holdings (per-ETF JSON) — current portfolio
    3. Normalize to model format
    4. Write to data/ark_trades.json and data/ark_holdings.json
    """

    def __init__(self, cache_dir: str = str(DATA_DIR)):
        self.cache = CacheManager(cache_dir)

    def normalize_trade(self, raw: Dict) -> Optional[Dict]:
        """Normalize a raw ARK change to ArkTrade model shape."""
        ticker = (raw.get("ticker") or "").upper().strip()
        if not ticker:
            return None  # Cash positions, money market

        trade_type = ark_change_to_trade_type(raw.get("type", ""))
        
        # Extract date from timestamp
        timestamp = raw.get("timestamp", "")
        trade_date = timestamp[:10] if timestamp else ""

        # Shares: different fields for different change types
        shares = raw.get("curr_shares") or raw.get("shares") or raw.get("prev_shares") or 0
        if isinstance(shares, float):
            shares = int(shares)

        return {
            "ticker": ticker,
            "etf": (raw.get("etf") or "").upper().strip(),
            "trade_type": trade_type,
            "date": trade_date,
            "shares": shares,
            "weight_pct": raw.get("weight"),
            "price_at_trade": None,  # Not available in current data
            "price_current": None,
            "return_pct": None,
            # Preserve extra useful info
            "company": raw.get("company"),
            "change_type": raw.get("type"),  # Original type (NEW_POSITION, INCREASED, etc.)
            "change_pct": round(raw.get("change_pct", 0), 2) if raw.get("change_pct") else None,
            "prev_shares": raw.get("prev_shares"),
        }

    def normalize_holding(self, raw: Dict, etf: str) -> Optional[Dict]:
        """Normalize a raw ARK holding to ArkHolding model shape."""
        ticker = (raw.get("ticker") or "").upper().strip()
        if not ticker:
            return None  # Cash/money market entries

        return {
            "ticker": ticker,
            "etf": etf.upper(),
            "shares": int(raw.get("shares", 0)),
            "weight_pct": round(raw.get("weight", 0), 2),
            "market_value": raw.get("market_value"),
            "date": raw.get("date", ""),
            "price": raw.get("share_price"),
            "company": raw.get("company"),
        }

    def process_trades(self, raw_changes: List[Dict]) -> List[Dict]:
        """Normalize all trade changes."""
        trades = []
        for raw in raw_changes:
            trade = self.normalize_trade(raw)
            if trade:
                trades.append(trade)
        
        # Sort by date descending
        trades.sort(key=lambda t: t.get("date", ""), reverse=True)
        return trades

    def process_holdings(self, raw_holdings: Dict[str, Dict]) -> List[Dict]:
        """Normalize all ETF holdings into a flat list."""
        holdings = []
        for etf, data in raw_holdings.items():
            for raw in data.get("holdings", []):
                holding = self.normalize_holding(raw, etf)
                if holding:
                    holdings.append(holding)
        
        # Sort by weight descending
        holdings.sort(key=lambda h: h.get("weight_pct", 0), reverse=True)
        return holdings

    def build_trades_metadata(self, trades: List[Dict]) -> Dict:
        buy_count = sum(1 for t in trades if t["trade_type"] == "Buy")
        sell_count = sum(1 for t in trades if t["trade_type"] == "Sell")
        
        etf_counts = {}
        for t in trades:
            etf = t.get("etf", "")
            etf_counts[etf] = etf_counts.get(etf, 0) + 1
        most_active = max(etf_counts, key=etf_counts.get) if etf_counts else ""

        return {
            "total_count": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "most_active_etf": most_active,
            "etf_breakdown": etf_counts,
            "last_updated": datetime.now().isoformat(),
        }

    def build_holdings_metadata(self, holdings: List[Dict]) -> Dict:
        etfs = set(h["etf"] for h in holdings)
        total_value = sum(h.get("market_value", 0) or 0 for h in holdings)
        top_holding = holdings[0]["ticker"] if holdings else ""

        return {
            "total_holdings": len(holdings),
            "etf_count": len(etfs),
            "total_value": round(total_value, 2),
            "top_holding": top_holding,
            "last_updated": datetime.now().isoformat(),
        }

    def save(self, trades: List[Dict], holdings: List[Dict]) -> bool:
        """Save both trades and holdings to cache."""
        ok1 = self.cache.write("ark_trades.json", {
            "trades": trades,
            "metadata": self.build_trades_metadata(trades),
        })
        ok2 = self.cache.write("ark_holdings.json", {
            "holdings": holdings,
            "metadata": self.build_holdings_metadata(holdings),
        })
        return ok1 and ok2

    def run(
        self,
        raw_changes: Optional[List[Dict]] = None,
        raw_holdings: Optional[Dict[str, Dict]] = None,
    ) -> tuple:
        """
        Main entry point.
        
        Returns:
            (trades, holdings) tuple
        """
        if raw_changes is None:
            raw_changes = []
        if raw_holdings is None:
            raw_holdings = {}

        trades = self.process_trades(raw_changes)
        holdings = self.process_holdings(raw_holdings)
        self.save(trades, holdings)
        
        logger.info(
            f"ARK: {len(trades)} trades, {len(holdings)} holdings saved"
        )
        return trades, holdings


def load_legacy_data() -> tuple:
    """
    Load from old-format ARK data files.
    
    Returns (changes_list, holdings_dict)
    """
    changes = []
    changes_path = Path("./data/ark/ark_changes.jsonl")
    if changes_path.exists():
        with open(changes_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    changes.append(json.loads(line))

    holdings = {}
    holdings_dir = Path("./data/ark/ark_holdings")
    if holdings_dir.exists():
        for f in holdings_dir.glob("*_latest.json"):
            etf = f.name.split("_")[0].upper()
            with open(f) as fh:
                holdings[etf] = json.load(fh)

    return changes, holdings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    changes, holdings = load_legacy_data()
    collector = ARKCollector()
    trades, holds = collector.run(raw_changes=changes, raw_holdings=holdings)
    
    print(f"\n✅ Migrated {len(trades)} trades, {len(holds)} holdings")
