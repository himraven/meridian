"""
Markdown formatters for Smart Money API responses.

When clients send Accept: text/markdown, these formatters convert JSON API
responses into clean, human-readable Markdown. Designed for AI agent consumption.

Token savings: ~70-80% vs raw JSON.
"""

from datetime import datetime


def format_number(n, decimals=0):
    """Format number with commas."""
    if n is None:
        return "—"
    if abs(n) >= 1e9:
        return f"${n/1e9:.1f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n/1e3:.0f}K"
    if decimals:
        return f"{n:,.{decimals}f}"
    return f"{n:,.0f}"


def format_confluence_signals(data: dict) -> str:
    """Format confluence signals as markdown."""
    signals = data.get("data", [])
    meta = data.get("metadata", {})
    
    lines = [
        "# 🎯 Smart Money Confluence Signals",
        f"*{meta.get('filtered', len(signals))} signals (from {meta.get('total', '?')} total) · Updated: {meta.get('last_updated', 'unknown')}*",
        ""
    ]
    
    if not signals:
        lines.append("No signals match current filters.")
        return "\n".join(lines)
    
    for s in signals[:30]:
        ticker = s.get("ticker", "?")
        score = s.get("score", 0)
        sources = s.get("sources", [])
        source_str = ", ".join(sources) if sources else "—"
        
        # Score emoji
        if score >= 8:
            emoji = "🔥"
        elif score >= 5:
            emoji = "⚡"
        else:
            emoji = "📊"
        
        lines.append(f"### {emoji} {ticker} — Score: {score}")
        lines.append(f"Sources: {source_str}")
        
        # Details
        details = s.get("details", [])
        for d in details:
            src = d.get("source", "?")
            detail = d.get("detail", "")
            lines.append(f"- **{src}**: {detail}")
        
        lines.append("")
    
    return "\n".join(lines)


def format_congress_trades(data: dict) -> str:
    """Format congress trades as markdown."""
    trades = data.get("data", [])
    meta = data.get("metadata", {})
    
    lines = [
        "# 🏛️ Congress Trading Activity",
        f"*{meta.get('filtered', len(trades))} trades · Last {meta.get('filters', {}).get('days', '?')} days*",
        ""
    ]
    
    if not trades:
        lines.append("No trades found.")
        return "\n".join(lines)
    
    # Summary stats
    buys = [t for t in trades if t.get("trade_type") == "Purchase"]
    sells = [t for t in trades if t.get("trade_type") != "Purchase"]
    lines.append(f"**Summary**: {len(buys)} buys, {len(sells)} sells")
    lines.append("")
    
    # Table header
    lines.append("| Ticker | Member | Party | Type | Date | Amount | Excess Return |")
    lines.append("|--------|--------|-------|------|------|--------|---------------|")
    
    for t in trades[:50]:
        ticker = t.get("ticker", "?")
        member = t.get("representative", "?")[:20]
        party = t.get("party", "?")[0] if t.get("party") else "?"
        trade_type = "Buy" if t.get("trade_type") == "Purchase" else "Sell"
        date = t.get("transaction_date", "?")
        amount = t.get("amount_range", "?")
        ret = t.get("excess_return_pct")
        ret_str = f"{ret:+.1f}%" if ret is not None else "—"
        
        lines.append(f"| {ticker} | {member} | {party} | {trade_type} | {date} | {amount} | {ret_str} |")
    
    if len(trades) > 50:
        lines.append(f"\n*... and {len(trades) - 50} more trades*")
    
    return "\n".join(lines)


def format_darkpool(data: dict) -> str:
    """Format dark pool anomalies as markdown."""
    anomalies = data.get("data", [])
    meta = data.get("metadata", {})
    
    lines = [
        "# 🌑 Dark Pool Anomalies",
        f"*{meta.get('filtered', len(anomalies))} anomalies detected*",
        ""
    ]
    
    if not anomalies:
        lines.append("No dark pool anomalies found.")
        return "\n".join(lines)
    
    lines.append("| Ticker | Date | Z-Score | DPI | Volume | Avg Volume |")
    lines.append("|--------|------|---------|-----|--------|------------|")
    
    for a in anomalies[:30]:
        ticker = a.get("ticker", "?")
        date = a.get("date", "?")
        zscore = a.get("z_score", 0)
        dpi = a.get("dpi_ratio", 0)
        vol = format_number(a.get("dp_volume", 0))
        avg = format_number(a.get("avg_volume", 0))
        
        lines.append(f"| {ticker} | {date} | {zscore:.1f} | {dpi:.0%} | {vol} | {avg} |")
    
    return "\n".join(lines)


def format_ark_trades(data: dict) -> str:
    """Format ARK trades as markdown."""
    trades = data.get("data", [])
    meta = data.get("metadata", {})
    
    lines = [
        "# 🚀 ARK Invest Trades",
        f"*{meta.get('filtered', len(trades))} trades · Last {meta.get('filters', {}).get('days', '?')} days*",
        ""
    ]
    
    if not trades:
        lines.append("No ARK trades found.")
        return "\n".join(lines)
    
    buys = [t for t in trades if t.get("trade_type") == "Buy"]
    sells = [t for t in trades if t.get("trade_type") != "Buy"]
    lines.append(f"**Summary**: {len(buys)} buys, {len(sells)} sells across {len(set(t.get('etf','') for t in trades))} ETFs")
    lines.append("")
    
    lines.append("| Date | ETF | Ticker | Company | Type | Shares | Weight% | Return |")
    lines.append("|------|-----|--------|---------|------|--------|---------|--------|")
    
    for t in trades[:50]:
        date = t.get("date", "?")
        etf = t.get("etf", "?")
        ticker = t.get("ticker", "?")
        company = (t.get("company") or "")[:20]
        trade_type = t.get("trade_type", "?")
        shares = format_number(t.get("shares", 0))
        weight = f"{t.get('weight_pct', 0):.2f}%" if t.get("weight_pct") else "—"
        ret = t.get("return_pct")
        ret_str = f"{ret:+.1f}%" if ret is not None else "—"
        
        lines.append(f"| {date} | {etf} | {ticker} | {company} | {trade_type} | {shares} | {weight} | {ret_str} |")
    
    if len(trades) > 50:
        lines.append(f"\n*... and {len(trades) - 50} more trades*")
    
    return "\n".join(lines)


def format_institutions(data: dict) -> str:
    """Format institution filings as markdown."""
    holdings = data.get("top_holdings", [])
    summary = data.get("summary", {})
    
    lines = [
        "# 🏦 Institutional Holdings (13F)",
        f"*{summary.get('filings_count', '?')} filings · {summary.get('unique_tickers', '?')} unique tickers · Total AUM: {format_number(summary.get('total_value', 0))}*",
        ""
    ]
    
    if not holdings:
        lines.append("No institution filings data.")
        return "\n".join(lines)
    
    lines.append("| Ticker | Issuer | Institution | Shares | Value | Portfolio% |")
    lines.append("|--------|--------|-------------|--------|-------|-----------|")
    
    for h in holdings[:50]:
        ticker = h.get("ticker", "?")
        issuer = (h.get("issuer") or "")[:20]
        inst = (h.get("institution") or "")[:20]
        shares = format_number(h.get("shares", 0))
        value = format_number(h.get("value", 0))
        pct = f"{h.get('pct_portfolio', 0):.1f}%" if h.get("pct_portfolio") else "—"
        
        lines.append(f"| {ticker} | {issuer} | {inst} | {shares} | {value} | {pct} |")
    
    if len(holdings) > 50:
        lines.append(f"\n*... and {len(holdings) - 50} more holdings*")
    
    return "\n".join(lines)


def format_ticker_aggregate(data: dict) -> str:
    """Format ticker aggregate data as markdown."""
    ticker = data.get("ticker", "?")
    meta = data.get("metadata", {})
    
    lines = [
        f"# 📊 {ticker} — Smart Money Intelligence",
        f"*{meta.get('total_signals', 0)} total signals across all sources*",
        ""
    ]
    
    # Confluence
    conf = data.get("confluence", {})
    if conf.get("score"):
        lines.append(f"## 🎯 Confluence Score: {conf['score']}")
        for s in conf.get("signals", []):
            for d in s.get("details", []):
                lines.append(f"- **{d.get('source', '?')}**: {d.get('detail', '')}")
        lines.append("")
    
    # Congress
    cong = data.get("congress", {})
    if cong.get("count", 0) > 0:
        lines.append(f"## 🏛️ Congress Trades ({cong['count']})")
        for t in cong.get("trades", [])[:10]:
            party = t.get("party", "?")[0] if t.get("party") else "?"
            trade = "Buy" if t.get("trade_type") == "Purchase" else "Sell"
            ret = t.get("excess_return_pct")
            ret_str = f" → {ret:+.1f}% excess" if ret else ""
            lines.append(f"- {t.get('transaction_date', '?')}: **{trade}** by {t.get('representative', '?')} ({party}) {t.get('amount_range', '')}{ret_str}")
        lines.append("")
    
    # ARK
    ark = data.get("ark", {})
    if ark.get("trade_count", 0) > 0 or ark.get("holding_etfs", 0) > 0:
        lines.append(f"## 🚀 ARK ({ark.get('trade_count', 0)} trades, {ark.get('holding_etfs', 0)} ETFs holding)")
        for t in ark.get("trades", [])[:10]:
            wt = t.get('weight_pct')
        wt_str = f"{wt:.2f}%" if wt is not None else "—"
        lines.append(f"- {t.get('date', '?')}: {t.get('etf', '?')} — {t.get('trade_type', '?')} {format_number(t.get('shares', 0))} shares ({wt_str})")
        for h in ark.get("holdings", []):
            lines.append(f"- Holding: {h.get('etf', '?')} — {format_number(h.get('shares', 0))} shares, {h.get('weight', 0):.2f}% weight")
        lines.append("")
    
    # Dark Pool
    dp = data.get("darkpool", {})
    if dp.get("count", 0) > 0:
        lines.append(f"## 🌑 Dark Pool Anomalies ({dp['count']})")
        for a in dp.get("anomalies", [])[:5]:
            lines.append(f"- {a.get('date', '?')}: Z-score {a.get('z_score', 0):.1f}, DPI {a.get('dpi_ratio', 0):.0%}")
        lines.append("")
    
    # Institutions
    inst = data.get("institutions", {})
    if inst.get("count", 0) > 0:
        lines.append(f"## 🏦 Institutional Holdings ({inst['count']})")
        for h in inst.get("holdings", [])[:10]:
            lines.append(f"- **{h.get('institution', '?')}**: {format_number(h.get('shares', 0))} shares ({format_number(h.get('value', 0))}), {h.get('pct_portfolio', 0):.1f}% of portfolio")
        lines.append("")
    
    if meta.get("total_signals", 0) == 0:
        lines.append("*No smart money signals found for this ticker.*")
    
    return "\n".join(lines)


# Route -> formatter mapping
MARKDOWN_FORMATTERS = {
    "/api/signals/confluence": format_confluence_signals,
    "/api/congress/trades": format_congress_trades,
    "/api/darkpool/analytics": format_darkpool,
    "/api/ark/trades": format_ark_trades,
    "/api/institutions/filings": format_institutions,
}

# Ticker aggregate uses a special pattern (dynamic path)
TICKER_PATTERN = "/api/ticker/"
