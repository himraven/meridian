"""
Data Access Layer — unified interface for reading smart money data.

Reads from SQLite database first, falls back to JSON files.
This allows gradual migration: routers call this instead of 
directly reading JSON files.

Usage in routers:
    from api.data_access import dao
    trades = dao.get_congress_trades(days=90)
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from api.database import SessionLocal, engine
from api import crud
from api.shared import smart_money_cache


class DataAccess:
    """Unified data access: SQLite primary, JSON fallback."""

    def _db_available(self) -> bool:
        """Check if SQLite DB has data."""
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM congress_trades")).scalar()
                return count > 0
        except Exception:
            return False

    # ── Congress ───────────────────────────────────────────────────────

    def get_congress_trades(self, days: int = 90, trade_type: str = None,
                            party: str = None, limit: int = 500) -> dict:
        """Get congress trades with metadata."""
        try:
            db = SessionLocal()
            trades = crud.get_congress_trades(db, days=days, trade_type=trade_type,
                                               party=party, limit=limit)
            db.close()

            if trades:
                buy_count = sum(1 for t in trades if 'purchase' in (t.get('trade_type') or '').lower()
                                or 'buy' in (t.get('trade_type') or '').lower())
                sell_count = len(trades) - buy_count
                return {
                    "trades": trades,
                    "metadata": {
                        "total_count": len(trades),
                        "buy_count": buy_count,
                        "sell_count": sell_count,
                        "source": "sqlite",
                    }
                }
        except Exception:
            pass

        # Fallback to JSON
        data = smart_money_cache.read("congress.json")
        if data:
            data.setdefault("metadata", {})["source"] = "json"
        return data or {"trades": [], "metadata": {"source": "none"}}

    # ── ARK ────────────────────────────────────────────────────────────

    def get_ark_trades(self, days: int = 30, fund: str = None,
                       ticker: str = None, limit: int = 500) -> dict:
        try:
            db = SessionLocal()
            trades = crud.get_ark_trades(db, days=days, fund=fund,
                                          ticker=ticker, limit=limit)
            db.close()

            if trades:
                buy_count = sum(1 for t in trades if 'buy' in (t.get('direction') or '').lower())
                return {
                    "trades": trades,
                    "metadata": {
                        "total_count": len(trades),
                        "buy_count": buy_count,
                        "sell_count": len(trades) - buy_count,
                        "source": "sqlite",
                    }
                }
        except Exception:
            pass

        data = smart_money_cache.read("ark_trades.json")
        if data:
            data.setdefault("metadata", {})["source"] = "json"
        return data or {"trades": [], "metadata": {"source": "none"}}

    def get_ark_holdings(self, fund: str = None, date: str = None) -> dict:
        try:
            db = SessionLocal()
            holdings = crud.get_ark_holdings(db, fund=fund, date=date)
            db.close()

            if holdings:
                return {
                    "holdings": holdings,
                    "metadata": {
                        "total_holdings": len(holdings),
                        "source": "sqlite",
                    }
                }
        except Exception:
            pass

        data = smart_money_cache.read("ark_holdings.json")
        if data:
            data.setdefault("metadata", {})["source"] = "json"
        return data or {"holdings": [], "metadata": {"source": "none"}}

    # ── Dark Pool ──────────────────────────────────────────────────────

    def get_darkpool_data(self, days: int = 30, anomalies_only: bool = False,
                          ticker: str = None) -> dict:
        try:
            db = SessionLocal()
            result = crud.get_darkpool_data(db, days=days,
                                             anomalies_only=anomalies_only,
                                             ticker=ticker)
            db.close()

            if result and result.get("tickers"):
                result["metadata"]["source"] = "sqlite"
                return result
        except Exception:
            pass

        data = smart_money_cache.read("darkpool.json")
        if data:
            data.setdefault("metadata", {})["source"] = "json"
        return data or {"tickers": [], "anomalies": [], "metadata": {"source": "none"}}

    # ── Institutions (13F) ─────────────────────────────────────────────

    def get_institution_filings(self, summary_only: bool = True) -> dict:
        try:
            db = SessionLocal()
            filings = crud.get_institution_filings(db, summary_only=summary_only)
            db.close()

            if filings:
                total_aum = sum(f.get("total_value", 0) or 0 for f in filings)
                return {
                    "filings": filings,
                    "metadata": {
                        "fund_count": len(filings),
                        "total_aum": total_aum,
                        "source": "sqlite",
                    }
                }
        except Exception:
            pass

        data = smart_money_cache.read("institutions.json")
        if data:
            data.setdefault("metadata", {})["source"] = "json"
        return data or {"filings": [], "metadata": {"source": "none"}}

    def get_institution_holdings(self, cik: str = None,
                                  ticker: str = None) -> list[dict]:
        try:
            db = SessionLocal()
            holdings = crud.get_institution_holdings(db, cik=cik, ticker=ticker)
            db.close()
            return holdings
        except Exception:
            return []

    # ── Signals ────────────────────────────────────────────────────────

    def get_signals(self, min_score: float = 0, days: int = 30) -> dict:
        try:
            db = SessionLocal()
            signals = crud.get_signals(db, min_score=min_score, days=days)
            db.close()

            if signals:
                return {
                    "signals": signals,
                    "metadata": {
                        "total_count": len(signals),
                        "source": "sqlite",
                    }
                }
        except Exception:
            pass

        data = smart_money_cache.read("signals.json")
        if data:
            data.setdefault("metadata", {})["source"] = "json"
        return data or {"signals": [], "metadata": {"source": "none"}}

    # ── Ticker Names ───────────────────────────────────────────────────

    def get_ticker_name(self, ticker: str) -> Optional[str]:
        try:
            db = SessionLocal()
            name = crud.get_ticker_name(db, ticker)
            db.close()
            return name
        except Exception:
            return None

    def get_all_ticker_names(self) -> dict[str, str]:
        try:
            db = SessionLocal()
            names = crud.get_all_ticker_names(db)
            db.close()
            if names:
                return names
        except Exception:
            pass

        data = smart_money_cache.read("ticker_names.json")
        return data.get("names", {}) if data else {}

    # ── Refresh Log ────────────────────────────────────────────────────

    def get_refresh_log(self, limit: int = 50) -> list[dict]:
        try:
            db = SessionLocal()
            log = crud.get_refresh_log(db, limit=limit)
            db.close()
            return log
        except Exception:
            return []


# Singleton
dao = DataAccess()
