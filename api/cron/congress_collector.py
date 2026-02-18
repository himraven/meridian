#!/usr/bin/env python3
"""
US Congress Trading Collector — Quiver Quant API + Free Fallback

Primary:  Quiver Quant API (paid, better data: ExcessReturn, Party, TickerType)
Fallback: House/Senate Stock Watcher (free, S3-hosted JSONs)

Tracks star politicians: Pelosi, Tuberville, Crenshaw, etc.
"""

import json
import os
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR

# ── Config ──────────────────────────────────────────────────
QUIVER_API_KEY = os.environ.get("QUIVER_API_KEY", "")
QUIVER_BASE = "https://api.quiverquant.com/beta"

# Load from credentials file if not in env
if not QUIVER_API_KEY:
    cred_path = Path.home() / ".credentials" / "quiver.env"
    if cred_path.exists():
        for line in cred_path.read_text().splitlines():
            if line.startswith("QUIVER_API_KEY="):
                QUIVER_API_KEY = line.split("=", 1)[1].strip()

# Star politicians to highlight
TRACKED_POLITICIANS = [
    "Pelosi", "Crenshaw", "Gottheimer", "Tuberville",
    "Greene", "McCaul", "Fallon", "Mast", "Ossoff",
    "Kelly", "Hickenlooper", "Mullin", "Hagerty",
]

# Free API URLs (fallback)
HOUSE_API = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
SENATE_API = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"


class CongressCollector:
    """国会交易采集器 — Quiver API primary, free API fallback"""

    def __init__(self):
        self.data_file = DATA_DIR / "congress_trades.json"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; SmartMoneyTracker/1.0)"
        })
        self.use_quiver = bool(QUIVER_API_KEY)
        if self.use_quiver:
            print("[Congress] Using Quiver Quant API ✅")
        else:
            print("[Congress] No Quiver API key, using free APIs")

    # ── Quiver API ──────────────────────────────────────────

    def _quiver_get(self, endpoint: str, params: dict = None) -> list:
        """Generic Quiver API call."""
        url = f"{QUIVER_BASE}/{endpoint}"
        headers = {"Authorization": f"Bearer {QUIVER_API_KEY}"}
        try:
            resp = self.session.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[Congress] Quiver API error: {e}")
            return []

    def fetch_quiver_trades(self, days: int = 30) -> List[dict]:
        """Fetch recent trades from Quiver Quant API."""
        trades = []
        data = self._quiver_get("live/congresstrading", {"page_size": 200})

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        for t in data:
            report_date = t.get("ReportDate", "")
            tx_date = t.get("TransactionDate", "")

            # Filter by report date (when we'd actually see it)
            if report_date < cutoff:
                continue

            # Skip non-stock transactions
            if t.get("TickerType") not in ("Stock", None):
                continue

            ticker = t.get("Ticker", "")
            if not ticker or ticker == "--":
                continue

            trades.append({
                "chamber": t.get("House", ""),
                "politician": t.get("Representative", ""),
                "party": t.get("Party", ""),
                "ticker": ticker,
                "asset": t.get("Description", "") or "",
                "trade_type": t.get("Transaction", ""),
                "amount": t.get("Range", t.get("Amount", "")),
                "trade_date": tx_date,
                "disclosed_date": report_date,
                "excess_return": t.get("ExcessReturn"),
                "price_change": t.get("PriceChange"),
                "spy_change": t.get("SPYChange"),
                "source": "quiver",
            })

        print(f"[Congress] Quiver: {len(trades)} trades in last {days} days")
        return trades

    # ── Free API (fallback) ─────────────────────────────────

    def fetch_house_trades(self) -> List[dict]:
        """获取众议院交易 (free API)."""
        trades = []
        try:
            resp = self.session.get(HOUSE_API, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            for t in data:
                tx_date = t.get("transaction_date", "")
                if tx_date >= cutoff:
                    trades.append({
                        "chamber": "House",
                        "politician": t.get("representative", ""),
                        "party": "",
                        "ticker": t.get("ticker", ""),
                        "asset": t.get("asset_description", ""),
                        "trade_type": t.get("type", ""),
                        "amount": t.get("amount", ""),
                        "trade_date": tx_date,
                        "disclosed_date": t.get("disclosure_date", ""),
                        "excess_return": None,
                        "price_change": None,
                        "spy_change": None,
                        "source": "free_house",
                    })
            print(f"[Congress] House (free): {len(trades)} recent trades")
        except Exception as e:
            print(f"[Congress] House API error: {e}")
        return trades

    def fetch_senate_trades(self) -> List[dict]:
        """获取参议院交易 (free API)."""
        trades = []
        try:
            resp = self.session.get(SENATE_API, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            for t in data:
                tx_date = t.get("transaction_date", "")
                if tx_date >= cutoff:
                    trades.append({
                        "chamber": "Senate",
                        "politician": f"{t.get('first_name', '')} {t.get('last_name', '')}".strip(),
                        "party": "",
                        "ticker": t.get("ticker", ""),
                        "asset": t.get("asset_description", ""),
                        "trade_type": t.get("type", ""),
                        "amount": t.get("amount", ""),
                        "trade_date": tx_date,
                        "disclosed_date": t.get("disclosure_date", ""),
                        "excess_return": None,
                        "price_change": None,
                        "spy_change": None,
                        "source": "free_senate",
                    })
            print(f"[Congress] Senate (free): {len(trades)} recent trades")
        except Exception as e:
            print(f"[Congress] Senate API error: {e}")
        return trades

    # ── Core Logic ──────────────────────────────────────────

    def fetch_all_trades(self) -> List[dict]:
        """Fetch all trades from best available source."""
        if self.use_quiver:
            trades = self.fetch_quiver_trades()
            if trades:
                return trades
            print("[Congress] Quiver returned empty, falling back to free APIs")

        house = self.fetch_house_trades()
        senate = self.fetch_senate_trades()
        return house + senate

    def load_previous_trades(self) -> List[dict]:
        if self.data_file.exists():
            with open(self.data_file) as f:
                return json.load(f)
        return []

    def save_trades(self, trades: List[dict]):
        with open(self.data_file, "w") as f:
            json.dump(trades, f, indent=2, default=str)
        # Dual-write to SQLite
        self._save_to_db(trades)

    def _save_to_db(self, trades: List[dict]):
        """Write trades to SQLite database (dual-write with JSON)."""
        try:
            from api.database import SessionLocal
            from api.crud import upsert_congress_trades, log_refresh
            import time
            db = SessionLocal()
            t0 = time.time()
            count = upsert_congress_trades(db, trades)
            ms = int((time.time() - t0) * 1000)
            log_refresh(db, "congress", "success", count, ms)
            db.close()
            print(f"[Congress] SQLite: {count} trades written ({ms}ms)")
        except Exception as e:
            print(f"[Congress] SQLite write failed (JSON still saved): {e}")

    def detect_new_trades(self, current: List[dict], previous: List[dict]) -> List[dict]:
        known_keys = set()
        for t in previous:
            key = f"{t.get('politician')}|{t.get('ticker')}|{t.get('trade_type')}|{t.get('trade_date')}"
            known_keys.add(key)

        new_trades = []
        for t in current:
            key = f"{t.get('politician')}|{t.get('ticker')}|{t.get('trade_type')}|{t.get('trade_date')}"
            if key not in known_keys:
                new_trades.append(t)
        return new_trades

    def filter_star_politicians(self, trades: List[dict]) -> List[dict]:
        star_trades = []
        for t in trades:
            politician = t.get("politician", "")
            for star in TRACKED_POLITICIANS:
                if star.lower() in politician.lower():
                    t["is_star"] = True
                    star_trades.append(t)
                    break
        return star_trades

    def run(self) -> List[dict]:
        """Run collection and detect new trades."""
        print(f"[Congress] Starting collection at {datetime.now()}")

        trades = self.fetch_all_trades()
        if not trades:
            print("[Congress] No trades fetched")
            return []

        previous = self.load_previous_trades()
        new_trades = self.detect_new_trades(trades, previous)

        if new_trades:
            print(f"[Congress] {len(new_trades)} new trades detected")
            star_trades = self.filter_star_politicians(new_trades)
            if star_trades:
                print(f"[Congress] {len(star_trades)} from tracked politicians!")
        else:
            print("[Congress] No new trades (all already known)")

        self.save_trades(trades)
        return new_trades


def format_congress_changes(trades: List[dict]) -> str:
    """Format congress trades as Telegram HTML message."""
    if not trades:
        return ""

    lines = ["🏛️ <b>国会交易提醒</b>\n"]

    star_trades = [t for t in trades if t.get("is_star")]
    other_trades = [t for t in trades if not t.get("is_star")]

    if star_trades:
        lines.append("⭐ <b>明星议员交易</b>")
        for t in star_trades:
            buy = "purchase" in t.get("trade_type", "").lower() or "buy" in t.get("trade_type", "").lower()
            emoji = "🟢" if buy else "🔴"
            party = f" ({t['party']})" if t.get("party") else ""
            excess = ""
            if t.get("excess_return") is not None:
                er = t["excess_return"]
                excess = f" | 超额{'+' if er > 0 else ''}{er:.1f}%"
            lines.append(f"{emoji} <b>{t['politician']}</b>{party}")
            lines.append(f"   {t['trade_type']} <code>{t['ticker']}</code> — {t.get('amount', 'N/A')}{excess}")
            lines.append(f"   📅 交易 {t.get('trade_date', '?')} | 披露 {t.get('disclosed_date', '?')}")
        lines.append("")

    if other_trades:
        lines.append(f"📋 其他 {len(other_trades)} 笔交易")
        for t in other_trades[:8]:
            buy = "purchase" in t.get("trade_type", "").lower() or "buy" in t.get("trade_type", "").lower()
            emoji = "🟢" if buy else "🔴"
            party = f"({t['party']})" if t.get("party") else ""
            lines.append(f"{emoji} {t['politician']}{party}: {t['trade_type']} <code>{t['ticker']}</code> — {t.get('amount', 'N/A')}")
        if len(other_trades) > 8:
            lines.append(f"... 还有 {len(other_trades) - 8} 笔")

    src = "Quiver Quant" if any(t.get("source") == "quiver" for t in trades) else "House/Senate Watcher"
    lines.append(f"\n<i>数据源: {src}</i>")
    return "\n".join(lines)


if __name__ == "__main__":
    collector = CongressCollector()
    new_trades = collector.run()

    if new_trades:
        msg = format_congress_changes(new_trades)
        print("\n" + "=" * 50)
        print(msg)
    else:
        print("\n[Congress] No new trades detected")
