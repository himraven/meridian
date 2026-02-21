"""
Meridian MCP Server — Model Context Protocol for Smart Money Intelligence

Exposes 10 tools for AI agents to query smart money data:
  1. get_congress_trades    — Congress trading activity (STOCK Act)
  2. get_ark_trades         — ARK Invest buy/sell activity
  3. get_ark_holdings       — Current ARK ETF holdings
  4. get_insider_trades     — SEC Form 4 insider trading data
  5. get_13f_filings        — 13F institutional holdings
  6. get_darkpool_activity  — Dark pool anomalies (FINRA)
  7. get_short_interest     — Short interest data (FINRA)
  8. get_superinvestor_activity — Superinvestor portfolio changes
  9. get_confluence_signals — Multi-source confluence signals
  10. get_market_regime     — Market regime (Green/Yellow/Red)

Transport: Streamable HTTP mounted at /mcp inside the FastAPI app.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import StreamableHTTPASGIApp
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

logger = logging.getLogger(__name__)

# ── MCP Server Instance ────────────────────────────────────────────────────
mcp = FastMCP(
    "Meridian Smart Money Intelligence",
    instructions=(
        "Meridian provides real-time smart money intelligence across US markets. "
        "Use these tools to query Congress trades, ARK Invest activity, insider trading, "
        "dark pool anomalies, institutional 13F filings, short interest, superinvestor "
        "positions, confluence signals, and market regime status. "
        "All data is sourced from SEC EDGAR, FINRA, ARK Invest, and Quiver Quantitative."
    ),
    stateless_http=True,  # Stateless for simpler mounting
)


# ── Shared Data Access ─────────────────────────────────────────────────────

def _get_cache():
    """Get smart_money_cache (lazy import to avoid circular imports)."""
    from api.shared import smart_money_cache
    return smart_money_cache


def _get_ticker_names():
    """Get ticker_names lookup (lazy import)."""
    from api.shared import ticker_names
    return ticker_names


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


def _enrich_tickers(items: list, ticker_field: str = "ticker", name_field: str = "company"):
    """Enrich items with company names, silently skip on error."""
    try:
        tn = _get_ticker_names()
        tn.enrich_list(items, ticker_field=ticker_field, name_field=name_field)
    except Exception:
        pass


def _cutoff_date(days: int) -> str:
    """Return ISO date string N days ago."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")


# ═══════════════════════════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_congress_trades(
    party: Optional[str] = None,
    chamber: Optional[str] = None,
    trade_type: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
) -> dict:
    """Get recent US Congress stock trading activity from STOCK Act disclosures.

    Tracks stock trades by members of Congress (House & Senate).
    Data sourced from mandatory STOCK Act filings via Quiver Quantitative.

    Args:
        party: Filter by political party — "Democrat" or "Republican"
        chamber: Filter by chamber — "House" or "Senate"
        trade_type: Filter by trade direction — "Purchase" or "Sale"
        days: Lookback period in days (default: 30)
        limit: Maximum number of trades to return (default: 100)

    Returns:
        Dict with "trades" list and "metadata" summary including buy/sell counts.
    """
    cache = _get_cache()

    # Try DuckDB fast path
    db = _get_duckdb()
    if db is not None:
        try:
            sql = "SELECT * FROM congress_trades WHERE 1=1"
            params = []

            if party:
                sql += " AND LOWER(party) = LOWER(?)"
                params.append(party)
            if chamber:
                sql += " AND LOWER(chamber) = LOWER(?)"
                params.append(chamber)
            if trade_type:
                norm = trade_type.lower().replace("sale", "sell")
                sql += " AND LOWER(REPLACE(trade_type, 'Sale', 'Sell')) = ?"
                params.append(norm)
            if days:
                sql += " AND transaction_date >= ?"
                params.append(_cutoff_date(days))

            sql += f" ORDER BY transaction_date DESC LIMIT {int(limit)}"
            trades = db.query(sql, params)
            _enrich_tickers(trades)

            buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
            sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

            return {
                "trades": trades,
                "metadata": {
                    "filtered": len(trades),
                    "buy_count": buy_count,
                    "sell_count": sell_count,
                    "filters": {"party": party, "chamber": chamber, "trade_type": trade_type, "days": days},
                    "source": "duckdb",
                },
            }
        except Exception as e:
            logger.debug(f"[mcp] DuckDB congress query failed: {e}")

    # JSON fallback
    data = cache.read("congress.json")
    if not data or "trades" not in data:
        return {"trades": [], "metadata": {"filtered": 0, "buy_count": 0, "sell_count": 0}}

    trades = data["trades"]
    if party:
        trades = [t for t in trades if t.get("party", "").lower() == party.lower()]
    if chamber:
        trades = [t for t in trades if t.get("chamber", "").lower() == chamber.lower()]
    if trade_type:
        norm = trade_type.lower().replace("sale", "sell")
        trades = [t for t in trades if t.get("trade_type", "").lower().replace("sale", "sell") == norm]
    if days:
        cutoff = _cutoff_date(days)
        trades = [t for t in trades if t.get("transaction_date", "9999") >= cutoff]

    trades = trades[:limit]
    _enrich_tickers(trades)

    buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
    sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

    return {
        "trades": trades,
        "metadata": {
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "filters": {"party": party, "chamber": chamber, "trade_type": trade_type, "days": days},
            "source": "json",
        },
    }


@mcp.tool()
def get_ark_trades(
    trade_type: Optional[str] = None,
    etf: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
) -> dict:
    """Get ARK Invest buy/sell trading activity across all ARK ETFs.

    ARK Invest publishes daily trade disclosures for ETFs: ARKK, ARKW, ARKG,
    ARKQ, ARKF, ARKX. Tracks Cathie Wood's high-conviction moves.

    Args:
        trade_type: Filter by direction — "Buy" or "Sell"
        etf: Filter by ETF — e.g. "ARKK", "ARKG"
        days: Lookback period in days (default: 30)
        limit: Maximum number of trades to return (default: 100)

    Returns:
        Dict with "trades" list and "metadata" summary including buy/sell counts.
    """
    cache = _get_cache()

    # DuckDB fast path
    db = _get_duckdb()
    if db is not None:
        try:
            sql = "SELECT * FROM ark_trades WHERE 1=1"
            params = []

            if trade_type:
                sql += " AND LOWER(trade_type) = LOWER(?)"
                params.append(trade_type)
            if etf:
                sql += " AND UPPER(etf) = UPPER(?)"
                params.append(etf)
            if days:
                sql += " AND date >= ?"
                params.append(_cutoff_date(days))

            sql += f" ORDER BY date DESC LIMIT {int(limit)}"
            trades = db.query(sql, params)

            buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
            sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

            return {
                "trades": trades,
                "metadata": {
                    "filtered": len(trades),
                    "buy_count": buy_count,
                    "sell_count": sell_count,
                    "filters": {"trade_type": trade_type, "etf": etf, "days": days},
                    "source": "duckdb",
                },
            }
        except Exception as e:
            logger.debug(f"[mcp] DuckDB ark_trades query failed: {e}")

    # JSON fallback
    data = cache.read("ark_trades.json")
    if not data or "trades" not in data:
        return {"trades": [], "metadata": {"filtered": 0, "buy_count": 0, "sell_count": 0}}

    trades = data["trades"]
    if trade_type:
        trades = [t for t in trades if t.get("trade_type", "").lower() == trade_type.lower()]
    if etf:
        trades = [t for t in trades if t.get("etf", "").upper() == etf.upper()]
    if days:
        cutoff = _cutoff_date(days)
        trades = [t for t in trades if t.get("date", "9999") >= cutoff]

    trades = trades[:limit]
    buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
    sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

    return {
        "trades": trades,
        "metadata": {
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "filters": {"trade_type": trade_type, "etf": etf, "days": days},
            "source": "json",
        },
    }


@mcp.tool()
def get_ark_holdings(
    etf: Optional[str] = None,
    min_weight: float = 0.0,
    limit: int = 100,
) -> dict:
    """Get current ARK ETF holdings with portfolio weights.

    Returns the latest holdings for each ARK ETF, showing position sizes
    and portfolio allocation percentages.

    Args:
        etf: Filter by ETF — e.g. "ARKK", "ARKG" (omit for all ETFs)
        min_weight: Minimum portfolio weight percentage (default: 0)
        limit: Maximum number of holdings to return (default: 100)

    Returns:
        Dict with "holdings" list and "metadata" summary.
    """
    cache = _get_cache()
    data = cache.read("ark_holdings.json")
    if not data or "holdings" not in data:
        return {"holdings": [], "metadata": {"filtered": 0}}

    holdings = data["holdings"]
    if etf:
        holdings = [h for h in holdings if h.get("etf", "").upper() == etf.upper()]
    if min_weight:
        holdings = [h for h in holdings if h.get("weight_pct", 0) >= min_weight]

    holdings = holdings[:limit]

    return {
        "holdings": holdings,
        "metadata": {
            "total": len(data.get("holdings", [])),
            "filtered": len(holdings),
            "filters": {"etf": etf, "min_weight": min_weight},
            "last_updated": data.get("last_updated"),
        },
    }


@mcp.tool()
def get_insider_trades(
    transaction_type: Optional[str] = None,
    ticker: Optional[str] = None,
    days: int = 30,
    cluster_only: bool = False,
    limit: int = 100,
) -> dict:
    """Get insider trading data from SEC Form 4 filings.

    Tracks insider buys and sells reported to the SEC. Insider cluster buys
    (multiple insiders buying the same stock) are particularly strong signals.

    Args:
        transaction_type: Filter by type — "Buy" or "Sale"
        ticker: Filter by specific stock ticker (e.g. "AAPL")
        days: Lookback period in days (default: 30)
        cluster_only: If True, only return stocks with insider cluster buying
        limit: Maximum number of trades to return (default: 100)

    Returns:
        Dict with "trades" list, "clusters" list, and "metadata" summary.
    """
    cache = _get_cache()

    # DuckDB fast path
    db = _get_duckdb()
    if db is not None:
        try:
            sql = "SELECT * FROM insider_trades WHERE 1=1"
            params = []

            if transaction_type:
                sql += " AND LOWER(transaction_type) = LOWER(?)"
                params.append(transaction_type)
            if ticker:
                sql += " AND UPPER(ticker) = ?"
                params.append(ticker.upper())
            if cluster_only:
                sql += " AND ticker IN (SELECT ticker FROM insider_clusters)"
            if days:
                sql += " AND COALESCE(trade_date, filing_date) >= ?"
                params.append(_cutoff_date(days))

            sql += f" ORDER BY COALESCE(trade_date, filing_date) DESC LIMIT {int(limit)}"
            trades = db.query(sql, params)

            cluster_sql = "SELECT * FROM insider_clusters"
            cluster_params = []
            if ticker:
                cluster_sql += " WHERE UPPER(ticker) = ?"
                cluster_params.append(ticker.upper())
            clusters = db.query(cluster_sql, cluster_params if cluster_params else None)

            _enrich_tickers(trades)
            buy_count = sum(1 for t in trades if t.get("transaction_type") == "Buy")
            sell_count = sum(1 for t in trades if t.get("transaction_type") == "Sale")

            return {
                "trades": trades,
                "clusters": clusters,
                "metadata": {
                    "filtered": len(trades),
                    "buy_count": buy_count,
                    "sell_count": sell_count,
                    "cluster_count": len(clusters),
                    "filters": {
                        "transaction_type": transaction_type,
                        "ticker": ticker,
                        "days": days,
                        "cluster_only": cluster_only,
                    },
                    "source": "duckdb",
                },
            }
        except Exception as e:
            logger.debug(f"[mcp] DuckDB insider query failed: {e}")

    # JSON fallback
    data = cache.read("insiders.json")
    if not data or "trades" not in data:
        return {"trades": [], "clusters": [], "metadata": {"filtered": 0, "buy_count": 0, "sell_count": 0, "cluster_count": 0}}

    trades = data["trades"]
    clusters = data.get("clusters", [])

    if transaction_type:
        trades = [t for t in trades if t.get("transaction_type", "").lower() == transaction_type.lower()]
    if ticker:
        tu = ticker.upper()
        trades = [t for t in trades if t.get("ticker", "").upper() == tu]
        clusters = [c for c in clusters if c.get("ticker", "").upper() == tu]
    if cluster_only:
        cluster_tickers = {c.get("ticker", "").upper() for c in data.get("clusters", [])}
        trades = [t for t in trades if t.get("ticker", "").upper() in cluster_tickers]
    if days:
        cutoff = _cutoff_date(days)
        trades = [t for t in trades if (t.get("trade_date") or t.get("filing_date", "9999")) >= cutoff]

    trades = trades[:limit]
    _enrich_tickers(trades)
    buy_count = sum(1 for t in trades if t.get("transaction_type") == "Buy")
    sell_count = sum(1 for t in trades if t.get("transaction_type") == "Sale")

    return {
        "trades": trades,
        "clusters": clusters,
        "metadata": {
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "cluster_count": len(clusters),
            "filters": {
                "transaction_type": transaction_type,
                "ticker": ticker,
                "days": days,
                "cluster_only": cluster_only,
            },
            "source": "json",
        },
    }


@mcp.tool()
def get_13f_filings(
    fund: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Get 13F institutional holdings from top hedge funds and asset managers.

    13F filings are mandatory quarterly disclosures by institutional investors
    managing >$100M. Tracks: Berkshire Hathaway, Bridgewater, Renaissance Tech,
    Citadel, Pershing Square, Soros Fund, Appaloosa, and others.

    Args:
        fund: Filter by fund name (partial match, e.g. "berkshire")
        limit: Maximum number of top holdings to return per fund (default: 50)

    Returns:
        Dict with "filings" (fund summaries) and "top_holdings" (flattened positions).
    """
    cache = _get_cache()

    # DuckDB fast path
    db = _get_duckdb()
    if db is not None:
        try:
            filing_sql = "SELECT cik, fund_name, company_name, filing_date, quarter, total_value, holdings_count FROM institution_filings WHERE 1=1"
            filing_params = []
            if fund:
                filing_sql += " AND LOWER(fund_name) LIKE ?"
                filing_params.append(f"%{fund.lower()}%")
            filings = db.query(filing_sql, filing_params if filing_params else None)

            holding_sql = """
                SELECT ticker, issuer, fund_name AS institution, cik,
                       shares, value, pct_portfolio, cusip, filing_date, quarter
                FROM institution_holdings
                WHERE ticker IS NOT NULL AND ticker != ''
            """
            hold_params = []
            if fund:
                holding_sql += " AND LOWER(fund_name) LIKE ?"
                hold_params.append(f"%{fund.lower()}%")
            holding_sql += f" ORDER BY value DESC LIMIT {int(limit)}"
            top_holdings = db.query(holding_sql, hold_params if hold_params else None)

            return {
                "filings": filings,
                "top_holdings": top_holdings,
                "metadata": {
                    "filings_count": len(filings),
                    "holdings_returned": len(top_holdings),
                    "filters": {"fund": fund},
                    "source": "duckdb",
                },
            }
        except Exception as e:
            logger.debug(f"[mcp] DuckDB 13f query failed: {e}")

    # JSON fallback
    data = cache.read("institutions.json")
    if not data or "filings" not in data:
        return {"filings": [], "top_holdings": [], "metadata": {"filings_count": 0, "holdings_returned": 0}}

    filings = data["filings"]
    if fund:
        filings = [f for f in filings if fund.lower() in f.get("fund_name", "").lower()]

    # Flatten holdings
    flattened = []
    for filing in filings:
        fund_name = filing.get("fund_name", "Unknown")
        filing_date = filing.get("filing_date", "")
        quarter = filing.get("quarter", "")
        fund_total = filing.get("total_value", 1) or 1

        for h in filing.get("holdings", []):
            tk = h.get("ticker", "").strip()
            if not tk:
                continue
            val = h.get("value", 0)
            flattened.append({
                "ticker": tk,
                "issuer": h.get("issuer", ""),
                "institution": fund_name,
                "cik": filing.get("cik", ""),
                "shares": h.get("shares", 0),
                "value": val,
                "pct_portfolio": (val / fund_total * 100) if fund_total else 0,
                "filing_date": filing_date,
                "quarter": quarter,
            })

    flattened.sort(key=lambda x: x.get("value", 0), reverse=True)
    top_holdings = flattened[:limit]

    filings_summary = [
        {
            "cik": f.get("cik", ""),
            "fund_name": f.get("fund_name", ""),
            "filing_date": f.get("filing_date", ""),
            "quarter": f.get("quarter", ""),
            "total_value": f.get("total_value", 0),
            "holdings_count": f.get("holdings_count", len(f.get("holdings", []))),
        }
        for f in filings
    ]

    return {
        "filings": filings_summary,
        "top_holdings": top_holdings,
        "metadata": {
            "filings_count": len(filings_summary),
            "holdings_returned": len(top_holdings),
            "filters": {"fund": fund},
            "source": "json",
        },
    }


@mcp.tool()
def get_darkpool_activity(
    min_zscore: float = 2.0,
    min_dpi: float = 0.4,
    days: int = 7,
    limit: int = 100,
) -> dict:
    """Get dark pool trading anomalies detected by statistical analysis.

    Monitors FINRA off-exchange (dark pool) volume for unusual activity.
    High Z-scores indicate volume significantly above historical norms.
    High DPI (Dark Pool Index) means large share of total volume is off-exchange.

    Args:
        min_zscore: Minimum Z-score threshold (default: 2.0 = 95th percentile)
        min_dpi: Minimum Dark Pool Index (default: 0.4 = 40% off-exchange)
        days: Lookback period in days (default: 7)
        limit: Maximum number of anomalies to return (default: 100)

    Returns:
        Dict with "anomalies" list and "metadata" summary.
    """
    cache = _get_cache()

    # DuckDB fast path
    db = _get_duckdb()
    if db is not None:
        try:
            sql = "SELECT * FROM darkpool_tickers WHERE z_score >= ? AND dpi >= ?"
            params = [min_zscore, min_dpi]
            if days:
                sql += " AND date >= ?"
                params.append(_cutoff_date(days))
            sql += f" ORDER BY z_score DESC LIMIT {int(limit)}"
            filtered = db.query(sql, params)
            _enrich_tickers(filtered)

            return {
                "anomalies": filtered,
                "metadata": {
                    "filtered": len(filtered),
                    "filters": {"min_zscore": min_zscore, "min_dpi": min_dpi, "days": days},
                    "source": "duckdb",
                },
            }
        except Exception as e:
            logger.debug(f"[mcp] DuckDB darkpool query failed: {e}")

    # JSON fallback
    data = cache.read("darkpool.json")
    if not data or "tickers" not in data:
        return {"anomalies": [], "metadata": {"filtered": 0}}

    tickers = data["tickers"]
    filtered = [t for t in tickers if t.get("z_score", 0) >= min_zscore]
    filtered = [t for t in filtered if t.get("dpi", 0) >= min_dpi]
    if days:
        cutoff = _cutoff_date(days)
        filtered = [t for t in filtered if t.get("date", "9999") >= cutoff]

    filtered = filtered[:limit]
    _enrich_tickers(filtered)

    return {
        "anomalies": filtered,
        "metadata": {
            "filtered": len(filtered),
            "filters": {"min_zscore": min_zscore, "min_dpi": min_dpi, "days": days},
            "source": "json",
        },
    }


@mcp.tool()
def get_short_interest(
    ticker: Optional[str] = None,
    min_short_ratio: Optional[float] = None,
    sort_by: str = "short_interest",
    limit: int = 50,
) -> dict:
    """Get short interest data from FINRA covering 8,600+ tickers.

    Shows shares sold short, short interest as % of float, days to cover,
    and changes between settlement dates. High short interest can indicate
    bearish sentiment or potential short squeeze setups.

    Args:
        ticker: Filter by specific ticker (e.g. "GME")
        min_short_ratio: Minimum short interest as % of float (e.g. 20.0)
        sort_by: Sort field — "short_interest", "short_ratio", "days_to_cover"
        limit: Maximum results to return (default: 50)

    Returns:
        Dict with "tickers" list and "metadata" summary.
    """
    cache = _get_cache()
    sort_col_map = {
        "short_ratio": "short_pct_float",
        "days_to_cover": "days_to_cover",
        "short_volume": "short_interest",
        "short_interest": "short_interest",
    }
    sort_col = sort_col_map.get(sort_by, "short_interest")

    # DuckDB fast path
    db = _get_duckdb()
    if db is not None and db.table_exists("short_interest"):
        try:
            sql = "SELECT * FROM short_interest WHERE 1=1"
            params = []
            if ticker:
                sql += " AND UPPER(ticker) = ?"
                params.append(ticker.upper())
            if min_short_ratio is not None:
                sql += " AND short_pct_float >= ?"
                params.append(min_short_ratio)
            sql += f" ORDER BY {sort_col} DESC NULLS LAST LIMIT {int(limit)}"
            rows = db.query(sql, params)
            _enrich_tickers(rows)

            return {
                "tickers": rows,
                "metadata": {
                    "filtered": len(rows),
                    "filters": {"ticker": ticker, "min_short_ratio": min_short_ratio, "sort_by": sort_by},
                    "source": "duckdb",
                },
            }
        except Exception as e:
            logger.debug(f"[mcp] DuckDB short_interest query failed: {e}")

    # JSON fallback
    from api.shared import DATA_DIR
    raw = {}
    try:
        import json as _json
        path = os.path.join(str(DATA_DIR), "short_interest.json")
        with open(path, "r") as f:
            raw = _json.load(f)
    except Exception:
        pass
    if not raw:
        raw = cache.read("short_interest.json")

    tickers_list = raw.get("tickers", [])

    if ticker:
        tickers_list = [r for r in tickers_list if r.get("ticker", "").upper() == ticker.upper()]
    if min_short_ratio is not None:
        tickers_list = [r for r in tickers_list if (r.get("short_pct_float") or 0) >= min_short_ratio]

    reverse_key = sort_col_map.get(sort_by, "short_interest")
    tickers_list = sorted(tickers_list, key=lambda r: r.get(reverse_key) or 0, reverse=True)

    filtered = tickers_list[:limit]
    _enrich_tickers(filtered)

    return {
        "tickers": filtered,
        "metadata": {
            "filtered": len(filtered),
            "filters": {"ticker": ticker, "min_short_ratio": min_short_ratio, "sort_by": sort_by},
            "settlement_date": raw.get("metadata", {}).get("settlement_date"),
            "source": "json",
        },
    }


@mcp.tool()
def get_superinvestor_activity(
    manager: Optional[str] = None,
    ticker: Optional[str] = None,
    activity_type: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """Get superinvestor portfolio changes from 13F filings (via Dataroma).

    Tracks ~80 legendary investors including Warren Buffett, George Soros,
    Bill Ackman, Carl Icahn, David Tepper, and others. Shows their latest
    buys, sells, position increases, and reductions.

    Args:
        manager: Filter by manager name (partial match, e.g. "buffett")
        ticker: Filter by specific ticker
        activity_type: Filter by action — "Buy", "Sell", "Add", or "Reduce"
        limit: Maximum results to return (default: 100)

    Returns:
        Dict with "activity" list and "metadata" summary.
    """
    cache = _get_cache()
    data = cache.read("superinvestors.json")
    if not data or "activity" not in data:
        return {"activity": [], "metadata": {"filtered": 0, "buy_count": 0, "sell_count": 0}}

    activity = data["activity"]

    if activity_type:
        activity = [a for a in activity if a.get("activity_type", "").lower() == activity_type.lower()]
    if ticker:
        tu = ticker.upper()
        activity = [a for a in activity if a.get("ticker", "").upper() == tu]
    if manager:
        ml = manager.lower()
        activity = [a for a in activity if ml in (a.get("manager") or "").lower()]

    activity = activity[:limit]
    _enrich_tickers(activity)

    buy_count = sum(1 for a in activity if a.get("activity_type") in ("Buy", "Add"))
    sell_count = sum(1 for a in activity if a.get("activity_type") in ("Sell", "Reduce"))

    return {
        "activity": activity,
        "metadata": {
            "filtered": len(activity),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "managers_tracked": data.get("metadata", {}).get("manager_count", 0),
            "filters": {"manager": manager, "ticker": ticker, "activity_type": activity_type},
            "source": "dataroma",
            "last_updated": data.get("metadata", {}).get("last_updated"),
        },
    }


@mcp.tool()
def get_confluence_signals(
    min_score: float = 6.0,
    sources: Optional[str] = None,
    days: int = 7,
    limit: int = 100,
) -> dict:
    """Get multi-source confluence signals showing smart money consensus.

    The confluence engine scores each stock by how many independent smart money
    sources agree: Congress trades, ARK Invest, dark pool anomalies, institutional
    13F positions, insider buying, and superinvestor activity. Higher scores
    indicate stronger multi-source agreement.

    Scoring (V3 engine, 0-100 scale):
    - Each source scored by signal strength (conviction × recency × size)
    - Multi-source bonus: +20 per additional source (max +40)
    - Direction-aware: separates bullish vs bearish signals

    Args:
        min_score: Minimum confluence score (default: 6.0)
        sources: Comma-separated source filter (e.g. "congress,ark,darkpool")
        days: Only include signals with activity in last N days (default: 7)
        limit: Maximum signals to return (default: 100)

    Returns:
        Dict with "signals" list (sorted by score desc) and "metadata".
    """
    cache = _get_cache()

    # Try V3 → V2 → V1
    data = cache.read("ranking_v3.json")
    if not data or "signals" not in data:
        data = cache.read("ranking_v2.json")
    if not data or "signals" not in data:
        data = cache.read("ranking.json")
    if not data or "signals" not in data:
        return {"signals": [], "metadata": {"total": 0, "filtered": 0}}

    signals = data["signals"]

    # Filter by min_score
    filtered = [s for s in signals if s.get("score", 0) >= min_score]

    # Filter by sources
    if sources:
        source_list = [s.strip().lower() for s in sources.split(",")]
        filtered = [
            s for s in filtered
            if any(src in [d.get("source") for d in s.get("details", [])] for src in source_list)
            or any(src in s.get("sources", []) for src in source_list)
        ]

    # Filter by days
    if days:
        cutoff = _cutoff_date(days)
        filtered = [s for s in filtered if s.get("signal_date", "9999") >= cutoff]

    _enrich_tickers(filtered)
    total_filtered = len(filtered)
    filtered = filtered[:limit]

    return {
        "signals": filtered,
        "metadata": {
            "total": len(signals),
            "filtered": total_filtered,
            "returned": len(filtered),
            "filters": {"min_score": min_score, "sources": sources, "days": days},
            "engine": data.get("metadata", {}).get("engine", "v3"),
            "last_updated": data.get("metadata", {}).get("last_updated"),
        },
    }


@mcp.tool()
def get_market_regime() -> dict:
    """Get current market regime assessment: Green (risk-on), Yellow (caution), or Red (defensive).

    Combines three independent indicators:
    1. VIX (fear index): <20 green, 20-30 yellow, >30 red
    2. SPY vs 200-day MA: above = bullish, below = bearish
    3. Credit spreads (ICE BofA HY OAS): <4% green, 4-6% yellow, >6% red

    Data sourced from Yahoo Finance (VIX, SPY) and FRED (credit spreads).
    Results are cached for 1 hour to avoid excessive API calls.

    Returns:
        Dict with "regime" (green/yellow/red), "summary" text, and
        detailed "components" breakdown for each indicator.
    """
    try:
        from api.routers.macro import _get_regime_data
        return _get_regime_data()
    except Exception as e:
        logger.error(f"[mcp] Market regime fetch failed: {e}")
        return {
            "regime": "unknown",
            "summary": "Unable to fetch market regime data",
            "error": str(e),
            "components": {},
        }


# ═══════════════════════════════════════════════════════════════════════════
# MOUNTING
# ═══════════════════════════════════════════════════════════════════════════


def mount_mcp(app):
    """
    Mount the MCP server into a FastAPI application at /mcp.

    Handles the known issue with FastAPI + MCP streamable HTTP by:
    1. Creating a fresh session manager each time
    2. Adding the StreamableHTTPASGIApp as a direct route
    3. Wrapping the existing lifespan to include session_manager.run()

    The session manager is created fresh on each call so the same
    FastMCP instance can be remounted (important for testing).

    Args:
        app: FastAPI application instance
    """
    from contextlib import asynccontextmanager
    from starlette.routing import Route

    # Always create a fresh session manager (MCP SDK requires a new instance
    # each time since .run() can only be called once per instance)
    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        json_response=mcp.settings.json_response,
        stateless=mcp.settings.stateless_http,
    )
    mcp._session_manager = session_manager
    http_handler = StreamableHTTPASGIApp(session_manager)

    # ── Wrap the existing lifespan to include MCP session manager ──────
    # FastAPI's existing lifespan (from on_event or lifespan parameter)
    # is stored in app.router.lifespan_context.
    existing_lifespan = getattr(app.router, "lifespan_context", None)

    @asynccontextmanager
    async def mcp_lifespan(app_instance):
        async with session_manager.run():
            logger.info("[mcp] Session manager started")
            if existing_lifespan is not None:
                async with existing_lifespan(app_instance) as state:
                    yield state
            else:
                yield
        logger.info("[mcp] Session manager stopped")

    app.router.lifespan_context = mcp_lifespan

    # ── Add MCP route ─────────────────────────────────────────────────
    # Remove any existing /mcp route first (idempotent remounting)
    app.router.routes = [r for r in app.router.routes if not (hasattr(r, "path") and r.path == "/mcp")]
    # Insert at position 0 so it takes priority over catch-all routes.
    # StreamableHTTPASGIApp is a class (ASGI app), so Starlette passes all
    # methods through to it. No methods= filter needed.
    app.router.routes.insert(0, Route("/mcp", endpoint=http_handler))

    logger.info("[mcp] MCP server mounted at /mcp (Streamable HTTP, stateless)")
