"""
Ticker lookup routes
"""
import json
import logging
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.shared import ARK_DATA_DIR, DATA_DIR, read_json, wants_markdown, markdown_response, smart_money_cache, ticker_names
from api.markdown_format import MARKDOWN_FORMATTERS, TICKER_PATTERN, format_ticker_aggregate
from api.ticker_lookup import TickerNameLookup

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_duckdb():
    """Get DuckDB store, or None if not available."""
    try:
        from api.modules.duckdb_store import get_store
        store = get_store()
        if store._initialized or store.table_exists("congress_trades"):
            return store
        return None
    except Exception:
        return None

# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/ticker/search")
def api_ticker_search(q: str = ""):
    """Search tickers by symbol or company name."""
    q = q.strip().upper()
    if len(q) < 1:
        return {"results": []}
    
    results = []
    names = ticker_names.get_all()
    
    # Exact symbol matches first
    for symbol, name in names.items():
        if symbol == q:
            results.insert(0, {"ticker": symbol, "company": name or ""})
        elif q in symbol:
            results.append({"ticker": symbol, "company": name or ""})
        elif name and q in name.upper():
            results.append({"ticker": symbol, "company": name or ""})
        if len(results) >= 20:
            break
    
    return {"results": results}


@router.get("/api/ticker/{symbol}")
def api_ticker_aggregate(request: Request, symbol: str):
    """
    Aggregate all smart money data for a single ticker across all sources.
    Returns:
      - Congress trades
      - ARK trades & holdings
      - Dark pool anomalies
      - Institution holdings
      - Insider trades
      - Confluence signals
    Uses DuckDB query layer with JSON fallback.
    """
    symbol = symbol.upper()

    # ── DuckDB fast path ──────────────────────────────────────────────
    db = _get_duckdb()
    if db is not None:
        try:
            # Batch all queries on a single connection (~40ms total vs ~240ms)
            batch_results = db.query_many([
                ("SELECT * FROM congress_trades WHERE UPPER(ticker) = ? ORDER BY transaction_date DESC", [symbol]),
                ("SELECT * FROM ark_trades WHERE UPPER(ticker) = ? ORDER BY date DESC", [symbol]),
                ("SELECT * FROM darkpool_tickers WHERE UPPER(ticker) = ? ORDER BY date DESC", [symbol]),
                ("SELECT * FROM institution_holdings WHERE UPPER(ticker) = ? ORDER BY value DESC", [symbol]),
                ("SELECT * FROM insider_trades WHERE UPPER(ticker) = ? ORDER BY COALESCE(trade_date, filing_date) DESC", [symbol]),
                ("SELECT * FROM ranking WHERE UPPER(ticker) = ?", [symbol]),
            ])
            congress_trades, ark_trades, darkpool_anomalies, institution_holdings, insider_trades, confluence_signals = batch_results

            # ARK holdings still from JSON (not in DuckDB - separate file)
            ark_holdings_data = smart_money_cache.read("ark_holdings.json")
            ark_holdings = [
                h for h in ark_holdings_data.get("holdings", [])
                if h.get("ticker", "").upper() == symbol
            ]
            if not confluence_signals:
                signals_data = smart_money_cache.read("ranking_v2.json")
                if not signals_data.get("signals"):
                    signals_data = smart_money_cache.read("ranking.json")
                confluence_signals = [
                    s for s in signals_data.get("signals", [])
                    if s.get("ticker", "").upper() == symbol
                ]

            # Extract company name — check all data sources
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
            if not company_name:
                for t in insider_trades:
                    if t.get("company"):
                        company_name = t["company"]
                        break
            if not company_name:
                for t in congress_trades:
                    if t.get("company"):
                        company_name = t["company"]
                        break
            if not company_name:
                company_name = ticker_names.get(symbol)

            # Parse JSON strings back for details/sources in confluence signals
            parsed_signals = []
            for s in confluence_signals:
                row = dict(s)
                if isinstance(row.get("details"), str):
                    try:
                        row["details"] = json.loads(row["details"])
                    except Exception:
                        row["details"] = []
                if isinstance(row.get("sources"), str):
                    try:
                        row["sources"] = json.loads(row["sources"])
                    except Exception:
                        row["sources"] = row.get("sources_str", "").split(",") if row.get("sources_str") else []
                parsed_signals.append(row)

            signal = parsed_signals[0] if parsed_signals else {}
            confluence_detail = {
                "signals": parsed_signals,
                "score": signal.get("score", 0),
                "direction": signal.get("direction"),
                "sources": signal.get("sources", []),
                "source_count": signal.get("source_count", 0),
                "signal_date": signal.get("signal_date"),
                "congress_score": signal.get("congress_conviction", signal.get("congress_score", 0)),
                "ark_score": signal.get("ark_conviction", signal.get("ark_score", 0)),
                "darkpool_score": signal.get("darkpool_conviction", signal.get("darkpool_score", 0)),
                "institution_score": signal.get("institution_conviction", signal.get("institution_score", 0)),
                "insider_score": signal.get("insider_conviction", signal.get("insider_score", 0)),
                "superinvestor_score": signal.get("superinvestor_conviction", signal.get("superinvestor_score", 0)),
                "short_interest_score": signal.get("short_interest_score", 0),
                "max_conviction": signal.get("max_conviction", 0),
                "multi_source_bonus": signal.get("multi_source_bonus", 0),
                "details": signal.get("details", []),
            }

            result = {
                "ticker": symbol,
                "company": company_name,
                "congress": {"trades": congress_trades, "count": len(congress_trades)},
                "ark": {
                    "trades": ark_trades,
                    "holdings": ark_holdings,
                    "trade_count": len(ark_trades),
                    "holding_etfs": len(ark_holdings),
                },
                "darkpool": {"anomalies": darkpool_anomalies, "count": len(darkpool_anomalies)},
                "institutions": {"holdings": institution_holdings, "count": len(institution_holdings)},
                "insiders": {
                    "trades": insider_trades,
                    "count": len(insider_trades),
                    "has_cluster": any(t.get("is_cluster") for t in insider_trades),
                },
                "confluence": confluence_detail,
                "metadata": {
                    "total_signals": (
                        len(congress_trades) + len(ark_trades) +
                        len(darkpool_anomalies) + len(institution_holdings) +
                        len(insider_trades)
                    ),
                    "has_confluence": len(parsed_signals) > 0,
                    "source": "duckdb",
                }
            }
            if wants_markdown(request):
                return markdown_response(result, format_ticker_aggregate)
            return result

        except Exception as e:
            logger.warning(f"[duckdb] ticker/{symbol} query failed, falling back to JSON: {e}")

    # ── JSON fallback ─────────────────────────────────────────────────
    congress_data = smart_money_cache.read("congress.json")
    congress_trades = [
        t for t in congress_data.get("trades", [])
        if t.get("ticker", "").upper() == symbol
    ]

    ark_trades_data = smart_money_cache.read("ark_trades.json")
    ark_trades = [
        t for t in ark_trades_data.get("trades", [])
        if t.get("ticker", "").upper() == symbol
    ]

    ark_holdings_data = smart_money_cache.read("ark_holdings.json")
    ark_holdings = [
        h for h in ark_holdings_data.get("holdings", [])
        if h.get("ticker", "").upper() == symbol
    ]

    darkpool_data = smart_money_cache.read("darkpool.json")
    darkpool_anomalies = [
        d for d in darkpool_data.get("tickers", [])
        if d.get("ticker", "").upper() == symbol
    ]

    institutions_data = smart_money_cache.read("institutions.json")
    institution_holdings = [
        f for f in institutions_data.get("filings", [])
        if f.get("ticker", "").upper() == symbol
    ]

    insiders_data = smart_money_cache.read("insiders.json")
    insider_trades = [
        t for t in insiders_data.get("trades", [])
        if t.get("ticker", "").upper() == symbol
    ]

    signals_data = smart_money_cache.read("ranking_v2.json")
    if not signals_data.get("signals"):
        signals_data = smart_money_cache.read("ranking.json")
    confluence_signals = [
        s for s in signals_data.get("signals", [])
        if s.get("ticker", "").upper() == symbol
    ]

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
    if not company_name:
        for filing in institutions_data.get("filings", []):
            for h in filing.get("holdings", []):
                if h.get("ticker", "").upper() == symbol and h.get("issuer"):
                    company_name = h["issuer"]
                    break
            if company_name:
                break
    if not company_name:
        for t in insider_trades:
            if t.get("company"):
                company_name = t["company"]
                break
    if not company_name:
        for t in congress_trades:
            if t.get("company"):
                company_name = t["company"]
                break
    if not company_name:
        company_name = ticker_names.get(symbol)

    signal = confluence_signals[0] if confluence_signals else {}
    confluence_detail = {
        "signals": confluence_signals,
        "score": signal.get("score", 0),
        "direction": signal.get("direction"),
        "sources": signal.get("sources", []),
        "source_count": signal.get("source_count", 0),
        "signal_date": signal.get("signal_date"),
        "congress_score": signal.get("congress_conviction", signal.get("congress_score", 0)),
        "ark_score": signal.get("ark_conviction", signal.get("ark_score", 0)),
        "darkpool_score": signal.get("darkpool_conviction", signal.get("darkpool_score", 0)),
        "institution_score": signal.get("institution_conviction", signal.get("institution_score", 0)),
        "insider_score": signal.get("insider_conviction", signal.get("insider_score", 0)),
        "superinvestor_score": signal.get("superinvestor_conviction", signal.get("superinvestor_score", 0)),
        "short_interest_score": signal.get("short_interest_score", 0),
        "max_conviction": signal.get("max_conviction", 0),
        "multi_source_bonus": signal.get("multi_source_bonus", 0),
        "details": signal.get("details", []),
    }

    result = {
        "ticker": symbol,
        "company": company_name,
        "congress": {"trades": congress_trades, "count": len(congress_trades)},
        "ark": {
            "trades": ark_trades,
            "holdings": ark_holdings,
            "trade_count": len(ark_trades),
            "holding_etfs": len(ark_holdings),
        },
        "darkpool": {"anomalies": darkpool_anomalies, "count": len(darkpool_anomalies)},
        "institutions": {"holdings": institution_holdings, "count": len(institution_holdings)},
        "insiders": {
            "trades": insider_trades,
            "count": len(insider_trades),
            "has_cluster": any(t.get("is_cluster") for t in insider_trades),
        },
        "confluence": confluence_detail,
        "metadata": {
            "total_signals": (
                len(congress_trades) + len(ark_trades) +
                len(darkpool_anomalies) + len(institution_holdings) +
                len(insider_trades)
            ),
            "has_confluence": len(confluence_signals) > 0,
            "source": "json",
        }
    }
    if wants_markdown(request):
        return markdown_response(result, format_ticker_aggregate)
    return result

