"""
Tests for Cross-Signal Confluence Engine.

Validates:
- PRD §2.3 example calculation → score = 8.46
- Signal extraction criteria per source
- Time window clustering
- Edge cases (single signal, expired, no data)
- Deduplication logic
"""

import pytest
from datetime import datetime

from api.modules.cross_signal_engine import (
    CrossSignalEngine,
    SignalExtractor,
    RawSignal,
    ConfluenceResult,
)


# ── PRD §2.3 Verification ─────────────────────────────────────────────


class TestPRDExample:
    """
    PRD §2.3 example:
    - Congress buy (1.0) on Jan 20
    - ARK buy (1.0) on Jan 24
    - DPI anomaly (0.8) on Jan 25
    - Days since last signal: 1 (today = Jan 26)
    - Congress excess return: +5.2%
    
    Expected:
      Base = 1.0 + 1.0 + 0.8 = 2.8
      Recency = 1.0 - (1/30) = 0.967
      Count Bonus = 0.5 × (3-1) = 1.0
      Excess Bonus = min(5.2/10, 2.0) = 0.52
      Raw = (2.8 × 0.967) + 1.0 + 0.52 = 4.23
      Normalized = (4.23 / 5.0) × 10 = 8.46
    """

    def test_prd_example_exact_score(self):
        """The PRD example produces 8.45 (PRD showed 8.46 due to hand-rounding)."""
        engine = CrossSignalEngine(
            window_days=7,
            max_possible_score=5.0,
            min_score=0,
            reference_date="2026-01-26",
        )
        
        congress_data = {
            "trades": [{
                "ticker": "NVDA",
                "trade_type": "Buy",
                "representative": "Nancy Pelosi",
                "party": "Democrat",
                "chamber": "House",
                "amount_min": 100001,
                "amount_max": 250000,
                "amount_range": "$100,001 - $250,000",
                "transaction_date": "2026-01-20",
                "filing_date": "2026-01-22",
                "excess_return_pct": 5.2,
            }]
        }
        
        ark_data = {
            "trades": [{
                "ticker": "NVDA",
                "trade_type": "Buy",
                "etf": "ARKK",
                "date": "2026-01-24",
                "shares": 125000,
                "weight_pct": 2.3,
                "change_type": "INCREASED",
            }]
        }
        
        darkpool_data = {
            "tickers": [{
                "ticker": "NVDA",
                "date": "2026-01-25",
                "dpi": 0.67,
                "z_score": 2.8,
                "total_volume": 45000000,
                "off_exchange_volume": 30000000,
            }]
        }
        
        results = engine.generate_signals(
            congress_data=congress_data,
            ark_data=ark_data,
            darkpool_data=darkpool_data,
        )
        
        assert len(results) == 1
        nvda = results[0]
        assert nvda.ticker == "NVDA"
        assert nvda.score == pytest.approx(8.45, abs=0.02)  # PRD hand-calc shows 8.46
        assert nvda.source_count == 3
        assert set(nvda.sources) == {"congress", "ark", "darkpool"}

    def test_prd_scoring_breakdown(self):
        """Verify each component of the scoring formula."""
        engine = CrossSignalEngine(
            window_days=7,
            max_possible_score=5.0,
            min_score=0,
            reference_date="2026-01-26",
        )
        
        signals = [
            RawSignal("NVDA", "congress", "Bullish", "2026-01-20", 1.0, "Pelosi bought", {"excess_return_pct": 5.2}),
            RawSignal("NVDA", "ark", "Bullish", "2026-01-24", 1.0, "ARK bought", {}),
            RawSignal("NVDA", "darkpool", "Bullish", "2026-01-25", 0.8, "DPI anomaly", {}),
        ]
        
        result = engine.score_cluster("NVDA", signals)
        
        # Base score
        assert result.base_score == 2.8
        
        # Recency: 1 day since Jan 25 → 1 - 1/30 = 0.967
        assert result.recency_multiplier == pytest.approx(0.967, abs=0.001)
        
        # Count bonus: 3 sources → 0.5 × (3-1) = 1.0
        assert result.signal_count_bonus == 1.0
        
        # Excess return bonus: 5.2/10 = 0.52
        assert result.excess_return_bonus == 0.52
        
        # Raw score: (2.8 × 0.967) + 1.0 + 0.52 ≈ 4.23
        assert result.raw_score == pytest.approx(4.23, abs=0.01)
        
        # Normalized: 4.227/5.0 × 10 = 8.45 (PRD hand-calc rounds to 8.46)
        assert result.score == pytest.approx(8.45, abs=0.02)


# ── Signal Extraction Tests ────────────────────────────────────────────


class TestCongressExtraction:
    """Test Congress signal extraction criteria."""

    @pytest.fixture
    def extractor(self):
        return SignalExtractor(reference_date="2026-02-13")

    def test_buy_above_threshold(self, extractor):
        data = {"trades": [{
            "ticker": "AAPL", "trade_type": "Buy",
            "amount_max": 50000, "transaction_date": "2026-02-10",
            "filing_date": "2026-02-12",
            "representative": "Pelosi", "party": "Democrat",
        }]}
        signals = extractor.extract_congress(data)
        assert len(signals) == 1
        assert signals[0].ticker == "AAPL"

    def test_sell_excluded(self, extractor):
        data = {"trades": [{
            "ticker": "AAPL", "trade_type": "Sell",
            "amount_max": 100000, "transaction_date": "2026-02-10",
            "filing_date": "2026-02-12",
        }]}
        signals = extractor.extract_congress(data)
        assert len(signals) == 0

    def test_below_amount_threshold(self, extractor):
        data = {"trades": [{
            "ticker": "AAPL", "trade_type": "Buy",
            "amount_max": 10000,  # Below $15K
            "transaction_date": "2026-02-10",
            "filing_date": "2026-02-12",
        }]}
        signals = extractor.extract_congress(data)
        assert len(signals) == 0

    def test_too_old_excluded(self, extractor):
        data = {"trades": [{
            "ticker": "AAPL", "trade_type": "Buy",
            "amount_max": 50000,
            "transaction_date": "2025-12-01",
            "filing_date": "2025-12-15",  # >45 days ago
        }]}
        signals = extractor.extract_congress(data)
        assert len(signals) == 0

    def test_multiple_members_same_ticker(self, extractor):
        data = {"trades": [
            {"ticker": "NVDA", "trade_type": "Buy", "amount_max": 50000,
             "transaction_date": "2026-02-08", "filing_date": "2026-02-10",
             "representative": "Pelosi", "party": "Democrat"},
            {"ticker": "NVDA", "trade_type": "Buy", "amount_max": 100000,
             "transaction_date": "2026-02-09", "filing_date": "2026-02-11",
             "representative": "Tuberville", "party": "Republican"},
        ]}
        signals = extractor.extract_congress(data)
        assert len(signals) == 2


class TestArkExtraction:
    @pytest.fixture
    def extractor(self):
        return SignalExtractor(reference_date="2026-02-13")

    def test_buy_included(self, extractor):
        data = {"trades": [{
            "ticker": "TSLA", "trade_type": "Buy",
            "etf": "ARKK", "date": "2026-02-12",
            "shares": 100000, "weight_pct": 5.0,
        }]}
        signals = extractor.extract_ark(data)
        assert len(signals) == 1

    def test_sell_excluded(self, extractor):
        data = {"trades": [{
            "ticker": "TSLA", "trade_type": "Sell",
            "etf": "ARKK", "date": "2026-02-12",
            "shares": 100000, "weight_pct": 5.0,
        }]}
        signals = extractor.extract_ark(data)
        assert len(signals) == 0

    def test_low_weight_excluded(self, extractor):
        data = {"trades": [{
            "ticker": "TSLA", "trade_type": "Buy",
            "etf": "ARKK", "date": "2026-02-12",
            "shares": 100, "weight_pct": 0.5,  # Below 1%
        }]}
        signals = extractor.extract_ark(data)
        assert len(signals) == 0

    def test_weight_none_included(self, extractor):
        """If weight is not available, include the signal."""
        data = {"trades": [{
            "ticker": "TSLA", "trade_type": "Buy",
            "etf": "ARKK", "date": "2026-02-12",
            "shares": 100000, "weight_pct": None,
        }]}
        signals = extractor.extract_ark(data)
        assert len(signals) == 1

    def test_too_old_excluded(self, extractor):
        data = {"trades": [{
            "ticker": "TSLA", "trade_type": "Buy",
            "etf": "ARKK", "date": "2026-01-01",  # >30 days
            "shares": 100000, "weight_pct": 5.0,
        }]}
        signals = extractor.extract_ark(data)
        assert len(signals) == 0


class TestDarkpoolExtraction:
    @pytest.fixture
    def extractor(self):
        return SignalExtractor(reference_date="2026-02-13")

    def test_anomaly_included(self, extractor):
        data = {"tickers": [{
            "ticker": "AMC", "date": "2026-02-12",
            "dpi": 0.67, "z_score": 2.8,
            "total_volume": 45000000,
        }]}
        signals = extractor.extract_darkpool(data)
        assert len(signals) == 1

    def test_low_zscore_excluded(self, extractor):
        data = {"tickers": [{
            "ticker": "AMC", "date": "2026-02-12",
            "dpi": 0.67, "z_score": 1.5,  # Below 2.0
            "total_volume": 45000000,
        }]}
        signals = extractor.extract_darkpool(data)
        assert len(signals) == 0

    def test_low_dpi_excluded(self, extractor):
        data = {"tickers": [{
            "ticker": "AMC", "date": "2026-02-12",
            "dpi": 0.3, "z_score": 3.0,  # DPI below 0.4
            "total_volume": 45000000,
        }]}
        signals = extractor.extract_darkpool(data)
        assert len(signals) == 0

    def test_low_volume_excluded(self, extractor):
        data = {"tickers": [{
            "ticker": "AMC", "date": "2026-02-12",
            "dpi": 0.67, "z_score": 2.8,
            "total_volume": 100000,  # Below 500K
        }]}
        signals = extractor.extract_darkpool(data)
        assert len(signals) == 0

    def test_percentage_dpi_normalized(self, extractor):
        """DPI stored as percentage (41.2) should be converted to 0.412."""
        data = {"tickers": [{
            "ticker": "AMC", "date": "2026-02-12",
            "dpi": 67.0,  # Stored as percentage
            "z_score": 2.8,
            "total_volume": 45000000,
        }]}
        signals = extractor.extract_darkpool(data)
        assert len(signals) == 1
        assert signals[0].raw_data["dpi"] == pytest.approx(0.67, abs=0.01)


class TestInstitutionExtraction:
    @pytest.fixture
    def extractor(self):
        return SignalExtractor(reference_date="2026-02-13")

    def test_new_position_large_value(self, extractor):
        data = {"filings": [{
            "fund_name": "Berkshire Hathaway",
            "filing_date": "2026-01-15",  # Within 90 days of reference
            "holdings": [{
                "ticker": "NVDA", "issuer": "NVIDIA CORP",
                "value": 5_000_000_000, "shares": 10000000,
                "change_type": "New", "change_pct": 0,
            }],
        }]}
        signals = extractor.extract_institutions(data)
        assert len(signals) == 1
        assert "Berkshire" in signals[0].description

    def test_small_value_excluded(self, extractor):
        data = {"filings": [{
            "fund_name": "Berkshire Hathaway",
            "filing_date": "2025-11-14",
            "holdings": [{
                "ticker": "XYZ", "value": 10_000_000,  # Below $50M
                "change_type": "New",
            }],
        }]}
        signals = extractor.extract_institutions(data)
        assert len(signals) == 0

    def test_small_increase_excluded(self, extractor):
        """Increase < 10% should be excluded."""
        data = {"filings": [{
            "fund_name": "Berkshire",
            "filing_date": "2025-11-14",
            "holdings": [{
                "ticker": "AAPL", "value": 100_000_000,
                "change_type": "Increased", "change_pct": 5,  # <10%
            }],
        }]}
        signals = extractor.extract_institutions(data)
        assert len(signals) == 0


# ── Clustering Tests ───────────────────────────────────────────────────


class TestClustering:
    def test_all_within_window(self):
        engine = CrossSignalEngine(window_days=7, min_score=0, reference_date="2026-02-13")
        signals = [
            RawSignal("X", "congress", "Bullish", "2026-02-08", 1.0, "a"),
            RawSignal("X", "ark", "Bullish", "2026-02-10", 1.0, "b"),
            RawSignal("X", "darkpool", "Bullish", "2026-02-12", 0.8, "c"),
        ]
        cluster = engine.find_best_cluster(signals)
        assert len(cluster) == 3

    def test_one_outside_window(self):
        engine = CrossSignalEngine(window_days=7, min_score=0, reference_date="2026-02-13")
        signals = [
            RawSignal("X", "congress", "Bullish", "2026-01-20", 1.0, "old"),
            RawSignal("X", "ark", "Bullish", "2026-02-10", 1.0, "recent"),
            RawSignal("X", "darkpool", "Bullish", "2026-02-12", 0.8, "recent"),
        ]
        cluster = engine.find_best_cluster(signals)
        # Should pick the recent cluster (2 signals) over including the old one
        assert len(cluster) == 2

    def test_single_signal(self):
        engine = CrossSignalEngine(window_days=7, min_score=0, reference_date="2026-02-13")
        signals = [RawSignal("X", "congress", "Bullish", "2026-02-10", 1.0, "a")]
        cluster = engine.find_best_cluster(signals)
        assert len(cluster) == 1


# ── Scoring Edge Cases ─────────────────────────────────────────────────


class TestScoringEdgeCases:
    def test_single_signal_score(self):
        """Single signal should score lower than multi-source."""
        engine = CrossSignalEngine(min_score=0, reference_date="2026-02-13")
        signals = [RawSignal("X", "congress", "Bullish", "2026-02-12", 1.0, "a", {"excess_return_pct": 3.0})]
        result = engine.score_cluster("X", signals)
        
        # base=1.0, recency≈0.967, count_bonus=0, excess=0.3
        assert result.score < 5  # Should be modest
        assert result.source_count == 1

    def test_no_excess_return(self):
        """If no congress excess return, bonus should be 0."""
        engine = CrossSignalEngine(min_score=0, reference_date="2026-02-13")
        signals = [
            RawSignal("X", "ark", "Bullish", "2026-02-12", 1.0, "a", {}),
            RawSignal("X", "darkpool", "Bullish", "2026-02-11", 0.8, "b", {}),
        ]
        result = engine.score_cluster("X", signals)
        assert result.excess_return_bonus == 0

    def test_old_signal_low_recency(self):
        """Signal from 25 days ago should have low recency multiplier."""
        engine = CrossSignalEngine(min_score=0, reference_date="2026-02-13")
        signals = [RawSignal("X", "congress", "Bullish", "2026-01-19", 1.0, "a")]
        result = engine.score_cluster("X", signals)
        assert result.recency_multiplier < 0.2

    def test_excess_return_capped(self):
        """Excess return bonus capped at 2.0."""
        engine = CrossSignalEngine(min_score=0, reference_date="2026-02-13")
        signals = [RawSignal("X", "congress", "Bullish", "2026-02-12", 1.0, "a", {"excess_return_pct": 50.0})]
        result = engine.score_cluster("X", signals)
        assert result.excess_return_bonus == 2.0

    def test_score_capped_at_10(self):
        """Maximum score should never exceed 10."""
        engine = CrossSignalEngine(min_score=0, max_possible_score=5.0, reference_date="2026-02-13")
        signals = [
            RawSignal("X", "congress", "Bullish", "2026-02-12", 1.0, "a", {"excess_return_pct": 50.0}),
            RawSignal("X", "ark", "Bullish", "2026-02-12", 1.0, "b"),
            RawSignal("X", "darkpool", "Bullish", "2026-02-12", 0.8, "c"),
            RawSignal("X", "institution", "Bullish", "2026-02-12", 0.6, "d"),
        ]
        result = engine.score_cluster("X", signals)
        assert result.score <= 10.0

    def test_min_score_filter(self):
        """Results below min_score should be filtered out."""
        engine = CrossSignalEngine(min_score=8.0, reference_date="2026-02-13")
        
        congress_data = {"trades": [{
            "ticker": "WEAK", "trade_type": "Buy",
            "amount_max": 15001, "transaction_date": "2026-02-10",
            "filing_date": "2026-02-12",
        }]}
        
        results = engine.generate_signals(congress_data=congress_data)
        # Single signal should score well below 8.0
        assert len(results) == 0


# ── Full Pipeline Tests ────────────────────────────────────────────────


class TestFullPipeline:
    def test_empty_data(self):
        engine = CrossSignalEngine(min_score=0, reference_date="2026-02-13")
        results = engine.generate_signals()
        assert results == []

    def test_multi_ticker_sorted(self):
        """Multiple tickers should be sorted by score descending."""
        engine = CrossSignalEngine(min_score=0, reference_date="2026-02-13")
        
        congress_data = {"trades": [
            {"ticker": "STRONG", "trade_type": "Buy", "amount_max": 250000,
             "transaction_date": "2026-02-12", "filing_date": "2026-02-12",
             "excess_return_pct": 10.0, "representative": "X", "party": "D"},
            {"ticker": "WEAK", "trade_type": "Buy", "amount_max": 15001,
             "transaction_date": "2026-02-10", "filing_date": "2026-02-12",
             "representative": "Y", "party": "R"},
        ]}
        
        ark_data = {"trades": [
            {"ticker": "STRONG", "trade_type": "Buy", "etf": "ARKK",
             "date": "2026-02-11", "shares": 100000, "weight_pct": 3.0},
        ]}
        
        results = engine.generate_signals(
            congress_data=congress_data, ark_data=ark_data,
        )
        
        assert len(results) >= 2
        assert results[0].ticker == "STRONG"
        assert results[0].score > results[1].score

    def test_json_serialization(self):
        """to_json should produce valid structure."""
        engine = CrossSignalEngine(min_score=0, reference_date="2026-02-13")
        
        congress_data = {"trades": [{
            "ticker": "AAPL", "trade_type": "Buy",
            "amount_max": 50000, "transaction_date": "2026-02-12",
            "filing_date": "2026-02-12",
        }]}
        
        results = engine.generate_signals(congress_data=congress_data)
        json_out = engine.to_json(results)
        
        assert "signals" in json_out
        assert "metadata" in json_out
        assert json_out["metadata"]["schema_version"] == "1.0.0"
        assert json_out["metadata"]["total_count"] == len(results)
        
        if results:
            sig = json_out["signals"][0]
            assert "ticker" in sig
            assert "score" in sig
            assert "sources" in sig
            assert "details" in sig
            assert "scoring" in sig


# ── Real Data Pipeline Test ────────────────────────────────────────────


class TestRealDataPipeline:
    """Run the engine against actual production data."""

    @pytest.fixture
    def real_data(self):
        import json
        from pathlib import Path
        
        data_dir = Path("")
        result = {}
        
        for name in ("congress", "ark_trades", "institutions"):
            path = data_dir / f"{name}.json"
            if path.exists():
                with open(path) as f:
                    result[name] = json.load(f)
        
        if not result:
            pytest.skip("No production data available")
        
        return result

    def test_generates_signals_from_real_data(self, real_data):
        """Should produce at least some signals from real data."""
        engine = CrossSignalEngine(min_score=0)
        
        results = engine.generate_signals(
            congress_data=real_data.get("congress"),
            ark_data=real_data.get("ark_trades"),
            institution_data=real_data.get("institutions"),
        )
        
        # Should have at least some signals
        assert len(results) > 0
        
        # All scores should be valid
        for r in results:
            assert 0 <= r.score <= 10
            assert r.source_count >= 1
            assert r.ticker
        
        # Print top 10 for manual inspection
        print(f"\nTop 10 confluence signals from real data:")
        for r in results[:10]:
            print(f"  {r.ticker:6s} | score={r.score:5.2f} | sources={r.sources} | {r.signal_date}")
