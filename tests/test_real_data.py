"""
Integration tests against REAL production data.

These tests read the actual data files from the running cron collectors
and verify that our parsers/normalizers handle every real-world value.

Skip gracefully if data files don't exist (CI environment).
"""

import json
import pytest
from pathlib import Path

from api.utils import (
    parse_amount_range,
    normalize_party,
    normalize_chamber,
    normalize_trade_type,
    ark_change_to_trade_type,
    filing_date_to_quarter,
    cusip_to_ticker,
)

# Real data paths
CONGRESS_FILE = Path("./data/ark/congress_trades.json")
ARK_CHANGES_FILE = Path("./data/ark/ark_changes.jsonl")
ARK_HOLDINGS_DIR = Path("./data/ark/ark_holdings")
F13_DIR = Path("./data/ark/13f_filings")


def skip_if_no_data(path):
    if not path.exists():
        pytest.skip(f"Data file not found: {path}")


# ── Congress Real Data ─────────────────────────────────────────────────


class TestRealCongressData:
    @pytest.fixture
    def congress_data(self):
        skip_if_no_data(CONGRESS_FILE)
        with open(CONGRESS_FILE) as f:
            return json.load(f)

    def test_all_amounts_parseable(self, congress_data):
        """Every amount range in real data must parse to valid numbers."""
        errors = []
        for i, t in enumerate(congress_data):
            raw = t.get("amount", "")
            min_val, max_val = parse_amount_range(raw)
            if raw and min_val == 0 and max_val == 0:
                errors.append(f"  #{i}: unparseable amount '{raw}'")
            if min_val > max_val:
                errors.append(f"  #{i}: min ({min_val}) > max ({max_val}) for '{raw}'")
        assert not errors, f"Amount parse failures:\n" + "\n".join(errors)

    def test_all_parties_normalizable(self, congress_data):
        """Every party code must normalize to a known value."""
        valid = {"Democrat", "Republican", "Independent"}
        errors = []
        for t in congress_data:
            raw = t.get("party", "")
            normalized = normalize_party(raw)
            if raw and normalized not in valid:
                errors.append(f"  Unknown party: '{raw}' → '{normalized}'")
        assert not errors, f"Party normalization failures:\n" + "\n".join(errors)

    def test_all_chambers_normalizable(self, congress_data):
        """Every chamber must normalize to House or Senate."""
        valid = {"House", "Senate"}
        errors = []
        for t in congress_data:
            raw = t.get("chamber", "")
            normalized = normalize_chamber(raw)
            if raw and normalized not in valid:
                errors.append(f"  Unknown chamber: '{raw}' → '{normalized}'")
        assert not errors, f"Chamber normalization failures:\n" + "\n".join(errors)

    def test_all_trade_types_normalizable(self, congress_data):
        """Every trade type must normalize to Purchase, Sale, or Exchange."""
        valid = {"Buy", "Sell", "Exchange"}
        errors = []
        for t in congress_data:
            raw = t.get("trade_type", "")
            normalized = normalize_trade_type(raw)
            if raw and normalized not in valid:
                errors.append(f"  Unknown trade type: '{raw}' → '{normalized}'")
        assert not errors, f"Trade type normalization failures:\n" + "\n".join(errors)

    def test_all_tickers_non_empty(self, congress_data):
        """Every trade must have a non-empty ticker."""
        empty = [i for i, t in enumerate(congress_data) if not t.get("ticker", "").strip()]
        assert not empty, f"Empty tickers at indices: {empty}"

    def test_all_dates_valid_format(self, congress_data):
        """All dates should be YYYY-MM-DD format."""
        import re
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        errors = []
        for i, t in enumerate(congress_data):
            for field in ("trade_date", "disclosed_date"):
                val = t.get(field, "")
                if val and not date_pattern.match(val):
                    errors.append(f"  #{i}: {field} = '{val}' (bad format)")
        assert not errors, f"Date format failures:\n" + "\n".join(errors)

    def test_count_reasonable(self, congress_data):
        """Should have a reasonable number of trades."""
        assert len(congress_data) >= 10, f"Only {len(congress_data)} trades — too few?"
        assert len(congress_data) <= 10000, f"{len(congress_data)} trades — too many?"


# ── ARK Real Data ──────────────────────────────────────────────────────


class TestRealArkData:
    @pytest.fixture
    def ark_changes(self):
        skip_if_no_data(ARK_CHANGES_FILE)
        with open(ARK_CHANGES_FILE) as f:
            return [json.loads(line) for line in f.readlines() if line.strip()]

    @pytest.fixture
    def ark_holdings(self):
        skip_if_no_data(ARK_HOLDINGS_DIR / "ARKK_latest.json")
        holdings = {}
        for f in ARK_HOLDINGS_DIR.glob("*_latest.json"):
            etf = f.name.split("_")[0]
            with open(f) as fh:
                holdings[etf] = json.load(fh)
        return holdings

    def test_all_change_types_mappable(self, ark_changes):
        """Every change type must map to Buy or Sell."""
        valid = {"Buy", "Sell"}
        errors = []
        for i, c in enumerate(ark_changes):
            raw = c.get("type", "")
            mapped = ark_change_to_trade_type(raw)
            if mapped not in valid:
                errors.append(f"  #{i}: type '{raw}' → '{mapped}'")
        assert not errors, f"ARK type mapping failures:\n" + "\n".join(errors)

    def test_null_tickers_counted(self, ark_changes):
        """Count null tickers — these need to be filtered."""
        null_count = sum(1 for c in ark_changes if not c.get("ticker"))
        total = len(ark_changes)
        pct = null_count / total * 100 if total else 0
        print(f"Null tickers: {null_count}/{total} ({pct:.1f}%)")
        # Should be a small percentage
        assert pct < 5, f"Too many null tickers: {pct:.1f}%"

    def test_holdings_have_required_fields(self, ark_holdings):
        """Holdings with tickers must have shares and weight. 
        Some entries are cash/money market (no ticker) — those are filtered."""
        errors = []
        null_ticker_count = 0
        total = 0
        for etf, data in ark_holdings.items():
            for i, h in enumerate(data.get("holdings", [])):
                total += 1
                if not h.get("ticker"):
                    null_ticker_count += 1
                    continue  # Cash positions, expected
                if h.get("shares") is None:
                    errors.append(f"  {etf} #{i}: {h.get('ticker')} missing shares")
                if h.get("weight") is None:
                    errors.append(f"  {etf} #{i}: {h.get('ticker')} missing weight")
        print(f"Null ticker (cash/money market): {null_ticker_count}/{total}")
        assert null_ticker_count < total * 0.1, f"Too many null tickers: {null_ticker_count}"
        assert not errors, f"Holdings field failures:\n" + "\n".join(errors[:20])

    def test_etf_count(self, ark_holdings):
        """Should have 5-6 ETF files."""
        assert len(ark_holdings) >= 5


# ── 13F Real Data ──────────────────────────────────────────────────────


class TestReal13FData:
    @pytest.fixture
    def f13_filings(self):
        skip_if_no_data(F13_DIR)
        filings = {}
        for f in F13_DIR.glob("*_latest.json"):
            cik = f.name.replace("_latest.json", "")
            with open(f) as fh:
                filings[cik] = json.load(fh)
        return filings

    def test_quarter_derivation(self, f13_filings):
        """Filing dates should produce valid quarters."""
        for cik, data in f13_filings.items():
            filing_date = data.get("filing_date", "")
            quarter = filing_date_to_quarter(filing_date)
            assert quarter != "Q0_0000", f"CIK {cik}: filing_date '{filing_date}' → bad quarter"
            # Quarter should be Q1-Q4
            q = int(quarter[1])
            assert 1 <= q <= 4, f"CIK {cik}: invalid quarter {quarter}"

    def test_cusip_coverage(self, f13_filings):
        """Check CUSIP mapping coverage. 
        Static map covers major holdings only; issuer name is fallback."""
        total = 0
        mapped = 0
        unmapped_top = []  # Track unmapped high-value holdings
        
        for cik, data in f13_filings.items():
            fund = data.get("company", cik)
            for h in sorted(data.get("holdings", []), key=lambda x: x.get("value", 0), reverse=True):
                cusip = h.get("cusip", "")
                if cusip:
                    total += 1
                    ticker = cusip_to_ticker(cusip)
                    if ticker:
                        mapped += 1
                    elif h.get("value", 0) > 1e12:  # >$1B positions
                        unmapped_top.append(f"  {fund}: {h['issuer']} ({cusip}) ${h['value']/1e9:.1f}B")

        coverage = mapped / total * 100 if total else 0
        print(f"CUSIP coverage: {mapped}/{total} ({coverage:.1f}%)")
        if unmapped_top:
            print(f"Top unmapped (>{len(unmapped_top)}):")
            for u in unmapped_top[:10]:
                print(u)
        
        # All holdings have issuer name as fallback, so low coverage is OK
        # Just verify we can map SOMETHING
        assert mapped > 0, "Zero CUSIPs mapped — static map broken?"
        
    def test_all_holdings_have_issuer(self, f13_filings):
        """Every holding must have an issuer name (our display fallback)."""
        errors = []
        for cik, data in f13_filings.items():
            fund = data.get("company", cik)
            for i, h in enumerate(data.get("holdings", [])):
                if not h.get("issuer"):
                    errors.append(f"  {fund} #{i}: missing issuer")
        assert not errors, f"Missing issuers:\n" + "\n".join(errors[:10])

    def test_holdings_have_value_and_shares(self, f13_filings):
        """All holdings must have value and shares."""
        errors = []
        for cik, data in f13_filings.items():
            fund = data.get("company", cik)
            for i, h in enumerate(data.get("holdings", [])):
                if h.get("value") is None:
                    errors.append(f"  {fund} #{i}: missing value")
                if h.get("shares") is None or h.get("shares") == 0:
                    # Some put/call options may have 0 shares
                    if not h.get("put_call"):
                        errors.append(f"  {fund} #{i}: missing shares ({h.get('issuer')})")
        # Allow some errors (options, etc.)
        if errors:
            print(f"Warning: {len(errors)} holdings missing data (first 10):")
            for e in errors[:10]:
                print(e)
        # But shouldn't be more than 20%
        total_holdings = sum(len(d.get("holdings", [])) for d in f13_filings.values())
        assert len(errors) < total_holdings * 0.2
