"""
Shared Utilities — Data parsing, normalization, mapping.

These are pure functions used across collectors and the signal engine.
No side effects, fully testable.
"""

import re
from typing import Optional, Tuple


# ── Amount Range Parser ────────────────────────────────────────────────


# Matches: "$1,001 - $15,000" or "$100,001 - $250,000" or "$50,001-$100,000"
_AMOUNT_PATTERN = re.compile(
    r"\$?([\d,]+)\s*-\s*\$?([\d,]+)"
)

# Single amount: "$1,000,001" or "Over $1,000,000"
_SINGLE_AMOUNT_PATTERN = re.compile(r"\$?([\d,]+)")


def parse_amount_range(raw: str) -> Tuple[float, float]:
    """
    Parse Congress trade amount range string into (min, max) floats.
    
    Examples:
        "$1,001 - $15,000"       → (1001.0, 15000.0)
        "$100,001 - $250,000"    → (100001.0, 250000.0)
        "$50,001-$100,000"       → (50001.0, 100000.0)
        "Over $1,000,000"        → (1000000.0, 1000000.0)
        ""                       → (0.0, 0.0)
    """
    if not raw:
        return 0.0, 0.0

    match = _AMOUNT_PATTERN.search(raw)
    if match:
        min_val = float(match.group(1).replace(",", ""))
        max_val = float(match.group(2).replace(",", ""))
        return min_val, max_val

    # Single amount
    match = _SINGLE_AMOUNT_PATTERN.search(raw)
    if match:
        val = float(match.group(1).replace(",", ""))
        return val, val

    return 0.0, 0.0


# ── Party Normalization ────────────────────────────────────────────────


_PARTY_MAP = {
    "D": "Democrat",
    "R": "Republican",
    "I": "Independent",
    "Democrat": "Democrat",
    "Republican": "Republican",
    "Independent": "Independent",
}


def normalize_party(raw: str) -> str:
    """
    Normalize party code to full name.
    "D" → "Democrat", "R" → "Republican", "I" → "Independent"
    """
    return _PARTY_MAP.get(raw.strip(), raw.strip())


# ── Chamber Normalization ──────────────────────────────────────────────


def normalize_chamber(raw: str) -> str:
    """Normalize chamber to 'House' or 'Senate'."""
    lower = raw.lower().strip()
    if "house" in lower:
        return "House"
    elif "senate" in lower:
        return "Senate"
    return raw.strip()


# ── Trade Type Normalization ───────────────────────────────────────────


def normalize_trade_type(raw: str) -> str:
    """
    Normalize trade type to canonical 'Buy' / 'Sell' / 'Exchange'.
    
    Per SCHEMA.md, all trade_type fields use Buy/Sell across the platform.
    
    "Purchase"        → "Buy"
    "Sale (Full)"     → "Sell"
    "Sale (Partial)"  → "Sell"
    "Buy"             → "Buy"
    "Sell"            → "Sell"
    """
    lower = raw.lower().strip()
    if "purchase" in lower or "buy" in lower:
        return "Buy"
    elif "sale" in lower or "sell" in lower:
        return "Sell"
    elif "exchange" in lower:
        return "Exchange"
    return raw.strip()


# ── ARK Change Type → Trade Type ──────────────────────────────────────


def ark_change_to_trade_type(change_type: str) -> str:
    """
    Map ARK change type to normalized trade type.
    
    "NEW_POSITION" → "Buy"
    "INCREASED"    → "Buy"
    "DECREASED"    → "Sell"
    "SOLD_OUT"     → "Sell"
    """
    if change_type in ("NEW_POSITION", "INCREASED"):
        return "Buy"
    elif change_type in ("DECREASED", "SOLD_OUT"):
        return "Sell"
    return change_type


# ── 13F Quarter Derivation ────────────────────────────────────────────


def filing_date_to_quarter(filing_date: str) -> str:
    """
    Derive quarter from 13F filing date.
    
    13F is filed ~45 days after quarter end, so:
    - Filed Jan-Mar → Q4 of prior year
    - Filed Apr-Jun → Q1 of same year  
    - Filed Jul-Sep → Q2 of same year
    - Filed Oct-Dec → Q3 of same year
    
    "2025-11-14" → "Q3_2025"
    "2025-02-14" → "Q4_2024"
    """
    if not filing_date or len(filing_date) < 10:
        return "Q0_0000"
    
    try:
        year = int(filing_date[:4])
        month = int(filing_date[5:7])
    except (ValueError, IndexError):
        return "Q0_0000"

    if month <= 3:
        return f"Q4_{year - 1}"
    elif month <= 6:
        return f"Q1_{year}"
    elif month <= 9:
        return f"Q2_{year}"
    else:
        return f"Q3_{year}"


# ── CUSIP → Ticker Mapping ────────────────────────────────────────────

# Common CUSIP mappings for major stocks held by tracked institutions.
# This is a static map for the most important holdings.
# For production, consider SEC EDGAR company search or OpenFIGI API.
CUSIP_TO_TICKER = {
    "02005N100": "ALLY",
    "023135106": "AMZN",
    "02079K107": "GOOGL",
    "02079K305": "GOOG",
    "030420103": "AIG",
    "03027X100": "AEO",
    "03783310": "AMAT",
    "037833100": "AAPL",
    "046353101": "ATVI",
    "05278C107": "AVTR",
    "064058100": "BAC",
    "084670702": "BRK.B",
    "11135F101": "BMY",
    "12504L109": "CB",
    "126650100": "CVS",
    "131347100": "C",
    "166764100": "CVX",
    "172967424": "C",
    "17275R102": "CSCO",
    "191216100": "KO",
    "20030N101": "COF",
    "22160K105": "COST",
    "23804L103": "DAL",
    "254709108": "DIS",
    "256219106": "DVA",
    "278642103": "EBAY",
    "30303M102": "META",
    "31428X106": "FDX",
    "345838106": "F",
    "369604103": "GE",
    "38141G104": "GS",
    "40412C101": "HPQ",
    "437076102": "HD",
    "459200101": "IBM",
    "46120E602": "ITOCY",
    "464287465": "IFF",
    "478160104": "JNJ",
    "48020Q107": "JPM",
    "500754106": "KHC",
    "513272104": "LLY",
    "532457108": "LMT",
    "571903202": "MARKEL",
    "580135101": "MCD",
    "585055106": "MDT",
    "594918104": "MSFT",
    "60871R209": "MHLD",
    "617446448": "MS",
    "629377508": "NUE",
    "637071101": "NRG",
    "654106103": "NKE",
    "68389X105": "ORCL",
    "693475105": "OXY",
    "698813102": "PM",
    "713448108": "PEP",
    "717081103": "PFE",
    "718172109": "PG",
    "742718109": "PNC",
    "74762E102": "QRVO",
    "806857108": "SLB",
    "808513105": "SNOW",
    "81369Y704": "SEN",
    "825690100": "SHEL",
    "83406F102": "SIRI",
    "842587107": "SPR",
    "871829107": "SYF",
    "87612E106": "TMUS",
    "88160R101": "TSLA",
    "89236T104": "TROW",
    "90184L102": "TWLO",
    "902973304": "UPS",
    "911312106": "UNP",
    "91324P102": "UNH",
    "92826C839": "V",
    "92343V104": "VRSN",
    "92556V106": "VZ",
    "931142103": "WMT",
    "949746101": "WFC",
}


def cusip_to_ticker(cusip: str) -> Optional[str]:
    """
    Map CUSIP to ticker symbol.
    
    Returns None if mapping not found.
    For production, extend with SEC EDGAR API or OpenFIGI.
    """
    return CUSIP_TO_TICKER.get(cusip)
