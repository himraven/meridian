#!/usr/bin/env python3
"""
Meridian Knowledge Hub — Weekly Recap Generator

Generates a weekly recap article from live signal data.
Output: /app/content/knowledge/weekly-recap-YYYY-WXX.json

Usage:
  python3 scripts/gen_weekly_recap.py           # Generate for current week
  python3 scripts/gen_weekly_recap.py 2026-W08  # Generate for specific week
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Paths
DATA_DIR = Path(os.getenv("DATA_DIR", "/home/raven/smart-money-platform/data"))
if not DATA_DIR.exists():
    DATA_DIR = Path("/app/data")
CONTENT_DIR = Path(os.getenv("CONTENT_DIR", "/home/raven/meridian/content/knowledge"))
if not CONTENT_DIR.exists():
    CONTENT_DIR = Path("/app/content/knowledge")


def load_json(filename):
    """Load a JSON file from DATA_DIR."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return {}
    with open(filepath) as f:
        return json.load(f)


def get_week_range(iso_week: str = None):
    """Get start/end dates for a given ISO week (YYYY-WXX) or current week."""
    if iso_week:
        year, week = iso_week.split("-W")
        # Monday of that week
        start = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
    else:
        today = datetime.utcnow()
        start = today - timedelta(days=today.weekday())  # Monday
    
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start, end


def filter_by_date(items, date_field, start, end):
    """Filter items by date range."""
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    return [
        item for item in items
        if start_str <= (item.get(date_field) or "")[:10] <= end_str
    ]


def generate_recap(iso_week: str = None):
    """Generate a weekly recap article."""
    start, end = get_week_range(iso_week)
    week_str = start.strftime("%Y-W%W")
    week_display = f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"
    
    # Load all data sources
    congress = load_json("congress.json")
    ark = load_json("ark_trades.json")
    darkpool = load_json("darkpool.json")
    insiders = load_json("insiders.json")
    ranking = load_json("ranking_v3.json")
    if not ranking:
        ranking = load_json("ranking_v2.json")
    
    # Filter to this week
    congress_trades = filter_by_date(
        congress.get("trades", []), "transaction_date", start, end
    )
    ark_trades = filter_by_date(
        ark.get("trades", []), "date", start, end
    )
    darkpool_tickers = filter_by_date(
        darkpool.get("tickers", []), "date", start, end
    )
    insider_trades = filter_by_date(
        insiders.get("trades", []), "trade_date", start, end
    )
    
    # Get top signals for this week
    signals = ranking.get("signals", [])
    week_signals = filter_by_date(signals, "signal_date", start, end)
    top_signals = sorted(week_signals, key=lambda s: s.get("score", 0), reverse=True)[:10]
    
    # === Build content ===
    
    # Congress summary
    congress_buys = [t for t in congress_trades if t.get("type", "").lower() in ("purchase", "buy")]
    congress_sells = [t for t in congress_trades if t.get("type", "").lower() in ("sale", "sell", "sale_full", "sale_partial")]
    congress_top = {}
    for t in congress_buys:
        ticker = t.get("ticker", "")
        if ticker:
            congress_top[ticker] = congress_top.get(ticker, 0) + 1
    congress_top_sorted = sorted(congress_top.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # ARK summary
    ark_buys = [t for t in ark_trades if t.get("trade_type", "").lower() == "buy"]
    ark_sells = [t for t in ark_trades if t.get("trade_type", "").lower() == "sell"]
    
    # Dark pool summary  
    dp_top = sorted(darkpool_tickers, key=lambda d: abs(d.get("z_score", 0)), reverse=True)[:5]
    
    # Insider summary
    insider_buys = [t for t in insider_trades if (t.get("transaction_type") or "").lower() == "buy"]
    
    # Build markdown content
    sections = []
    
    # Hero section
    sections.append(f"# Weekly Smart Money Recap: {week_display}\n")
    sections.append(f"This week's smart money activity across all {len([s for s in ['congress', 'ark', 'darkpool', 'insider'] if locals().get(f'{s}_trades')])} tracked sources.\n")
    
    # Top Conviction Signals
    if top_signals:
        sections.append("## 🔥 Top Conviction Signals This Week\n")
        sections.append("Stocks where multiple smart money sources converge:\n")
        for i, sig in enumerate(top_signals[:5], 1):
            ticker = sig.get("ticker", "?")
            score = sig.get("score", 0)
            sources = sig.get("sources", [])
            direction = sig.get("direction", "").upper()
            source_str = ", ".join(s.title() for s in sources)
            sections.append(f"**{i}. {ticker}** — Score: {score:.0f}/100 ({direction})")
            sections.append(f"   Sources: {source_str} ({len(sources)} signals converging)\n")
    
    # Congress
    sections.append(f"## 🏛️ Congressional Trading\n")
    sections.append(f"**{len(congress_buys)} buys** and **{len(congress_sells)} sells** this week.\n")
    if congress_top_sorted:
        sections.append("Most-bought tickers by Congress members:")
        for ticker, count in congress_top_sorted:
            sections.append(f"- **{ticker}**: {count} member(s) buying")
        sections.append("")
    
    # ARK
    sections.append(f"## 🦅 ARK Invest Trades\n")
    sections.append(f"**{len(ark_buys)} buys** and **{len(ark_sells)} sells** across all ARK ETFs.\n")
    if ark_buys:
        # Group by ticker
        ark_buy_tickers = {}
        for t in ark_buys:
            tk = t.get("ticker", "")
            if tk:
                ark_buy_tickers.setdefault(tk, []).append(t.get("etf", ""))
        sections.append("Notable buys:")
        for ticker, etfs in sorted(ark_buy_tickers.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            etf_str = ", ".join(sorted(set(etfs)))
            sections.append(f"- **{ticker}** ({etf_str})")
        sections.append("")
    
    # Dark Pool
    sections.append(f"## 🌑 Dark Pool Anomalies\n")
    sections.append(f"**{len(darkpool_tickers)} tickers** with unusual dark pool activity.\n")
    if dp_top:
        sections.append("Highest z-score anomalies:")
        for d in dp_top:
            ticker = d.get("ticker", "?")
            zscore = d.get("z_score", 0)
            dpi = d.get("dpi", 0)
            sections.append(f"- **{ticker}**: z-score {zscore:.1f}, DPI {dpi:.1%}" if isinstance(dpi, float) else f"- **{ticker}**: z-score {zscore:.1f}")
        sections.append("")
    
    # Insider
    sections.append(f"## 👔 Insider Trading\n")
    sections.append(f"**{len(insider_buys)} insider buys** this week.\n")
    if insider_buys:
        # Top buys by value
        valued = sorted(insider_buys, key=lambda t: abs(t.get("value", 0) or 0), reverse=True)[:5]
        sections.append("Largest insider purchases:")
        for t in valued:
            ticker = t.get("ticker", "?")
            name = t.get("insider_name", t.get("owner", "Unknown"))
            value = t.get("value", 0) or 0
            title = t.get("insider_title", t.get("title", ""))
            val_str = f"${value:,.0f}" if value else "undisclosed"
            sections.append(f"- **{ticker}** — {name} ({title}) bought {val_str}")
        sections.append("")
    
    # Methodology note
    sections.append("---\n")
    sections.append("*Data sourced from SEC EDGAR, FINRA, and public filings. Conviction scores calculated using Meridian's V7 multi-source engine. [Learn more about our methodology](/knowledge/confluence-signals-explained).*")
    
    content_md = "\n".join(sections)
    
    # Build key takeaways
    takeaways = []
    if top_signals:
        top = top_signals[0]
        takeaways.append(f"Top conviction signal: {top['ticker']} with score {top.get('score',0):.0f}/100 from {len(top.get('sources',[]))} sources")
    takeaways.append(f"Congress: {len(congress_buys)} buys, {len(congress_sells)} sells")
    takeaways.append(f"ARK: {len(ark_buys)} buys, {len(ark_sells)} sells")
    takeaways.append(f"Dark pool: {len(darkpool_tickers)} anomalies detected")
    takeaways.append(f"Insider buying: {len(insider_buys)} open-market purchases")
    
    # Hero stat
    hero_stat = None
    if top_signals:
        hero_stat = {
            "value": str(len(top_signals)),
            "label": "High-conviction signals this week",
            "source": f"Meridian V7 Engine, {week_display}"
        }
    
    # Build article
    slug = f"weekly-recap-{week_str.lower()}"
    article = {
        "slug": slug,
        "title": f"Weekly Smart Money Recap: {week_display}",
        "subtitle": f"Congress trades, ARK moves, dark pool anomalies, and insider buying — all in one view.",
        "category": "weekly-recap",
        "signal_source": "all",
        "layer": "recurring",
        "tldr": f"This week saw {len(congress_buys)} congressional buys, {len(ark_buys)} ARK purchases, {len(darkpool_tickers)} dark pool anomalies, and {len(insider_buys)} insider buys. " + (f"Top conviction signal: {top_signals[0]['ticker']} ({top_signals[0].get('score',0):.0f}/100)." if top_signals else ""),
        "hero_stat": hero_stat,
        "content_md": content_md,
        "content_zh": f"本周聪明钱动向：国会{len(congress_buys)}笔买入、ARK {len(ark_buys)}笔买入、{len(darkpool_tickers)}只暗池异常、{len(insider_buys)}笔内部人买入。" + (f"最强信号：{top_signals[0]['ticker']}（{top_signals[0].get('score',0):.0f}/100）。" if top_signals else ""),
        "key_takeaways": takeaways,
        "related_articles": ["confluence-signals-explained", "congress-trading-alpha", "dark-pool-activity"],
        "seo": {
            "keywords": [
                f"smart money signals {start.strftime('%B %Y').lower()}",
                "weekly stock signals",
                "congress stock trades this week",
                "dark pool activity today",
                "insider buying this week",
                "smart money tracker",
            ],
            "description": f"Weekly smart money recap for {week_display}. Track Congress trades, ARK moves, dark pool anomalies, and insider buying all in one view."
        },
        "social": {
            "hook_en": f"This week: {len(congress_buys)} Congress buys, {len(ark_buys)} ARK trades, {len(darkpool_tickers)} dark pool anomalies. Here's where smart money is moving.",
            "hook_zh": f"本周聪明钱：国会{len(congress_buys)}笔买入、ARK {len(ark_buys)}笔操作、{len(darkpool_tickers)}只暗池异常。",
            "hashtags": ["#SmartMoney", "#CongressTrading", "#DarkPool", "#InsiderBuying", "#Meridian"]
        },
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    
    return slug, article


def main():
    iso_week = sys.argv[1] if len(sys.argv) > 1 else None
    slug, article = generate_recap(iso_week)
    
    output_path = CONTENT_DIR / f"{slug}.json"
    with open(output_path, "w") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated: {output_path}")
    print(f"   Title: {article['title']}")
    print(f"   Takeaways: {len(article['key_takeaways'])}")
    print(f"   Content: {len(article['content_md'])} chars")
    
    return article


if __name__ == "__main__":
    main()
