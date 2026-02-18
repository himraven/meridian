#!/usr/bin/env python3
"""
Daily Smart Money Signal Digest

Generates a Telegram-friendly summary of today's top signals.
Designed to run after all data collectors have completed.

Output: JSON with 'message' field for Telegram, 'has_alerts' boolean.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent / "data"
SIGNALS_DIR = Path("./data/signals")
STATE_FILE = Path(__file__).parent / ".digest_state.json"


def load_json(path: Path) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_state() -> dict:
    return load_json(STATE_FILE)


def save_state(state: dict):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_v2_signals(min_score: int = 30) -> list:
    """Load v2 signals above threshold."""
    data = load_json(DATA_DIR / "signals_v2.json")
    signals = data.get("signals", [])
    return [s for s in signals if s.get("score", 0) >= min_score]


def get_hk_signals() -> dict:
    """Load HK VMQ state."""
    return load_json(SIGNALS_DIR / "hk_daily_state.json")


def get_hk_portfolio() -> list:
    """Load HK portfolio positions."""
    data = load_json(SIGNALS_DIR / "paper_portfolio.json")
    return [p for p in data.get("positions", []) if p.get("market") == "HK" and p.get("status") == "open"]


def get_us_portfolio() -> list:
    """Load US portfolio positions."""
    data = load_json(SIGNALS_DIR / "paper_portfolio.json")
    return [p for p in data.get("positions", []) if p.get("market", "US") not in ("HK", "CN") and p.get("status") == "open"]


def get_cn_metrics() -> dict:
    """Load CN 12x30 strategy metrics."""
    return load_json(SIGNALS_DIR / "cn-12x30" / "strategy_metrics_12x30.json")


def detect_new_signals(current: list, prev_tickers: list) -> list:
    """Find signals that weren't in previous digest."""
    prev_set = set(prev_tickers)
    return [s for s in current if s["ticker"] not in prev_set]


def format_digest(today: str) -> dict:
    """Generate the daily digest message."""
    
    state = load_state()
    prev_tickers = state.get("last_top_tickers", [])
    
    # === US Smart Money v2 ===
    signals = get_v2_signals(min_score=30)
    top_signals = signals[:10]
    high_conviction = [s for s in signals if s["score"] >= 60]
    multi_source = [s for s in signals if s["source_count"] >= 2]
    new_signals = detect_new_signals(high_conviction, prev_tickers)
    
    # === HK ===
    hk_state = get_hk_signals()
    hk_picks = hk_state.get("picks", [])
    hk_portfolio = get_hk_portfolio()
    
    # === Portfolio P&L ===
    us_portfolio = get_us_portfolio()
    us_winners = [p for p in us_portfolio if (p.get("pnl_pct") or 0) > 3]
    us_losers = [p for p in us_portfolio if (p.get("pnl_pct") or 0) < -3]
    
    # === CN ===
    cn_metrics = get_cn_metrics()
    
    # === Build Message ===
    lines = []
    lines.append(f"📊 **Smart Money 每日信号** | {today}")
    lines.append("")
    
    has_alerts = False
    
    # --- New High Conviction Signals ---
    if new_signals:
        has_alerts = True
        lines.append("🔥 **新增高信心信号**")
        for s in new_signals[:5]:
            sources = "+".join(s["sources"]).upper()
            lines.append(f"  • **{s['ticker']}** {s['score']:.0f}分 [{sources}] {s.get('company', '')[:20]}")
            if s.get("details"):
                for d in s["details"][:2]:
                    lines.append(f"    ↳ {d['description'][:60]}")
        lines.append("")
    
    # --- Multi-Source Signals ---
    if multi_source:
        lines.append(f"🎯 **多源共振** ({len(multi_source)})")
        for s in multi_source[:5]:
            sources = "+".join(s["sources"]).upper()
            score_parts = []
            if s.get("congress_score"): score_parts.append(f"GOV:{s['congress_score']:.0f}")
            if s.get("ark_score"): score_parts.append(f"ARK:{s['ark_score']:.0f}")
            if s.get("darkpool_score"): score_parts.append(f"DP:{s['darkpool_score']:.0f}")
            if s.get("institution_score"): score_parts.append(f"13F:{s['institution_score']:.0f}")
            lines.append(f"  • **{s['ticker']}** {s['score']:.0f}分 [{' | '.join(score_parts)}]")
        lines.append("")
    
    # --- Top 5 by Score ---
    lines.append(f"📈 **Top 5 信号** (共{len(signals)})")
    for s in top_signals[:5]:
        sources = "+".join(s["sources"]).upper()
        lines.append(f"  {s['score']:3.0f} | {s['ticker']:6s} | {sources:15s} | {s.get('company', '')[:25]}")
    lines.append("")
    
    # --- Portfolio Alerts ---
    if us_winners or us_losers:
        lines.append("💼 **持仓异动**")
        for p in sorted(us_winners, key=lambda x: -(x.get("pnl_pct") or 0))[:3]:
            lines.append(f"  🟢 {p['ticker']} +{p['pnl_pct']:.1f}%")
        for p in sorted(us_losers, key=lambda x: (x.get("pnl_pct") or 0))[:3]:
            lines.append(f"  🔴 {p['ticker']} {p['pnl_pct']:.1f}%")
        if us_winners or us_losers:
            has_alerts = True
        lines.append("")
    
    # --- HK Summary ---
    if hk_picks:
        lines.append(f"🇭🇰 **港股 VMQ Top 3** ({hk_state.get('date', '')})")
        for p in hk_picks[:3]:
            lines.append(f"  • {p['ticker']} VMQ={p.get('vmq_score', 0):.1f} | {p.get('name', '')[:20]}")
        lines.append("")
    
    # --- CN Summary ---
    if cn_metrics:
        ret = cn_metrics.get("total_return", 0)
        sharpe = cn_metrics.get("sharpe", 0)
        # total_return is already in percentage form (e.g., 237.25 = +237.25%)
        lines.append(f"🇨🇳 **CN 12×30** 收益{ret:+.1f}% | Sharpe {sharpe:.2f}")
        lines.append("")
    
    # --- Footer ---
    lines.append(f"🔗 meridianfin.io/signals | meridianfin.io/portfolio")
    lines.append("— Meridian 📊")
    
    message = "\n".join(lines)
    
    # Save state
    save_state({
        "last_run": today,
        "last_top_tickers": [s["ticker"] for s in high_conviction],
        "total_signals": len(signals),
        "high_conviction_count": len(high_conviction),
    })
    
    return {
        "message": message,
        "has_alerts": has_alerts,
        "stats": {
            "total_signals": len(signals),
            "high_conviction": len(high_conviction),
            "multi_source": len(multi_source),
            "new_signals": len(new_signals),
        }
    }


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    result = format_digest(today)
    
    print(result["message"])
    print("\n---")
    print(f"Stats: {json.dumps(result['stats'], indent=2)}")
    print(f"Has alerts: {result['has_alerts']}")
