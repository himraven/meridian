"""
Tests for shared utilities.

Validates:
- Amount range parsing (all real Congress data patterns)
- Party normalization (D/R/I → full names)
- Chamber normalization
- Trade type normalization (all real patterns)
- ARK change type mapping
- 13F quarter derivation from filing date
- CUSIP → Ticker mapping
"""

import pytest
from api.utils import (
    parse_amount_range,
    normalize_party,
    normalize_chamber,
    normalize_trade_type,
    ark_change_to_trade_type,
    filing_date_to_quarter,
    cusip_to_ticker,
)


# ── Amount Range Parser ────────────────────────────────────────────────


class TestParseAmountRange:
    """Test against all real patterns seen in Congress data."""

    def test_standard_range(self):
        assert parse_amount_range("$1,001 - $15,000") == (1001.0, 15000.0)

    def test_medium_range(self):
        assert parse_amount_range("$15,001 - $50,000") == (15001.0, 50000.0)

    def test_large_range(self):
        assert parse_amount_range("$50,001 - $100,000") == (50001.0, 100000.0)

    def test_very_large_range(self):
        assert parse_amount_range("$100,001 - $250,000") == (100001.0, 250000.0)

    def test_million_range(self):
        assert parse_amount_range("$250,001 - $500,000") == (250001.0, 500000.0)

    def test_no_spaces(self):
        assert parse_amount_range("$50,001-$100,000") == (50001.0, 100000.0)

    def test_over_amount(self):
        assert parse_amount_range("Over $1,000,000") == (1000000.0, 1000000.0)

    def test_empty_string(self):
        assert parse_amount_range("") == (0.0, 0.0)

    def test_none_safe(self):
        assert parse_amount_range("") == (0.0, 0.0)

    def test_unparseable(self):
        assert parse_amount_range("Unknown") == (0.0, 0.0)


# ── Party Normalization ────────────────────────────────────────────────


class TestNormalizeParty:
    def test_d_to_democrat(self):
        assert normalize_party("D") == "Democrat"

    def test_r_to_republican(self):
        assert normalize_party("R") == "Republican"

    def test_i_to_independent(self):
        assert normalize_party("I") == "Independent"

    def test_full_name_passthrough(self):
        assert normalize_party("Democrat") == "Democrat"
        assert normalize_party("Republican") == "Republican"

    def test_whitespace_stripped(self):
        assert normalize_party("  D  ") == "Democrat"

    def test_unknown_passthrough(self):
        assert normalize_party("Other") == "Other"


# ── Chamber Normalization ──────────────────────────────────────────────


class TestNormalizeChamber:
    def test_house(self):
        assert normalize_chamber("House") == "House"

    def test_senate(self):
        assert normalize_chamber("Senate") == "Senate"

    def test_case_insensitive(self):
        assert normalize_chamber("house") == "House"
        assert normalize_chamber("SENATE") == "Senate"

    def test_whitespace(self):
        assert normalize_chamber("  Senate  ") == "Senate"


# ── Trade Type Normalization ───────────────────────────────────────────


class TestNormalizeTradeType:
    """Test against all real patterns from Congress data."""

    def test_purchase(self):
        assert normalize_trade_type("Purchase") == "Buy"

    def test_sale_full(self):
        assert normalize_trade_type("Sale (Full)") == "Sell"

    def test_sale_partial(self):
        assert normalize_trade_type("Sale (Partial)") == "Sell"

    def test_buy(self):
        assert normalize_trade_type("Buy") == "Buy"

    def test_sell(self):
        assert normalize_trade_type("Sell") == "Sell"

    def test_exchange(self):
        assert normalize_trade_type("Exchange") == "Exchange"

    def test_case_insensitive(self):
        assert normalize_trade_type("purchase") == "Buy"
        assert normalize_trade_type("SALE") == "Sell"


# ── ARK Change Type Mapping ───────────────────────────────────────────


class TestArkChangeToTradeType:
    def test_new_position(self):
        assert ark_change_to_trade_type("NEW_POSITION") == "Buy"

    def test_increased(self):
        assert ark_change_to_trade_type("INCREASED") == "Buy"

    def test_decreased(self):
        assert ark_change_to_trade_type("DECREASED") == "Sell"

    def test_sold_out(self):
        assert ark_change_to_trade_type("SOLD_OUT") == "Sell"

    def test_unknown_passthrough(self):
        assert ark_change_to_trade_type("OTHER") == "OTHER"


# ── Quarter Derivation ────────────────────────────────────────────────


class TestFilingDateToQuarter:
    """
    13F filed ~45 days after quarter end:
    - Q4 (Oct-Dec) → filed Jan-Mar next year
    - Q1 (Jan-Mar) → filed Apr-Jun
    - Q2 (Apr-Jun) → filed Jul-Sep
    - Q3 (Jul-Sep) → filed Oct-Dec
    """

    def test_q4_filing_in_february(self):
        assert filing_date_to_quarter("2025-02-14") == "Q4_2024"

    def test_q4_filing_in_january(self):
        assert filing_date_to_quarter("2025-01-15") == "Q4_2024"

    def test_q3_filing_in_november(self):
        assert filing_date_to_quarter("2025-11-14") == "Q3_2025"

    def test_q1_filing_in_may(self):
        assert filing_date_to_quarter("2025-05-15") == "Q1_2025"

    def test_q2_filing_in_august(self):
        assert filing_date_to_quarter("2025-08-14") == "Q2_2025"

    def test_empty_string(self):
        assert filing_date_to_quarter("") == "Q0_0000"

    def test_invalid_date(self):
        assert filing_date_to_quarter("not-a-date") == "Q0_0000"

    def test_boundary_march(self):
        """March filing → Q4 of prior year."""
        assert filing_date_to_quarter("2025-03-31") == "Q4_2024"

    def test_boundary_april(self):
        """April filing → Q1 of same year."""
        assert filing_date_to_quarter("2025-04-01") == "Q1_2025"

    def test_boundary_june(self):
        assert filing_date_to_quarter("2025-06-30") == "Q1_2025"

    def test_boundary_july(self):
        assert filing_date_to_quarter("2025-07-01") == "Q2_2025"

    def test_boundary_september(self):
        assert filing_date_to_quarter("2025-09-30") == "Q2_2025"

    def test_boundary_october(self):
        assert filing_date_to_quarter("2025-10-01") == "Q3_2025"

    def test_boundary_december(self):
        assert filing_date_to_quarter("2025-12-31") == "Q3_2025"


# ── CUSIP → Ticker ─────────────────────────────────────────────────────


class TestCusipToTicker:
    def test_known_cusip(self):
        assert cusip_to_ticker("037833100") == "AAPL"
        assert cusip_to_ticker("594918104") == "MSFT"
        assert cusip_to_ticker("88160R101") == "TSLA"

    def test_unknown_cusip(self):
        assert cusip_to_ticker("000000000") is None

    def test_berkshire(self):
        assert cusip_to_ticker("084670702") == "BRK.B"

    def test_meta(self):
        assert cusip_to_ticker("30303M102") == "META"
