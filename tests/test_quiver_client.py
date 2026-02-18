"""
Tests for Quiver API Client.

Tests cover:
- Rate limiting (per-minute and daily)
- Retry logic with exponential backoff
- API key loading
- Response normalization for Congress, DarkPool, ARK
- Error handling (auth, server, connection)
- Trade type normalization
- Health check
"""

import time
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timedelta

# Use dynamic dates so tests don't break over time
_TODAY = datetime.now().strftime("%Y-%m-%d")
_YESTERDAY = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
_3DAYS_AGO = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
_OLD_DATE = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")

from api.modules.quiver_client import (
    QuiverClient,
    QuiverClientError,
    QuiverRateLimitError,
    QuiverAuthError,
    _normalize_trade_type,
    fetch_free_congress_trades,
)


@pytest.fixture
def client():
    """Create a QuiverClient with a dummy key and no rate limit wait."""
    c = QuiverClient(api_key="test_key_123", rate_limit_per_min=100, max_retries=1)
    return c


@pytest.fixture
def mock_response():
    """Factory for mock HTTP responses."""
    def _make(status_code=200, json_data=None, text=""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_data if json_data is not None else []
        resp.text = text
        return resp
    return _make


# ── Initialization ─────────────────────────────────────────────────────


class TestInit:
    def test_with_key(self):
        c = QuiverClient(api_key="my_key")
        assert c.is_configured is True

    def test_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with patch("api.modules.quiver_client._load_api_key", return_value=""):
                c = QuiverClient(api_key="")
                assert c.is_configured is False

    def test_custom_params(self):
        c = QuiverClient(
            api_key="k",
            base_url="https://custom.api.com/v1/",
            rate_limit_per_min=10,
            max_retries=5,
            timeout=60,
        )
        assert c.base_url == "https://custom.api.com/v1"
        assert c.rate_limit_per_min == 10
        assert c.max_retries == 5
        assert c.timeout == 60


# ── Trade Type Normalization ───────────────────────────────────────────


class TestNormalizeTradeType:
    @pytest.mark.parametrize("raw,expected", [
        ("Purchase", "Buy"),
        ("purchase", "Buy"),
        ("Sale", "Sell"),
        ("sale (partial)", "Sell"),
        ("Buy", "Buy"),
        ("Sell", "Sell"),
        ("Exchange", "Exchange"),
        ("Unknown", "Unknown"),
        ("  Purchase  ", "Buy"),
    ])
    def test_normalize(self, raw, expected):
        assert _normalize_trade_type(raw) == expected


# ── Rate Limiting ──────────────────────────────────────────────────────


class TestRateLimiting:
    def test_records_requests(self, client):
        client._record_request()
        assert client._daily_count == 1
        assert len(client._request_timestamps) == 1

    def test_daily_remaining(self, client):
        client._daily_count = 100
        assert client.daily_requests_remaining == 1900  # 2000 - 100

    def test_daily_limit_raises(self, client):
        client._daily_count = 2000
        client._daily_reset = datetime.now().date()
        with pytest.raises(QuiverRateLimitError, match="Daily limit"):
            client._wait_for_rate_limit()

    def test_daily_reset_on_new_day(self, client):
        from datetime import date
        client._daily_count = 1500
        client._daily_reset = date(2020, 1, 1)  # Old date
        client._wait_for_rate_limit()  # Should reset
        assert client._daily_count == 0


# ── Request Error Handling ─────────────────────────────────────────────


class TestRequestErrors:
    def test_no_api_key_raises(self):
        c = QuiverClient(api_key="")
        c.api_key = ""
        with pytest.raises(QuiverAuthError, match="No API key"):
            c.get("test/endpoint")

    def test_401_raises_auth_error(self, client, mock_response):
        with patch.object(client._session, "request", return_value=mock_response(401)):
            with pytest.raises(QuiverAuthError, match="401"):
                client.get("test/endpoint")

    def test_403_raises_auth_error(self, client, mock_response):
        with patch.object(client._session, "request", return_value=mock_response(403)):
            with pytest.raises(QuiverAuthError, match="403"):
                client.get("test/endpoint")

    def test_unexpected_status_raises(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(418, text="I'm a teapot")):
            with pytest.raises(QuiverClientError, match="418"):
                client.get("test/endpoint")

    def test_connection_error_retries(self, client):
        import requests as req
        with patch.object(client._session, "request",
                          side_effect=req.ConnectionError("Network down")):
            with pytest.raises(QuiverClientError, match="Connection error"):
                client.get("test/endpoint")

    def test_timeout_error_retries(self, client):
        import requests as req
        with patch.object(client._session, "request",
                          side_effect=req.Timeout("Timed out")):
            with pytest.raises(QuiverClientError, match="Connection error"):
                client.get("test/endpoint")


# ── Congress Trades ────────────────────────────────────────────────────


class TestCongressTrades:
    SAMPLE_QUIVER_DATA = [
        {
            "Representative": "Nancy Pelosi",
            "Party": "Democrat",
            "House": "House",
            "Transaction": "Purchase",
            "Ticker": "NVDA",
            "TickerType": "Stock",
            "Range": "$100,001 - $250,000",
            "TransactionDate": _3DAYS_AGO,
            "ReportDate": _YESTERDAY,
            "ExcessReturn": 5.2,
            "PriceChange": 6.7,
            "SPYChange": 1.5,
        },
        {
            "Representative": "Tommy Tuberville",
            "Party": "Republican",
            "House": "Senate",
            "Transaction": "Sale (Partial)",
            "Ticker": "AAPL",
            "TickerType": "Stock",
            "Range": "$50,001 - $100,000",
            "TransactionDate": _3DAYS_AGO,
            "ReportDate": _YESTERDAY,
            "ExcessReturn": -1.5,
            "PriceChange": -2.0,
            "SPYChange": -0.5,
        },
        {
            "Representative": "Test Rep",
            "Ticker": "--",  # Should be filtered
            "ReportDate": _YESTERDAY,
            "TickerType": "Stock",
        },
        {
            "Representative": "Test Rep 2",
            "Ticker": "SPY",
            "TickerType": "ETF",  # Non-stock, filtered
            "ReportDate": _YESTERDAY,
        },
    ]

    def test_parses_valid_trades(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, self.SAMPLE_QUIVER_DATA)):
            trades = client.get_congress_trades(days=30)

        assert len(trades) == 2  # 2 of 4 pass filters

        pelosi = trades[0]
        assert pelosi["ticker"] == "NVDA"
        assert pelosi["representative"] == "Nancy Pelosi"
        assert pelosi["party"] == "Democrat"
        assert pelosi["chamber"] == "House"
        assert pelosi["trade_type"] == "Buy"
        assert pelosi["excess_return"] == 5.2

        tuberville = trades[1]
        assert tuberville["ticker"] == "AAPL"
        assert tuberville["trade_type"] == "Sell"

    def test_filters_old_trades_by_date(self, client, mock_response):
        old_data = [
            {
                "Representative": "Old Timer",
                "Party": "Democrat",
                "House": "House",
                "Transaction": "Purchase",
                "Ticker": "OLD",
                "TickerType": "Stock",
                "Range": "$15,001 - $50,000",
                "TransactionDate": _OLD_DATE,
                "ReportDate": _OLD_DATE,
            }
        ]
        with patch.object(client._session, "request",
                          return_value=mock_response(200, old_data)):
            trades = client.get_congress_trades(days=30)
        assert len(trades) == 0

    def test_empty_response(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, [])):
            trades = client.get_congress_trades()
        assert trades == []

    def test_non_list_response(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, {"error": "bad"})):
            trades = client.get_congress_trades()
        assert trades == []


# ── Dark Pool Data ─────────────────────────────────────────────────────


class TestDarkPoolData:
    SAMPLE_DARKPOOL = [
        {
            "Ticker": "NVDA",
            "Date": _YESTERDAY,
            "ShortVolume": 45200000,
            "TotalVolume": 50800000,
            "Price": 875.43,
        },
        {
            "Ticker": "NVDA",
            "Date": _3DAYS_AGO,
            "ShortVolume": 30000000,
            "TotalVolume": 40000000,
            "Price": 860.10,
        },
        {
            "Ticker": "NVDA",
            "Date": _OLD_DATE,  # Old, should be filtered with days=90
            "ShortVolume": 10000000,
            "TotalVolume": 20000000,
        },
    ]

    def test_parses_darkpool_data(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, self.SAMPLE_DARKPOOL)):
            records = client.get_darkpool_data(ticker="NVDA", days=90)

        assert len(records) == 2  # 2 recent, 1 old (>400 days) filtered out
        assert records[0]["ticker"] == "NVDA"
        assert records[0]["otc_short"] == 45200000
        assert records[0]["otc_total"] == 50800000
        assert records[0]["price"] == 875.43

    def test_filters_old_data_by_date(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, self.SAMPLE_DARKPOOL)):
            records = client.get_darkpool_data(ticker="NVDA", days=1)
        # Only yesterday's record should pass (days=1 cutoff)
        assert len(records) == 1
        assert records[0]["date"] == _YESTERDAY

    def test_uses_ticker_in_endpoint(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, [])) as mock_req:
            client.get_darkpool_data(ticker="AAPL")
        call_args = mock_req.call_args
        assert "AAPL" in call_args[1].get("url", call_args[0][1] if len(call_args[0]) > 1 else "")


# ── ARK Trades ─────────────────────────────────────────────────────────


class TestArkTrades:
    SAMPLE_ARK = [
        {
            "Ticker": "COIN",
            "Fund": "ARKK",
            "Direction": "Buy",
            "Date": _YESTERDAY,
            "Shares": 125000,
            "Weight": 2.3,
        },
        {
            "Ticker": "TSLA",
            "Fund": "ARKK",
            "Direction": "Sell",
            "Date": _3DAYS_AGO,
            "Shares": 50000,
            "Weight": 0.5,
        },
    ]

    def test_parses_ark_trades(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, self.SAMPLE_ARK)):
            trades = client.get_ark_trades(days=30)

        assert len(trades) == 2
        assert trades[0]["ticker"] == "COIN"
        assert trades[0]["etf"] == "ARKK"
        assert trades[0]["trade_type"] == "Buy"
        assert trades[0]["shares"] == 125000
        assert trades[1]["trade_type"] == "Sell"

    def test_empty_tickers_filtered(self, client, mock_response):
        data = [{"Ticker": "", "Fund": "ARKK", "Date": _YESTERDAY, "Direction": "Buy"}]
        with patch.object(client._session, "request",
                          return_value=mock_response(200, data)):
            trades = client.get_ark_trades(days=30)
        assert len(trades) == 0


# ── Health Check ───────────────────────────────────────────────────────


class TestHealthCheck:
    def test_healthy(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(200, [{"test": True}])):
            result = client.health_check()
        assert result["ok"] is True
        assert "daily_remaining" in result

    def test_auth_failure(self, client, mock_response):
        with patch.object(client._session, "request",
                          return_value=mock_response(401)):
            result = client.health_check()
        assert result["ok"] is False
        assert "401" in result["error"]

    def test_no_key(self):
        c = QuiverClient(api_key="")
        c.api_key = ""
        result = c.health_check()
        assert result["ok"] is False
        assert "No API key" in result["error"]
