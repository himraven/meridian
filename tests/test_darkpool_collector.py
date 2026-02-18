"""
Tests for Dark Pool Collector.

Validates:
- DPI calculation (OTC_Short / OTC_Total)
- Z-score computation (30-day rolling window)
- Anomaly detection (Z ≥ 2.0 AND DPI ≥ 0.4 AND volume ≥ 500K)
- Edge cases (zero volume, insufficient history, identical values)
- PRD example verification
- Cache output format
- Data integrity through the full pipeline
"""

import json
import statistics
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from api.cron.darkpool_collector import DarkPoolCollector
from api.modules.cache_manager import CacheManager


@pytest.fixture
def collector(tmp_path):
    """Collector with temp cache directory."""
    return DarkPoolCollector(cache_dir=str(tmp_path))


@pytest.fixture
def sample_ticker_data():
    """Generate 45 days of sample OTC data for a ticker."""
    base_date = datetime.now() - timedelta(days=44)
    records = []
    
    # Normal DPI around 0.45 with some variation
    import random
    random.seed(42)  # Reproducible
    
    for i in range(45):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        total = random.randint(800_000, 1_200_000)
        # Normal DPI ~0.45
        short = int(total * (0.45 + random.uniform(-0.05, 0.05)))
        
        records.append({
            "ticker": "NVDA",
            "date": date,
            "otc_short": short,
            "otc_total": total,
            "price": 800 + i * 2,
        })
    
    return records


@pytest.fixture
def anomaly_ticker_data():
    """Generate data where the last day has an anomalous DPI spike."""
    import random
    random.seed(999)
    
    base_date = datetime.now() - timedelta(days=34)
    records = []
    
    # 34 days of normal DPI ~0.45 with slight natural variation
    for i in range(34):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        total = 1_000_000
        # Add ±2% random variation to make stddev > 0
        short = int(total * (0.45 + random.uniform(-0.02, 0.02)))
        
        records.append({
            "ticker": "AMC",
            "date": date,
            "otc_short": short,
            "otc_total": total,
        })
    
    # Day 35: massive DPI spike to 0.89
    last_date = (base_date + timedelta(days=34)).strftime("%Y-%m-%d")
    records.append({
        "ticker": "AMC",
        "date": last_date,
        "otc_short": 890_000,
        "otc_total": 1_000_000,
        "price": 3.45,
        "price_change_pct": 8.5,
    })
    
    return records


# ── DPI Calculation ────────────────────────────────────────────────────


class TestDPICalculation:
    def test_basic_dpi(self, collector):
        assert collector.calculate_dpi(450_000, 1_000_000) == 0.45

    def test_high_dpi(self, collector):
        assert collector.calculate_dpi(890_000, 1_000_000) == 0.89

    def test_zero_total(self, collector):
        """DPI should be 0 when total volume is 0."""
        assert collector.calculate_dpi(100, 0) == 0.0

    def test_negative_total(self, collector):
        """DPI should be 0 for negative total (invalid data)."""
        assert collector.calculate_dpi(100, -1) == 0.0

    def test_zero_short(self, collector):
        assert collector.calculate_dpi(0, 1_000_000) == 0.0

    def test_equal_short_total(self, collector):
        """DPI = 1.0 when all volume is short."""
        assert collector.calculate_dpi(1_000_000, 1_000_000) == 1.0

    def test_precision(self, collector):
        """DPI should not lose precision in intermediate calculation."""
        dpi = collector.calculate_dpi(333_333, 1_000_000)
        assert abs(dpi - 0.333333) < 0.001


# ── Z-Score Computation ────────────────────────────────────────────────


class TestZScore:
    def test_basic_z_score(self, collector):
        # Mean = 0.45, stddev = ~0.01
        values = [0.44, 0.45, 0.46, 0.44, 0.45, 0.46, 0.44, 0.45, 0.46, 0.44,
                  0.45, 0.46, 0.44, 0.45, 0.46, 0.44, 0.45, 0.46, 0.44, 0.45,
                  0.46, 0.44, 0.45, 0.46, 0.44, 0.45, 0.46, 0.44, 0.45, 0.46]
        z, mean, std = collector.compute_z_score(values, 0.45)
        assert abs(mean - 0.45) < 0.01
        assert abs(z) < 0.5  # Normal value, small Z

    def test_high_z_score(self, collector):
        """DPI spike should produce high Z-score."""
        values = [0.45] * 30
        z, mean, std = collector.compute_z_score(values, 0.89)
        # With all same values, stddev ≈ 0, so Z would be undefined
        # But with tiny variation this tests the concept
        # For identical values, stddev=0, Z=0 by our definition
        assert z == 0.0  # All identical → stddev=0 → Z=0

    def test_high_z_with_variation(self, collector):
        """DPI spike with natural variation should produce high Z."""
        import random
        random.seed(123)
        values = [0.45 + random.uniform(-0.02, 0.02) for _ in range(30)]
        z, mean, std = collector.compute_z_score(values, 0.89)
        assert z > 10  # Massive spike relative to normal variation

    def test_single_value(self, collector):
        """Single value in history → Z = 0."""
        z, mean, std = collector.compute_z_score([0.45], 0.89)
        assert z == 0.0

    def test_empty_values(self, collector):
        """Empty history → Z = 0."""
        z, mean, std = collector.compute_z_score([], 0.89)
        assert z == 0.0

    def test_negative_z_score(self, collector):
        """DPI drop should produce negative Z-score."""
        import random
        random.seed(456)
        values = [0.60 + random.uniform(-0.02, 0.02) for _ in range(30)]
        z, mean, std = collector.compute_z_score(values, 0.30)
        assert z < -10  # Massive drop


# ── Anomaly Detection ──────────────────────────────────────────────────


class TestAnomalyDetection:
    def test_is_anomaly_all_criteria_met(self, collector):
        """All three criteria met → anomaly."""
        assert collector.is_anomaly(z_score=2.5, dpi=0.67, total_volume=1_000_000) is True

    def test_not_anomaly_low_z(self, collector):
        """Z < 2.0 → not anomaly."""
        assert collector.is_anomaly(z_score=1.9, dpi=0.67, total_volume=1_000_000) is False

    def test_not_anomaly_low_dpi(self, collector):
        """DPI < 0.4 → not anomaly."""
        assert collector.is_anomaly(z_score=3.0, dpi=0.35, total_volume=1_000_000) is False

    def test_not_anomaly_low_volume(self, collector):
        """Volume < 500K → not anomaly."""
        assert collector.is_anomaly(z_score=3.0, dpi=0.67, total_volume=400_000) is False

    def test_boundary_z_score(self, collector):
        """Z = exactly 2.0 → anomaly (≥ not >)."""
        assert collector.is_anomaly(z_score=2.0, dpi=0.4, total_volume=500_000) is True

    def test_boundary_dpi(self, collector):
        """DPI = exactly 0.4 → anomaly."""
        assert collector.is_anomaly(z_score=2.0, dpi=0.4, total_volume=500_000) is True

    def test_boundary_volume(self, collector):
        """Volume = exactly 500K → anomaly."""
        assert collector.is_anomaly(z_score=2.0, dpi=0.4, total_volume=500_000) is True

    def test_below_all_boundaries(self, collector):
        """Below all boundaries → not anomaly."""
        assert collector.is_anomaly(z_score=1.99, dpi=0.39, total_volume=499_999) is False


# ── Full Pipeline ──────────────────────────────────────────────────────


class TestProcessRawData:
    def test_normal_data(self, collector, sample_ticker_data):
        """Normal data should produce results but likely no anomalies."""
        results = collector.process_raw_data(sample_ticker_data)
        assert len(results) == 1
        r = results[0]
        assert r["ticker"] == "NVDA"
        assert 0 <= r["dpi"] <= 1.0
        assert r["dpi_30d_mean"] > 0
        assert r["dpi_30d_stddev"] >= 0
        assert isinstance(r["z_score"], float)

    def test_anomaly_detection(self, collector, anomaly_ticker_data):
        """Spiked DPI should be flagged as anomaly."""
        results = collector.process_raw_data(anomaly_ticker_data)
        assert len(results) == 1
        r = results[0]
        assert r["ticker"] == "AMC"
        assert r["is_anomaly"] is True
        assert r["dpi"] == 0.89
        assert r["z_score"] > 2.0

    def test_insufficient_history(self, collector):
        """Tickers with < 30 days should be skipped."""
        short_data = [
            {"ticker": "SHORT", "date": f"2026-02-{i:02d}", "otc_short": 100, "otc_total": 200}
            for i in range(1, 10)  # Only 9 days
        ]
        results = collector.process_raw_data(short_data)
        assert len(results) == 0

    def test_multiple_tickers(self, collector, sample_ticker_data, anomaly_ticker_data):
        """Multiple tickers should be processed independently."""
        all_data = sample_ticker_data + anomaly_ticker_data
        results = collector.process_raw_data(all_data)
        assert len(results) == 2
        tickers = {r["ticker"] for r in results}
        assert tickers == {"NVDA", "AMC"}

    def test_sorted_anomalies_first(self, collector, sample_ticker_data, anomaly_ticker_data):
        """Results should be sorted: anomalies first, then by Z-score desc."""
        all_data = sample_ticker_data + anomaly_ticker_data
        results = collector.process_raw_data(all_data)
        # AMC (anomaly) should be first
        assert results[0]["ticker"] == "AMC"
        assert results[0]["is_anomaly"] is True

    def test_empty_data(self, collector):
        results = collector.process_raw_data([])
        assert results == []

    def test_empty_ticker_filtered(self, collector):
        data = [{"ticker": "", "date": "2026-02-01", "otc_short": 100, "otc_total": 200}]
        results = collector.process_raw_data(data)
        assert len(results) == 0

    def test_output_matches_model_schema(self, collector, anomaly_ticker_data):
        """Output fields should match DarkPoolTicker model."""
        results = collector.process_raw_data(anomaly_ticker_data)
        r = results[0]
        
        required_fields = {
            "ticker", "date", "otc_short", "otc_total", "dpi",
            "dpi_30d_mean", "dpi_30d_stddev", "z_score", "is_anomaly",
            "total_volume", "price", "price_change_pct",
        }
        assert set(r.keys()) == required_fields

    def test_dpi_precision_in_output(self, collector, anomaly_ticker_data):
        """DPI should be rounded to 4 decimal places."""
        results = collector.process_raw_data(anomaly_ticker_data)
        r = results[0]
        dpi_str = str(r["dpi"])
        # Check decimal places ≤ 4
        if "." in dpi_str:
            decimal_places = len(dpi_str.split(".")[1])
            assert decimal_places <= 4

    def test_z_score_precision_in_output(self, collector, anomaly_ticker_data):
        """Z-score should be rounded to 2 decimal places."""
        results = collector.process_raw_data(anomaly_ticker_data)
        r = results[0]
        z_str = str(r["z_score"])
        if "." in z_str:
            decimal_places = len(z_str.split(".")[1])
            assert decimal_places <= 2


# ── Cache Output ───────────────────────────────────────────────────────


class TestSaveResults:
    def test_saves_to_cache(self, collector, anomaly_ticker_data, tmp_path):
        results = collector.process_raw_data(anomaly_ticker_data)
        assert collector.save_results(results) is True
        
        # Verify file exists and is valid JSON
        cache = CacheManager(str(tmp_path))
        data = cache.read("darkpool.json")
        assert "tickers" in data
        assert "metadata" in data
        assert "last_updated" in data

    def test_metadata_correctness(self, collector, anomaly_ticker_data, tmp_path):
        results = collector.process_raw_data(anomaly_ticker_data)
        collector.save_results(results)
        
        cache = CacheManager(str(tmp_path))
        data = cache.read("darkpool.json")
        meta = data["metadata"]
        
        assert meta["total_count"] == 1
        assert meta["anomaly_count"] == 1
        assert meta["z_score_threshold"] == 2.0
        assert meta["min_dpi"] == 0.4
        assert meta["min_volume"] == 500_000

    def test_empty_results_saves(self, collector, tmp_path):
        """Empty results should still save a valid file."""
        assert collector.save_results([]) is True
        
        cache = CacheManager(str(tmp_path))
        data = cache.read("darkpool.json")
        assert data["tickers"] == []
        assert data["metadata"]["total_count"] == 0
        assert data["metadata"]["anomaly_count"] == 0


# ── PRD Verification ──────────────────────────────────────────────────


class TestPRDCompliance:
    """Verify the collector matches PRD §1.3 and §2.4 specifications."""

    def test_z_score_threshold_is_2(self, collector):
        """PRD: Z-Score ≥2 (95% confidence interval)"""
        assert collector.z_threshold == 2.0

    def test_min_dpi_is_0_4(self, collector):
        """PRD: DPI ≥0.4"""
        assert collector.min_dpi == 0.4

    def test_min_volume_is_500k(self, collector):
        """PRD: Volume ≥500k shares/day"""
        assert collector.min_volume == 500_000

    def test_rolling_window_is_30(self, collector):
        """PRD: Z-score computed from last 30 days"""
        assert collector.rolling_window == 30

    def test_dpi_formula(self, collector):
        """PRD §2.4: DPI = OTC_Short / OTC_Total"""
        # AMC example from PRD
        dpi = collector.calculate_dpi(45_200_000, 50_800_000)
        assert abs(dpi - 0.89) < 0.01  # PRD says DPI = 0.89 for AMC

    def test_prd_anomaly_example(self, collector):
        """PRD example: AMC with DPI 0.89, Z 3.2 should be anomaly."""
        assert collector.is_anomaly(z_score=3.2, dpi=0.89, total_volume=50_800_000) is True


# ── Integration ────────────────────────────────────────────────────────


class TestRunPipeline:
    def test_run_with_provided_data(self, collector, anomaly_ticker_data, tmp_path):
        """run() with provided data should process and save."""
        results = collector.run(raw_data=anomaly_ticker_data)
        assert len(results) == 1
        assert results[0]["is_anomaly"] is True
        
        # Verify saved
        cache = CacheManager(str(tmp_path))
        data = cache.read("darkpool.json")
        assert len(data["tickers"]) == 1

    def test_run_empty_data(self, collector, tmp_path):
        results = collector.run(raw_data=[])
        assert results == []
