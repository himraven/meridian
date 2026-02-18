"""
SQLAlchemy ORM models for Meridian.

All tables map to the data previously stored in JSON files.
Schema designed for easy migration to PostgreSQL later.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, Float, String, Text, DateTime, Index,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from api.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ── Congress Trades ────────────────────────────────────────────────────────
class CongressTrade(Base):
    __tablename__ = "congress_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    politician = Column(String(200), nullable=False, index=True)
    party = Column(String(10))          # D/R/I
    chamber = Column(String(20))        # House/Senate
    bio_guide_id = Column(String(20))
    ticker = Column(String(20), nullable=False, index=True)
    company = Column(String(200))
    trade_type = Column(String(20))     # Purchase/Sale/Exchange
    amount_low = Column(Float)
    amount_high = Column(Float)
    amount_range = Column(String(50))   # "$1,001 - $15,000"
    trade_date = Column(String(10), index=True)       # YYYY-MM-DD
    filing_date = Column(String(10))
    price_at_trade = Column(Float)
    price_current = Column(Float)
    stock_return_pct = Column(Float)
    spy_return_pct = Column(Float)
    excess_return_pct = Column(Float)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint('politician', 'ticker', 'trade_date', 'trade_type',
                         name='uq_congress_trade'),
    )


# ── ARK Trades ─────────────────────────────────────────────────────────────
class ArkTrade(Base):
    __tablename__ = "ark_trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    fund = Column(String(10), nullable=False)        # ARKK/ARKW/etc
    direction = Column(String(10))                    # Buy/Sell
    ticker = Column(String(20), nullable=False, index=True)
    company = Column(String(200))
    cusip = Column(String(20))
    shares = Column(Float)
    weight = Column(Float)                            # % of ETF
    price_at_trade = Column(Float)
    price_current = Column(Float)
    return_pct = Column(Float)
    change_type = Column(String(20))
    change_pct = Column(Float)
    prev_shares = Column(Float)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint('date', 'fund', 'ticker', 'direction',
                         name='uq_ark_trade'),
    )


# ── ARK Holdings ──────────────────────────────────────────────────────────
class ArkHolding(Base):
    __tablename__ = "ark_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    fund = Column(String(10), nullable=False)
    ticker = Column(String(20), nullable=False, index=True)
    company = Column(String(200))
    cusip = Column(String(20))
    shares = Column(Float)
    market_value = Column(Float)
    weight = Column(Float)                            # % of ETF
    price = Column(Float)
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint('date', 'fund', 'ticker', name='uq_ark_holding'),
    )


# ── Dark Pool Anomalies ───────────────────────────────────────────────────
class DarkpoolAnomaly(Base):
    __tablename__ = "darkpool_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    off_exchange_volume = Column(Float)
    short_volume = Column(Float)
    total_volume = Column(Float)
    dpi = Column(Float)                               # Dark Pool Index
    off_exchange_pct = Column(Float)
    short_pct = Column(Float)
    z_score = Column(Float)
    z_score_window = Column(Integer)
    is_anomaly = Column(Integer, default=0)            # 1 if anomaly
    source = Column(String(50))
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint('ticker', 'date', name='uq_darkpool_data'),
    )


# ── Institution Filings (13F) ─────────────────────────────────────────────
class InstitutionFiling(Base):
    __tablename__ = "institution_filings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cik = Column(String(20), nullable=False, index=True)
    fund_name = Column(String(200))
    company_name = Column(String(200))
    filing_date = Column(String(10))
    quarter = Column(String(10))                      # Q3_2025
    accession = Column(String(50))
    total_value = Column(Float)
    holdings_count = Column(Integer)
    created_at = Column(DateTime, default=_utcnow)

    holdings = relationship("InstitutionHolding", back_populates="filing",
                            cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('cik', 'quarter', name='uq_institution_filing'),
    )


class InstitutionHolding(Base):
    __tablename__ = "institution_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filing_id = Column(Integer, ForeignKey("institution_filings.id"), nullable=False, index=True)
    cusip = Column(String(20))
    ticker = Column(String(20), index=True)
    issuer = Column(String(200))
    class_title = Column(String(100))
    value = Column(Float)
    shares = Column(Float)
    put_call = Column(String(10))
    investment_discretion = Column(String(20))
    pct_portfolio = Column(Float)
    created_at = Column(DateTime, default=_utcnow)

    filing = relationship("InstitutionFiling", back_populates="holdings")

    __table_args__ = (
        Index('idx_inst_holding_filing_cusip', 'filing_id', 'cusip'),
    )


# ── Confluence Signals ─────────────────────────────────────────────────────
class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    company = Column(String(200))
    score = Column(Float, index=True)
    direction = Column(String(10))                    # bullish/bearish
    source_count = Column(Integer)
    sources = Column(Text)                            # JSON array
    signal_date = Column(String(10))
    congress_score = Column(Float)
    ark_score = Column(Float)
    darkpool_score = Column(Float)
    institution_score = Column(Float)
    details = Column(Text)                            # JSON blob
    scoring = Column(Text)                            # JSON blob
    created_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint('ticker', 'signal_date', name='uq_signal'),
    )


# ── Ticker Names Cache ────────────────────────────────────────────────────
class TickerName(Base):
    __tablename__ = "ticker_names"

    ticker = Column(String(20), primary_key=True)
    company_name = Column(String(200), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    updated_at = Column(DateTime, default=_utcnow)


# ── Data Refresh Log ──────────────────────────────────────────────────────
class DataRefreshLog(Base):
    __tablename__ = "data_refresh_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)       # congress/ark/darkpool/13f/signals
    status = Column(String(20))                       # success/failed
    records_count = Column(Integer)
    duration_ms = Column(Integer)
    error_msg = Column(Text)
    created_at = Column(DateTime, default=_utcnow)
