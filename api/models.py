"""
Pydantic Data Models — Smart Money Intelligence Platform

All data structures defined here with validation rules matching PRD specifications.
These models are the single source of truth for data shape across:
- Cache files (JSON)
- API responses
- Signal engine internal data
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# ── Enums ──────────────────────────────────────────────────────────────────


class SignalType(str, Enum):
    CONGRESS = "congress"
    ARK = "ark"
    DARKPOOL = "darkpool"
    INSTITUTIONS = "institutions"


class TradeType(str, Enum):
    PURCHASE = "Buy"
    SALE = "Sell"


class Party(str, Enum):
    DEMOCRAT = "Democrat"
    REPUBLICAN = "Republican"
    INDEPENDENT = "Independent"


class Chamber(str, Enum):
    HOUSE = "House"
    SENATE = "Senate"


class ArkTradeType(str, Enum):
    BUY = "Buy"
    SELL = "Sell"


class ChangeType(str, Enum):
    NEW = "New"
    INCREASED = "Increased"
    DECREASED = "Decreased"
    SOLD = "Sold"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ── Signal Weights (PRD §2.3) ─────────────────────────────────────────────

SIGNAL_WEIGHTS: Dict[SignalType, float] = {
    SignalType.CONGRESS: 1.0,
    SignalType.ARK: 1.0,
    SignalType.DARKPOOL: 0.8,
    SignalType.INSTITUTIONS: 0.6,
}


# ── Core Signal Model ─────────────────────────────────────────────────────


class Signal(BaseModel):
    """A single smart money signal from any source."""
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    type: SignalType
    date: date
    weight: float = Field(..., ge=0, le=2.0, description="Signal weight per PRD")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper().strip()


# ── Confluence Score ───────────────────────────────────────────────────────


class ConfluenceScore(BaseModel):
    """
    Computed confluence score per PRD §2.3.
    
    Formula:
        Base_Score = Sum of signal weights in window
        Recency_Multiplier = 1.0 - (Days_Since_Last_Signal / 30)
        Signal_Count_Bonus = 0.5 * (Signal_Count - 1)
        Excess_Return_Bonus = min(Congress_Excess_Return / 10, 2.0)
        Confluence_Score = (Base_Score * Recency_Multiplier) + Signal_Count_Bonus + Excess_Return_Bonus
        Normalized_Score = min(Confluence_Score / 5.0 * 10, 10)
    """
    normalized_score: float = Field(..., ge=0, le=10)
    base_score: float = Field(..., ge=0)
    recency_multiplier: float = Field(..., ge=0, le=1.0)
    signal_count_bonus: float = Field(..., ge=0)
    excess_return_bonus: float = Field(..., ge=0, le=2.0)

    @property
    def confidence(self) -> Confidence:
        if self.normalized_score >= 8:
            return Confidence.HIGH
        elif self.normalized_score >= 6:
            return Confidence.MEDIUM
        else:
            return Confidence.LOW


# ── Congress Models ────────────────────────────────────────────────────────


class CongressTrade(BaseModel):
    """A single congressional stock trade."""
    ticker: str = Field(..., min_length=1, max_length=10)
    representative: str
    party: Party
    chamber: Chamber
    trade_type: TradeType
    amount_range: str = Field(..., description="e.g. '$100,001 - $250,000'")
    amount_min: float = Field(..., ge=0, description="Minimum of reported range")
    amount_max: float = Field(..., ge=0, description="Maximum of reported range")
    transaction_date: date
    filing_date: Optional[date] = None
    price_at_trade: Optional[float] = Field(None, ge=0)
    price_current: Optional[float] = Field(None, ge=0)
    stock_return_pct: Optional[float] = None
    spy_return_pct: Optional[float] = None
    excess_return_pct: Optional[float] = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("amount_min")
    @classmethod
    def validate_amount_min(cls, v: float) -> float:
        # PRD: Signal criterion is amount ≥$15K
        # We store all trades but filter in engine
        return v


class CongressBacktestPoint(BaseModel):
    """A single data point in the backtest curve."""
    date: date
    strategy_return_pct: float
    spy_return_pct: float


class CongressBacktest(BaseModel):
    """Backtest data for Congress trading strategy."""
    strategy: str = "all_purchases"
    period: str = "1yr"
    data_points: List[CongressBacktestPoint]
    total_return_pct: float
    spy_return_pct: float
    excess_return_pct: float
    win_rate_pct: Optional[float] = None
    avg_holding_days: Optional[int] = None
    sharpe_ratio: Optional[float] = None


# ── Dark Pool Models ───────────────────────────────────────────────────────


class DarkPoolTicker(BaseModel):
    """Dark pool analytics for a single ticker on a single date."""
    ticker: str = Field(..., min_length=1, max_length=10)
    date: date
    otc_short: int = Field(..., ge=0, description="Off-exchange short volume")
    otc_total: int = Field(..., ge=0, description="Total off-exchange volume")
    dpi: float = Field(..., ge=0, le=1.0, description="Dark Pool Index = otc_short / otc_total")
    dpi_30d_mean: float = Field(..., ge=0, le=1.0)
    dpi_30d_stddev: float = Field(..., ge=0)
    z_score: float = Field(..., description="Standard deviations from 30d mean")
    is_anomaly: bool = Field(default=False, description="True if Z ≥ 2, DPI ≥ 0.4, volume ≥ 500K")
    total_volume: int = Field(..., ge=0)
    price: Optional[float] = Field(None, ge=0)
    price_change_pct: Optional[float] = None
    sector: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("dpi")
    @classmethod
    def validate_dpi(cls, v: float) -> float:
        return round(v, 4)

    @field_validator("z_score")
    @classmethod
    def validate_z_score(cls, v: float) -> float:
        return round(v, 2)


# ── ARK Models ─────────────────────────────────────────────────────────────


class ArkTrade(BaseModel):
    """A single ARK ETF trade."""
    ticker: str = Field(..., min_length=1, max_length=10)
    etf: str = Field(..., description="e.g. ARKK, ARKG, ARKF")
    trade_type: ArkTradeType
    date: date
    shares: int = Field(..., ge=0)
    weight_pct: Optional[float] = Field(None, ge=0, le=100, description="% of ETF portfolio")
    price_at_trade: Optional[float] = Field(None, ge=0)
    price_current: Optional[float] = Field(None, ge=0)
    return_pct: Optional[float] = None

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("etf")
    @classmethod
    def normalize_etf(cls, v: str) -> str:
        return v.upper().strip()


class ArkHolding(BaseModel):
    """Current ARK ETF holding."""
    ticker: str = Field(..., min_length=1, max_length=10)
    etf: str
    shares: int = Field(..., ge=0)
    weight_pct: float = Field(..., ge=0, le=100)
    market_value: Optional[float] = Field(None, ge=0)
    date: date
    price: Optional[float] = Field(None, ge=0)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper().strip()


class ArkTimelinePoint(BaseModel):
    """Position timeline data point for a ticker in an ARK ETF."""
    date: date
    etf: str
    shares: int = Field(..., ge=0)
    weight_pct: Optional[float] = None
    event_type: Optional[str] = None  # "buy", "sell", or None
    shares_traded: Optional[int] = None


# ── Institutions Models ────────────────────────────────────────────────────


class InstitutionFiling(BaseModel):
    """A 13F institutional filing entry."""
    ticker: str = Field(..., min_length=1, max_length=10)
    institution: str
    quarter: str = Field(..., pattern=r"^Q[1-4]_\d{4}$", description="e.g. Q4_2024")
    shares: int = Field(..., ge=0)
    value: float = Field(..., ge=0, description="Position value in USD")
    pct_portfolio: Optional[float] = Field(None, ge=0, le=100)
    pct_change_qoq: Optional[float] = None
    change_type: ChangeType
    filing_date: date
    prev_shares: Optional[int] = Field(None, ge=0)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, v: str) -> str:
        return v.upper().strip()


# ── Confluence Signal (API output) ─────────────────────────────────────────


class ConflueceSignal(BaseModel):
    """A scored confluence signal combining multiple sources."""
    ticker: str
    score: float = Field(..., ge=0, le=10, description="Normalized confluence score")
    signal_count: int = Field(..., ge=1)
    signals: List[Signal]
    last_activity: date
    price_current: Optional[float] = None
    price_change_pct: Optional[float] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    confidence: Confidence


# ── Ticker Explorer (Aggregated View) ──────────────────────────────────────


class PriceDataPoint(BaseModel):
    """OHLCV data for price charts."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int = Field(..., ge=0)


class TickerExplorer(BaseModel):
    """Aggregated data for Ticker Explorer modal."""
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    price_current: Optional[float] = None
    price_change_1d_pct: Optional[float] = None
    price_change_7d_pct: Optional[float] = None
    price_change_30d_pct: Optional[float] = None
    chart_data: List[PriceDataPoint] = Field(default_factory=list)
    confluence_score: Optional[float] = None
    congress_trades: List[CongressTrade] = Field(default_factory=list)
    ark_trades: List[ArkTrade] = Field(default_factory=list)
    darkpool_data: List[DarkPoolTicker] = Field(default_factory=list)
    institution_filings: List[InstitutionFiling] = Field(default_factory=list)
    external_links: Dict[str, str] = Field(default_factory=dict)


# ── API Response Wrappers ──────────────────────────────────────────────────


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    total_count: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)


class SignalsResponse(BaseModel):
    """Response for GET /api/signals/confluence"""
    signals: List[ConflueceSignal]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # metadata includes: total_count, high_confidence_count, new_today, avg_score, last_updated


class CongressResponse(BaseModel):
    """Response for GET /api/congress/trades"""
    trades: List[CongressTrade]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # metadata includes: total_count, buy_count, sell_count, avg_position, avg_excess_return_30d, last_updated


class DarkPoolResponse(BaseModel):
    """Response for GET /api/darkpool/analytics"""
    tickers: List[DarkPoolTicker]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # metadata includes: total_count, anomaly_count, avg_dpi, highest_dpi, last_updated


class ArkTradesResponse(BaseModel):
    """Response for GET /api/ark/trades"""
    trades: List[ArkTrade]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArkHoldingsResponse(BaseModel):
    """Response for GET /api/ark/holdings"""
    holdings: List[ArkHolding]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ArkTimelineResponse(BaseModel):
    """Response for GET /api/ark/timeline/{ticker}"""
    ticker: str
    timeline: List[ArkTimelinePoint]
    summary: Dict[str, Any] = Field(default_factory=dict)


class InstitutionsResponse(BaseModel):
    """Response for GET /api/institutions/filings"""
    filings: List[InstitutionFiling]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: Dict[str, Any]
    # error includes: code, message, details
