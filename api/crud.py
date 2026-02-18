"""
CRUD operations for Meridian.

All database reads/writes go through here.
Provides a clean interface for routers and collectors.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, desc, text
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from api.db_models import (
    CongressTrade, ArkTrade, ArkHolding,
    DarkpoolAnomaly, InstitutionFiling, InstitutionHolding,
    Signal, TickerName, DataRefreshLog,
)


# ── Congress ───────────────────────────────────────────────────────────────

def upsert_congress_trades(db: Session, trades: list[dict]) -> int:
    """Bulk upsert congress trades. Returns count of rows affected."""
    count = 0
    for t in trades:
        stmt = sqlite_upsert(CongressTrade).values(
            politician=t.get("representative", t.get("politician", "")),
            party=t.get("party"),
            chamber=t.get("chamber"),
            bio_guide_id=t.get("bio_guide_id"),
            ticker=t.get("ticker", ""),
            company=t.get("company"),
            trade_type=t.get("trade_type"),
            amount_low=t.get("amount_min", t.get("amount_low")),
            amount_high=t.get("amount_max", t.get("amount_high")),
            amount_range=t.get("amount_range"),
            trade_date=t.get("transaction_date", t.get("trade_date")),
            filing_date=t.get("filing_date"),
            price_at_trade=t.get("price_at_trade"),
            price_current=t.get("price_current"),
            stock_return_pct=t.get("stock_return_pct"),
            spy_return_pct=t.get("spy_return_pct"),
            excess_return_pct=t.get("excess_return_pct"),
        ).on_conflict_do_update(
            index_elements=['politician', 'ticker', 'trade_date', 'trade_type'],
            set_={
                "price_current": t.get("price_current"),
                "stock_return_pct": t.get("stock_return_pct"),
                "spy_return_pct": t.get("spy_return_pct"),
                "excess_return_pct": t.get("excess_return_pct"),
            }
        )
        db.execute(stmt)
        count += 1
    db.commit()
    return count


def get_congress_trades(db: Session, days: int = 90, trade_type: str = None,
                        party: str = None, limit: int = 500) -> list[dict]:
    """Query congress trades with filters."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    q = db.query(CongressTrade).filter(CongressTrade.trade_date >= cutoff)
    if trade_type:
        q = q.filter(CongressTrade.trade_type.ilike(f"%{trade_type}%"))
    if party:
        q = q.filter(CongressTrade.party == party)
    q = q.order_by(desc(CongressTrade.trade_date)).limit(limit)
    return [_row_to_dict(r) for r in q.all()]


# ── ARK ────────────────────────────────────────────────────────────────────

def upsert_ark_trades(db: Session, trades: list[dict]) -> int:
    count = 0
    for t in trades:
        stmt = sqlite_upsert(ArkTrade).values(
            date=t.get("date", ""),
            fund=t.get("etf", t.get("fund", "")),
            direction=t.get("trade_type", t.get("direction")),
            ticker=t.get("ticker", ""),
            company=t.get("company"),
            cusip=t.get("cusip"),
            shares=t.get("shares"),
            weight=t.get("weight_pct", t.get("weight")),
            price_at_trade=t.get("price_at_trade"),
            price_current=t.get("price_current"),
            return_pct=t.get("return_pct"),
            change_type=t.get("change_type"),
            change_pct=t.get("change_pct"),
            prev_shares=t.get("prev_shares"),
        ).on_conflict_do_update(
            index_elements=['date', 'fund', 'ticker', 'direction'],
            set_={
                "shares": t.get("shares"),
                "weight": t.get("weight_pct", t.get("weight")),
                "price_current": t.get("price_current"),
                "return_pct": t.get("return_pct"),
            }
        )
        db.execute(stmt)
        count += 1
    db.commit()
    return count


def get_ark_trades(db: Session, days: int = 30, fund: str = None,
                   ticker: str = None, limit: int = 500) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    q = db.query(ArkTrade).filter(ArkTrade.date >= cutoff)
    if fund:
        q = q.filter(ArkTrade.fund == fund.upper())
    if ticker:
        q = q.filter(ArkTrade.ticker == ticker.upper())
    q = q.order_by(desc(ArkTrade.date)).limit(limit)
    return [_row_to_dict(r) for r in q.all()]


def upsert_ark_holdings(db: Session, holdings: list[dict]) -> int:
    count = 0
    for h in holdings:
        stmt = sqlite_upsert(ArkHolding).values(
            date=h.get("date", ""),
            fund=h.get("etf", h.get("fund", "")),
            ticker=h.get("ticker", ""),
            company=h.get("company"),
            cusip=h.get("cusip"),
            shares=h.get("shares"),
            market_value=h.get("market_value"),
            weight=h.get("weight_pct", h.get("weight")),
            price=h.get("price"),
        ).on_conflict_do_update(
            index_elements=['date', 'fund', 'ticker'],
            set_={
                "shares": h.get("shares"),
                "market_value": h.get("market_value"),
                "weight": h.get("weight_pct", h.get("weight")),
            }
        )
        db.execute(stmt)
        count += 1
    db.commit()
    return count


def get_ark_holdings(db: Session, fund: str = None, date: str = None) -> list[dict]:
    q = db.query(ArkHolding)
    if fund:
        q = q.filter(ArkHolding.fund == fund.upper())
    if date:
        q = q.filter(ArkHolding.date == date)
    else:
        # Get latest date
        latest = db.query(func.max(ArkHolding.date)).scalar()
        if latest:
            q = q.filter(ArkHolding.date == latest)
    q = q.order_by(desc(ArkHolding.weight))
    return [_row_to_dict(r) for r in q.all()]


# ── Dark Pool ──────────────────────────────────────────────────────────────

def upsert_darkpool_data(db: Session, tickers: list[dict],
                         anomaly_tickers: set = None) -> int:
    anomaly_tickers = anomaly_tickers or set()
    count = 0
    for t in tickers:
        stmt = sqlite_upsert(DarkpoolAnomaly).values(
            ticker=t.get("ticker", ""),
            date=t.get("date", ""),
            off_exchange_volume=t.get("off_exchange_volume"),
            short_volume=t.get("short_volume"),
            total_volume=t.get("total_volume"),
            dpi=t.get("dpi"),
            off_exchange_pct=t.get("off_exchange_pct"),
            short_pct=t.get("short_pct"),
            z_score=t.get("z_score"),
            z_score_window=t.get("z_score_window"),
            is_anomaly=1 if t.get("ticker") in anomaly_tickers else 0,
            source=t.get("source"),
        ).on_conflict_do_update(
            index_elements=['ticker', 'date'],
            set_={
                "dpi": t.get("dpi"),
                "z_score": t.get("z_score"),
                "is_anomaly": 1 if t.get("ticker") in anomaly_tickers else 0,
            }
        )
        db.execute(stmt)
        count += 1
    db.commit()
    return count


def get_darkpool_data(db: Session, days: int = 30, anomalies_only: bool = False,
                      ticker: str = None, limit: int = 500) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    q = db.query(DarkpoolAnomaly).filter(DarkpoolAnomaly.date >= cutoff)
    if ticker:
        q = q.filter(DarkpoolAnomaly.ticker == ticker.upper())

    all_data = q.order_by(desc(DarkpoolAnomaly.date)).limit(limit).all()
    tickers = [_row_to_dict(r) for r in all_data]
    anomalies = [_row_to_dict(r) for r in all_data if r.is_anomaly]

    return {
        "tickers": tickers,
        "anomalies": anomalies,
        "metadata": {
            "total_tickers": len(tickers),
            "anomaly_count": len(anomalies),
        }
    }


# ── Institutions (13F) ────────────────────────────────────────────────────

def upsert_institution_filing(db: Session, filing: dict, holdings: list[dict]) -> int:
    """Upsert a single institution filing with its holdings."""
    stmt = sqlite_upsert(InstitutionFiling).values(
        cik=filing.get("cik", ""),
        fund_name=filing.get("fund_name"),
        company_name=filing.get("company_name"),
        filing_date=filing.get("filing_date"),
        quarter=filing.get("quarter"),
        accession=filing.get("accession"),
        total_value=filing.get("total_value"),
        holdings_count=filing.get("holdings_count", len(holdings)),
    ).on_conflict_do_update(
        index_elements=['cik', 'quarter'],
        set_={
            "total_value": filing.get("total_value"),
            "holdings_count": filing.get("holdings_count", len(holdings)),
        }
    )
    result = db.execute(stmt)

    # Get filing ID
    filing_row = db.query(InstitutionFiling).filter_by(
        cik=filing.get("cik"), quarter=filing.get("quarter")
    ).first()

    if filing_row:
        # Delete old holdings and insert new
        db.query(InstitutionHolding).filter_by(filing_id=filing_row.id).delete()
        for h in holdings:
            db.add(InstitutionHolding(
                filing_id=filing_row.id,
                cusip=h.get("cusip"),
                ticker=h.get("ticker"),
                issuer=h.get("issuer"),
                class_title=h.get("class"),
                value=h.get("value"),
                shares=h.get("shares"),
                put_call=h.get("put_call"),
                investment_discretion=h.get("investment_discretion"),
                pct_portfolio=h.get("pct_portfolio"),
            ))
    db.commit()
    return len(holdings)


def get_institution_filings(db: Session, summary_only: bool = True) -> list[dict]:
    """Get institution filings. summary_only=True excludes holdings."""
    filings = db.query(InstitutionFiling).order_by(
        desc(InstitutionFiling.total_value)
    ).all()

    result = []
    for f in filings:
        d = _row_to_dict(f)
        if not summary_only:
            d["holdings"] = [_row_to_dict(h) for h in f.holdings]
        result.append(d)
    return result


def get_institution_holdings(db: Session, cik: str = None,
                             ticker: str = None, limit: int = 100) -> list[dict]:
    """Query specific holdings across institutions."""
    q = db.query(InstitutionHolding).join(InstitutionFiling)
    if cik:
        q = q.filter(InstitutionFiling.cik == cik)
    if ticker:
        q = q.filter(InstitutionHolding.ticker == ticker.upper())
    q = q.order_by(desc(InstitutionHolding.value)).limit(limit)
    return [_row_to_dict(r) for r in q.all()]


# ── Signals ────────────────────────────────────────────────────────────────

def upsert_signals(db: Session, signals: list[dict]) -> int:
    count = 0
    for s in signals:
        stmt = sqlite_upsert(Signal).values(
            ticker=s.get("ticker", ""),
            company=s.get("company"),
            score=s.get("score"),
            direction=s.get("direction"),
            source_count=s.get("source_count"),
            sources=json.dumps(s.get("sources", [])),
            signal_date=s.get("signal_date"),
            congress_score=s.get("congress_score"),
            ark_score=s.get("ark_score"),
            darkpool_score=s.get("darkpool_score"),
            institution_score=s.get("institution_score"),
            details=json.dumps(s.get("details", {})),
            scoring=json.dumps(s.get("scoring", {})),
        ).on_conflict_do_update(
            index_elements=['ticker', 'signal_date'],
            set_={
                "score": s.get("score"),
                "source_count": s.get("source_count"),
                "sources": json.dumps(s.get("sources", [])),
            }
        )
        db.execute(stmt)
        count += 1
    db.commit()
    return count


def get_signals(db: Session, min_score: float = 0, days: int = 30,
                limit: int = 200) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    q = db.query(Signal).filter(
        Signal.score >= min_score,
        Signal.signal_date >= cutoff,
    ).order_by(desc(Signal.score)).limit(limit)

    results = []
    for r in q.all():
        d = _row_to_dict(r)
        # Parse JSON fields back
        for field in ("sources", "details", "scoring"):
            if isinstance(d.get(field), str):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        results.append(d)
    return results


# ── Ticker Names ───────────────────────────────────────────────────────────

def upsert_ticker_names(db: Session, names: dict[str, str]) -> int:
    count = 0
    for ticker, name in names.items():
        stmt = sqlite_upsert(TickerName).values(
            ticker=ticker,
            company_name=name,
        ).on_conflict_do_update(
            index_elements=['ticker'],
            set_={"company_name": name, "updated_at": datetime.now(timezone.utc)}
        )
        db.execute(stmt)
        count += 1
    db.commit()
    return count


def get_ticker_name(db: Session, ticker: str) -> Optional[str]:
    row = db.query(TickerName).filter_by(ticker=ticker.upper()).first()
    return row.company_name if row else None


def get_all_ticker_names(db: Session) -> dict[str, str]:
    rows = db.query(TickerName).all()
    return {r.ticker: r.company_name for r in rows}


# ── Data Refresh Log ──────────────────────────────────────────────────────

def log_refresh(db: Session, source: str, status: str,
                records_count: int = 0, duration_ms: int = 0,
                error_msg: str = None):
    db.add(DataRefreshLog(
        source=source,
        status=status,
        records_count=records_count,
        duration_ms=duration_ms,
        error_msg=error_msg,
    ))
    db.commit()


def get_refresh_log(db: Session, limit: int = 50) -> list[dict]:
    rows = db.query(DataRefreshLog).order_by(
        desc(DataRefreshLog.created_at)
    ).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


# ── Helpers ────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    """Convert a SQLAlchemy model instance to dict."""
    d = {}
    for c in row.__table__.columns:
        v = getattr(row, c.name)
        if isinstance(v, datetime):
            v = v.isoformat()
        d[c.name] = v
    return d
