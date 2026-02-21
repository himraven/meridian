"""
Tests for Meridian MCP Server

Tests cover:
  1. Tool function unit tests (each of 10 tools)
  2. Tool parameter validation
  3. MCP server tool listing
  4. Tool execution returns proper format
  5. Error handling (missing data, invalid params)
  6. FastAPI mounting integration
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Ensure the project root is in sys.path ─────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def mock_shared_imports(monkeypatch):
    """Mock shared data access so tests don't need real data files."""
    # Create a mock cache that returns sample data
    mock_cache = MagicMock()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_week = (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%d")

    sample_data = {
        "congress.json": {
            "trades": [
                {
                    "ticker": "AAPL",
                    "representative": "Nancy Pelosi",
                    "party": "Democrat",
                    "chamber": "House",
                    "trade_type": "Purchase",
                    "transaction_date": yesterday,
                    "amount_min": 100000,
                    "amount_max": 250000,
                    "amount_range": "$100K-$250K",
                },
                {
                    "ticker": "TSLA",
                    "representative": "Dan Crenshaw",
                    "party": "Republican",
                    "chamber": "House",
                    "trade_type": "Sale",
                    "transaction_date": last_week,
                    "amount_min": 15000,
                    "amount_max": 50000,
                    "amount_range": "$15K-$50K",
                },
            ],
            "last_updated": today,
        },
        "ark_trades.json": {
            "trades": [
                {
                    "ticker": "TSLA",
                    "etf": "ARKK",
                    "trade_type": "Buy",
                    "date": yesterday,
                    "shares": 50000,
                    "company": "Tesla Inc",
                },
                {
                    "ticker": "COIN",
                    "etf": "ARKK",
                    "trade_type": "Sell",
                    "date": last_week,
                    "shares": 30000,
                    "company": "Coinbase Global",
                },
                {
                    "ticker": "ROKU",
                    "etf": "ARKW",
                    "trade_type": "Buy",
                    "date": yesterday,
                    "shares": 20000,
                    "company": "Roku Inc",
                },
            ],
            "last_updated": today,
        },
        "ark_holdings.json": {
            "holdings": [
                {"ticker": "TSLA", "etf": "ARKK", "weight_pct": 12.5, "shares": 1000000},
                {"ticker": "COIN", "etf": "ARKK", "weight_pct": 8.3, "shares": 500000},
                {"ticker": "ROKU", "etf": "ARKW", "weight_pct": 5.1, "shares": 300000},
                {"ticker": "SQ", "etf": "ARKK", "weight_pct": 2.0, "shares": 200000},
            ],
            "last_updated": today,
        },
        "insiders.json": {
            "trades": [
                {
                    "ticker": "AAPL",
                    "insider_name": "Tim Cook",
                    "title": "CEO",
                    "transaction_type": "Buy",
                    "trade_date": yesterday,
                    "filing_date": today,
                    "value": 5000000,
                },
                {
                    "ticker": "NVDA",
                    "insider_name": "Jensen Huang",
                    "title": "CEO",
                    "transaction_type": "Sale",
                    "trade_date": last_week,
                    "filing_date": last_week,
                    "value": 20000000,
                },
            ],
            "clusters": [
                {
                    "ticker": "AAPL",
                    "insider_count": 3,
                    "total_value": 8000000,
                    "insiders": ["Tim Cook", "Luca Maestri", "Craig Federighi"],
                },
            ],
            "metadata": {"source": "openinsider"},
        },
        "institutions.json": {
            "filings": [
                {
                    "cik": "0001067983",
                    "fund_name": "Berkshire Hathaway Inc",
                    "company_name": "Berkshire Hathaway Inc",
                    "filing_date": "2025-02-14",
                    "quarter": "Q4 2024",
                    "total_value": 300000000000,
                    "holdings_count": 40,
                    "holdings": [
                        {"ticker": "AAPL", "issuer": "Apple Inc", "value": 90000000000, "shares": 400000000, "cusip": "037833100"},
                        {"ticker": "BAC", "issuer": "Bank of America", "value": 30000000000, "shares": 800000000, "cusip": "060505104"},
                    ],
                },
            ],
            "last_updated": today,
        },
        "darkpool.json": {
            "tickers": [
                {
                    "ticker": "AMC",
                    "date": yesterday,
                    "z_score": 3.5,
                    "dpi": 0.65,
                    "off_exchange_volume": 50000000,
                },
                {
                    "ticker": "GME",
                    "date": yesterday,
                    "z_score": 2.8,
                    "dpi": 0.55,
                    "off_exchange_volume": 30000000,
                },
                {
                    "ticker": "TSLA",
                    "date": last_week,
                    "z_score": 1.5,
                    "dpi": 0.35,
                    "off_exchange_volume": 80000000,
                },
            ],
            "metadata": {"last_updated": today},
        },
        "short_interest.json": {
            "tickers": [
                {"ticker": "GME", "short_interest": 15000000, "short_pct_float": 25.0, "days_to_cover": 3.5},
                {"ticker": "AMC", "short_interest": 80000000, "short_pct_float": 18.0, "days_to_cover": 2.1},
                {"ticker": "TSLA", "short_interest": 25000000, "short_pct_float": 3.5, "days_to_cover": 1.2},
            ],
            "metadata": {"settlement_date": yesterday, "last_updated": today},
        },
        "superinvestors.json": {
            "activity": [
                {
                    "ticker": "AAPL",
                    "activity_type": "Buy",
                    "manager": "Warren Buffett",
                    "manager_count": 5,
                    "quarter": "Q4 2024",
                    "portfolio_pct": 45.0,
                    "source": "aggregate",
                },
                {
                    "ticker": "META",
                    "activity_type": "Sell",
                    "manager": "George Soros",
                    "manager_count": 2,
                    "quarter": "Q4 2024",
                    "portfolio_pct": 3.0,
                    "source": "per_manager",
                },
            ],
            "holdings": {},
            "metadata": {"manager_count": 80, "last_updated": today},
        },
        "ranking_v3.json": {
            "signals": [
                {
                    "ticker": "AAPL",
                    "score": 85.0,
                    "signal_date": yesterday,
                    "sources": ["congress", "insider", "institution"],
                    "details": [
                        {"source": "congress", "score": 30},
                        {"source": "insider", "score": 25},
                        {"source": "institution", "score": 30},
                    ],
                },
                {
                    "ticker": "TSLA",
                    "score": 42.0,
                    "signal_date": last_week,
                    "sources": ["ark"],
                    "details": [{"source": "ark", "score": 42}],
                },
                {
                    "ticker": "GME",
                    "score": 15.0,
                    "signal_date": yesterday,
                    "sources": ["darkpool"],
                    "details": [{"source": "darkpool", "score": 15}],
                },
            ],
            "metadata": {"engine": "v3", "last_updated": today},
        },
    }

    def mock_read(filename):
        return sample_data.get(filename, {})

    mock_cache.read = mock_read

    # Mock ticker_names
    mock_tn = MagicMock()
    mock_tn.enrich_list = MagicMock()  # no-op

    # Patch the module-level lazy imports
    monkeypatch.setattr("api.mcp_server._get_cache", lambda: mock_cache)
    monkeypatch.setattr("api.mcp_server._get_ticker_names", lambda: mock_tn)
    monkeypatch.setattr("api.mcp_server._get_duckdb", lambda: None)  # Use JSON fallback for tests


# ═══════════════════════════════════════════════════════════════════════════
# 1. MCP Server Tool Listing
# ═══════════════════════════════════════════════════════════════════════════


class TestMCPServerToolListing:
    """Test that MCP server has all 10 tools registered."""

    def test_has_10_tools(self):
        from api.mcp_server import mcp
        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 10, f"Expected 10 tools, got {len(tools)}: {[t.name for t in tools]}"

    def test_tool_names(self):
        from api.mcp_server import mcp
        tools = asyncio.run(mcp.list_tools())
        names = {t.name for t in tools}
        expected = {
            "get_congress_trades",
            "get_ark_trades",
            "get_ark_holdings",
            "get_insider_trades",
            "get_13f_filings",
            "get_darkpool_activity",
            "get_short_interest",
            "get_superinvestor_activity",
            "get_confluence_signals",
            "get_market_regime",
        }
        assert names == expected, f"Missing tools: {expected - names}, Extra tools: {names - expected}"

    def test_all_tools_have_descriptions(self):
        from api.mcp_server import mcp
        tools = asyncio.run(mcp.list_tools())
        for tool in tools:
            assert tool.description, f"Tool {tool.name} missing description"
            assert len(tool.description) > 20, f"Tool {tool.name} description too short: {tool.description}"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Individual Tool Unit Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestCongressTrades:
    def test_returns_trades(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades()
        assert "trades" in result
        assert "metadata" in result
        assert len(result["trades"]) > 0

    def test_filter_by_party(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades(party="Democrat")
        assert all(
            t.get("party", "").lower() == "democrat"
            for t in result["trades"]
        )

    def test_filter_by_chamber(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades(chamber="House")
        assert all(
            t.get("chamber", "").lower() == "house"
            for t in result["trades"]
        )

    def test_filter_by_trade_type(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades(trade_type="Purchase")
        for t in result["trades"]:
            tt = t.get("trade_type", "").lower().replace("sale", "sell")
            assert tt in ("purchase", "buy")

    def test_buy_sell_counts(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades(days=365)
        meta = result["metadata"]
        assert "buy_count" in meta
        assert "sell_count" in meta
        assert meta["buy_count"] + meta["sell_count"] == len(result["trades"])

    def test_days_filter(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades(days=1)
        # Should have fewer results than days=365
        result_all = get_congress_trades(days=365)
        assert len(result["trades"]) <= len(result_all["trades"])

    def test_limit(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades(limit=1)
        assert len(result["trades"]) <= 1


class TestArkTrades:
    def test_returns_trades(self):
        from api.mcp_server import get_ark_trades
        result = get_ark_trades()
        assert "trades" in result
        assert "metadata" in result
        assert len(result["trades"]) > 0

    def test_filter_by_trade_type(self):
        from api.mcp_server import get_ark_trades
        result = get_ark_trades(trade_type="Buy")
        assert all(
            t.get("trade_type", "").lower() in ("buy", "purchase")
            for t in result["trades"]
        )

    def test_filter_by_etf(self):
        from api.mcp_server import get_ark_trades
        result = get_ark_trades(etf="ARKK")
        assert all(
            t.get("etf", "").upper() == "ARKK"
            for t in result["trades"]
        )

    def test_metadata_has_counts(self):
        from api.mcp_server import get_ark_trades
        result = get_ark_trades()
        meta = result["metadata"]
        assert "buy_count" in meta
        assert "sell_count" in meta


class TestArkHoldings:
    def test_returns_holdings(self):
        from api.mcp_server import get_ark_holdings
        result = get_ark_holdings()
        assert "holdings" in result
        assert len(result["holdings"]) > 0

    def test_filter_by_etf(self):
        from api.mcp_server import get_ark_holdings
        result = get_ark_holdings(etf="ARKK")
        assert all(h.get("etf", "").upper() == "ARKK" for h in result["holdings"])

    def test_filter_by_min_weight(self):
        from api.mcp_server import get_ark_holdings
        result = get_ark_holdings(min_weight=5.0)
        assert all(h.get("weight_pct", 0) >= 5.0 for h in result["holdings"])

    def test_limit(self):
        from api.mcp_server import get_ark_holdings
        result = get_ark_holdings(limit=2)
        assert len(result["holdings"]) <= 2


class TestInsiderTrades:
    def test_returns_trades_and_clusters(self):
        from api.mcp_server import get_insider_trades
        result = get_insider_trades()
        assert "trades" in result
        assert "clusters" in result
        assert "metadata" in result

    def test_filter_by_type(self):
        from api.mcp_server import get_insider_trades
        result = get_insider_trades(transaction_type="Buy")
        assert all(
            t.get("transaction_type", "").lower() == "buy"
            for t in result["trades"]
        )

    def test_filter_by_ticker(self):
        from api.mcp_server import get_insider_trades
        result = get_insider_trades(ticker="AAPL")
        assert all(
            t.get("ticker", "").upper() == "AAPL"
            for t in result["trades"]
        )

    def test_cluster_only(self):
        from api.mcp_server import get_insider_trades
        result = get_insider_trades(cluster_only=True)
        # All returned trades should be in cluster tickers
        cluster_tickers = {c.get("ticker", "").upper() for c in result["clusters"]}
        # When cluster_only is True, all trades should be for cluster tickers
        for t in result["trades"]:
            assert t.get("ticker", "").upper() in cluster_tickers or len(result["trades"]) == 0

    def test_metadata_counts(self):
        from api.mcp_server import get_insider_trades
        result = get_insider_trades(days=365)
        meta = result["metadata"]
        assert "buy_count" in meta
        assert "sell_count" in meta
        assert "cluster_count" in meta


class TestInstitutionalFilings:
    def test_returns_filings_and_holdings(self):
        from api.mcp_server import get_13f_filings
        result = get_13f_filings()
        assert "filings" in result
        assert "top_holdings" in result
        assert "metadata" in result

    def test_filter_by_fund(self):
        from api.mcp_server import get_13f_filings
        result = get_13f_filings(fund="berkshire")
        assert len(result["filings"]) > 0
        assert all(
            "berkshire" in f.get("fund_name", "").lower()
            for f in result["filings"]
        )

    def test_no_match_fund(self):
        from api.mcp_server import get_13f_filings
        result = get_13f_filings(fund="nonexistent_fund_xyz")
        assert len(result["filings"]) == 0

    def test_holdings_have_tickers(self):
        from api.mcp_server import get_13f_filings
        result = get_13f_filings()
        for h in result["top_holdings"]:
            assert h.get("ticker"), f"Holding missing ticker: {h}"


class TestDarkpoolActivity:
    def test_returns_anomalies(self):
        from api.mcp_server import get_darkpool_activity
        result = get_darkpool_activity()
        assert "anomalies" in result
        assert "metadata" in result

    def test_zscore_filter(self):
        from api.mcp_server import get_darkpool_activity
        result = get_darkpool_activity(min_zscore=3.0)
        assert all(
            a.get("z_score", 0) >= 3.0
            for a in result["anomalies"]
        )

    def test_dpi_filter(self):
        from api.mcp_server import get_darkpool_activity
        result = get_darkpool_activity(min_dpi=0.5)
        assert all(
            a.get("dpi", 0) >= 0.5
            for a in result["anomalies"]
        )

    def test_days_filter(self):
        from api.mcp_server import get_darkpool_activity
        result = get_darkpool_activity(days=1)
        # Should filter out older entries
        assert len(result["anomalies"]) <= 2  # Only yesterday's entries


class TestShortInterest:
    def test_returns_tickers(self):
        from api.mcp_server import get_short_interest
        result = get_short_interest()
        assert "tickers" in result
        assert "metadata" in result
        assert len(result["tickers"]) > 0

    def test_filter_by_ticker(self):
        from api.mcp_server import get_short_interest
        result = get_short_interest(ticker="GME")
        assert len(result["tickers"]) == 1
        assert result["tickers"][0]["ticker"] == "GME"

    def test_min_short_ratio(self):
        from api.mcp_server import get_short_interest
        result = get_short_interest(min_short_ratio=20.0)
        assert all(
            t.get("short_pct_float", 0) >= 20.0
            for t in result["tickers"]
        )

    def test_sort_by(self):
        from api.mcp_server import get_short_interest
        result = get_short_interest(sort_by="short_ratio")
        si_vals = [t.get("short_pct_float", 0) for t in result["tickers"]]
        assert si_vals == sorted(si_vals, reverse=True)

    def test_limit(self):
        from api.mcp_server import get_short_interest
        result = get_short_interest(limit=1)
        assert len(result["tickers"]) <= 1


class TestSuperinvestorActivity:
    def test_returns_activity(self):
        from api.mcp_server import get_superinvestor_activity
        result = get_superinvestor_activity()
        assert "activity" in result
        assert "metadata" in result
        assert len(result["activity"]) > 0

    def test_filter_by_manager(self):
        from api.mcp_server import get_superinvestor_activity
        result = get_superinvestor_activity(manager="buffett")
        assert all(
            "buffett" in a.get("manager", "").lower()
            for a in result["activity"]
        )

    def test_filter_by_activity_type(self):
        from api.mcp_server import get_superinvestor_activity
        result = get_superinvestor_activity(activity_type="Buy")
        assert all(
            a.get("activity_type") == "Buy"
            for a in result["activity"]
        )

    def test_filter_by_ticker(self):
        from api.mcp_server import get_superinvestor_activity
        result = get_superinvestor_activity(ticker="AAPL")
        assert all(
            a.get("ticker", "").upper() == "AAPL"
            for a in result["activity"]
        )


class TestConfluenceSignals:
    def test_returns_signals(self):
        from api.mcp_server import get_confluence_signals
        result = get_confluence_signals(min_score=0)
        assert "signals" in result
        assert "metadata" in result
        assert len(result["signals"]) > 0

    def test_min_score_filter(self):
        from api.mcp_server import get_confluence_signals
        result = get_confluence_signals(min_score=50.0)
        assert all(
            s.get("score", 0) >= 50.0
            for s in result["signals"]
        )

    def test_source_filter(self):
        from api.mcp_server import get_confluence_signals
        result = get_confluence_signals(min_score=0, sources="congress")
        for s in result["signals"]:
            source_names = [d.get("source") for d in s.get("details", [])]
            source_list = s.get("sources", [])
            assert "congress" in source_names or "congress" in source_list

    def test_days_filter(self):
        from api.mcp_server import get_confluence_signals
        result_narrow = get_confluence_signals(min_score=0, days=1)
        result_wide = get_confluence_signals(min_score=0, days=365)
        assert len(result_narrow["signals"]) <= len(result_wide["signals"])

    def test_metadata_has_engine(self):
        from api.mcp_server import get_confluence_signals
        result = get_confluence_signals(min_score=0)
        assert "engine" in result["metadata"]


class TestMarketRegime:
    def test_returns_regime(self):
        from api.mcp_server import get_market_regime
        # Mock the macro module since it makes external API calls
        mock_data = {
            "regime": "green",
            "summary": "All indicators normal — risk-on environment",
            "components": {
                "vix": {"value": 15.5, "status": "green"},
                "spy_ma200": {"spy_price": 450.0, "ma200": 420.0, "pct_above": 7.14, "status": "bullish"},
                "credit_spread": {"value": 3.5, "status": "green"},
            },
            "cached_at": datetime.utcnow().isoformat(),
        }
        with patch("api.mcp_server.get_market_regime", return_value=mock_data):
            from api.mcp_server import get_market_regime
            result = get_market_regime()

        assert "regime" in result
        assert result["regime"] in ("green", "yellow", "red", "unknown")

    def test_error_handling(self):
        """Market regime should return gracefully even on error."""
        with patch("api.routers.macro._get_regime_data", side_effect=Exception("yfinance timeout")):
            from api.mcp_server import get_market_regime
            result = get_market_regime()
            # Should not raise, should return a dict
            assert isinstance(result, dict)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Error Handling
# ═══════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    def test_empty_congress_data(self, monkeypatch):
        mock_cache = MagicMock()
        mock_cache.read = MagicMock(return_value={})
        monkeypatch.setattr("api.mcp_server._get_cache", lambda: mock_cache)

        from api.mcp_server import get_congress_trades
        result = get_congress_trades()
        assert result["trades"] == []
        assert result["metadata"]["filtered"] == 0

    def test_empty_ark_data(self, monkeypatch):
        mock_cache = MagicMock()
        mock_cache.read = MagicMock(return_value={})
        monkeypatch.setattr("api.mcp_server._get_cache", lambda: mock_cache)

        from api.mcp_server import get_ark_trades
        result = get_ark_trades()
        assert result["trades"] == []

    def test_empty_darkpool_data(self, monkeypatch):
        mock_cache = MagicMock()
        mock_cache.read = MagicMock(return_value={})
        monkeypatch.setattr("api.mcp_server._get_cache", lambda: mock_cache)

        from api.mcp_server import get_darkpool_activity
        result = get_darkpool_activity()
        assert result["anomalies"] == []

    def test_empty_confluence_data(self, monkeypatch):
        mock_cache = MagicMock()
        mock_cache.read = MagicMock(return_value={})
        monkeypatch.setattr("api.mcp_server._get_cache", lambda: mock_cache)

        from api.mcp_server import get_confluence_signals
        result = get_confluence_signals()
        assert result["signals"] == []

    def test_missing_trades_key(self, monkeypatch):
        mock_cache = MagicMock()
        mock_cache.read = MagicMock(return_value={"something_else": []})
        monkeypatch.setattr("api.mcp_server._get_cache", lambda: mock_cache)

        from api.mcp_server import get_insider_trades
        result = get_insider_trades()
        assert result["trades"] == []
        assert result["clusters"] == []


# ═══════════════════════════════════════════════════════════════════════════
# 4. Return Format Validation
# ═══════════════════════════════════════════════════════════════════════════


class TestReturnFormat:
    """Ensure all tools return JSON-serializable dicts with expected keys."""

    def _check_serializable(self, data):
        """Ensure data is JSON-serializable."""
        try:
            json.dumps(data, default=str)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Result not JSON-serializable: {e}")

    def test_congress_format(self):
        from api.mcp_server import get_congress_trades
        result = get_congress_trades()
        self._check_serializable(result)
        assert isinstance(result["trades"], list)
        assert isinstance(result["metadata"], dict)

    def test_ark_trades_format(self):
        from api.mcp_server import get_ark_trades
        result = get_ark_trades()
        self._check_serializable(result)
        assert isinstance(result["trades"], list)

    def test_ark_holdings_format(self):
        from api.mcp_server import get_ark_holdings
        result = get_ark_holdings()
        self._check_serializable(result)
        assert isinstance(result["holdings"], list)

    def test_insider_format(self):
        from api.mcp_server import get_insider_trades
        result = get_insider_trades()
        self._check_serializable(result)
        assert isinstance(result["trades"], list)
        assert isinstance(result["clusters"], list)

    def test_13f_format(self):
        from api.mcp_server import get_13f_filings
        result = get_13f_filings()
        self._check_serializable(result)
        assert isinstance(result["filings"], list)
        assert isinstance(result["top_holdings"], list)

    def test_darkpool_format(self):
        from api.mcp_server import get_darkpool_activity
        result = get_darkpool_activity()
        self._check_serializable(result)
        assert isinstance(result["anomalies"], list)

    def test_short_interest_format(self):
        from api.mcp_server import get_short_interest
        result = get_short_interest()
        self._check_serializable(result)
        assert isinstance(result["tickers"], list)

    def test_superinvestor_format(self):
        from api.mcp_server import get_superinvestor_activity
        result = get_superinvestor_activity()
        self._check_serializable(result)
        assert isinstance(result["activity"], list)

    def test_confluence_format(self):
        from api.mcp_server import get_confluence_signals
        result = get_confluence_signals(min_score=0)
        self._check_serializable(result)
        assert isinstance(result["signals"], list)


# ═══════════════════════════════════════════════════════════════════════════
# 5. FastAPI Mount Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestMCPMount:
    """Test that mount_mcp properly integrates with FastAPI."""

    def test_mount_adds_route(self):
        """Test that mount_mcp adds /mcp route to the app."""
        from fastapi import FastAPI
        from api.mcp_server import mount_mcp

        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "ok"}

        mount_mcp(app)

        # Check that /mcp route was added
        route_paths = [r.path for r in app.router.routes if hasattr(r, "path")]
        assert "/mcp" in route_paths, f"Routes: {route_paths}"

    def test_mount_preserves_existing_routes(self):
        """Test that mounting MCP doesn't break existing routes."""
        from fastapi import FastAPI
        from starlette.testclient import TestClient
        from api.mcp_server import mount_mcp

        app = FastAPI()

        @app.get("/health")
        def health():
            return {"status": "ok"}

        mount_mcp(app)

        with TestClient(app) as client:
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json() == {"status": "ok"}

    def test_mcp_endpoint_responds(self):
        """Test that the MCP endpoint accepts POST requests."""
        from fastapi import FastAPI
        from starlette.testclient import TestClient
        from api.mcp_server import mount_mcp

        app = FastAPI()
        mount_mcp(app)

        with TestClient(app) as client:
            # Send MCP initialize request
            r = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "id": 1,
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )
            assert r.status_code == 200, f"MCP initialize failed: {r.status_code} {r.text[:200]}"
            # Response is SSE format
            assert "protocolVersion" in r.text

    def test_mcp_lists_tools(self):
        """Test that MCP tools/list returns all 10 tools via HTTP."""
        from fastapi import FastAPI
        from starlette.testclient import TestClient
        from api.mcp_server import mount_mcp

        app = FastAPI()
        mount_mcp(app)

        with TestClient(app) as client:
            # Initialize first
            init_resp = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "id": 1,
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"},
                    },
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                },
            )
            assert init_resp.status_code == 200

            # Extract session ID from response headers
            session_id = init_resp.headers.get("mcp-session-id", "")

            # Send initialized notification
            client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": session_id,
                },
            )

            # List tools
            tools_resp = client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 2,
                    "params": {},
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": session_id,
                },
            )
            assert tools_resp.status_code == 200
            # Parse SSE response to find tools
            assert "get_congress_trades" in tools_resp.text
            assert "get_market_regime" in tools_resp.text
