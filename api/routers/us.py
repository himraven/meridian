"""
US market routes - ARK, 13F, Congress, Dark Pool, Institutions
"""
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.shared import (
    ARK_DATA_DIR, DATA_DIR, read_json, read_jsonl, file_mtime,
    wants_markdown, markdown_response, smart_money_cache, ticker_names
)
from api.markdown_format import MARKDOWN_FORMATTERS

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_duckdb():
    """Get DuckDB store, or None if not available."""
    try:
        from api.modules.duckdb_store import get_store
        store = get_store()
        # Check DB is initialized (file exists and has been populated)
        if store._initialized or store.table_exists("congress_trades"):
            return store
        return None
    except Exception:
        return None

# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/us/ark")
def api_us_ark():
    """Latest ARK trades and current holdings — enhanced with timing data."""
    all_changes = _load_ark_changes()
    all_holdings_raw = _load_all_holdings()

    # Per-ETF holdings (top 30 each)
    holdings = {}
    for etf, data in all_holdings_raw.items():
        holdings[etf] = data.get("holdings", [])[:30]

    trends = read_json(os.path.join(ARK_DATA_DIR, "trend_cache.json")) or {}

    # Enhance changes with trade date and direction info
    enhanced_changes = []
    for c in all_changes:
        ec = dict(c)
        ts = c.get("timestamp", "")
        ec["trade_date"] = ts[:10] if ts else None
        ctype = c.get("type", "")
        if ctype in ("NEW_POSITION", "INCREASED"):
            ec["direction"] = "buy"
        elif ctype in ("DECREASED", "SOLD_OUT"):
            ec["direction"] = "sell"
        else:
            ec["direction"] = "unknown"
        enhanced_changes.append(ec)

    # Cross-ETF summary for holding duration ranking
    cross_etf = _build_cross_etf_summary(all_holdings_raw, all_changes)

    # Top traded tickers (most trade actions)
    top_traded = sorted(
        [x for x in cross_etf if x["trade_count"] > 0],
        key=lambda x: x["trade_count"],
        reverse=True,
    )[:15]

    return {
        "changes": enhanced_changes,
        "holdings": holdings,
        "trends": trends,
        "cross_etf_summary": cross_etf[:50],
        "top_traded": top_traded,
        "updated_at": file_mtime(os.path.join(ARK_DATA_DIR, "ark_changes.jsonl")),
    }

@router.get("/api/us/ark/timeline/{ticker}")
def api_us_ark_timeline(ticker: str):
    """All ARK trades for a specific ticker across all ETFs."""
    ticker = ticker.upper()
    all_changes = _load_ark_changes()
    all_holdings_raw = _load_all_holdings()

    # Filter changes for this ticker
    trades = []
    for c in all_changes:
        if (c.get("ticker") or "").upper() == ticker:
            trades.append({
                "date": c.get("timestamp", "")[:10],
                "etf": c.get("etf"),
                "type": c.get("type"),
                "direction": "buy" if c.get("type") in ("NEW_POSITION", "INCREASED") else "sell",
                "prev_shares": c.get("prev_shares"),
                "curr_shares": c.get("curr_shares") or c.get("shares"),
                "change_pct": c.get("change_pct"),
                "weight": c.get("weight"),
                "company": c.get("company"),
            })

    # Current holdings for this ticker
    current = []
    for etf, data in all_holdings_raw.items():
        for h in data.get("holdings", []):
            if (h.get("ticker") or "").upper() == ticker:
                current.append({
                    "etf": etf,
                    "shares": h.get("shares"),
                    "weight": h.get("weight"),
                    "market_value": h.get("market_value"),
                    "date": h.get("date") or data.get("date"),
                })

    # Compute first seen and holding days
    first_seen = None
    for t in trades:
        d = t.get("date")
        if d and (not first_seen or d < first_seen):
            first_seen = d
    for c in current:
        d = c.get("date")
        if d and (not first_seen or d < first_seen):
            first_seen = d

    holding_days = 0
    if first_seen:
        try:
            first = datetime.strptime(first_seen, "%Y-%m-%d")
            today = datetime.strptime(datetime.now(timezone.utc).strftime("%Y-%m-%d"), "%Y-%m-%d")
            holding_days = (today - first).days
        except Exception:
            pass

    return {
        "ticker": ticker,
        "trades": sorted(trades, key=lambda x: x.get("date", ""), reverse=True),
        "current_holdings": current,
        "first_seen": first_seen,
        "holding_days": holding_days,
        "total_etfs": len(current),
    }

@router.get("/api/us/13f")
def api_us_13f():
    """13F filings summary — enhanced with quarter info and comparisons."""
    filings_dir = os.path.join(ARK_DATA_DIR, "13f_filings")
    results = []
    if os.path.isdir(filings_dir):
        for fname in os.listdir(filings_dir):
            if fname.endswith("_latest.json"):
                cik = fname.replace("_latest.json", "")
                data = read_json(os.path.join(filings_dir, fname))
                if not data:
                    continue
                all_holdings = data.get("holdings", [])
                # Aggregate duplicate issuers (same company may have multiple
                # sub-portfolio entries in 13F, e.g. Berkshire has 12 APPLE entries)
                from collections import defaultdict
                agg = defaultdict(lambda: {"issuer": "", "class": "", "cusip": "", "value": 0, "shares": 0, "put_call": ""})
                for h in all_holdings:
                    key = (h.get("issuer", ""), h.get("class", ""), h.get("put_call", ""))
                    agg[key]["issuer"] = h.get("issuer", "")
                    agg[key]["class"] = h.get("class", "")
                    agg[key]["cusip"] = h.get("cusip", "")
                    agg[key]["put_call"] = h.get("put_call", "")
                    agg[key]["value"] += h.get("value", 0)
                    agg[key]["shares"] += h.get("shares", 0)
                all_holdings_agg = list(agg.values())
                holdings = sorted(
                    all_holdings_agg,
                    key=lambda x: x.get("value", 0),
                    reverse=True,
                )[:15]
                # Determine quarter reported from filing date
                filing_date = data.get("filing_date", "")
                quarter = ""
                if filing_date:
                    try:
                        fd = datetime.strptime(filing_date, "%Y-%m-%d")
                        # 13F filed ~45 days after quarter end
                        # Filing in Feb = Q4 prev year, May = Q1, Aug = Q2, Nov = Q3
                        month = fd.month
                        year = fd.year
                        if month <= 2:
                            quarter = f"Q4 {year - 1}"
                        elif month <= 5:
                            quarter = f"Q1 {year}"
                        elif month <= 8:
                            quarter = f"Q2 {year}"
                        else:
                            quarter = f"Q3 {year}"
                    except Exception:
                        pass
                # Total portfolio value (13F values are in $1000s, convert to dollars)
                total_value = sum(h.get("value", 0) for h in all_holdings_agg) // 1000
                # Convert individual holding values too
                for h in holdings:
                    if "value" in h:
                        h["value"] = h["value"] // 1000
                # Count puts/calls
                puts = sum(1 for h in all_holdings_agg if h.get("put_call") == "PUT")
                calls = sum(1 for h in all_holdings_agg if h.get("put_call") == "CALL")
                results.append({
                    "cik": data.get("cik"),
                    "company": data.get("company"),
                    "filing_date": filing_date,
                    "form": data.get("form"),
                    "quarter": quarter,
                    "total_holdings": len(all_holdings_agg),
                    "total_value": total_value,
                    "puts_count": puts,
                    "calls_count": calls,
                    "top_holdings": holdings,
                })
    results.sort(key=lambda x: x.get("company", ""))
    return {"filings": results, "updated_at": file_mtime(filings_dir) if os.path.isdir(filings_dir) else None}

@router.get("/api/us/alpha-research")
def api_us_alpha_research():
    """US Quiver alpha research results."""
    report_path = "/home/raven/clawd/projects/quant-engine/us-signals/quiver-alpha-research/results/alpha_research_report.json"
    data = read_json(report_path)
    if not data:
        return {"status": "pending", "message": "Research in progress..."}
    return {"status": "ready", **data}

@router.get("/api/us/insiders")
def api_us_insiders(
    request: Request,
    transaction_type: str = None,  # Buy, Sale
    ticker: str = None,
    min_value: float = None,
    cluster_only: bool = False,
    days: int = 30,
):
    """
    Get insider trading data from SEC Form 4 filings.
    Uses DuckDB query layer with JSON fallback.
    """
    # ── DuckDB fast path ──────────────────────────────────────────────
    db = _get_duckdb()
    if db is not None:
        try:
            # Build trades query
            trade_sql = "SELECT * FROM insider_trades WHERE 1=1"
            trade_params = []

            if transaction_type:
                trade_sql += " AND LOWER(transaction_type) = LOWER(?)"
                trade_params.append(transaction_type)
            if ticker:
                trade_sql += " AND UPPER(ticker) = ?"
                trade_params.append(ticker.upper())
            if min_value is not None:
                trade_sql += " AND value >= ?"
                trade_params.append(min_value)
            if cluster_only:
                trade_sql += " AND ticker IN (SELECT ticker FROM insider_clusters)"
            if days:
                cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
                trade_sql += " AND COALESCE(trade_date, filing_date) >= ?"
                trade_params.append(cutoff)

            trade_sql += " ORDER BY COALESCE(trade_date, filing_date) DESC"
            trades = db.query(trade_sql, trade_params)
            total = db.query("SELECT COUNT(*) AS cnt FROM insider_trades")[0]["cnt"]

            # Clusters
            cluster_sql = "SELECT * FROM insider_clusters"
            cluster_params = []
            if ticker:
                cluster_sql += " WHERE UPPER(ticker) = ?"
                cluster_params.append(ticker.upper())
            clusters = db.query(cluster_sql, cluster_params if ticker else None)

            ticker_names.enrich_list(trades, ticker_field="ticker", name_field="company")
            buy_count = sum(1 for t in trades if t.get("transaction_type") == "Buy")
            sell_count = sum(1 for t in trades if t.get("transaction_type") == "Sale")

            return {
                "data": trades,
                "clusters": clusters,
                "metadata": {
                    "total": total,
                    "filtered": len(trades),
                    "buy_count": buy_count,
                    "sell_count": sell_count,
                    "cluster_count": len(clusters),
                    "filters": {
                        "transaction_type": transaction_type, "ticker": ticker,
                        "min_value": min_value, "cluster_only": cluster_only, "days": days,
                    },
                    "source": "duckdb",
                }
            }

        except Exception as e:
            logger.warning(f"[duckdb] insider_trades query failed, falling back to JSON: {e}")

    # ── JSON fallback ─────────────────────────────────────────────────
    data = smart_money_cache.read("insiders.json")
    if not data or "trades" not in data:
        return {"data": [], "clusters": [], "metadata": {"total": 0, "filtered": 0}}

    trades = data["trades"]
    clusters = data.get("clusters", [])

    if transaction_type:
        trades = [t for t in trades if t.get("transaction_type", "").lower() == transaction_type.lower()]
    if ticker:
        ticker_upper = ticker.upper()
        trades = [t for t in trades if t.get("ticker", "").upper() == ticker_upper]
        clusters = [c for c in clusters if c.get("ticker", "").upper() == ticker_upper]
    if min_value is not None:
        trades = [t for t in trades if t.get("value", 0) >= min_value]
    if cluster_only:
        cluster_tickers = set(c.get("ticker", "").upper() for c in data.get("clusters", []))
        cluster_tickers.update(data.get("metadata", {}).get("cluster_tickers", []))
        trades = [t for t in trades if t.get("ticker", "").upper() in cluster_tickers]
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = [
            t for t in trades
            if (t.get("trade_date") or t.get("filing_date", "9999")) >= cutoff
        ]

    ticker_names.enrich_list(trades, ticker_field="ticker", name_field="company")
    buy_count = sum(1 for t in trades if t.get("transaction_type") == "Buy")
    sell_count = sum(1 for t in trades if t.get("transaction_type") == "Sale")

    return {
        "data": trades,
        "clusters": clusters,
        "metadata": {
            "total": len(data.get("trades", [])),
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "cluster_count": len(clusters),
            "filters": {
                "transaction_type": transaction_type, "ticker": ticker,
                "min_value": min_value, "cluster_only": cluster_only, "days": days,
            },
            "source": data.get("metadata", {}).get("source", "openinsider"),
            "last_updated": data.get("metadata", {}).get("last_updated"),
        }
    }


@router.get("/api/us/superinvestors")
def api_us_superinvestors(
    request: Request,
    manager: str = None,
    ticker: str = None,
    activity_type: str = None,  # Buy, Sell, Add, Reduce
    min_managers: int = None,   # minimum manager count (aggregate)
    source_type: str = None,    # aggregate, per_manager
):
    """
    Get superinvestor portfolio activity from Dataroma (13F filings).
    
    Tracks ~80 legendary investors (Buffett, Soros, Ackman, Icahn, etc.)
    
    Query params:
      - manager: filter by manager name (partial match)
      - ticker: filter by specific ticker
      - activity_type: Buy, Sell, Add, or Reduce
      - min_managers: only show stocks with N+ managers buying/selling (aggregate only)
      - source_type: 'aggregate' (cross-manager) or 'per_manager' (individual)
    """
    data = smart_money_cache.read("superinvestors.json")
    if not data or "activity" not in data:
        return {"data": [], "holdings": {}, "metadata": {"total": 0, "filtered": 0}}
    
    activity = data["activity"]
    holdings = data.get("holdings", {})
    
    # Filter by source_type
    if source_type:
        activity = [a for a in activity if a.get("source", "") == source_type]
    
    # Filter by activity_type
    if activity_type:
        activity = [
            a for a in activity
            if a.get("activity_type", "").lower() == activity_type.lower()
        ]
    
    # Filter by ticker
    if ticker:
        ticker_upper = ticker.upper()
        activity = [a for a in activity if a.get("ticker", "").upper() == ticker_upper]
        # Also filter holdings to show only relevant managers
        filtered_holdings = {}
        for code, h in holdings.items():
            for th in h.get("top_holdings", []):
                if th.get("ticker", "").upper() == ticker_upper:
                    filtered_holdings[code] = h
                    break
        holdings = filtered_holdings
    
    # Filter by manager (partial match on manager name)
    if manager:
        manager_lower = manager.lower()
        activity = [
            a for a in activity
            if manager_lower in (a.get("manager") or "").lower()
        ]
    
    # Filter by min_managers (aggregate entries only)
    if min_managers is not None:
        activity = [
            a for a in activity
            if a.get("manager_count", 0) >= min_managers or a.get("source") != "aggregate"
        ]
    
    # Enrich with company names
    ticker_names.enrich_list(activity, ticker_field="ticker", name_field="company")
    
    # Stats
    buy_count = sum(1 for a in activity if a.get("activity_type") in ("Buy", "Add"))
    sell_count = sum(1 for a in activity if a.get("activity_type") in ("Sell", "Reduce"))
    
    return {
        "data": activity,
        "holdings": holdings,
        "metadata": {
            "total": len(data.get("activity", [])),
            "filtered": len(activity),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "managers_tracked": data.get("metadata", {}).get("manager_count", 0),
            "holdings_scraped": len(data.get("holdings", {})),
            "filters": {
                "manager": manager,
                "ticker": ticker,
                "activity_type": activity_type,
                "min_managers": min_managers,
                "source_type": source_type,
            },
            "source": "dataroma",
            "last_updated": data.get("metadata", {}).get("last_updated"),
        }
    }


@router.get("/api/us/short-interest")
def api_us_short_interest(
    ticker: str = None,
    min_short_ratio: float = None,
    min_days_to_cover: float = None,
    sort_by: str = "short_interest",   # short_ratio | days_to_cover | short_volume
    limit: int = 100,
):
    """
    Short interest data from FINRA (8,600+ tickers).
    DuckDB fast path with JSON fallback.
    """
    # normalise sort_by alias
    sort_col_map = {
        "short_ratio": "short_pct_float",
        "days_to_cover": "days_to_cover",
        "short_volume": "short_interest",
        "short_interest": "short_interest",
        "change_pct": "change_pct",
    }
    sort_col = sort_col_map.get(sort_by, "short_interest")

    # ── DuckDB fast path ──────────────────────────────────────────────
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
            if min_days_to_cover is not None:
                sql += " AND days_to_cover >= ?"
                params.append(min_days_to_cover)

            total_sql = "SELECT COUNT(*) AS cnt FROM short_interest"
            total = db.query(total_sql)[0]["cnt"]

            # Count with filters applied (before LIMIT) for accurate pagination
            filtered_sql = sql.replace("SELECT *", "SELECT COUNT(*) AS cnt")
            filtered_count = db.query(filtered_sql, params)[0]["cnt"]

            sql += f" ORDER BY {sort_col} DESC NULLS LAST LIMIT ?"
            params.append(limit)

            rows = db.query(sql, params)
            ticker_names.enrich_list(rows, ticker_field="ticker", name_field="company")

            return {
                "data": rows,
                "metadata": {
                    "total": total,
                    "filtered": filtered_count,
                    "sort_by": sort_by,
                    "filters": {
                        "ticker": ticker,
                        "min_short_ratio": min_short_ratio,
                        "min_days_to_cover": min_days_to_cover,
                    },
                    "source": "duckdb",
                },
            }
        except Exception as e:
            logger.warning(f"[duckdb] short_interest query failed, falling back to JSON: {e}")

    # ── JSON fallback ─────────────────────────────────────────────────
    raw = read_json(os.path.join(DATA_DIR, "short_interest.json")) or {}
    tickers_list: list = raw.get("tickers", [])
    meta = raw.get("metadata", {})

    if ticker:
        tickers_list = [r for r in tickers_list if r.get("ticker", "").upper() == ticker.upper()]
    if min_short_ratio is not None:
        tickers_list = [r for r in tickers_list if (r.get("short_pct_float") or 0) >= min_short_ratio]
    if min_days_to_cover is not None:
        tickers_list = [r for r in tickers_list if (r.get("days_to_cover") or 0) >= min_days_to_cover]

    # sort
    reverse_key = {
        "short_ratio": "short_pct_float",
        "days_to_cover": "days_to_cover",
        "short_volume": "short_interest",
        "short_interest": "short_interest",
    }.get(sort_by, "short_interest")
    tickers_list = sorted(tickers_list, key=lambda r: r.get(reverse_key) or 0, reverse=True)

    total_all = len(raw.get("tickers", []))
    filtered = tickers_list[:limit]
    ticker_names.enrich_list(filtered, ticker_field="ticker", name_field="company")

    return {
        "data": filtered,
        "metadata": {
            "total": total_all,
            "filtered": len(filtered),
            "sort_by": sort_by,
            "filters": {
                "ticker": ticker,
                "min_short_ratio": min_short_ratio,
                "min_days_to_cover": min_days_to_cover,
            },
            "settlement_date": meta.get("settlement_date"),
            "last_updated": meta.get("last_updated"),
            "source": "json",
        },
    }

@router.get("/api/ranking/feed")
def api_ranking_feed(
    days: int = 30,
    source: str = None,
    ticker: str = None,
    limit: int = 50,
):
    """
    Unified event timeline merging all smart money data sources.
    Returns a chronological feed of congress trades, ARK trades,
    dark pool anomalies, insider trades, and 13F position changes.
    """
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    # 13F filings are quarterly — use 180-day lookback so they always show
    institution_cutoff = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%d")
    events: list[dict] = []

    TOP_FUNDS = {"berkshire hathaway", "renaissance technologies", "bridgewater associates",
                 "pershing square", "soros fund"}

    # ── Congress trades ──────────────────────────────────────────────
    if not source or source == "congress":
        congress_data = smart_money_cache.read("congress.json")
        if congress_data and "trades" in congress_data:
            for t in congress_data["trades"]:
                tx_date = t.get("transaction_date", "")
                if tx_date < cutoff:
                    continue
                if ticker and t.get("ticker", "").upper() != ticker.upper():
                    continue
                trade_type = (t.get("trade_type") or "").lower()
                is_buy = trade_type in ("buy", "purchase")
                amt_min = t.get("amount_min", 0) or 0
                amt_max = t.get("amount_max", 0) or 0
                mid_val = (amt_min + amt_max) / 2 if amt_max else amt_min

                if mid_val > 500000:
                    sig = "high"
                elif mid_val > 100000:
                    sig = "medium"
                else:
                    sig = "low"

                rep = t.get("representative", "Unknown")
                chamber = t.get("chamber", "")
                party_short = "R" if t.get("party") == "Republican" else "D"
                action = "bought" if is_buy else "sold"
                tk = t.get("ticker", "???")

                events.append({
                    "id": f"congress-{tk}-{tx_date}-{rep[:10]}",
                    "source": "congress",
                    "ticker": tk,
                    "company": "",
                    "date": tx_date,
                    "headline": f"{rep} ({party_short}) {action} {tk}",
                    "description": f"{t.get('amount_range', '')} by {chamber} member",
                    "value": mid_val,
                    "sentiment": "bullish" if is_buy else "bearish",
                    "significance": sig,
                })

    # ── ARK trades ───────────────────────────────────────────────────
    if not source or source == "ark":
        ark_data = smart_money_cache.read("ark_trades.json")
        if ark_data and "trades" in ark_data:
            for t in ark_data["trades"]:
                trade_date = t.get("date", "")
                if trade_date < cutoff:
                    continue
                if ticker and t.get("ticker", "").upper() != ticker.upper():
                    continue
                change_type = (t.get("change_type") or "").upper()
                trade_type = (t.get("trade_type") or "").lower()
                is_buy = trade_type == "buy"
                shares = abs(t.get("shares", 0) or 0)
                etf = t.get("etf", "")
                tk = t.get("ticker", "???")
                company = t.get("company", "")

                if change_type in ("NEW_POSITION", "INCREASED"):
                    sig = "high"
                elif change_type in ("DECREASED", "SOLD_OUT"):
                    sig = "medium"
                else:
                    sig = "low"

                action = "bought" if is_buy else "sold"
                shares_fmt = f"{shares:,.0f}" if shares else "?"

                events.append({
                    "id": f"ark-{tk}-{trade_date}-{etf}",
                    "source": "ark",
                    "ticker": tk,
                    "company": company,
                    "date": trade_date,
                    "headline": f"ARK {etf} {action} {tk}",
                    "description": f"{shares_fmt} shares · {change_type.replace('_', ' ').title()}",
                    "value": None,
                    "sentiment": "bullish" if is_buy else "bearish",
                    "significance": sig,
                })

    # ── Dark pool anomalies ──────────────────────────────────────────
    if not source or source == "darkpool":
        dp_data = smart_money_cache.read("darkpool.json")
        if dp_data and "tickers" in dp_data:
            for t in dp_data["tickers"]:
                dp_date = t.get("date", "")
                if dp_date < cutoff:
                    continue
                if ticker and t.get("ticker", "").upper() != ticker.upper():
                    continue
                z = t.get("z_score", 0) or 0
                if z < 2.0:
                    continue
                tk = t.get("ticker", "???")
                dpi = t.get("dpi", 0) or 0

                if z >= 2.5:
                    sig = "high"
                else:
                    sig = "medium"

                vol = t.get("off_exchange_volume", 0) or 0
                vol_fmt = f"{vol / 1e6:.1f}M" if vol >= 1e6 else f"{vol / 1e3:.0f}K"

                events.append({
                    "id": f"darkpool-{tk}-{dp_date}",
                    "source": "darkpool",
                    "ticker": tk,
                    "company": "",
                    "date": dp_date,
                    "headline": f"Dark pool anomaly on {tk}",
                    "description": f"Z-score {z:.1f} · DPI {dpi:.0%} · {vol_fmt} off-exchange vol",
                    "value": None,
                    "sentiment": "neutral",
                    "significance": sig,
                })

    # ── Insider trades ───────────────────────────────────────────────
    if not source or source == "insider":
        insider_data = smart_money_cache.read("insiders.json")
        if insider_data and "trades" in insider_data:
            clusters = insider_data.get("clusters", [])
            cluster_tickers = {c.get("ticker", "").upper() for c in clusters}
            cluster_map = {c.get("ticker", "").upper(): c for c in clusters}
            seen_cluster_tickers: set[str] = set()

            for t in insider_data["trades"]:
                trade_date = t.get("trade_date") or t.get("filing_date", "")
                if trade_date < cutoff:
                    continue
                if ticker and t.get("ticker", "").upper() != ticker.upper():
                    continue
                tx_type = (t.get("transaction_type") or "").lower()
                if tx_type != "buy":
                    continue
                tk = t.get("ticker", "???").upper()
                val = abs(t.get("value", 0) or 0)
                company = t.get("company", "")

                # Cluster buy → one event per cluster ticker
                if tk in cluster_tickers and tk not in seen_cluster_tickers:
                    seen_cluster_tickers.add(tk)
                    c = cluster_map[tk]
                    c_val = c.get("total_value", 0)
                    c_count = c.get("insider_count", 0)
                    events.append({
                        "id": f"insider-cluster-{tk}-{c.get('first_date', trade_date)}",
                        "source": "insider",
                        "ticker": tk,
                        "company": company or c.get("company", ""),
                        "date": c.get("last_date", trade_date),
                        "headline": f"{c_count} insiders cluster buy {tk}",
                        "description": f"${c_val / 1e6:.1f}M total · {', '.join(c.get('insiders', [])[:3])}",
                        "value": c_val,
                        "sentiment": "bullish",
                        "significance": "high",
                    })
                    continue

                # Skip individual trades that are part of a cluster
                if tk in cluster_tickers:
                    continue

                # Individual buy
                if val > 500000:
                    sig = "high"
                elif val > 100000:
                    sig = "medium"
                else:
                    sig = "low"

                insider_name = t.get("insider_name", "Insider")
                title = t.get("title", "")
                val_fmt = f"${val / 1e6:.1f}M" if val >= 1e6 else f"${val / 1e3:.0f}K"

                events.append({
                    "id": f"insider-{tk}-{trade_date}-{insider_name[:10]}",
                    "source": "insider",
                    "ticker": tk,
                    "company": company,
                    "date": trade_date,
                    "headline": f"{insider_name} bought {tk}",
                    "description": f"{val_fmt} · {title}" if title else f"{val_fmt} purchase",
                    "value": val,
                    "sentiment": "bullish",
                    "significance": sig,
                })

    # ── 13F institution changes ──────────────────────────────────────
    if not source or source == "institution":
        inst_data = smart_money_cache.read("institutions.json")
        if inst_data and "filings" in inst_data:
            for filing in inst_data["filings"]:
                fund_name = filing.get("fund_name", "Unknown")
                filing_date = filing.get("filing_date", "")
                if filing_date < institution_cutoff:
                    continue
                is_top_fund = any(tf in fund_name.lower() for tf in TOP_FUNDS)
                sig = "high" if is_top_fund else "medium"
                quarter = filing.get("quarter", "")

                # Top 5 holdings by value for this fund
                holdings = filing.get("holdings", [])
                top_5 = sorted(holdings, key=lambda h: h.get("value", 0), reverse=True)[:5]

                for h in top_5:
                    tk = (h.get("ticker") or "").strip()
                    if not tk:
                        # Try to derive ticker from issuer
                        continue
                    if ticker and tk.upper() != ticker.upper():
                        continue
                    issuer = h.get("issuer", "")
                    val = h.get("value", 0) or 0
                    pct = h.get("pct_portfolio", 0)
                    val_fmt = f"${val / 1e9:.1f}B" if val >= 1e9 else f"${val / 1e6:.0f}M"

                    events.append({
                        "id": f"institution-{tk}-{fund_name[:15]}-{quarter}",
                        "source": "institution",
                        "ticker": tk.upper(),
                        "company": issuer,
                        "date": filing_date,
                        "headline": f"{fund_name} holds {tk.upper()}",
                        "description": f"{val_fmt} · {pct:.1f}% of portfolio · {quarter}",
                        "value": val,
                        "sentiment": "neutral",
                        "significance": sig,
                    })

    # ── Superinvestor activity ────────────────────────────────────────
    if not source or source == "superinvestor":
        super_data = smart_money_cache.read("superinvestors.json")
        if super_data and "activity" in super_data:
            super_events_tmp = []
            for a in super_data["activity"]:
                tk = (a.get("ticker") or "").strip()
                if not tk:
                    continue
                if ticker and tk.upper() != ticker.upper():
                    continue
                action = a.get("activity_type", "").capitalize()
                company = a.get("company", "")
                quarter = a.get("quarter", "")
                mgr_count = a.get("manager_count", 0) or 0
                pct = a.get("portfolio_pct", 0)
                src_type = a.get("source", "")  # aggregate or per_manager
                # Only show aggregate (cross-manager consensus) in main feed
                if src_type == "per_manager":
                    continue
                # When showing ALL sources, only include high-conviction (3+ managers)
                if not source and mgr_count < 3:
                    continue
                sig = "high" if mgr_count >= 5 else "medium" if mgr_count >= 3 else "low"
                sentiment = "bullish" if action == "Buy" else "bearish" if action == "Sell" else "neutral"
                # Use metadata last_updated as proxy date (no per-activity date)
                act_date = super_data.get("metadata", {}).get("last_updated", "")[:10]

                super_events_tmp.append({
                    "id": f"super-{tk}-{action}-{quarter}",
                    "source": "superinvestor",
                    "ticker": tk.upper(),
                    "company": company,
                    "date": act_date,
                    "headline": f"{mgr_count} superinvestors {action.lower()} {tk.upper()}",
                    "description": f"{pct:.1f}% avg portfolio weight · {quarter}",
                    "value": mgr_count,  # sort key
                    "sentiment": sentiment,
                    "significance": sig,
                })
            # Cap superinvestor events: top 50 by manager consensus
            super_events_tmp.sort(key=lambda e: e["value"], reverse=True)
            max_super = 50 if source else 20  # fewer when mixed with other sources
            events.extend(super_events_tmp[:max_super])

    # ── Short Interest anomalies ───────────────────────────────────────
    if not source or source == "short_interest":
        si_data = smart_money_cache.read("short_interest.json")
        if si_data and "tickers" in si_data:
            settlement = si_data.get("metadata", {}).get("settlement_date", "")
            # Only show tickers with high short interest ratio (>20%) or big changes
            for t in si_data["tickers"]:
                tk = (t.get("ticker") or "").strip()
                if not tk:
                    continue
                if ticker and tk.upper() != ticker.upper():
                    continue
                si_ratio = t.get("short_pct_float", 0) or 0
                si_change = t.get("change_pct", 0) or 0
                short_vol = t.get("current_short", 0) or 0
                # Filter: only show notable SI (>20% of float OR >30% change)
                if si_ratio < 20 and abs(si_change) < 30:
                    continue
                sig = "high" if si_ratio > 30 or abs(si_change) > 50 else "medium"
                sentiment = "bearish" if si_change > 10 else "bullish" if si_change < -10 else "neutral"
                change_dir = "↑" if si_change > 0 else "↓"
                vol_fmt = f"{short_vol / 1e6:.1f}M" if short_vol >= 1e6 else f"{short_vol / 1e3:.0f}K"

                events.append({
                    "id": f"si-{tk}-{settlement}",
                    "source": "short_interest",
                    "ticker": tk.upper(),
                    "company": t.get("company", tk),
                    "date": settlement,
                    "headline": f"{tk.upper()} short interest {si_ratio:.1f}% of float",
                    "description": f"{vol_fmt} shares short · {change_dir}{abs(si_change):.1f}% change",
                    "value": short_vol,
                    "sentiment": sentiment,
                    "significance": sig,
                })

    # ── Cross-reference with scoring engine to align significance ────
    # Load ranking data to check which tickers actually have scores
    ranking_data = smart_money_cache.read("ranking_v3.json")
    if not ranking_data or not ranking_data.get("signals"):
        ranking_data = smart_money_cache.read("ranking_v2.json")
    if not ranking_data or not ranking_data.get("signals"):
        ranking_data = smart_money_cache.read("ranking.json")
    scored_tickers = set()
    if ranking_data and ranking_data.get("signals"):
        for s in ranking_data["signals"]:
            scored_tickers.add((s.get("ticker", "").upper()))

    for e in events:
        tk = e.get("ticker", "").upper()
        # Mark whether this event's ticker has a confluence score
        e["has_score"] = tk in scored_tickers
        # Downgrade significance for events that won't produce a score
        # (keeps them visible but de-emphasizes them)
        if not e["has_score"] and e["significance"] != "low":
            # Insider individual buys under $10K → already low
            # Other unscored events: cap at "low"
            src = e.get("source", "")
            val = e.get("value") or 0
            if src == "insider" and val < 10_000:
                e["significance"] = "low"
            elif src == "congress" and val < 15_000:
                e["significance"] = "low"

    # ── Enrich company names, sort, limit ────────────────────────────
    ticker_names.enrich_list(events, ticker_field="ticker", name_field="company")

    events.sort(key=lambda e: e.get("date", ""), reverse=True)
    events = events[:limit]

    return {
        "events": events,
        "metadata": {
            "total": len(events),
            "filters": {"days": days, "source": source, "ticker": ticker, "limit": limit},
        },
    }


@router.get("/api/ranking/confluence")
def api_ranking_confluence(
    request: Request,
    min_score: float = 6.0,
    sources: str = None,  # comma-separated: congress,ark,darkpool,institutions
    days: int = 7,
    limit: int = 200,
):
    """
    Get confluence signals filtered by score, sources, and recency.
    Query params:
      - min_score: minimum confluence score (default: 6.0)
      - sources: comma-separated source filter (e.g., 'congress,ark')
      - days: only signals with activity in last N days (default: 7)
    """
    # Primary: V7 direction-aware ranking
    data = smart_money_cache.read("ranking_v3.json")
    if not data or "signals" not in data:
        # Fallback: V2 engine
        data = smart_money_cache.read("ranking_v2.json")
    if not data or "signals" not in data:
        # Last resort: ranking.json
        data = smart_money_cache.read("ranking.json")
    if not data or "signals" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}
    signals = data["signals"]
    
    # Filter by min_score
    filtered = [s for s in signals if s.get("score", 0) >= min_score]
    
    # Filter by sources
    if sources:
        source_list = [s.strip().lower() for s in sources.split(",")]
        filtered = [
            s for s in filtered
            if any(src in [d.get("source") for d in s.get("details", [])] for src in source_list)
        ]
    
    # Filter by days (last activity within N days)
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [s for s in filtered if s.get("signal_date", "9999-99-99") >= cutoff]
    
    # Enrich with company names
    ticker_names.enrich_list(filtered, ticker_field="ticker", name_field="company")
    
    # Apply limit
    total_filtered = len(filtered)
    if limit and limit > 0:
        filtered = filtered[:limit]
    
    result = {
        "data": filtered,
        "metadata": {
            "total": len(signals),
            "filtered": total_filtered,
            "filters": {
                "min_score": min_score,
                "sources": sources,
                "days": days,
                "limit": limit,
            },
            "engine": data.get("metadata", {}).get("engine", "v1"),
            "last_updated": data.get("metadata", {}).get("last_updated", data.get("last_updated"))
        }
    }
    if wants_markdown(request):
        from api.markdown_format import format_confluence_signals
        return markdown_response(result, format_confluence_signals)
    return result


@router.get("/api/ranking/smart-money")
def api_ranking_smart_money(
    request: Request,
    min_score: float = 0,
    source: str = None,
    days: int = 30,
    limit: int = 200,
):
    """
    Smart Money v2 signals — conviction-based scoring (0-100).
    
    Each source scored independently by signal strength:
    - Congress: amount × recency × member count × excess return
    - ARK: fund count × shares × position type × weight
    - Dark Pool: z-score × DPI × volume
    - Institutions: position value × change % × fund prestige
    
    Multi-source bonus: +20 per additional source (max +40).
    """
    # Primary: V3/V7 direction-aware ranking
    data = smart_money_cache.read("ranking_v3.json")
    if not data or "signals" not in data:
        # Fallback: V2 engine
        data = smart_money_cache.read("ranking_v2.json")
    if not data or "signals" not in data:
        # Last resort: generate on-the-fly with V2
        from api.modules.cross_signal_engine_v2 import SmartMoneyEngineV2
        engine = SmartMoneyEngineV2()
        
        congress = smart_money_cache.read("congress.json")
        ark = smart_money_cache.read("ark_trades.json")
        darkpool = smart_money_cache.read("darkpool.json")
        institutions = smart_money_cache.read("institutions.json")
        insiders = smart_money_cache.read("insiders.json")
        superinvestors = smart_money_cache.read("superinvestors.json")
        ark_holdings_data = smart_money_cache.read("ark_holdings.json")
        ark_holdings = ark_holdings_data.get("holdings", ark_holdings_data.get("data", [])) if ark_holdings_data else None
        
        results = engine.generate(
            congress_data=congress,
            ark_data=ark,
            darkpool_data=darkpool,
            institution_data=institutions,
            insider_data=insiders,
            superinvestor_data=superinvestors,
            ark_holdings=ark_holdings,
            min_score=0,
        )
        signals = engine.to_json(results)
        metadata = {"engine": "v2", "total": len(results), "last_updated": datetime.utcnow().isoformat()}
    else:
        signals = data["signals"]
        metadata = data.get("metadata", {})
    
    # Filter
    filtered = signals
    
    if min_score > 0:
        filtered = [s for s in filtered if s.get("score", 0) >= min_score]
    
    if source:
        filtered = [s for s in filtered if source.lower() in s.get("sources", [])]
    
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [s for s in filtered if s.get("signal_date", "9999") >= cutoff]
    
    # Enrich with company names
    ticker_names.enrich_list(filtered, ticker_field="ticker", name_field="company")
    
    # Apply limit
    total_filtered = len(filtered)
    if limit and limit > 0:
        filtered = filtered[:limit]
    
    return {
        "data": filtered,
        "metadata": {
            "total": metadata.get("total", len(signals)),
            "filtered": total_filtered,
            "engine": "v2",
            "filters": {"min_score": min_score, "source": source, "days": days, "limit": limit},
            "last_updated": metadata.get("last_updated"),
        }
    }


@router.get("/api/congress/trades")
def api_congress_trades(
    request: Request,
    party: str = None,  # Democrat, Republican
    chamber: str = None,  # House, Senate
    trade_type: str = None,  # Purchase, Sale, Sell
    min_amount: float = None,
    days: int = 30
):
    """
    Get Congress trades filtered by party, chamber, type, amount, and recency.
    Uses DuckDB query layer with JSON fallback.
    """
    # ── DuckDB fast path ──────────────────────────────────────────────
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
                # Normalize Sale/Sell
                norm = trade_type.lower().replace("sale", "sell")
                sql += " AND LOWER(REPLACE(trade_type, 'Sale', 'Sell')) = ?"
                params.append(norm)
            if min_amount is not None:
                sql += " AND amount_min >= ?"
                params.append(min_amount)
            if days:
                cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
                sql += " AND transaction_date >= ?"
                params.append(cutoff)

            sql += " ORDER BY transaction_date DESC"
            trades = db.query(sql, params)

            # Total count (unfiltered)
            total = db.query("SELECT COUNT(*) AS cnt FROM congress_trades")[0]["cnt"]

            ticker_names.enrich_list(trades, ticker_field="ticker", name_field="company")
            buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
            sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

            result = {
                "data": trades,
                "metadata": {
                    "total": total,
                    "filtered": len(trades),
                    "buy_count": buy_count,
                    "sell_count": sell_count,
                    "filters": {"party": party, "chamber": chamber, "trade_type": trade_type,
                                "min_amount": min_amount, "days": days},
                    "source": "duckdb",
                }
            }
            if wants_markdown(request):
                from api.markdown_format import format_congress_trades
                return markdown_response(result, format_congress_trades)
            return result

        except Exception as e:
            logger.warning(f"[duckdb] congress_trades query failed, falling back to JSON: {e}")

    # ── JSON fallback ─────────────────────────────────────────────────
    data = smart_money_cache.read("congress.json")
    if not data or "trades" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}

    trades = data["trades"]

    if party:
        trades = [t for t in trades if t.get("party", "").lower() == party.lower()]
    if chamber:
        trades = [t for t in trades if t.get("chamber", "").lower() == chamber.lower()]
    if trade_type:
        normalized_type = trade_type.lower().replace("sale", "sell")
        trades = [
            t for t in trades
            if t.get("trade_type", "").lower().replace("sale", "sell") == normalized_type
        ]
    if min_amount is not None:
        trades = [t for t in trades if t.get("amount_min", 0) >= min_amount]
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = [t for t in trades if t.get("transaction_date", "9999-99-99") >= cutoff]

    ticker_names.enrich_list(trades, ticker_field="ticker", name_field="company")
    buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
    sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

    result = {
        "data": trades,
        "metadata": {
            "total": len(data.get("trades", [])),
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "filters": {"party": party, "chamber": chamber, "trade_type": trade_type,
                        "min_amount": min_amount, "days": days},
            "last_updated": data.get("last_updated"),
            "source": "json",
        }
    }
    if wants_markdown(request):
        from api.markdown_format import format_congress_trades
        return markdown_response(result, format_congress_trades)
    return result

@router.get("/api/darkpool/analytics")
def api_darkpool_analytics(
    request: Request,
    min_zscore: float = 2.0,
    min_dpi: float = 0.4,
    days: int = 7
):
    """
    Get dark pool anomalies filtered by Z-score, DPI, and recency.
    Uses DuckDB query layer with JSON fallback.
    """
    # ── DuckDB fast path ──────────────────────────────────────────────
    db = _get_duckdb()
    if db is not None:
        try:
            sql = "SELECT * FROM darkpool_tickers WHERE z_score >= ? AND dpi >= ?"
            params = [min_zscore, min_dpi]

            if days:
                cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
                sql += " AND date >= ?"
                params.append(cutoff)

            sql += " ORDER BY z_score DESC"
            filtered = db.query(sql, params)
            total = db.query("SELECT COUNT(*) AS cnt FROM darkpool_tickers")[0]["cnt"]

            ticker_names.enrich_list(filtered, ticker_field="ticker", name_field="company")

            result = {
                "data": filtered,
                "metadata": {
                    "total": total,
                    "filtered": len(filtered),
                    "filters": {"min_zscore": min_zscore, "min_dpi": min_dpi, "days": days},
                    "source": "duckdb",
                }
            }
            if wants_markdown(request):
                from api.markdown_format import format_darkpool
                return markdown_response(result, format_darkpool)
            return result

        except Exception as e:
            logger.warning(f"[duckdb] darkpool_tickers query failed, falling back to JSON: {e}")

    # ── JSON fallback ─────────────────────────────────────────────────
    data = smart_money_cache.read("darkpool.json")
    if not data or "tickers" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}

    tickers = data["tickers"]
    filtered = [t for t in tickers if t.get("z_score", 0) >= min_zscore]
    filtered = [t for t in filtered if t.get("dpi", 0) >= min_dpi]

    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [t for t in filtered if t.get("date", "9999-99-99") >= cutoff]

    ticker_names.enrich_list(filtered, ticker_field="ticker", name_field="company")

    result = {
        "data": filtered,
        "metadata": {
            "total": len(tickers),
            "filtered": len(filtered),
            "filters": {"min_zscore": min_zscore, "min_dpi": min_dpi, "days": days},
            "last_updated": data.get("metadata", {}).get("last_updated"),
            "source": "json",
        }
    }
    if wants_markdown(request):
        from api.markdown_format import format_darkpool
        return markdown_response(result, format_darkpool)
    return result

@router.get("/api/ark/trades")
def api_ark_trades(
    request: Request,
    trade_type: str = None,  # Buy, Sell
    etf: str = None,  # ARKK, ARKG, etc.
    days: int = 30
):
    """
    Get ARK trades filtered by type, ETF, and recency.
    Uses DuckDB query layer with JSON fallback.
    """
    # ── DuckDB fast path ──────────────────────────────────────────────
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
                cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
                sql += " AND date >= ?"
                params.append(cutoff)

            sql += " ORDER BY date DESC"
            trades = db.query(sql, params)
            total = db.query("SELECT COUNT(*) AS cnt FROM ark_trades")[0]["cnt"]

            buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
            sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

            result = {
                "data": trades,
                "metadata": {
                    "total": total,
                    "filtered": len(trades),
                    "buy_count": buy_count,
                    "sell_count": sell_count,
                    "filters": {"trade_type": trade_type, "etf": etf, "days": days},
                    "source": "duckdb",
                }
            }
            if wants_markdown(request):
                from api.markdown_format import format_ark_trades
                return markdown_response(result, format_ark_trades)
            return result

        except Exception as e:
            logger.warning(f"[duckdb] ark_trades query failed, falling back to JSON: {e}")

    # ── JSON fallback ─────────────────────────────────────────────────
    data = smart_money_cache.read("ark_trades.json")
    if not data or "trades" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}

    trades = data["trades"]

    if trade_type:
        trades = [t for t in trades if t.get("trade_type", "").lower() == trade_type.lower()]
    if etf:
        trades = [t for t in trades if t.get("etf", "").upper() == etf.upper()]
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = [t for t in trades if t.get("date", "9999-99-99") >= cutoff]

    buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
    sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

    result = {
        "data": trades,
        "metadata": {
            "total": len(data.get("trades", [])),
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "filters": {"trade_type": trade_type, "etf": etf, "days": days},
            "last_updated": data.get("last_updated"),
            "source": "json",
        }
    }
    if wants_markdown(request):
        from api.markdown_format import format_ark_trades
        return markdown_response(result, format_ark_trades)
    return result

@router.get("/api/ark/holdings")
def api_ark_holdings(
    etf: str = None,  # ARKK, ARKG, etc.
    min_weight: float = 0.0  # minimum weight % in portfolio
):
    """
    Get ARK current holdings filtered by ETF and weight.
    """
    data = smart_money_cache.read("ark_holdings.json")
    if not data or "holdings" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}
    
    holdings = data["holdings"]
    
    # Filter by etf
    if etf:
        holdings = [h for h in holdings if h.get("etf", "").upper() == etf.upper()]
    
    # Filter by min_weight
    if min_weight:
        holdings = [h for h in holdings if h.get("weight_pct", 0) >= min_weight]
    
    return {
        "data": holdings,
        "metadata": {
            "total": len(data.get("holdings", [])),
            "filtered": len(holdings),
            "filters": {
                "etf": etf,
                "min_weight": min_weight
            },
            "last_updated": data.get("last_updated")
        }
    }

@router.get("/api/institutions/filings")
def api_institutions_filings(
    request: Request,
    fund: str = None,  # Institution name filter
    min_value: float = None  # minimum position value ($)
):
    """
    Get 13F institutional filings filtered by fund and position size.
    Returns both fund-level summary and flattened top holdings.
    Uses DuckDB query layer with JSON fallback.
    """
    # ── DuckDB fast path ──────────────────────────────────────────────
    db = _get_duckdb()
    if db is not None:
        try:
            # Fund-level summary
            filing_sql = "SELECT cik, fund_name, company_name, filing_date, quarter, total_value, holdings_count FROM institution_filings WHERE 1=1"
            filing_params = []
            if fund:
                filing_sql += " AND LOWER(fund_name) LIKE ?"
                filing_params.append(f"%{fund.lower()}%")

            filings_summary = db.query(filing_sql, filing_params if filing_params else None)
            total_filings = db.query("SELECT COUNT(*) AS cnt FROM institution_filings")[0]["cnt"]

            # Top holdings (flattened)
            holding_sql = """
                SELECT ticker, issuer, fund_name AS institution, cik,
                       shares, value, pct_portfolio, cusip, filing_date, quarter
                FROM institution_holdings
                WHERE ticker IS NOT NULL AND ticker != ''
            """
            holding_params = []
            if fund:
                holding_sql += " AND LOWER(fund_name) LIKE ?"
                holding_params.append(f"%{fund.lower()}%")
            if min_value is not None:
                holding_sql += " AND value >= ?"
                holding_params.append(min_value)

            holding_sql += " ORDER BY value DESC LIMIT 100"
            top_holdings = db.query(holding_sql, holding_params if holding_params else None)

            total_value = sum(f.get("total_value") or 0 for f in filings_summary)
            unique_tickers = db.query("SELECT COUNT(DISTINCT ticker) AS cnt FROM institution_holdings WHERE ticker != ''")[0]["cnt"]

            result = {
                "data": filings_summary,
                "top_holdings": top_holdings,
                "summary": {
                    "total_value": total_value,
                    "unique_tickers": unique_tickers,
                    "filings_count": len(filings_summary),
                },
                "metadata": {
                    "total": total_filings,
                    "filtered": len(filings_summary),
                    "filters": {"fund": fund, "min_value": min_value},
                    "source": "duckdb",
                }
            }
            if wants_markdown(request):
                from api.markdown_format import format_institutions
                return markdown_response(result, format_institutions)
            return result

        except Exception as e:
            logger.warning(f"[duckdb] institution_filings query failed, falling back to JSON: {e}")

    # ── JSON fallback ─────────────────────────────────────────────────
    data = smart_money_cache.read("institutions.json")
    if not data or "filings" not in data:
        return {"data": [], "summary": {"total_value": 0, "unique_tickers": 0, "filings_count": 0}, "top_holdings": [], "metadata": {"total": 0, "filtered": 0}}

    filings = data["filings"]

    if fund:
        filings = [f for f in filings if fund.lower() in f.get("fund_name", "").lower()]

    total_value = sum(f.get("total_value", 0) for f in filings)

    all_tickers = set()
    for f in filings:
        for h in f.get("holdings", []):
            ticker = h.get("ticker", "").strip()
            if ticker:
                all_tickers.add(ticker)

    flattened = []
    for filing in filings:
        fund_name = filing.get("fund_name", "Unknown")
        filing_date = filing.get("filing_date", "")
        quarter = filing.get("quarter", "")

        for holding in filing.get("holdings", []):
            ticker = holding.get("ticker", "").strip()
            if not ticker:
                continue
            fund_total = filing.get("total_value", 1)
            holding_value = holding.get("value", 0)
            pct_portfolio = (holding_value / fund_total * 100) if fund_total > 0 else 0
            flattened.append({
                "ticker": ticker,
                "issuer": holding.get("issuer", ""),
                "institution": fund_name,
                "cik": filing.get("cik", ""),
                "shares": holding.get("shares", 0),
                "value": holding_value,
                "pct_portfolio": pct_portfolio,
                "cusip": holding.get("cusip", ""),
                "filing_date": filing_date,
                "quarter": quarter,
            })

    top_holdings = sorted(flattened, key=lambda x: x.get("value", 0), reverse=True)[:100]
    if min_value is not None:
        top_holdings = [h for h in top_holdings if h.get("value", 0) >= min_value]

    filings_summary = []
    for f in filings:
        filings_summary.append({
            "cik": f.get("cik", ""),
            "fund_name": f.get("fund_name", ""),
            "company_name": f.get("company_name", f.get("company", "")),
            "filing_date": f.get("filing_date", ""),
            "quarter": f.get("quarter", ""),
            "total_value": f.get("total_value", 0),
            "holdings_count": f.get("holdings_count", len(f.get("holdings", []))),
        })

    result = {
        "data": filings_summary,
        "top_holdings": top_holdings,
        "summary": {
            "total_value": total_value,
            "unique_tickers": len(all_tickers),
            "filings_count": len(filings),
        },
        "metadata": {
            "total": len(data.get("filings", [])),
            "filtered": len(filings),
            "filters": {"fund": fund, "min_value": min_value},
            "last_updated": data.get("last_updated"),
            "source": "json",
        }
    }
    if wants_markdown(request):
        from api.markdown_format import format_institutions
        return markdown_response(result, format_institutions)
    return result

def _load_ark_changes() -> list:
    """Load all ARK changes from JSONL."""
    return read_jsonl(os.path.join(ARK_DATA_DIR, "ark_changes.jsonl"), limit=5000)

def _load_all_holdings() -> dict:
    """Load all ARK ETF holdings."""
    holdings = {}
    ark_dir = os.path.join(ARK_DATA_DIR, "ark_holdings")
    if os.path.isdir(ark_dir):
        for fname in os.listdir(ark_dir):
            if fname.endswith("_latest.json"):
                etf = fname.replace("_latest.json", "")
                data = read_json(os.path.join(ark_dir, fname))
                if data and "holdings" in data:
                    holdings[etf] = data
    return holdings

def _build_cross_etf_summary(all_holdings: dict, all_changes: list) -> list:
    """Build a cross-ETF summary: aggregate each ticker across all funds."""
    from collections import defaultdict
    ticker_data = defaultdict(lambda: {
        "ticker": "", "company": "", "etfs": [],
        "total_shares": 0, "total_value": 0, "total_weight": 0,
        "trade_count": 0, "net_direction": "hold",
        "first_seen_date": None, "last_trade_date": None,
        "buys": 0, "sells": 0,
    })

    for etf, data in all_holdings.items():
        for h in data.get("holdings", []):
            t = h.get("ticker")
            if not t:
                continue
            d = ticker_data[t]
            d["ticker"] = t
            d["company"] = h.get("company", d["company"])
            d["etfs"].append(etf)
            d["total_shares"] += h.get("shares", 0)
            d["total_value"] += h.get("market_value", 0)
            d["total_weight"] += h.get("weight", 0)
            date_str = h.get("date") or data.get("date")
            if date_str:
                if not d["first_seen_date"] or date_str < d["first_seen_date"]:
                    d["first_seen_date"] = date_str

    # Enrich with changes data
    for c in all_changes:
        t = c.get("ticker")
        if not t:
            continue
        d = ticker_data[t]
        d["ticker"] = t
        d["company"] = c.get("company", d["company"])
        d["trade_count"] += 1
        ts = c.get("timestamp", "")[:10]
        if ts:
            if not d["first_seen_date"] or ts < d["first_seen_date"]:
                d["first_seen_date"] = ts
            if not d["last_trade_date"] or ts > d["last_trade_date"]:
                d["last_trade_date"] = ts
        ctype = c.get("type", "")
        if ctype in ("NEW_POSITION", "INCREASED"):
            d["buys"] += 1
        elif ctype in ("DECREASED", "SOLD_OUT"):
            d["sells"] += 1

    # Calculate net direction and holding days
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for t, d in ticker_data.items():
        if d["buys"] > d["sells"]:
            d["net_direction"] = "accumulating"
        elif d["sells"] > d["buys"]:
            d["net_direction"] = "trimming"
        else:
            d["net_direction"] = "hold"
        # Holding days
        if d["first_seen_date"]:
            try:
                first = datetime.strptime(d["first_seen_date"], "%Y-%m-%d")
                today = datetime.strptime(today_str, "%Y-%m-%d")
                d["holding_days"] = (today - first).days
            except Exception:
                d["holding_days"] = 0
        else:
            d["holding_days"] = 0
        d["etfs"] = sorted(set(d["etfs"]))

    return sorted(ticker_data.values(), key=lambda x: x["total_value"], reverse=True)

