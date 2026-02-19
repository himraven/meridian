"""
US market routes - ARK, 13F, Congress, Dark Pool, Institutions
"""
import json
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
    
    Query params:
      - transaction_type: Buy or Sale (default: all)
      - ticker: filter by specific ticker
      - min_value: minimum trade value ($)
      - cluster_only: only show cluster buys (3+ insiders buying same stock)
      - days: only trades in last N days (default: 30)
    """
    data = smart_money_cache.read("insiders.json")
    if not data or "trades" not in data:
        return {"data": [], "clusters": [], "metadata": {"total": 0, "filtered": 0}}
    
    trades = data["trades"]
    clusters = data.get("clusters", [])
    
    # Filter by transaction_type
    if transaction_type:
        trades = [t for t in trades if t.get("transaction_type", "").lower() == transaction_type.lower()]
    
    # Filter by ticker
    if ticker:
        ticker_upper = ticker.upper()
        trades = [t for t in trades if t.get("ticker", "").upper() == ticker_upper]
        clusters = [c for c in clusters if c.get("ticker", "").upper() == ticker_upper]
    
    # Filter by min_value
    if min_value is not None:
        trades = [t for t in trades if t.get("value", 0) >= min_value]
    
    # Filter cluster_only
    if cluster_only:
        cluster_tickers = set(c.get("ticker", "").upper() for c in data.get("clusters", []))
        cluster_tickers.update(data.get("metadata", {}).get("cluster_tickers", []))
        trades = [t for t in trades if t.get("ticker", "").upper() in cluster_tickers]
    
    # Filter by days
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = [
            t for t in trades
            if (t.get("trade_date") or t.get("filing_date", "9999")) >= cutoff
        ]
    
    # Enrich with company names
    ticker_names.enrich_list(trades, ticker_field="ticker", name_field="company")
    
    # Stats
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
                "transaction_type": transaction_type,
                "ticker": ticker,
                "min_value": min_value,
                "cluster_only": cluster_only,
                "days": days,
            },
            "source": data.get("metadata", {}).get("source", "openinsider"),
            "last_updated": data.get("metadata", {}).get("last_updated"),
        }
    }


@router.get("/api/signals/feed")
def api_signals_feed(
    days: int = 7,
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
                if filing_date < cutoff:
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


@router.get("/api/signals/confluence")
def api_signals_confluence(
    request: Request,
    min_score: float = 6.0,
    sources: str = None,  # comma-separated: congress,ark,darkpool,institutions
    days: int = 7
):
    """
    Get confluence signals filtered by score, sources, and recency.
    Query params:
      - min_score: minimum confluence score (default: 6.0)
      - sources: comma-separated source filter (e.g., 'congress,ark')
      - days: only signals with activity in last N days (default: 7)
    """
    # Primary: V2 engine (conviction-based, 0-100 scale)
    data = smart_money_cache.read("signals_v2.json")
    if data and "signals" in data:
        signals = data["signals"]
    else:
        # Fallback: V1 engine
        data = smart_money_cache.read("signals.json")
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
    
    result = {
        "data": filtered,
        "metadata": {
            "total": len(signals),
            "filtered": len(filtered),
            "filters": {
                "min_score": min_score,
                "sources": sources,
                "days": days
            },
            "engine": data.get("metadata", {}).get("engine", "v1"),
            "last_updated": data.get("metadata", {}).get("last_updated", data.get("last_updated"))
        }
    }
    if wants_markdown(request):
        from api.markdown_format import format_confluence_signals
        return markdown_response(result, format_confluence_signals)
    return result


@router.get("/api/signals/smart-money")
def api_signals_smart_money(
    request: Request,
    min_score: float = 0,
    source: str = None,
    days: int = 30,
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
    data = smart_money_cache.read("signals_v2.json")
    if not data or "signals" not in data:
        # Fallback: generate on-the-fly
        from api.modules.cross_signal_engine_v2 import SmartMoneyEngineV2
        engine = SmartMoneyEngineV2()
        
        congress = smart_money_cache.read("congress.json")
        ark = smart_money_cache.read("ark_trades.json")
        darkpool = smart_money_cache.read("darkpool.json")
        institutions = smart_money_cache.read("institutions.json")
        insiders = smart_money_cache.read("insiders.json")
        ark_holdings_data = smart_money_cache.read("ark_holdings.json")
        ark_holdings = ark_holdings_data.get("holdings", ark_holdings_data.get("data", [])) if ark_holdings_data else None
        
        results = engine.generate(
            congress_data=congress,
            ark_data=ark,
            darkpool_data=darkpool,
            institution_data=institutions,
            insider_data=insiders,
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
    
    return {
        "data": filtered,
        "metadata": {
            "total": metadata.get("total", len(signals)),
            "filtered": len(filtered),
            "engine": "v2",
            "filters": {"min_score": min_score, "source": source, "days": days},
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
    """
    data = smart_money_cache.read("congress.json")
    if not data or "trades" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}
    
    trades = data["trades"]
    
    # Filter by party
    if party:
        trades = [t for t in trades if t.get("party", "").lower() == party.lower()]
    
    # Filter by chamber
    if chamber:
        trades = [t for t in trades if t.get("chamber", "").lower() == chamber.lower()]
    
    # Filter by trade_type (handle both "Sale" and "Sell")
    if trade_type:
        normalized_type = trade_type.lower().replace("sale", "sell")
        trades = [
            t for t in trades
            if t.get("trade_type", "").lower().replace("sale", "sell") == normalized_type
        ]
    
    # Filter by min_amount
    if min_amount is not None:
        trades = [t for t in trades if t.get("amount_min", 0) >= min_amount]
    
    # Filter by days
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = [t for t in trades if t.get("transaction_date", "9999-99-99") >= cutoff]
    
    # Enrich trades with company names
    ticker_names.enrich_list(trades, ticker_field="ticker", name_field="company")
    
    # Count buys/sells from filtered results
    buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
    sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

    result = {
        "data": trades,
        "metadata": {
            "total": len(data.get("trades", [])),
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "filters": {
                "party": party,
                "chamber": chamber,
                "trade_type": trade_type,
                "min_amount": min_amount,
                "days": days
            },
            "last_updated": data.get("last_updated")
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
    """
    data = smart_money_cache.read("darkpool.json")
    if not data or "tickers" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}
    
    tickers = data["tickers"]
    
    # Filter by min_zscore
    filtered = [t for t in tickers if t.get("z_score", 0) >= min_zscore]
    
    # Filter by min_dpi
    filtered = [t for t in filtered if t.get("dpi", 0) >= min_dpi]
    
    # Filter by days
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        filtered = [t for t in filtered if t.get("date", "9999-99-99") >= cutoff]
    
    # Enrich with company names
    ticker_names.enrich_list(filtered, ticker_field="ticker", name_field="company")
    
    result = {
        "data": filtered,
        "metadata": {
            "total": len(tickers),
            "filtered": len(filtered),
            "filters": {
                "min_zscore": min_zscore,
                "min_dpi": min_dpi,
                "days": days
            },
            "last_updated": data.get("metadata", {}).get("last_updated")
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
    """
    data = smart_money_cache.read("ark_trades.json")
    if not data or "trades" not in data:
        return {"data": [], "metadata": {"total": 0, "filtered": 0}}
    
    trades = data["trades"]
    
    # Filter by trade_type
    if trade_type:
        trades = [t for t in trades if t.get("trade_type", "").lower() == trade_type.lower()]
    
    # Filter by etf
    if etf:
        trades = [t for t in trades if t.get("etf", "").upper() == etf.upper()]
    
    # Filter by days
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = [t for t in trades if t.get("date", "9999-99-99") >= cutoff]
    
    # Count buys/sells from filtered results
    buy_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("buy", "purchase"))
    sell_count = sum(1 for t in trades if (t.get("trade_type") or "").lower() in ("sell", "sale"))

    result = {
        "data": trades,
        "metadata": {
            "total": len(data.get("trades", [])),
            "filtered": len(trades),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "filters": {
                "trade_type": trade_type,
                "etf": etf,
                "days": days
            },
            "last_updated": data.get("last_updated")
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
    """
    data = smart_money_cache.read("institutions.json")
    if not data or "filings" not in data:
        return {"data": [], "summary": {"total_value": 0, "unique_tickers": 0, "filings_count": 0}, "top_holdings": [], "metadata": {"total": 0, "filtered": 0}}
    
    filings = data["filings"]
    
    # Filter by fund (institution name)
    if fund:
        filings = [f for f in filings if fund.lower() in f.get("fund_name", "").lower()]
    
    # Calculate summary stats from raw filings (which have nested holdings)
    total_value = sum(f.get("total_value", 0) for f in filings)
    
    # Collect all unique tickers from nested holdings
    all_tickers = set()
    for f in filings:
        for h in f.get("holdings", []):
            ticker = h.get("ticker", "").strip()
            if ticker:
                all_tickers.add(ticker)
    
    # Flatten holdings across all filings for top holdings table
    flattened = []
    for filing in filings:
        fund_name = filing.get("fund_name", "Unknown")
        filing_date = filing.get("filing_date", "")
        quarter = filing.get("quarter", "")
        
        for holding in filing.get("holdings", []):
            ticker = holding.get("ticker", "").strip()
            if not ticker:
                continue
            
            # Calculate % of portfolio for this fund
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
    
    # Sort by value and get top 100
    top_holdings = sorted(flattened, key=lambda x: x.get("value", 0), reverse=True)[:100]
    
    # Filter by min_value if specified
    if min_value is not None:
        top_holdings = [h for h in top_holdings if h.get("value", 0) >= min_value]
    
    # Strip nested holdings from fund-level data to reduce payload
    # (was 4MB → ~5KB without holdings; frontend only needs fund name + AUM)
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
        "data": filings_summary,  # Fund-level summary (no nested holdings)
        "top_holdings": top_holdings,  # Flattened top 100 holdings
        "summary": {
            "total_value": total_value,
            "unique_tickers": len(all_tickers),
            "filings_count": len(filings),
        },
        "metadata": {
            "total": len(data.get("filings", [])),
            "filtered": len(filings),
            "filters": {
                "fund": fund,
                "min_value": min_value
            },
            "last_updated": data.get("last_updated")
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

