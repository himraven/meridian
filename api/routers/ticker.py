"""
Ticker lookup routes
"""
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.shared import ARK_DATA_DIR, DATA_DIR, read_json, wants_markdown, markdown_response, smart_money_cache, ticker_names
from api.markdown_format import MARKDOWN_FORMATTERS, TICKER_PATTERN, format_ticker_aggregate
from api.ticker_lookup import TickerNameLookup

router = APIRouter()

# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/ticker/{symbol}")
def api_ticker_aggregate(request: Request, symbol: str):
    """
    Aggregate all smart money data for a single ticker across all sources.
    Returns:
      - Congress trades
      - ARK trades & holdings
      - Dark pool anomalies
      - Institution holdings
      - Confluence signals
    """
    symbol = symbol.upper()
    
    # Congress trades
    congress_data = smart_money_cache.read("congress.json")
    congress_trades = [
        t for t in congress_data.get("trades", [])
        if t.get("ticker", "").upper() == symbol
    ]
    
    # ARK trades
    ark_trades_data = smart_money_cache.read("ark_trades.json")
    ark_trades = [
        t for t in ark_trades_data.get("trades", [])
        if t.get("ticker", "").upper() == symbol
    ]
    
    # ARK holdings
    ark_holdings_data = smart_money_cache.read("ark_holdings.json")
    ark_holdings = [
        h for h in ark_holdings_data.get("holdings", [])
        if h.get("ticker", "").upper() == symbol
    ]
    
    # Dark pool
    darkpool_data = smart_money_cache.read("darkpool.json")
    darkpool_anomalies = [
        d for d in darkpool_data.get("tickers", [])
        if d.get("ticker", "").upper() == symbol
    ]
    
    # Institutions
    institutions_data = smart_money_cache.read("institutions.json")
    institution_holdings = [
        f for f in institutions_data.get("filings", [])
        if f.get("ticker", "").upper() == symbol
    ]
    
    # Confluence signals
    signals_data = smart_money_cache.read("signals.json")
    confluence_signals = [
        s for s in signals_data.get("signals", [])
        if s.get("ticker", "").upper() == symbol
    ]
    
    # Extract company name from available sources
    company_name = None
    for t in ark_trades:
        if t.get("company"):
            company_name = t["company"]
            break
    if not company_name:
        for h in ark_holdings:
            if h.get("company"):
                company_name = h["company"]
                break
    if not company_name:
        for h in institution_holdings:
            if h.get("issuer"):
                company_name = h["issuer"]
                break
    # Also search within institution filing holdings for company/issuer name
    if not company_name:
        for filing in institutions_data.get("filings", []):
            for h in filing.get("holdings", []):
                if h.get("ticker", "").upper() == symbol and h.get("issuer"):
                    company_name = h["issuer"]
                    break
            if company_name:
                break
    # Fallback to global ticker name cache (includes yfinance data)
    if not company_name:
        company_name = ticker_names.get(symbol)
    
    result = {
        "ticker": symbol,
        "company": company_name,
        "congress": {
            "trades": congress_trades,
            "count": len(congress_trades)
        },
        "ark": {
            "trades": ark_trades,
            "holdings": ark_holdings,
            "trade_count": len(ark_trades),
            "holding_etfs": len(ark_holdings)
        },
        "darkpool": {
            "anomalies": darkpool_anomalies,
            "count": len(darkpool_anomalies)
        },
        "institutions": {
            "holdings": institution_holdings,
            "count": len(institution_holdings)
        },
        "confluence": {
            "signals": confluence_signals,
            "score": confluence_signals[0].get("score") if confluence_signals else None
        },
        "metadata": {
            "total_signals": len(congress_trades) + len(ark_trades) + len(darkpool_anomalies) + len(institution_holdings),
            "has_confluence": len(confluence_signals) > 0
        }
    }
    if wants_markdown(request):
        return markdown_response(result, format_ticker_aggregate)
    return result

