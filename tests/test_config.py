"""
Tests for configuration module.

Validates:
- All threshold values match PRD specifications
- Paths exist or are constructable
- Signal weights match PRD §2.3
- Cache filenames are defined for all data sources
- Tracked institutions list is populated
"""

import pytest
from pathlib import Path

from api.config import (
    PROJECT_ROOT, API_ROOT, DATA_DIR, FRONTEND_DIR,
    CACHE_FILES,
    SIGNAL_WEIGHTS,
    CONGRESS, DARKPOOL, ARK, INSTITUTIONS, CONFLUENCE,
    ARK_ETFS,
    QUIVER_BASE_URL, QUIVER_ENDPOINTS,
    SECTORS,
    TRACKED_INSTITUTIONS,
)


class TestPaths:
    def test_project_root_exists(self):
        assert PROJECT_ROOT.exists()

    def test_api_root_exists(self):
        assert API_ROOT.exists()

    def test_data_dir_exists(self):
        assert DATA_DIR.exists()

    def test_project_root_is_parent_of_api(self):
        assert API_ROOT.parent == PROJECT_ROOT


class TestCacheFiles:
    def test_all_required_cache_files_defined(self):
        required = ["congress", "darkpool", "ark_trades", "ark_holdings",
                     "institutions", "signals", "congress_backtest", "ticker_metadata"]
        for key in required:
            assert key in CACHE_FILES, f"Missing cache file key: {key}"

    def test_cache_files_are_json(self):
        for key, filename in CACHE_FILES.items():
            assert filename.endswith(".json"), f"{key}: {filename} should end with .json"


class TestSignalWeights:
    """PRD §2.3: Signal weights must match specification."""

    def test_congress_weight(self):
        assert SIGNAL_WEIGHTS["congress"] == 1.0

    def test_ark_weight(self):
        assert SIGNAL_WEIGHTS["ark"] == 1.0

    def test_darkpool_weight(self):
        assert SIGNAL_WEIGHTS["darkpool"] == 0.8

    def test_institutions_weight(self):
        assert SIGNAL_WEIGHTS["institutions"] == 0.6


class TestCongressThresholds:
    def test_min_amount(self):
        """PRD: Signal criterion amount ≥$15K."""
        assert CONGRESS.min_amount == 15_000

    def test_max_age_days(self):
        """PRD: Regulatory filing limit 45 days."""
        assert CONGRESS.max_age_days == 45

    def test_signal_lookback(self):
        assert CONGRESS.signal_lookback_days == 30


class TestDarkPoolThresholds:
    def test_min_dpi(self):
        """PRD: DPI ≥0.4."""
        assert DARKPOOL.min_dpi == 0.4

    def test_z_score_threshold(self):
        """PRD: Z-score ≥2 (95% confidence)."""
        assert DARKPOOL.z_score_threshold == 2.0

    def test_min_volume(self):
        """PRD: Volume ≥500K shares/day."""
        assert DARKPOOL.min_volume == 500_000

    def test_rolling_window(self):
        """PRD: 30-day rolling window for Z-score."""
        assert DARKPOOL.rolling_window_days == 30

    def test_history_days(self):
        """PRD: 90 days of history for DPI calculation."""
        assert DARKPOOL.history_days == 90

    def test_signal_lookback(self):
        """PRD: DPI anomaly within last 7 days."""
        assert DARKPOOL.signal_lookback_days == 7


class TestArkThresholds:
    def test_min_weight(self):
        """PRD: Position ≥1% of ETF portfolio."""
        assert ARK.min_weight_pct == 1.0

    def test_signal_lookback(self):
        assert ARK.signal_lookback_days == 30


class TestInstitutionThresholds:
    def test_min_value(self):
        """PRD: Position value ≥$50M."""
        assert INSTITUTIONS.min_value == 50_000_000

    def test_min_change(self):
        """PRD: New or increased ≥10% QoQ."""
        assert INSTITUTIONS.min_change_pct == 10.0

    def test_signal_lookback(self):
        """PRD: Quarterly cadence (90 days)."""
        assert INSTITUTIONS.signal_lookback_days == 90


class TestConfluenceThresholds:
    def test_time_window(self):
        """PRD: ±7 days for signal grouping."""
        assert CONFLUENCE.time_window_days == 7

    def test_max_possible_score(self):
        """PRD: Max possible score assumption = 5.0 for normalization."""
        assert CONFLUENCE.max_possible_score == 5.0

    def test_min_signals(self):
        """PRD: Require at least 2 signals for confluence."""
        assert CONFLUENCE.min_signals_for_confluence == 2

    def test_default_min_score(self):
        """PRD: Default score filter threshold = 6."""
        assert CONFLUENCE.default_min_score == 6.0


class TestArkEtfs:
    def test_all_six_etfs(self):
        expected = {"ARKK", "ARKW", "ARKQ", "ARKG", "ARKF", "ARKX"}
        assert set(ARK_ETFS.keys()) == expected

    def test_etf_names_not_empty(self):
        for etf, name in ARK_ETFS.items():
            assert len(name) > 0, f"ETF {etf} has empty name"


class TestQuiverEndpoints:
    def test_base_url_format(self):
        assert QUIVER_BASE_URL.startswith("https://")
        assert "quiverquant" in QUIVER_BASE_URL

    def test_required_endpoints(self):
        required = ["congress_house", "congress_senate", "darkpool", "ark_trades"]
        for key in required:
            assert key in QUIVER_ENDPOINTS, f"Missing endpoint: {key}"
            assert QUIVER_ENDPOINTS[key].startswith("https://")


class TestSectors:
    def test_sectors_not_empty(self):
        assert len(SECTORS) >= 10

    def test_key_sectors_present(self):
        assert "Technology" in SECTORS
        assert "Healthcare" in SECTORS
        assert "Finance" in SECTORS
        assert "Energy" in SECTORS


class TestTrackedInstitutions:
    def test_institutions_populated(self):
        """PRD mentions 7 tracked institutions."""
        assert len(TRACKED_INSTITUTIONS) == 7

    def test_key_institutions(self):
        names = [v["name"].lower() for v in TRACKED_INSTITUTIONS.values()]
        assert any("berkshire" in n for n in names)
        assert any("bridgewater" in n for n in names)
        assert any("renaissance" in n for n in names)

    def test_institutions_have_cik_keys(self):
        for cik in TRACKED_INSTITUTIONS:
            assert cik.startswith("000"), f"CIK should be zero-padded: {cik}"
            assert "name" in TRACKED_INSTITUTIONS[cik]
            assert "manager" in TRACKED_INSTITUTIONS[cik]


class TestFrozenDataclasses:
    """Threshold configs should be immutable."""

    def test_congress_frozen(self):
        with pytest.raises(AttributeError):
            CONGRESS.min_amount = 999

    def test_darkpool_frozen(self):
        with pytest.raises(AttributeError):
            DARKPOOL.z_score_threshold = 999

    def test_ark_frozen(self):
        with pytest.raises(AttributeError):
            ARK.min_weight_pct = 999

    def test_institutions_frozen(self):
        with pytest.raises(AttributeError):
            INSTITUTIONS.min_value = 999

    def test_confluence_frozen(self):
        with pytest.raises(AttributeError):
            CONFLUENCE.time_window_days = 999
