#!/usr/bin/env python3
"""
ARK Historical Trades Backfill Script

Fetches historical trades from arkfunds.io API and backfills ark_changes.jsonl
Date range: 2025-11-01 to 2026-02-07 (3 months)
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import sys
import time

sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR, ARK_ETFS

# arkfunds.io trades API
TRADES_API_URL = "https://arkfunds.io/api/v2/etf/trades"

# Date range for backfill
START_DATE = "2025-11-01"
END_DATE = "2026-02-06"  # Exclude today since we already have it


class ARKBackfill:
    """ARK historical trades backfill"""
    
    def __init__(self):
        self.changes_file = DATA_DIR / "ark_changes.jsonl"
        self.backup_file = DATA_DIR / "ark_changes.jsonl.backup"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; SmartMoneyTracker/1.0)"
        })
    
    def fetch_trades(self, symbol: str, date_from: str, date_to: str) -> Optional[dict]:
        """Fetch trades from arkfunds.io API"""
        url = f"{TRADES_API_URL}?symbol={symbol}&date_from={date_from}&date_to={date_to}"
        try:
            print(f"[BACKFILL] Fetching {symbol} trades from {date_from} to {date_to}...")
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            trades_count = len(data.get("trades", []))
            print(f"[BACKFILL] {symbol}: {trades_count} trades fetched")
            return data
        except Exception as e:
            print(f"[BACKFILL] Error fetching {symbol}: {e}")
            return None
    
    def convert_trade_to_change(self, trade: dict) -> dict:
        """Convert arkfunds.io trade format to ark_changes.jsonl format"""
        direction = trade.get("direction", "")
        
        # Determine change type
        if direction == "Buy":
            change_type = "INCREASED"  # Could be NEW_POSITION but we'll use INCREASED for simplicity
        elif direction == "Sell":
            change_type = "DECREASED"
        else:
            change_type = "UNKNOWN"
        
        # Convert trade to change format
        change = {
            "type": change_type,
            "etf": trade.get("fund"),
            "ticker": trade.get("ticker"),
            "company": trade.get("company"),
            "shares": trade.get("shares"),  # This is the traded shares (delta), not total position
            "change_pct": trade.get("etf_percent"),
            "weight": trade.get("etf_percent"),
            "timestamp": f"{trade.get('date')}T00:00:00",
            "source": "backfill",
            "cusip": trade.get("cusip"),
            "direction": direction,  # Keep original for reference
        }
        
        return change
    
    def fetch_all_historical_trades(self) -> list:
        """Fetch all historical trades for all ARK ETFs"""
        all_changes = []
        
        for etf_symbol in ARK_ETFS.keys():
            data = self.fetch_trades(etf_symbol, START_DATE, END_DATE)
            
            if data and "trades" in data:
                trades = data["trades"]
                for trade in trades:
                    change = self.convert_trade_to_change(trade)
                    all_changes.append(change)
            
            # Rate limiting - be nice to the API
            time.sleep(1)
        
        return all_changes
    
    def load_existing_changes(self) -> list:
        """Load existing changes from jsonl file"""
        changes = []
        if self.changes_file.exists():
            with open(self.changes_file, 'r') as f:
                for line in f:
                    if line.strip():
                        changes.append(json.loads(line))
        return changes
    
    def backup_existing_file(self):
        """Backup the existing ark_changes.jsonl"""
        if self.changes_file.exists():
            import shutil
            shutil.copy2(self.changes_file, self.backup_file)
            print(f"[BACKFILL] Backed up to {self.backup_file}")
    
    def deduplicate_changes(self, changes: list) -> list:
        """Remove duplicates based on date + ETF + ticker"""
        seen = set()
        unique_changes = []
        
        for change in changes:
            # Create a unique key from date, etf, and ticker
            timestamp = change.get("timestamp", "")
            date_part = timestamp.split("T")[0] if timestamp else ""
            etf = change.get("etf", "")
            ticker = change.get("ticker", "")
            
            key = (date_part, etf, ticker)
            
            if key not in seen:
                seen.add(key)
                unique_changes.append(change)
        
        return unique_changes
    
    def write_sorted_changes(self, changes: list):
        """Write changes sorted by timestamp"""
        # Sort by timestamp
        sorted_changes = sorted(changes, key=lambda x: x.get("timestamp", ""))
        
        # Write to file
        with open(self.changes_file, 'w') as f:
            for change in sorted_changes:
                f.write(json.dumps(change) + "\n")
        
        print(f"[BACKFILL] Wrote {len(sorted_changes)} changes to {self.changes_file}")
    
    def run(self):
        """Run the backfill process"""
        print(f"[BACKFILL] Starting ARK historical trades backfill")
        print(f"[BACKFILL] Date range: {START_DATE} to {END_DATE}")
        print(f"[BACKFILL] ETFs: {', '.join(ARK_ETFS.keys())}")
        print()
        
        # Step 1: Backup existing file
        self.backup_existing_file()
        
        # Step 2: Load existing changes (today's data)
        existing_changes = self.load_existing_changes()
        print(f"[BACKFILL] Loaded {len(existing_changes)} existing changes")
        
        # Step 3: Fetch historical trades
        historical_changes = self.fetch_all_historical_trades()
        print(f"[BACKFILL] Fetched {len(historical_changes)} historical trades")
        
        # Step 4: Combine and deduplicate
        all_changes = historical_changes + existing_changes
        unique_changes = self.deduplicate_changes(all_changes)
        print(f"[BACKFILL] After deduplication: {unique_changes} unique changes")
        
        # Step 5: Write sorted changes
        self.write_sorted_changes(unique_changes)
        
        # Summary
        print()
        print("="*60)
        print("[BACKFILL] Summary:")
        print(f"  Historical trades: {len(historical_changes)}")
        print(f"  Existing changes: {len(existing_changes)}")
        print(f"  Total unique: {len(unique_changes)}")
        
        # Date range check
        if unique_changes:
            dates = sorted(set(c.get("timestamp", "").split("T")[0] for c in unique_changes if c.get("timestamp")))
            if dates:
                print(f"  Date range: {dates[0]} to {dates[-1]}")
                print(f"  Unique dates: {len(dates)}")
        
        print("="*60)
        print(f"[BACKFILL] Backup saved at: {self.backup_file}")
        print("[BACKFILL] Done!")


if __name__ == "__main__":
    backfill = ARKBackfill()
    backfill.run()
