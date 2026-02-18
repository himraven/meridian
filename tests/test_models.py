"""
Tests for Pydantic data models.

Validates:
- All models instantiate correctly with valid data
- Validation rules catch invalid data
- Ticker normalization works
- Enum constraints are enforced
- Edge cases (boundary values, optional fields)
- PRD-specified constraints
"""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from api.models import (
    Signal, SignalType, ConfluenceScore, Confidence,
    CongressTrade, TradeType, Party, Chamber,
    DarkPoolTicker,
    ArkTrade, ArkTradeType, ArkHolding, ArkTimelinePoint,
    InstitutionFiling, ChangeType,
    ConflueceSignal,
    TickerExplorer, PriceDataPoint,
    SignalsResponse, CongressResponse, DarkPoolResponse,
    ArkTradesResponse, InstitutionsResponse,
    SIGNAL_WEIGHTS,
)


# ── Signal Tests ───────────────────────────────────────────────────────────


class TestSignal:
    def test_valid_signal(self):
        s = Signal(
            ticker="NVDA",
            type=SignalType.CONGRESS,
            date=date(2025, 1, 20),
            weight=1.0,
            metadata={"representative": "Pelosi"}
        )
        assert s.ticker == "NVDA"
        assert s.type == SignalType.CONGRESS
        assert s.weight == 1.0

    def test_ticker_normalization(self):
        s = Signal(ticker="  nvda  ", type=SignalType.ARK, date=date.today(), weight=1.0)
        assert s.ticker == "NVDA"

    def test_empty_ticker_rejected(self):
        with pytest.raises(ValidationError):
            Signal(ticker="", type=SignalType.ARK, date=date.today(), weight=1.0)

    def test_long_ticker_rejected(self):
        with pytest.raises(ValidationError):
            Signal(ticker="A" * 11, type=SignalType.ARK, date=date.today(), weight=1.0)

    def test_negative_weight_rejected(self):
        with pytest.raises(ValidationError):
            Signal(ticker="NVDA", type=SignalType.ARK, date=date.today(), weight=-0.1)

    def test_excessive_weight_rejected(self):
        with pytest.raises(ValidationError):
            Signal(ticker="NVDA", type=SignalType.ARK, date=date.today(), weight=2.1)

    def test_all_signal_types(self):
        for st in SignalType:
            s = Signal(ticker="AAPL", type=st, date=date.today(), weight=0.5)
            assert s.type == st

    def test_default_metadata_empty(self):
        s = Signal(ticker="AAPL", type=SignalType.ARK, date=date.today(), weight=1.0)
        assert s.metadata == {}


class TestSignalWeights:
    def test_prd_weights(self):
        """PRD §2.3: Congress=1.0, ARK=1.0, DPI=0.8, 13F=0.6"""
        assert SIGNAL_WEIGHTS[SignalType.CONGRESS] == 1.0
        assert SIGNAL_WEIGHTS[SignalType.ARK] == 1.0
        assert SIGNAL_WEIGHTS[SignalType.DARKPOOL] == 0.8
        assert SIGNAL_WEIGHTS[SignalType.INSTITUTIONS] == 0.6


# ── ConfluenceScore Tests ──────────────────────────────────────────────────


class TestConfluenceScore:
    def test_valid_score(self):
        cs = ConfluenceScore(
            normalized_score=8.46,
            base_score=2.8,
            recency_multiplier=0.967,
            signal_count_bonus=1.0,
            excess_return_bonus=0.52
        )
        assert cs.normalized_score == 8.46
        assert cs.confidence == Confidence.HIGH

    def test_prd_example_score(self):
        """
        PRD §2.3: Example calculation.
        
        PRD states result = 8.46, but precise math:
          Base = 1.0 + 1.0 + 0.8 = 2.8
          Recency = 1.0 - (1/30) = 0.96667
          Count bonus = 0.5 * (3-1) = 1.0
          Excess bonus = min(5.2/10, 2.0) = 0.52
          Score = (2.8 * 0.96667) + 1.0 + 0.52 = 4.2267
          Normalized = (4.2267 / 5.0) * 10 = 8.4533
          
        PRD rounds this to 8.46 (rounding up from 8.453), which implies
        the PRD used slightly rounded intermediates. We accept 8.45 as the
        precise result and verify the formula is correct.
        """
        base_score = 2.8
        recency_multiplier = 1.0 - (1 / 30)  # 0.96667
        signal_count_bonus = 0.5 * (3 - 1)  # 1.0
        excess_return_bonus = min(5.2 / 10, 2.0)  # 0.52
        confluence_score = (base_score * recency_multiplier) + signal_count_bonus + excess_return_bonus
        normalized = min((confluence_score / 5.0) * 10, 10)
        
        # Precise result: 8.4533... — PRD says 8.46 (rounded intermediates)
        # We accept 8.45 as the correct precise answer
        assert round(normalized, 2) == 8.45
        # Verify it's close to PRD's stated 8.46
        assert abs(normalized - 8.46) < 0.02

        cs = ConfluenceScore(
            normalized_score=round(normalized, 2),
            base_score=base_score,
            recency_multiplier=round(recency_multiplier, 4),
            signal_count_bonus=signal_count_bonus,
            excess_return_bonus=excess_return_bonus
        )
        assert cs.normalized_score == 8.45
        assert cs.confidence == Confidence.HIGH

    def test_medium_confidence(self):
        cs = ConfluenceScore(
            normalized_score=7.0,
            base_score=1.5,
            recency_multiplier=0.8,
            signal_count_bonus=0.5,
            excess_return_bonus=0.0
        )
        assert cs.confidence == Confidence.MEDIUM

    def test_low_confidence(self):
        cs = ConfluenceScore(
            normalized_score=4.0,
            base_score=1.0,
            recency_multiplier=0.5,
            signal_count_bonus=0.0,
            excess_return_bonus=0.0
        )
        assert cs.confidence == Confidence.LOW

    def test_score_boundaries(self):
        # Score 0 (minimum)
        cs = ConfluenceScore(
            normalized_score=0, base_score=0,
            recency_multiplier=0, signal_count_bonus=0,
            excess_return_bonus=0
        )
        assert cs.confidence == Confidence.LOW

        # Score 10 (maximum)
        cs = ConfluenceScore(
            normalized_score=10, base_score=5.0,
            recency_multiplier=1.0, signal_count_bonus=2.0,
            excess_return_bonus=2.0
        )
        assert cs.confidence == Confidence.HIGH

    def test_score_out_of_range(self):
        with pytest.raises(ValidationError):
            ConfluenceScore(
                normalized_score=11, base_score=5.0,
                recency_multiplier=1.0, signal_count_bonus=0,
                excess_return_bonus=0
            )

    def test_excess_return_bonus_capped(self):
        with pytest.raises(ValidationError):
            ConfluenceScore(
                normalized_score=8, base_score=2.0,
                recency_multiplier=0.9, signal_count_bonus=0.5,
                excess_return_bonus=3.0  # Max is 2.0
            )


# ── CongressTrade Tests ────────────────────────────────────────────────────


class TestCongressTrade:
    def test_valid_trade(self):
        t = CongressTrade(
            ticker="NVDA",
            representative="Nancy Pelosi",
            party=Party.DEMOCRAT,
            chamber=Chamber.HOUSE,
            trade_type=TradeType.PURCHASE,
            amount_range="$100,001 - $250,000",
            amount_min=100_001,
            amount_max=250_000,
            transaction_date=date(2025, 1, 20),
            filing_date=date(2025, 1, 22),
            price_at_trade=820.50,
            price_current=875.43,
            stock_return_pct=6.7,
            spy_return_pct=1.5,
            excess_return_pct=5.2,
        )
        assert t.ticker == "NVDA"
        assert t.excess_return_pct == 5.2

    def test_ticker_normalization(self):
        t = CongressTrade(
            ticker="nvda",
            representative="Test",
            party=Party.REPUBLICAN,
            chamber=Chamber.SENATE,
            trade_type=TradeType.SALE,
            amount_range="$1,001 - $15,000",
            amount_min=1_001,
            amount_max=15_000,
            transaction_date=date.today(),
        )
        assert t.ticker == "NVDA"

    def test_optional_fields(self):
        t = CongressTrade(
            ticker="AAPL",
            representative="Test",
            party=Party.DEMOCRAT,
            chamber=Chamber.HOUSE,
            trade_type=TradeType.PURCHASE,
            amount_range="$15,001 - $50,000",
            amount_min=15_001,
            amount_max=50_000,
            transaction_date=date.today(),
        )
        assert t.filing_date is None
        assert t.price_at_trade is None
        assert t.excess_return_pct is None

    def test_negative_amount_rejected(self):
        with pytest.raises(ValidationError):
            CongressTrade(
                ticker="AAPL",
                representative="Test",
                party=Party.DEMOCRAT,
                chamber=Chamber.HOUSE,
                trade_type=TradeType.PURCHASE,
                amount_range="invalid",
                amount_min=-100,
                amount_max=50_000,
                transaction_date=date.today(),
            )


# ── DarkPoolTicker Tests ──────────────────────────────────────────────────


class TestDarkPoolTicker:
    def test_valid_anomaly(self):
        dp = DarkPoolTicker(
            ticker="AMC",
            date=date(2025, 1, 25),
            otc_short=45_200_000,
            otc_total=50_800_000,
            dpi=0.89,
            dpi_30d_mean=0.55,
            dpi_30d_stddev=0.12,
            z_score=3.2,
            is_anomaly=True,
            total_volume=50_800_000,
            price=3.45,
            price_change_pct=8.5,
            sector="Entertainment",
        )
        assert dp.is_anomaly is True
        assert dp.dpi == 0.89
        assert dp.z_score == 3.2

    def test_dpi_rounding(self):
        dp = DarkPoolTicker(
            ticker="TEST",
            date=date.today(),
            otc_short=100,
            otc_total=300,
            dpi=0.33333,
            dpi_30d_mean=0.3,
            dpi_30d_stddev=0.05,
            z_score=0.67,
            total_volume=1_000_000,
        )
        assert dp.dpi == 0.3333  # Rounded to 4 decimal places

    def test_dpi_out_of_range(self):
        with pytest.raises(ValidationError):
            DarkPoolTicker(
                ticker="TEST",
                date=date.today(),
                otc_short=100,
                otc_total=300,
                dpi=1.5,  # DPI max is 1.0
                dpi_30d_mean=0.3,
                dpi_30d_stddev=0.05,
                z_score=0.5,
                total_volume=1_000_000,
            )

    def test_z_score_rounding(self):
        dp = DarkPoolTicker(
            ticker="TEST",
            date=date.today(),
            otc_short=100,
            otc_total=200,
            dpi=0.5,
            dpi_30d_mean=0.4,
            dpi_30d_stddev=0.03,
            z_score=3.333,
            total_volume=1_000_000,
        )
        assert dp.z_score == 3.33  # Rounded to 2 decimal places


# ── ArkTrade Tests ─────────────────────────────────────────────────────────


class TestArkTrade:
    def test_valid_trade(self):
        t = ArkTrade(
            ticker="COIN",
            etf="ARKK",
            trade_type=ArkTradeType.BUY,
            date=date(2025, 1, 24),
            shares=125_000,
            weight_pct=2.3,
            price_at_trade=215.50,
        )
        assert t.ticker == "COIN"
        assert t.etf == "ARKK"

    def test_etf_normalization(self):
        t = ArkTrade(
            ticker="tsla",
            etf="arkk",
            trade_type=ArkTradeType.SELL,
            date=date.today(),
            shares=50_000,
        )
        assert t.ticker == "TSLA"
        assert t.etf == "ARKK"


# ── ArkHolding Tests ───────────────────────────────────────────────────────


class TestArkHolding:
    def test_valid_holding(self):
        h = ArkHolding(
            ticker="TSLA",
            etf="ARKK",
            shares=3_200_000,
            weight_pct=8.5,
            market_value=2_100_000_000,
            date=date(2025, 1, 25),
            price=656.25,
        )
        assert h.shares == 3_200_000
        assert h.weight_pct == 8.5


# ── InstitutionFiling Tests ───────────────────────────────────────────────


class TestInstitutionFiling:
    def test_valid_filing(self):
        f = InstitutionFiling(
            ticker="NVDA",
            institution="Berkshire Hathaway",
            quarter="Q4_2024",
            shares=5_200_000,
            value=4_500_000_000,
            pct_portfolio=3.8,
            pct_change_qoq=15.3,
            change_type=ChangeType.INCREASED,
            filing_date=date(2024, 11, 14),
            prev_shares=4_500_000,
        )
        assert f.change_type == ChangeType.INCREASED

    def test_quarter_format_valid(self):
        for q in ["Q1_2024", "Q2_2025", "Q3_2023", "Q4_2026"]:
            f = InstitutionFiling(
                ticker="AAPL",
                institution="Test",
                quarter=q,
                shares=100,
                value=10_000,
                change_type=ChangeType.NEW,
                filing_date=date.today(),
            )
            assert f.quarter == q

    def test_invalid_quarter_format(self):
        with pytest.raises(ValidationError):
            InstitutionFiling(
                ticker="AAPL",
                institution="Test",
                quarter="Q5_2024",  # Invalid quarter
                shares=100,
                value=10_000,
                change_type=ChangeType.NEW,
                filing_date=date.today(),
            )

    def test_invalid_quarter_format_no_underscore(self):
        with pytest.raises(ValidationError):
            InstitutionFiling(
                ticker="AAPL",
                institution="Test",
                quarter="Q4-2024",  # Wrong separator
                shares=100,
                value=10_000,
                change_type=ChangeType.NEW,
                filing_date=date.today(),
            )

    def test_all_change_types(self):
        for ct in ChangeType:
            f = InstitutionFiling(
                ticker="AAPL",
                institution="Test",
                quarter="Q4_2024",
                shares=100,
                value=10_000,
                change_type=ct,
                filing_date=date.today(),
            )
            assert f.change_type == ct


# ── ConflueceSignal Tests ─────────────────────────────────────────────────


class TestConflueceSignal:
    def test_valid_signal(self):
        cs = ConflueceSignal(
            ticker="NVDA",
            score=8.46,
            signal_count=3,
            signals=[
                Signal(ticker="NVDA", type=SignalType.CONGRESS, date=date(2025, 1, 20), weight=1.0),
                Signal(ticker="NVDA", type=SignalType.ARK, date=date(2025, 1, 24), weight=1.0),
                Signal(ticker="NVDA", type=SignalType.DARKPOOL, date=date(2025, 1, 25), weight=0.8),
            ],
            last_activity=date(2025, 1, 25),
            confidence=Confidence.HIGH,
        )
        assert cs.score == 8.46
        assert len(cs.signals) == 3


# ── TickerExplorer Tests ───────────────────────────────────────────────────


class TestTickerExplorer:
    def test_minimal(self):
        te = TickerExplorer(ticker="AAPL")
        assert te.ticker == "AAPL"
        assert te.congress_trades == []
        assert te.chart_data == []

    def test_with_data(self):
        te = TickerExplorer(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            sector="Technology",
            market_cap=2_100_000_000_000,
            price_current=875.43,
            chart_data=[
                PriceDataPoint(
                    date=date(2025, 1, 25),
                    open=860, high=880, low=855, close=875, volume=45_000_000
                )
            ],
            external_links={
                "yahoo_finance": "https://finance.yahoo.com/quote/NVDA",
            }
        )
        assert len(te.chart_data) == 1
        assert te.external_links["yahoo_finance"].endswith("NVDA")


# ── Response Wrapper Tests ─────────────────────────────────────────────────


class TestResponseWrappers:
    def test_signals_response(self):
        sr = SignalsResponse(
            signals=[],
            metadata={"total_count": 0, "high_confidence_count": 0}
        )
        assert sr.signals == []

    def test_congress_response(self):
        cr = CongressResponse(
            trades=[],
            metadata={"total_count": 0}
        )
        assert cr.trades == []

    def test_darkpool_response(self):
        dr = DarkPoolResponse(
            tickers=[],
            metadata={"anomaly_count": 0}
        )
        assert dr.tickers == []


# ── Serialization Tests ───────────────────────────────────────────────────


class TestSerialization:
    def test_signal_to_dict(self):
        s = Signal(ticker="AAPL", type=SignalType.CONGRESS, date=date(2025, 1, 20), weight=1.0)
        d = s.model_dump()
        assert d["ticker"] == "AAPL"
        assert d["type"] == "congress"
        assert d["date"] == date(2025, 1, 20)

    def test_signal_to_json(self):
        s = Signal(ticker="AAPL", type=SignalType.CONGRESS, date=date(2025, 1, 20), weight=1.0)
        j = s.model_dump_json()
        assert "AAPL" in j
        assert "congress" in j

    def test_congress_trade_roundtrip(self):
        original = CongressTrade(
            ticker="NVDA",
            representative="Pelosi",
            party=Party.DEMOCRAT,
            chamber=Chamber.HOUSE,
            trade_type=TradeType.PURCHASE,
            amount_range="$100K-$250K",
            amount_min=100_000,
            amount_max=250_000,
            transaction_date=date(2025, 1, 20),
        )
        d = original.model_dump()
        reconstructed = CongressTrade(**d)
        assert reconstructed.ticker == original.ticker
        assert reconstructed.representative == original.representative
