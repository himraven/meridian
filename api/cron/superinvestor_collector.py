#!/usr/bin/env python3
"""
Superinvestor Portfolio Collector — Dataroma Scraper

Scrapes dataroma.com to track 13F filings of ~80 famous superinvestors
(Buffett, Soros, Ackman, Icahn, Einhorn, etc.).

Data includes:
- Aggregate quarterly buys/sells across all tracked managers
- Individual manager holdings for top ~20 managers
- Activity type (Buy/Sell/Add/Reduce) with portfolio impact

Dataroma presents 13F data in a clean, scrapable format.
Quarter filings typically appear ~45 days after quarter end.
"""

import json
import re
import sys
import time
import logging
import requests
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import DATA_DIR

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────
DATAROMA_BASE = "https://www.dataroma.com/m"

# Grand Portfolio pages (aggregate across all managers)
PORTFOLIO_BUYS_URL = f"{DATAROMA_BASE}/g/portfolio_b.php?q=q&L={{page}}"
PORTFOLIO_SELLS_URL = f"{DATAROMA_BASE}/g/portfolio_s.php?q=q&L={{page}}"

# All activity page (per-manager top 10 buys/sells)
ALL_ACTIVITY_URL = f"{DATAROMA_BASE}/allact.php?typ=a"

# Manager holdings (individual)
HOLDINGS_URL = f"{DATAROMA_BASE}/holdings.php?m={{manager}}"

# Manager activity (buys/sells)
MANAGER_ACTIVITY_URL = f"{DATAROMA_BASE}/m_activity.php?m={{manager}}&typ={{typ}}"

# Managers list
MANAGERS_URL = f"{DATAROMA_BASE}/managers.php"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Top-tier managers to scrape individual holdings for
TOP_MANAGERS = [
    "BRK",    # Warren Buffett - Berkshire Hathaway
    "psc",    # Bill Ackman - Pershing Square
    "ic",     # Carl Icahn - Icahn Capital
    "tp",     # Daniel Loeb - Third Point
    "GLRE",   # David Einhorn - Greenlight Capital
    "AM",     # David Tepper - Appaloosa Management
    "BAUPOST",# Seth Klarman - Baupost Group
    "LPC",    # Stephen Mandel - Lone Pine Capital
    "TGM",    # Chase Coleman - Tiger Global Management
    "tci",    # Chris Hohn - TCI Fund Management
    "HC",     # Li Lu - Himalaya Capital
    "SAM",    # Michael Burry - Scion Asset Management
    "PI",     # Mohnish Pabrai - Pabrai Investments
    "GFT",    # Bill & Melinda Gates Foundation Trust
    "MKL",    # Thomas Gayner - Markel Group
    "LMM",    # Bill Miller - Miller Value Partners
    "AC",     # Chuck Akre - Akre Capital Management
    "oc",     # Howard Marks - Oaktree Capital
    "vg",     # Viking Global Investors
    "VA",     # ValueAct Capital
]

REQUEST_DELAY = 1.5  # seconds between requests


class SuperinvestorCollector:
    """Superinvestor portfolio data collector using Dataroma."""

    def __init__(self):
        self.data_file = DATA_DIR / "superinvestors.json"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._manager_map: Dict[str, str] = {}  # code → full name

    # ── HTML Parsing Helpers ────────────────────────────────

    @staticmethod
    def _clean(text: str) -> str:
        """Strip HTML tags and unescape entities."""
        text = re.sub(r'<[^>]+>', '', text)
        return unescape(text).strip()

    @staticmethod
    def _parse_number(text: str) -> float:
        """Parse a number string, handling $, commas, +/- signs, %."""
        cleaned = text.replace('$', '').replace(',', '').replace('+', '').replace('%', '').strip()
        try:
            return float(cleaned) if cleaned else 0
        except ValueError:
            return 0

    @staticmethod
    def _parse_int(text: str) -> int:
        """Parse an integer from text."""
        cleaned = text.replace(',', '').replace('+', '').strip()
        try:
            return int(float(cleaned)) if cleaned else 0
        except ValueError:
            return 0

    def _fetch(self, url: str) -> Optional[str]:
        """Fetch a URL with error handling and rate limiting."""
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return resp.text
        except requests.RequestException as e:
            logger.error(f"[Superinvestor] Fetch error for {url}: {e}")
            return None

    # ── Manager List ────────────────────────────────────────

    def fetch_managers(self) -> Dict[str, str]:
        """Fetch the full list of tracked managers from Dataroma."""
        html = self._fetch(MANAGERS_URL)
        if not html:
            return {}

        managers = {}
        matches = re.findall(
            r'<a href="/m/holdings\.php\?m=([^"]+)"[^>]*>([^<]+)</a>',
            html
        )
        for code, name in matches:
            managers[code] = name.strip()

        self._manager_map = managers
        logger.info(f"[Superinvestor] Found {len(managers)} managers")
        return managers

    # ── Grand Portfolio (Aggregate Buys/Sells) ──────────────

    def _parse_portfolio_table(self, html: str, activity_type: str) -> List[dict]:
        """Parse the grand portfolio buys or sells table."""
        results = []

        # Extract quarter info
        quarter_match = re.search(r'<b>(Q\d)\s+(\d{4})</b>', html)
        quarter = f"{quarter_match.group(1)} {quarter_match.group(2)}" if quarter_match else ""

        # Find all rows in the grid table
        tbody_match = re.search(r'<tbody>(.*?)</tbody>', html, re.DOTALL)
        if not tbody_match:
            return results

        rows = re.findall(r'<tr>(.*?)</tr>', tbody_match.group(1), re.DOTALL)

        for row in rows:
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) < 7:
                continue

            try:
                # Cell 0: Symbol with link
                sym_match = re.search(r'sym=([^"]+)', cells[0])
                ticker = sym_match.group(1) if sym_match else ""

                # Cell 1: Stock name with link
                stock_text = self._clean(cells[1])

                # Cell 2: % of portfolio
                portfolio_pct = self._parse_number(self._clean(cells[2]))

                # Cell 3: Number of buys/sells (manager count)
                manager_count = self._parse_int(self._clean(cells[3]))

                # Cell 4: Hold price
                hold_price = self._parse_number(self._clean(cells[4]))

                # Cell 5: Current price
                current_price = self._parse_number(self._clean(cells[5]))

                if not ticker:
                    continue

                results.append({
                    "ticker": ticker,
                    "company": stock_text,
                    "activity_type": activity_type,
                    "portfolio_pct": portfolio_pct,
                    "manager_count": manager_count,
                    "hold_price": hold_price,
                    "current_price": current_price,
                    "quarter": quarter,
                })
            except (ValueError, IndexError) as e:
                logger.debug(f"Skip row parse error: {e}")
                continue

        return results

    def fetch_aggregate_activity(self, activity_type: str = "Buy", pages: int = 3) -> List[dict]:
        """Fetch aggregate buys or sells across all managers."""
        all_results = []
        url_template = PORTFOLIO_BUYS_URL if activity_type == "Buy" else PORTFOLIO_SELLS_URL

        for page in range(1, pages + 1):
            url = url_template.format(page=page)
            html = self._fetch(url)
            if not html:
                break

            results = self._parse_portfolio_table(html, activity_type)
            all_results.extend(results)
            logger.info(f"[Superinvestor] {activity_type} page {page}: {len(results)} stocks")

            if not results:
                break

        return all_results

    # ── All Activity (Per-Manager Top 10) ───────────────────

    def fetch_all_activity(self) -> List[dict]:
        """Fetch the all-activity page showing top 10 buys/sells per manager."""
        html = self._fetch(ALL_ACTIVITY_URL)
        if not html:
            return []

        results = []
        tbody_match = re.search(r'<tbody>(.*?)</tbody>', html, re.DOTALL)
        if not tbody_match:
            return results

        rows = re.findall(r'<tr>(.*?)</tr>', tbody_match.group(1), re.DOTALL)

        for row in rows:
            # Extract manager name from first cell
            firm_match = re.search(r'<td class="firm"><a[^>]*>([^<]+)</a>', row)
            if not firm_match:
                continue

            manager_name = firm_match.group(1).strip()

            # Extract period
            period_match = re.search(r'<td class="period">([^<]+)</td>', row)
            period = period_match.group(1).strip() if period_match else ""

            # Extract all stock activities (they're in tooltip divs)
            activities = re.findall(
                r'<a class="(buy|sell)"[^>]*>([A-Z][A-Z0-9.]*)</a>\s*'
                r'<div>([^<]+)<br/>(Buy|Sell|Add[^<]*|Reduce[^<]*)<br/>'
                r'Change to portfolio:\s*([\d.]+)%</div>',
                row, re.DOTALL
            )

            for direction, ticker, company, action, pct_change in activities:
                action_clean = action.strip()
                # Classify activity type
                if action_clean.startswith("Buy"):
                    activity_type = "Buy"
                elif action_clean.startswith("Add"):
                    activity_type = "Add"
                elif action_clean.startswith("Sell"):
                    activity_type = "Sell"
                elif action_clean.startswith("Reduce"):
                    activity_type = "Reduce"
                else:
                    activity_type = action_clean

                # Parse percentage change from action (e.g., "Add 12.34%", "Reduce -33.76%")
                pct_match = re.search(r'(-?[\d.]+)%', action_clean)
                change_pct = float(pct_match.group(1)) if pct_match else 0

                results.append({
                    "manager": manager_name,
                    "ticker": ticker,
                    "company": company.strip(),
                    "activity_type": activity_type,
                    "change_pct": change_pct,
                    "portfolio_impact_pct": float(pct_change),
                    "period": period,
                    "direction": "Bullish" if direction == "buy" else "Bearish",
                })

        logger.info(f"[Superinvestor] All activity: {len(results)} entries from {len(rows)} managers")
        return results

    # ── Individual Manager Holdings ─────────────────────────

    def _parse_holdings_page(self, html: str, manager_code: str) -> dict:
        """Parse an individual manager's holdings page."""
        result = {
            "code": manager_code,
            "manager": "",
            "period": "",
            "portfolio_date": "",
            "num_stocks": 0,
            "portfolio_value": "",
            "top_holdings": [],
        }

        # Extract manager name
        name_match = re.search(r'<div id="f_name">([^<]+)</div>', html)
        if name_match:
            result["manager"] = name_match.group(1).strip()

        # Extract metadata
        period_match = re.search(r'Period:\s*<span>([^<]+)</span>', html)
        if period_match:
            result["period"] = period_match.group(1).strip()

        date_match = re.search(r'Portfolio date:\s*<span>([^<]+)</span>', html)
        if date_match:
            result["portfolio_date"] = date_match.group(1).strip()

        stocks_match = re.search(r'No\. of stocks:\s*<span>(\d+)</span>', html)
        if stocks_match:
            result["num_stocks"] = int(stocks_match.group(1))

        value_match = re.search(r'Portfolio value:\s*<span>\$([^<]+)</span>', html)
        if value_match:
            result["portfolio_value"] = value_match.group(1).strip()

        # Parse holdings table - rows are not wrapped in <tr> consistently
        # Each holding has cells: history, stock, %portfolio, activity, shares, price, value
        # The structure is: <td class="hist">... followed by <td class="stock">...
        # Then: <td>pct</td> <td class="...">activity</td> <td>shares</td> <td>price</td> <td>value</td>

        # Find all holding rows by looking for stock cells
        stock_entries = re.findall(
            r'<td class="stock"><a href="/m/stock\.php\?sym=([^"]+)">([^<]+)<span>\s*-\s*([^<]+)</span></a></td>\s*'
            r'<td>([\d.]+)</td>\s*'
            r'<td class="[^"]*">([^<]*)</td>\s*'
            r'<td>([\d,]+)</td>\s*'
            r'<td>\$?([\d.,]+)</td>\s*'
            r'<td>\$?([\d.,]+)</td>',
            html, re.DOTALL
        )

        for ticker, ticker_dup, company, pct, activity, shares, price, value in stock_entries:
            activity = activity.strip()
            activity_type = ""
            change_pct = 0.0

            if activity:
                if "Buy" in activity:
                    activity_type = "Buy"
                elif "Add" in activity:
                    activity_type = "Add"
                    pct_m = re.search(r'([\d.]+)%', activity)
                    if pct_m:
                        change_pct = float(pct_m.group(1))
                elif "Sell" in activity:
                    activity_type = "Sell"
                    pct_m = re.search(r'([\d.]+)%', activity)
                    if pct_m:
                        change_pct = -float(pct_m.group(1))
                elif "Reduce" in activity:
                    activity_type = "Reduce"
                    pct_m = re.search(r'([\d.]+)%', activity)
                    if pct_m:
                        change_pct = -float(pct_m.group(1))

            result["top_holdings"].append({
                "ticker": ticker.strip(),
                "company": company.strip(),
                "portfolio_pct": float(pct),
                "recent_activity": activity_type,
                "change_pct": change_pct,
                "shares": self._parse_int(shares),
                "reported_price": self._parse_number(price),
                "value": self._parse_number(value),
            })

        return result

    def fetch_manager_holdings(self, manager_code: str) -> Optional[dict]:
        """Fetch holdings for a specific manager."""
        url = HOLDINGS_URL.format(manager=manager_code)
        html = self._fetch(url)
        if not html:
            return None

        result = self._parse_holdings_page(html, manager_code)
        logger.info(
            f"[Superinvestor] {result['manager']}: "
            f"{len(result['top_holdings'])} holdings, "
            f"${result['portfolio_value']}"
        )
        return result

    # ── Manager Activity (Buys/Sells Detail) ────────────────

    def _parse_manager_activity(self, html: str, manager_code: str, typ: str) -> List[dict]:
        """Parse a manager's buy or sell activity page."""
        results = []
        manager_name = self._manager_map.get(manager_code, manager_code)

        # Name from page
        name_match = re.search(r'<div id="f_name">([^<]+)</div>', html)
        if name_match:
            manager_name = name_match.group(1).strip()

        # The activity data is in rows, but without proper <tr> tags after tbody
        # Pattern: quarter headers + activity rows
        # Quarter headers: <tr class="q_chg"><td colspan="5"><b>Q4</b> &nbsp<b>2025</b></td></tr>
        # Activity rows: <td class="hist">... <td class="stock">... <td class="buy/sell">...

        current_quarter = ""

        # Split content by quarter headers
        parts = re.split(r'<tr class="q_chg"><td colspan="5"><b>(Q\d)</b>\s*&nbsp;?\s*<b>(\d{4})</b></td></tr>', html)

        for i in range(1, len(parts), 3):
            if i + 2 > len(parts):
                break
            q_num = parts[i]
            q_year = parts[i + 1]
            current_quarter = f"{q_num} {q_year}"
            chunk = parts[i + 2]

            # Extract activity entries from this quarter
            entries = re.findall(
                r'<td class="stock"><a href="/m/stock\.php\?sym=([^"]+)">([^<]+)<span>\s*-\s*([^<]+)</span></a></td>\s*'
                r'<td class="(?:buy|sell)">([^<]*)</td>\s*'
                r'<td class="(?:buy|sell)">([\d,]+)</td>\s*'
                r'<td>([\d.]+)</td>',
                chunk, re.DOTALL
            )

            for ticker, _dup, company, action, share_change, pct_change in entries:
                action = action.strip()
                if "Buy" in action:
                    activity_type = "Buy"
                elif "Add" in action:
                    activity_type = "Add"
                elif "Sell" in action:
                    activity_type = "Sell"
                elif "Reduce" in action:
                    activity_type = "Reduce"
                else:
                    activity_type = action or typ.capitalize()

                change_pct = 0.0
                pct_m = re.search(r'([\d.]+)%', action)
                if pct_m:
                    change_pct = float(pct_m.group(1))
                    if activity_type in ("Sell", "Reduce"):
                        change_pct = -change_pct

                results.append({
                    "manager": manager_name,
                    "ticker": ticker.strip(),
                    "company": company.strip(),
                    "activity_type": activity_type,
                    "share_change": self._parse_int(share_change),
                    "change_pct": change_pct,
                    "portfolio_impact_pct": float(pct_change) if pct_change else 0,
                    "quarter": current_quarter,
                })

        return results

    def fetch_manager_activity(self, manager_code: str, typ: str = "b") -> List[dict]:
        """Fetch buy or sell activity for a specific manager."""
        url = MANAGER_ACTIVITY_URL.format(manager=manager_code, typ=typ)
        html = self._fetch(url)
        if not html:
            return []

        results = self._parse_manager_activity(html, manager_code, typ)
        logger.info(f"[Superinvestor] {manager_code} {'buys' if typ == 'b' else 'sells'}: {len(results)} entries")
        return results

    # ── Main Pipeline ───────────────────────────────────────

    def run(self) -> dict:
        """Run the full collection pipeline."""
        print(f"[Superinvestor] Starting collection at {datetime.now()}")

        # Step 1: Fetch manager list
        managers = self.fetch_managers()

        # Step 2: Fetch aggregate buys and sells (Grand Portfolio)
        print("[Superinvestor] Fetching aggregate buys...")
        agg_buys = self.fetch_aggregate_activity("Buy", pages=5)
        print(f"[Superinvestor] Got {len(agg_buys)} aggregate buy entries")

        print("[Superinvestor] Fetching aggregate sells...")
        agg_sells = self.fetch_aggregate_activity("Sell", pages=5)
        print(f"[Superinvestor] Got {len(agg_sells)} aggregate sell entries")

        # Step 3: Fetch all-activity page (per-manager top 10)
        print("[Superinvestor] Fetching all-manager activity...")
        all_activity = self.fetch_all_activity()
        print(f"[Superinvestor] Got {len(all_activity)} activity entries")

        # Step 4: Fetch individual manager holdings for top managers
        print(f"[Superinvestor] Fetching holdings for {len(TOP_MANAGERS)} top managers...")
        holdings = {}
        for code in TOP_MANAGERS:
            manager_data = self.fetch_manager_holdings(code)
            if manager_data and manager_data.get("top_holdings"):
                holdings[code] = manager_data

        print(f"[Superinvestor] Got holdings for {len(holdings)} managers")

        # Step 5: Build output
        # Combine aggregate data with per-manager activity
        activity = []

        # Add aggregate buy/sell data
        for entry in agg_buys + agg_sells:
            activity.append({
                "ticker": entry["ticker"],
                "company": entry["company"],
                "activity_type": entry["activity_type"],
                "portfolio_pct": entry.get("portfolio_pct", 0),
                "manager_count": entry.get("manager_count", 0),
                "hold_price": entry.get("hold_price", 0),
                "current_price": entry.get("current_price", 0),
                "quarter": entry.get("quarter", ""),
                "source": "aggregate",
            })

        # Add per-manager activity data
        for entry in all_activity:
            activity.append({
                "manager": entry["manager"],
                "ticker": entry["ticker"],
                "company": entry["company"],
                "activity_type": entry["activity_type"],
                "change_pct": entry.get("change_pct", 0),
                "portfolio_impact_pct": entry.get("portfolio_impact_pct", 0),
                "period": entry.get("period", ""),
                "direction": entry.get("direction", ""),
                "source": "per_manager",
            })

        # Compute some summary stats
        buy_tickers = set(e["ticker"] for e in activity if e["activity_type"] in ("Buy", "Add"))
        sell_tickers = set(e["ticker"] for e in activity if e["activity_type"] in ("Sell", "Reduce"))

        output = {
            "activity": activity,
            "holdings": holdings,
            "managers": managers,
            "metadata": {
                "source": "dataroma",
                "manager_count": len(managers),
                "holdings_scraped": len(holdings),
                "activity_count": len(activity),
                "aggregate_buys": len(agg_buys),
                "aggregate_sells": len(agg_sells),
                "per_manager_activities": len(all_activity),
                "unique_buy_tickers": len(buy_tickers),
                "unique_sell_tickers": len(sell_tickers),
                "last_updated": datetime.now().isoformat(),
            },
        }

        # Write to file
        with open(self.data_file, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print(f"[Superinvestor] Saved → {self.data_file}")
        print(f"[Superinvestor] Activity: {len(activity)} entries")
        print(f"[Superinvestor] Holdings: {len(holdings)} managers")
        print(f"[Superinvestor] Buy tickers: {len(buy_tickers)}, Sell tickers: {len(sell_tickers)}")

        return output


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = SuperinvestorCollector()
    result = collector.run()

    print(f"\n{'='*50}")
    print(f"Superinvestor Collection Result:")
    print(f"  Managers tracked: {result['metadata']['manager_count']}")
    print(f"  Holdings scraped: {result['metadata']['holdings_scraped']}")
    print(f"  Activity entries: {result['metadata']['activity_count']}")
    print(f"  Aggregate buys: {result['metadata']['aggregate_buys']}")
    print(f"  Aggregate sells: {result['metadata']['aggregate_sells']}")

    # Show top buys by manager count
    agg = [a for a in result["activity"] if a.get("source") == "aggregate" and a.get("activity_type") == "Buy"]
    agg.sort(key=lambda x: x.get("manager_count", 0), reverse=True)
    if agg:
        print(f"\nTop Buys by Manager Count:")
        for a in agg[:15]:
            print(f"  {a['ticker']:8s} | {a.get('manager_count', 0):2d} managers | "
                  f"{a.get('portfolio_pct', 0):.3f}% portfolio | {a['company']}")
