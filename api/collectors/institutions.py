#!/usr/bin/env python3
"""
13F Institutional Filing Collector — Migrated to new platform format.

Reads from SEC EDGAR 13F filings for tracked funds,
normalizes holdings with CUSIP→ticker mapping (+ issuer fallback),
writes to data/institutions.json.

Tracked Institutions:
- Berkshire Hathaway (0001067983) - Warren Buffett
- Bridgewater Associates (0001350694) - Ray Dalio
- Citadel Advisors (0001423053) - Ken Griffin
- Renaissance Technologies (0001037389) - Jim Simons  
- Pershing Square (0001336528) - Bill Ackman
- Soros Fund Management (0001029160) - George Soros
- Appaloosa Management (0001656456) - David Tepper

Schedule: Weekly Sunday 10:00 ET
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import DATA_DIR, TRACKED_INSTITUTIONS
from api.modules.cache_manager import CacheManager
from api.utils import filing_date_to_quarter, cusip_to_ticker

logger = logging.getLogger(__name__)


class InstitutionsCollector:
    """
    Normalizes 13F institutional filings data.
    
    Key design decisions:
    - CUSIP→ticker mapping via static map (covers top holdings)
    - Issuer name always preserved as primary display name
    - Quarter derived from filing date
    - Cross-quarter change calculation (New/Increased/Decreased/Sold)
    """

    def __init__(self, cache_dir: str = str(DATA_DIR)):
        self.cache = CacheManager(cache_dir)

    def normalize_holding(self, raw: Dict, fund_name: str, filing_date: str) -> Dict:
        """Normalize a single 13F holding."""
        cusip = raw.get("cusip", "")
        ticker = cusip_to_ticker(cusip) or ""  # Empty string if not mapped
        value_raw = raw.get("value", 0)
        shares = raw.get("shares", 0)

        # Legacy collector double-multiplied value by 1000.
        # SEC 13F reports value in thousands of USD.
        # Old collector: read thousands, stored as value * 1000 (= raw USD * 1000).
        # Fix: divide by 1000 to get actual USD.
        if value_raw > 0:
            value_raw = value_raw / 1000
        
        return {
            "cusip": cusip,
            "ticker": ticker,
            "issuer": raw.get("issuer", ""),
            "class": raw.get("class", "COM"),
            "value": round(value_raw),  # Actual USD
            "shares": shares,
            "put_call": raw.get("put_call"),
            "investment_discretion": raw.get("investment_discretion"),
            "voting_authority": raw.get("voting_authority"),
        }

    def normalize_filing(self, raw: Dict) -> Dict:
        """Normalize a complete 13F filing."""
        cik = raw.get("cik", "")
        filing_date = raw.get("filing_date", "")
        company = raw.get("company", "")
        quarter = filing_date_to_quarter(filing_date)

        # Normalize holdings
        holdings = []
        total_value = 0
        for h in raw.get("holdings", []):
            normalized = self.normalize_holding(h, company, filing_date)
            holdings.append(normalized)
            total_value += normalized["value"]

        # Calculate portfolio weights
        for h in holdings:
            if total_value > 0:
                h["pct_portfolio"] = round(h["value"] / total_value * 100, 2)
            else:
                h["pct_portfolio"] = 0

        # Sort by value descending
        holdings.sort(key=lambda h: h["value"], reverse=True)

        # Fund name mapping
        fund_display = TRACKED_INSTITUTIONS.get(cik, {}).get("name", company)

        return {
            "cik": cik,
            "fund_name": fund_display,
            "company_name": company,
            "filing_date": filing_date,
            "quarter": quarter,
            "accession": raw.get("accession", ""),
            "total_value": total_value,
            "holdings_count": len(holdings),
            "holdings": holdings,
        }

    def process_filings(self, raw_filings: Dict[str, Dict]) -> List[Dict]:
        """Process all filings from all tracked institutions."""
        filings = []
        for cik, raw in raw_filings.items():
            filing = self.normalize_filing(raw)
            filings.append(filing)
        
        # Sort by total value descending
        filings.sort(key=lambda f: f["total_value"], reverse=True)
        return filings

    def build_metadata(self, filings: List[Dict]) -> Dict:
        """Build summary metadata."""
        total_aum = sum(f["total_value"] for f in filings)
        quarters = set(f["quarter"] for f in filings)
        
        return {
            "fund_count": len(filings),
            "total_aum": total_aum,
            "quarters": sorted(quarters),
            "top_fund": filings[0]["fund_name"] if filings else "",
            "last_updated": datetime.now().isoformat(),
        }

    def save(self, filings: List[Dict]) -> bool:
        """Save normalized filings to cache."""
        output = {
            "filings": filings,
            "metadata": self.build_metadata(filings),
        }
        return self.cache.write("institutions.json", output)

    def run(self, raw_filings: Optional[Dict[str, Dict]] = None) -> List[Dict]:
        """
        Main entry point.
        
        Args:
            raw_filings: Dict of {cik: filing_data}. If None, attempt API fetch.
            
        Returns:
            List of normalized filings.
        """
        if raw_filings is None:
            raw_filings = {}

        filings = self.process_filings(raw_filings)
        self.save(filings)
        
        logger.info(
            f"13F: {len(filings)} filings saved, "
            f"total AUM ${sum(f['total_value'] for f in filings)/1e9:.1f}B"
        )
        return filings


def load_legacy_data() -> Dict[str, Dict]:
    """Load from old-format 13F filing files."""
    filings_dir = Path("./data/ark/13f_filings")
    filings = {}
    
    if filings_dir.exists():
        for f in filings_dir.glob("*_latest.json"):
            cik = f.name.replace("_latest.json", "")
            with open(f) as fh:
                filings[cik] = json.load(fh)
    
    return filings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    raw_filings = load_legacy_data()
    collector = InstitutionsCollector()
    filings = collector.run(raw_filings=raw_filings)
    
    print(f"\n✅ Migrated {len(filings)} institutional filings:")
    for f in filings:
        mapped = sum(1 for h in f["holdings"] if h["ticker"])
        print(f"  {f['fund_name']:40s} | {f['holdings_count']:4d} holdings | ${f['total_value']/1e9:>8.1f}B | {mapped} tickers mapped")
