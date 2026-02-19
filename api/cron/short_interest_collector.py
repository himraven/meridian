#!/usr/bin/env python3
"""
Short Interest Collector — FINRA Consolidated Short Interest

Source: FINRA API (free, no auth required)
  https://api.finra.org/data/group/OTCMarket/name/consolidatedShortInterest

FINRA publishes short interest twice a month:
  - Mid-month settlement (around the 15th)
  - End-of-month settlement (last business day)

Data includes:
  - Current short position (shares short)
  - Previous short position
  - Change (absolute and %)
  - Days to cover (short interest ratio)
  - Average daily volume
  - Settlement date

Note: FINRA does NOT provide short % of float directly.
We estimate it using shares outstanding from Yahoo Finance for top tickers.

The real alpha is in CROSS-REFERENCING:
  - High short interest + insider buying = potential squeeze
  - High short interest + institutional accumulation = smart money disagrees with shorts
"""

import json
import logging
import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import DATA_DIR

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────
FINRA_API_URL = "https://api.finra.org/data/group/OTCMarket/name/consolidatedShortInterest"

FINRA_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

FINRA_FIELDS = [
    "symbolCode",
    "currentShortPositionQuantity",
    "previousShortPositionQuantity",
    "changePreviousNumber",
    "changePercent",
    "averageDailyVolumeQuantity",
    "daysToCoverQuantity",
    "settlementDate",
]

# Batch size for FINRA API requests
BATCH_SIZE = 5000
MAX_BATCHES = 8  # Cap at ~40,000 records

# S&P 500 + popular high-short-interest tickers
# We fetch ALL tickers from FINRA for the latest date, then filter/rank
# But we also specifically look for these well-known names
PRIORITY_TICKERS = {
    # Mega caps
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
    "JPM", "V", "UNH", "JNJ", "XOM", "PG", "MA", "HD", "COST", "ABBV",
    "MRK", "AVGO", "PEP", "KO", "LLY", "TMO", "ADBE", "CRM", "WMT", "CSCO",
    "ACN", "MCD", "ABT", "NKE", "TXN", "DHR", "NEE", "PM", "RTX", "QCOM",
    "UNP", "INTC", "HON", "LOW", "IBM", "AMAT", "DE", "GE", "BA", "CAT",
    "ISRG", "AXP", "BKNG", "AMD", "MDLZ", "ADI", "SYK", "GILD", "SBUX",
    "TMUS", "MMC", "VRTX", "TJX", "PLD", "BDX", "REGN", "ZTS", "LRCX",
    "NOW", "PANW", "KLAC", "ADP", "CI", "CME", "ETN", "HUM", "DUK", "SO",
    # Popular short squeeze / retail favorites
    "GME", "AMC", "BBBY", "BB", "NOK", "PLTR", "SOFI", "RIVN", "LCID",
    "NIO", "MARA", "RIOT", "COIN", "HOOD", "SNAP", "PINS", "RBLX", "DKNG",
    "CRWD", "SNOW", "NET", "SHOP", "SQ", "PYPL", "ROKU", "UBER", "LYFT",
    "DASH", "ABNB", "ZM", "DOCU", "PTON", "BYND", "SPCE", "CLOV",
    # Biotech (often high short interest)
    "MRNA", "BNTX", "SGEN", "BIIB", "BMRN", "ALNY", "EXAS", "HALO",
}

# Minimum short interest to include in output (filter out tiny positions)
MIN_SHORT_INTEREST = 100_000  # At least 100K shares short


class ShortInterestCollector:
    """FINRA Short Interest data collector."""

    def __init__(self):
        self.data_file = DATA_DIR / "short_interest.json"
        self.session = requests.Session()
        self.session.headers.update(FINRA_HEADERS)

    # ── FINRA API ───────────────────────────────────────────

    def _fetch_finra_batch(
        self,
        settlement_date_after: str,
        limit: int = BATCH_SIZE,
        offset: int = 0,
    ) -> List[dict]:
        """Fetch a batch from the FINRA consolidated short interest API."""
        payload = {
            "fields": FINRA_FIELDS,
            "limit": limit,
            "offset": offset,
            "compareFilters": [
                {
                    "fieldName": "settlementDate",
                    "fieldValue": settlement_date_after,
                    "compareType": "GREATER",
                },
            ],
        }
        try:
            resp = self.session.post(FINRA_API_URL, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            else:
                logger.error(f"[ShortInterest] FINRA API error: {data.get('message', 'Unknown')}")
                return []
        except requests.RequestException as e:
            logger.error(f"[ShortInterest] FINRA API request failed: {e}")
            return []

    def _discover_latest_settlement_date(self) -> Optional[str]:
        """Find the most recent settlement date in FINRA data."""
        # Fetch a small sample from recent data
        cutoff = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        data = self._fetch_finra_batch(cutoff, limit=10)
        if not data:
            return None

        # All records in a batch typically share the same settlement date
        # (FINRA returns oldest first within a date filter)
        # We need to check a few to find the latest
        dates = set(d.get("settlementDate", "") for d in data)

        # Also probe with a more recent cutoff
        recent_cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        data2 = self._fetch_finra_batch(recent_cutoff, limit=10)
        if data2:
            dates.update(d.get("settlementDate", "") for d in data2)

        if not dates:
            return None

        latest = max(dates)
        logger.info(f"[ShortInterest] Latest settlement date: {latest}")
        return latest

    def fetch_all_for_date(self, settlement_date: str) -> List[dict]:
        """
        Fetch all short interest records for a specific settlement date.
        Uses pagination with offset to get all records.
        """
        # Use the day before as the filter (GREATER, not GREATER_EQUAL)
        try:
            dt = datetime.strptime(settlement_date, "%Y-%m-%d")
            filter_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
        except ValueError:
            filter_date = settlement_date

        all_records = []
        for batch_num in range(MAX_BATCHES):
            offset = batch_num * BATCH_SIZE
            batch = self._fetch_finra_batch(filter_date, limit=BATCH_SIZE, offset=offset)

            if not batch:
                break

            # Only keep records matching our target date
            matching = [r for r in batch if r.get("settlementDate") == settlement_date]
            all_records.extend(matching)

            logger.info(
                f"[ShortInterest] Batch {batch_num + 1}: {len(batch)} fetched, "
                f"{len(matching)} matching, {len(all_records)} total"
            )

            if len(batch) < BATCH_SIZE:
                break  # No more data

            time.sleep(0.5)  # Be polite to the API

        return all_records

    # ── Float / Shares Outstanding (yfinance) ─────────────

    def _fetch_float_data(self, tickers: List[str]) -> Dict[str, dict]:
        """
        Fetch shares outstanding and float data using yfinance.
        Only enriches a subset of tickers (top by SI + priority list).

        Returns dict of ticker → {shares_outstanding, float_shares, short_pct_of_float_yahoo}
        """
        float_data = {}

        try:
            import yfinance as yf
        except ImportError:
            logger.warning("[ShortInterest] yfinance not installed, skipping float enrichment")
            return float_data

        for i, ticker in enumerate(tickers):
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                float_shares = info.get("floatShares", 0) or 0
                shares_out = info.get("sharesOutstanding", 0) or 0
                short_pct = info.get("shortPercentOfFloat", 0) or 0

                if float_shares or shares_out:
                    float_data[ticker] = {
                        "shares_outstanding": shares_out,
                        "float_shares": float_shares,
                        "short_pct_of_float_yahoo": round(short_pct * 100, 2) if short_pct else 0,
                    }

                # Progress every 50 tickers
                if (i + 1) % 50 == 0:
                    print(f"[ShortInterest] Float enrichment: {i + 1}/{len(tickers)}")

            except Exception as e:
                logger.debug(f"[ShortInterest] yfinance error for {ticker}: {e}")
                continue

            # Small delay to avoid rate limits
            if (i + 1) % 10 == 0:
                time.sleep(0.3)

        logger.info(f"[ShortInterest] Got float data for {len(float_data)}/{len(tickers)} tickers")
        return float_data

    # ── Data Processing ─────────────────────────────────────

    def _process_records(
        self,
        records: List[dict],
        float_data: Dict[str, dict],
    ) -> List[dict]:
        """
        Process raw FINRA records into our standard format.
        Filters, enriches with float data, and sorts by short interest.
        """
        tickers = []

        for r in records:
            ticker = r.get("symbolCode", "")
            short_interest = r.get("currentShortPositionQuantity", 0)

            if not ticker or short_interest < MIN_SHORT_INTEREST:
                continue

            # Skip obviously non-equity symbols (warrants, units, etc.)
            if any(c in ticker for c in ["+", "=", "^"]):
                continue
            if len(ticker) > 6:
                continue

            prior = r.get("previousShortPositionQuantity", 0)
            change_pct = r.get("changePercent", 0)
            days_to_cover = r.get("daysToCoverQuantity", 0)
            avg_volume = r.get("averageDailyVolumeQuantity", 0)
            settlement_date = r.get("settlementDate", "")

            # Compute our own change_pct if not provided
            if not change_pct and prior > 0:
                change_pct = round((short_interest - prior) / prior * 100, 2)

            # Float enrichment
            fdata = float_data.get(ticker, {})
            float_shares = fdata.get("float_shares", 0)
            shares_outstanding = fdata.get("shares_outstanding", 0)
            short_pct_float = 0

            if float_shares > 0:
                short_pct_float = round(short_interest / float_shares * 100, 2)
            elif fdata.get("short_pct_of_float_yahoo"):
                short_pct_float = fdata["short_pct_of_float_yahoo"]

            tickers.append({
                "ticker": ticker,
                "short_interest": short_interest,
                "prior_short_interest": prior,
                "change": short_interest - prior,
                "change_pct": round(change_pct, 2),
                "days_to_cover": round(days_to_cover, 2) if days_to_cover else 0,
                "avg_daily_volume": avg_volume,
                "short_pct_float": short_pct_float,
                "float_shares": float_shares,
                "shares_outstanding": shares_outstanding,
                "settlement_date": settlement_date,
            })

        # Sort by short interest descending
        tickers.sort(key=lambda x: x["short_interest"], reverse=True)

        return tickers

    def _should_update(self) -> Tuple[bool, Optional[str]]:
        """
        Check if we should update. FINRA data only changes ~2x/month.
        Returns (should_update, reason).
        """
        if not self.data_file.exists():
            return True, "No existing data file"

        try:
            with open(self.data_file) as f:
                existing = json.load(f)

            existing_date = existing.get("metadata", {}).get("settlement_date", "")
            existing_updated = existing.get("metadata", {}).get("last_updated", "")

            if not existing_date:
                return True, "No settlement date in existing data"

            # Check if there's a newer settlement date available
            latest_date = self._discover_latest_settlement_date()
            if not latest_date:
                return False, "Could not determine latest settlement date"

            if latest_date > existing_date:
                return True, f"New data available: {latest_date} > {existing_date}"

            # Don't update if we already have the latest
            return False, f"Already have latest data ({existing_date})"

        except (json.JSONDecodeError, KeyError) as e:
            return True, f"Error reading existing data: {e}"

    # ── Main Pipeline ───────────────────────────────────────

    def run(self, force: bool = False) -> dict:
        """Run the full short interest collection pipeline."""
        print(f"[ShortInterest] Starting collection at {datetime.now()}")

        # Check if update is needed
        if not force:
            should_update, reason = self._should_update()
            print(f"[ShortInterest] Update check: {reason}")
            if not should_update:
                print("[ShortInterest] No update needed, skipping")
                with open(self.data_file) as f:
                    return json.load(f)

        # Step 1: Find latest settlement date
        latest_date = self._discover_latest_settlement_date()
        if not latest_date:
            print("[ShortInterest] ERROR: Could not find latest settlement date")
            return {"tickers": [], "metadata": {"error": "No settlement date found"}}

        print(f"[ShortInterest] Fetching data for settlement date: {latest_date}")

        # Step 2: Fetch all records for that date
        records = self.fetch_all_for_date(latest_date)
        if not records:
            print("[ShortInterest] ERROR: No records fetched")
            return {"tickers": [], "metadata": {"error": "No records fetched"}}

        print(f"[ShortInterest] Fetched {len(records)} total records")

        # Step 3: Do initial processing to find top tickers for float enrichment
        # First pass without float data to identify the top tickers
        preliminary = self._process_records(records, {})

        # Get top N tickers by short interest for float data enrichment
        # Keep this modest (100 tickers) to avoid slow yfinance lookups
        top_tickers = [t["ticker"] for t in preliminary[:80]]
        # Also add priority tickers if they're in the data
        all_tickers_in_data = set(t["ticker"] for t in preliminary)
        priority_in_data = [t for t in PRIORITY_TICKERS if t in all_tickers_in_data]
        tickers_for_float = list(set(top_tickers + priority_in_data))[:150]

        print(f"[ShortInterest] Fetching float data for {len(tickers_for_float)} tickers...")
        float_data = self._fetch_float_data(tickers_for_float)

        # Step 4: Final processing with float data
        processed = self._process_records(records, float_data)

        # Step 5: Find the prior settlement date from the data
        prior_dates = set()
        for r in records[:100]:
            prior = r.get("previousShortPositionQuantity", 0)
            if prior > 0:
                # We know there's prior data; compute the approximate prior date
                # FINRA settlement dates are ~15 days apart
                try:
                    dt = datetime.strptime(latest_date, "%Y-%m-%d")
                    if dt.day > 20:
                        prior_dt = dt.replace(day=15)
                    else:
                        # Go to last day of previous month
                        first_of_month = dt.replace(day=1)
                        prior_dt = first_of_month - timedelta(days=1)
                    prior_dates.add(prior_dt.strftime("%Y-%m-%d"))
                except ValueError:
                    pass
                break

        prior_settlement = max(prior_dates) if prior_dates else ""

        # Step 6: Build output
        output = {
            "tickers": processed,
            "metadata": {
                "source": "finra",
                "ticker_count": len(processed),
                "total_fetched": len(records),
                "settlement_date": latest_date,
                "prior_settlement_date": prior_settlement,
                "float_enriched_count": len(float_data),
                "last_updated": datetime.now().isoformat(),
                "schema_version": "1.0.0",
            },
        }

        # Write to file
        with open(self.data_file, "w") as f:
            json.dump(output, f, indent=2, default=str)

        # Stats
        high_short = [t for t in processed if t.get("short_pct_float", 0) >= 10]
        increasing = [t for t in processed if t.get("change_pct", 0) > 10]

        print(f"[ShortInterest] Saved {len(processed)} tickers → {self.data_file}")
        print(f"[ShortInterest] Settlement date: {latest_date}")
        print(f"[ShortInterest] High short % (≥10%): {len(high_short)}")
        print(f"[ShortInterest] Increasing (>10% change): {len(increasing)}")

        return output


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = ShortInterestCollector()
    result = collector.run(force="--force" in sys.argv)

    print(f"\n{'=' * 60}")
    print(f"Short Interest Collection Result:")
    print(f"  Tickers: {result['metadata'].get('ticker_count', 0)}")
    print(f"  Settlement: {result['metadata'].get('settlement_date', 'N/A')}")
    print(f"  Float enriched: {result['metadata'].get('float_enriched_count', 0)}")

    tickers = result.get("tickers", [])
    if tickers:
        print(f"\nTop 20 by Short Interest:")
        for t in tickers[:20]:
            pct = f"{t['short_pct_float']:.1f}%" if t.get("short_pct_float") else "N/A"
            print(
                f"  {t['ticker']:6s} | "
                f"SI={t['short_interest']:>14,} | "
                f"Chg={t['change_pct']:>7.1f}% | "
                f"DTC={t['days_to_cover']:>5.1f} | "
                f"SI/Float={pct:>6s}"
            )

        # Show highest short % of float
        with_pct = [t for t in tickers if t.get("short_pct_float", 0) > 0]
        if with_pct:
            with_pct.sort(key=lambda x: x["short_pct_float"], reverse=True)
            print(f"\nTop 20 by Short % of Float:")
            for t in with_pct[:20]:
                print(
                    f"  {t['ticker']:6s} | "
                    f"SI/Float={t['short_pct_float']:>6.1f}% | "
                    f"SI={t['short_interest']:>14,} | "
                    f"Chg={t['change_pct']:>7.1f}% | "
                    f"DTC={t['days_to_cover']:>5.1f}"
                )
