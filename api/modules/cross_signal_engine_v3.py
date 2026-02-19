#!/usr/bin/env python3
"""
Smart Money Signal Engine V3 — V7 Ranking Algorithm

Builds on V2's per-source conviction scores and applies the V7 ranking algorithm,
which measures directional alignment and signal confluence.

V7 Key Improvements over V2:
- Direction detection: sources that agree on direction boost each other
- Opposing signals create penalties (not just ignored)
- Neutral sources (dark pool, institutions, short interest) are discounted by 0.6x
- Cap system prevents passive-only or single-active-source tickers from over-ranking
- Diminishing-returns bonus for 3rd, 4th... additional sources

Usage:
    from api.modules.cross_signal_engine_v3 import rank_v7
    ranked = rank_v7(v2_signals, data_dir)
"""

import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── V7 Constants ─────────────────────────────────────────────────────

WEIGHTS: Dict[str, int] = {
    "congress": 20,
    "insider": 20,
    "ark": 15,
    "darkpool": 15,
    "institution": 10,
    "superinvestor": 10,
    "short_interest": 10,
}

# "Active" sources require deliberate human capital allocation decisions
ACTIVE_SOURCES = {"congress", "insider", "ark", "darkpool", "institution"}

# These sources never have meaningful directional information
ALWAYS_NEUTRAL = {"darkpool", "institution", "short_interest"}

NEUTRAL_BASE_DISCOUNT = 0.6


# ── Direction Detection ───────────────────────────────────────────────

def _detect_directions(data_dir: Path) -> Dict[str, Dict[str, str]]:
    """
    Detect per-ticker direction for each directional source from raw trade files.

    Direction is detected by comparing buy vs sell counts:
    - congress:       trade_type contains "Purchase" → buy, "Sell"/"Sale" → sell
    - ark:            trade_type == "Buy" → buy, "Sell" → sell
    - insider:        transaction_type == "Buy" → buy, "Sale"/"Sell" → sell
    - superinvestor:  activity_type in ("Buy", "Add") → buy, ("Sell", "Reduce") → sell

    Sources in ALWAYS_NEUTRAL (darkpool, institution, short_interest) are always
    returned as "neutral" — direction detection is skipped for them.

    Returns:
        {ticker: {source: direction}}  where direction ∈ {"bullish", "bearish", "neutral"}
    """
    directions: Dict[str, Dict[str, str]] = {}

    def ensure_ticker(ticker: str) -> None:
        if ticker not in directions:
            directions[ticker] = {}

    def resolve_direction(counts: Dict[str, int]) -> str:
        if counts["buy"] > counts["sell"]:
            return "bullish"
        elif counts["sell"] > counts["buy"]:
            return "bearish"
        return "neutral"

    # ── Congress ────────────────────────────────────────────────────
    congress_file = data_dir / "congress.json"
    if congress_file.exists():
        try:
            with open(congress_file) as f:
                data = json.load(f)
            trade_counts: Dict[str, Dict[str, int]] = {}
            for trade in data.get("trades", []):
                ticker = (trade.get("ticker") or "").upper().strip()
                if not ticker:
                    continue
                trade_type = trade.get("trade_type", "")
                if ticker not in trade_counts:
                    trade_counts[ticker] = {"buy": 0, "sell": 0}
                if "Purchase" in trade_type or trade_type == "Buy":
                    trade_counts[ticker]["buy"] += 1
                elif "Sell" in trade_type or "Sale" in trade_type:
                    trade_counts[ticker]["sell"] += 1
            for ticker, counts in trade_counts.items():
                ensure_ticker(ticker)
                directions[ticker]["congress"] = resolve_direction(counts)
        except Exception as e:
            logger.warning(f"Direction detection failed for congress: {e}")

    # ── ARK ─────────────────────────────────────────────────────────
    ark_file = data_dir / "ark_trades.json"
    if ark_file.exists():
        try:
            with open(ark_file) as f:
                data = json.load(f)
            trade_counts = {}
            for trade in data.get("trades", []):
                ticker = (trade.get("ticker") or "").upper().strip()
                if not ticker:
                    continue
                trade_type = trade.get("trade_type", "")
                if ticker not in trade_counts:
                    trade_counts[ticker] = {"buy": 0, "sell": 0}
                if trade_type == "Buy":
                    trade_counts[ticker]["buy"] += 1
                elif trade_type == "Sell":
                    trade_counts[ticker]["sell"] += 1
            for ticker, counts in trade_counts.items():
                ensure_ticker(ticker)
                directions[ticker]["ark"] = resolve_direction(counts)
        except Exception as e:
            logger.warning(f"Direction detection failed for ark: {e}")

    # ── Insiders ─────────────────────────────────────────────────────
    insiders_file = data_dir / "insiders.json"
    if insiders_file.exists():
        try:
            with open(insiders_file) as f:
                data = json.load(f)
            trade_counts = {}
            for trade in data.get("trades", []):
                ticker = (trade.get("ticker") or "").upper().strip()
                if not ticker:
                    continue
                tx_type = trade.get("transaction_type", "")
                if ticker not in trade_counts:
                    trade_counts[ticker] = {"buy": 0, "sell": 0}
                if tx_type == "Buy":
                    trade_counts[ticker]["buy"] += 1
                elif tx_type in ("Sale", "Sell"):
                    trade_counts[ticker]["sell"] += 1
            for ticker, counts in trade_counts.items():
                ensure_ticker(ticker)
                directions[ticker]["insider"] = resolve_direction(counts)
        except Exception as e:
            logger.warning(f"Direction detection failed for insider: {e}")

    # ── Superinvestors ──────────────────────────────────────────────
    superinvestors_file = data_dir / "superinvestors.json"
    if superinvestors_file.exists():
        try:
            with open(superinvestors_file) as f:
                data = json.load(f)
            # Prefer aggregate manager counts; fall back to per_manager counts
            agg_counts: Dict[str, Dict[str, int]] = {}
            per_manager_counts: Dict[str, Dict[str, int]] = {}

            for entry in data.get("activity", []):
                ticker = (entry.get("ticker") or "").upper().strip()
                if not ticker:
                    continue
                activity_type = entry.get("activity_type", "")
                source = entry.get("source", "")
                manager_count = entry.get("manager_count", 1)

                if source == "aggregate":
                    if ticker not in agg_counts:
                        agg_counts[ticker] = {"buy": 0, "sell": 0}
                    if activity_type in ("Buy", "Add"):
                        agg_counts[ticker]["buy"] = max(
                            agg_counts[ticker]["buy"], manager_count
                        )
                    elif activity_type in ("Sell", "Reduce"):
                        agg_counts[ticker]["sell"] = max(
                            agg_counts[ticker]["sell"], manager_count
                        )
                elif source == "per_manager":
                    if ticker not in per_manager_counts:
                        per_manager_counts[ticker] = {"buy": 0, "sell": 0}
                    if activity_type in ("Buy", "Add"):
                        per_manager_counts[ticker]["buy"] += 1
                    elif activity_type in ("Sell", "Reduce"):
                        per_manager_counts[ticker]["sell"] += 1

            all_si_tickers = set(list(agg_counts.keys()) + list(per_manager_counts.keys()))
            for ticker in all_si_tickers:
                ensure_ticker(ticker)
                counts = agg_counts.get(ticker) or per_manager_counts.get(ticker, {"buy": 0, "sell": 0})
                directions[ticker]["superinvestor"] = resolve_direction(counts)
        except Exception as e:
            logger.warning(f"Direction detection failed for superinvestor: {e}")

    return directions


# ── V7 Scoring Algorithm ──────────────────────────────────────────────

def _score_v7(
    ticker: str,
    source_convictions: Dict[str, float],
    ticker_directions: Dict[str, str],
) -> Tuple[float, dict]:
    """
    Apply V7 ranking algorithm for a single ticker.

    Args:
        ticker:             Ticker symbol (for logging)
        source_convictions: {source: conviction_score (0-100)}
        ticker_directions:  {source: direction} from _detect_directions()

    Returns:
        (v7_score, breakdown_dict)
    """
    # Only process sources with a non-zero conviction score
    sources = {src: conv for src, conv in source_convictions.items() if conv > 0}

    if not sources:
        return 0.0, {"dominant": "none", "contributions": []}

    # Assign direction per source: always_neutral overrides detected direction
    directions: Dict[str, str] = {}
    for src in sources:
        if src in ALWAYS_NEUTRAL:
            directions[src] = "neutral"
        else:
            directions[src] = ticker_directions.get(src, "neutral")

    # ── Step 1: Determine dominant direction ─────────────────────────
    dir_votes: Dict[str, float] = {"bullish": 0.0, "bearish": 0.0}
    for src, conv in sources.items():
        d = directions[src]
        if d in dir_votes:
            dir_votes[d] += WEIGHTS.get(src, 10) * conv

    if dir_votes["bullish"] == 0 and dir_votes["bearish"] == 0:
        dominant = "none"
    elif dir_votes["bullish"] >= dir_votes["bearish"]:
        dominant = "bullish"
    else:
        dominant = "bearish"

    # ── Step 2: Classify contributions ──────────────────────────────
    contributions = []
    for src, conv in sources.items():
        weight = WEIGHTS.get(src, 10)
        d = directions[src]

        if d == "neutral" or dominant == "none":
            effective_conviction = conv * NEUTRAL_BASE_DISCOUNT
            contribution = weight * effective_conviction / 100
            status = "neutral"
        elif d == dominant:
            effective_conviction = conv
            contribution = weight * conv / 100
            status = "aligned"
        else:
            # Opposing: negative contribution, excluded from positive sorting
            effective_conviction = 0.0
            contribution = -(weight * conv / 100 * 0.7)
            status = "opposing"

        contributions.append({
            "source": src,
            "weight": weight,
            "conviction": conv,
            "effective_conviction": effective_conviction,
            "contribution": contribution,
            "status": status,
            "direction": d,
        })

    # ── Step 3: Base score from top-2 positive contributions ─────────
    positive = sorted(
        [c for c in contributions if c["status"] in ("aligned", "neutral")],
        key=lambda c: c["effective_conviction"],
        reverse=True,
    )
    opposing = [c for c in contributions if c["status"] == "opposing"]

    if not positive:
        return 0.0, {
            "dominant": dominant,
            "dir_votes": dir_votes,
            "base": 0,
            "extra": 0,
            "dir_bonus": 0,
            "penalty": round(sum(abs(c["contribution"]) for c in opposing), 2),
            "cap": 50,
            "aligned_active": 0,
            "aligned_passive": 0,
            "contributions": _format_contributions(contributions),
        }

    top2 = positive[:2]
    remaining = positive[2:]

    top2_contrib_sum = sum(c["contribution"] for c in top2)
    top2_weight_sum = sum(c["weight"] for c in top2)
    base = (top2_contrib_sum / top2_weight_sum * 100) if top2_weight_sum > 0 else 0

    # ── Step 4: Extra source bonus (diminishing returns) ─────────────
    rates = [0.5, 0.3, 0.15, 0.1]
    extra = 0.0
    for i, c in enumerate(remaining):
        rate = rates[i] if i < len(rates) else rates[-1]
        extra += c["contribution"] * rate

    # ── Step 5: Direction alignment bonus ────────────────────────────
    aligned_active = sum(
        1 for c in contributions
        if c["status"] == "aligned" and c["source"] in ACTIVE_SOURCES
    )
    aligned_passive = sum(
        1 for c in contributions
        if c["status"] == "aligned" and c["source"] not in ACTIVE_SOURCES
    )
    dir_bonus = max(aligned_active - 1, 0) * 6 + aligned_passive * 2

    # ── Step 6: Penalty from opposing ────────────────────────────────
    penalty = sum(abs(c["contribution"]) for c in opposing)

    # ── Step 7: Cap by source count ────────────────────────────────
    # Uses BOTH aligned_active and total_sources to set cap
    # This ensures multi-source tickers aren't penalized just because
    # direction detection couldn't determine alignment (e.g., mixed buy/sell)
    total_sources = len([c for c in contributions if c["status"] != "opposing"])
    cap_by_aligned = {0: 40, 1: 55, 2: 85, 3: 95}.get(aligned_active, 100)
    cap_by_total = {1: 45, 2: 65, 3: 80, 4: 92, 5: 97}.get(min(total_sources, 5), 100)
    cap = max(cap_by_aligned, cap_by_total)  # take the more generous cap

    # ── Step 8: Confluence multiplier (multi-source bonus) ──────────
    # More sources = higher multiplier, smooth stepped curve
    # This is Meridian's core value prop: signal convergence
    _confluence_mult = {1: 1.0, 2: 1.08, 3: 1.18, 4: 1.28, 5: 1.35, 6: 1.40, 7: 1.40}
    confluence = _confluence_mult.get(min(total_sources, 7), 1.40)

    # ── Final score ──────────────────────────────────────────────────
    raw_score = (base + extra + dir_bonus - penalty) * confluence
    score = min(float(cap), max(0.0, raw_score))

    breakdown = {
        "dominant": dominant,
        "dir_votes": {k: round(v, 2) for k, v in dir_votes.items()},
        "base": round(base, 2),
        "extra": round(extra, 2),
        "dir_bonus": round(dir_bonus, 2),
        "confluence_multiplier": confluence,
        "total_sources": total_sources,
        "penalty": round(penalty, 2),
        "cap": cap,
        "aligned_active": aligned_active,
        "aligned_passive": aligned_passive,
        "contributions": _format_contributions(contributions),
    }

    return round(score, 1), breakdown


def _format_contributions(contributions: list) -> list:
    """Serialize contribution dicts for JSON output."""
    return [
        {
            "source": c["source"],
            "weight": c["weight"],
            "conviction": c["conviction"],
            "effective_conviction": round(c["effective_conviction"], 2),
            "contribution": round(c["contribution"], 2),
            "status": c["status"],
            "direction": c["direction"],
        }
        for c in contributions
    ]


# ── Public API ───────────────────────────────────────────────────────

def rank_v7(
    v2_results: List[dict],
    data_dir: Path,
) -> List[dict]:
    """
    Apply V7 ranking algorithm on top of V2 per-source conviction scores.

    Reads raw trade files from data_dir to detect per-ticker directional signals,
    then applies the V7 confluence-and-direction algorithm to produce a final score.

    Args:
        v2_results: List of signal dicts from SmartMoneyEngineV2.to_json()
        data_dir:   Path to data directory containing raw JSON files

    Returns:
        List of ranked ticker dicts sorted by V7 score descending.
        Each dict includes V7 score, V2 score, per-source convictions, and breakdown.
    """
    logger.info("V7: Detecting directions from raw trade data...")
    directions = _detect_directions(data_dir)
    logger.info(f"V7: Got directions for {len(directions)} tickers")

    ranked = []
    for signal in v2_results:
        ticker = signal.get("ticker", "")
        if not ticker:
            continue

        # Extract per-source conviction scores from V2 output
        source_convictions = {
            "congress":      signal.get("congress_score", 0),
            "ark":           signal.get("ark_score", 0),
            "darkpool":      signal.get("darkpool_score", 0),
            "institution":   signal.get("institution_score", 0),
            "insider":       signal.get("insider_score", 0),
            "superinvestor": signal.get("superinvestor_score", 0),
            "short_interest":signal.get("short_interest_score", 0),
        }

        ticker_directions = directions.get(ticker, {})
        v7_score, breakdown = _score_v7(ticker, source_convictions, ticker_directions)

        # Compute multi_source_bonus-equivalent for UI compatibility
        multi_source_bonus = round(
            breakdown.get("extra", 0) + breakdown.get("dir_bonus", 0), 1
        )

        ranked.append({
            # Identity
            "ticker":       ticker,
            "company":      signal.get("company", ""),
            # Scores
            "score":        v7_score,
            "v2_score":     signal.get("score", 0),
            # Direction
            "direction":    breakdown.get("dominant", "none"),
            # Source metadata (same as V2)
            "sources":      signal.get("sources", []),
            "source_count": signal.get("source_count", 0),
            "signal_date":  signal.get("signal_date", ""),
            # Per-source conviction scores
            "congress_score":       signal.get("congress_score", 0),
            "ark_score":            signal.get("ark_score", 0),
            "darkpool_score":       signal.get("darkpool_score", 0),
            "institution_score":    signal.get("institution_score", 0),
            "insider_score":        signal.get("insider_score", 0),
            "superinvestor_score":  signal.get("superinvestor_score", 0),
            "short_interest_score": signal.get("short_interest_score", 0),
            # V7-specific fields
            "multi_source_bonus": multi_source_bonus,
            "max_conviction":     signal.get("max_conviction", 0),
            "v7_breakdown":       breakdown,
            # Signal details from V2
            "details": signal.get("details", []),
        })

    # Sort by V7 score descending, then by source count, then alphabetically
    ranked.sort(key=lambda r: (-r["score"], -r["source_count"], r["ticker"]))

    logger.info(f"V7: Ranked {len(ranked)} tickers")
    return ranked


def generate_ranking_v3(
    data_dir: Path,
    min_score: float = 0,
) -> dict:
    """
    Full pipeline: load ranking_v2.json → apply V7 → return ranking_v3 structure.

    This is the convenience entry point used by signal_refresh.py.

    Args:
        data_dir:  Path to data directory
        min_score: Minimum V7 score to include in output

    Returns:
        Dict with "signals" list and "metadata" dict — same structure as ranking_v2.json
    """
    ranking_v2_file = data_dir / "ranking_v2.json"
    if not ranking_v2_file.exists():
        logger.error("ranking_v2.json not found — cannot generate V3 ranking")
        return {"signals": [], "metadata": {"engine": "v3", "total": 0, "error": "ranking_v2.json missing"}}

    with open(ranking_v2_file) as f:
        v2_data = json.load(f)

    v2_signals = v2_data.get("signals", [])
    logger.info(f"V7: Loaded {len(v2_signals)} signals from ranking_v2.json")

    ranked = rank_v7(v2_signals, data_dir)

    # Apply min_score filter
    if min_score > 0:
        ranked = [r for r in ranked if r["score"] >= min_score]

    return {
        "signals": ranked,
        "metadata": {
            "engine": "v3",
            "algorithm": "v7",
            "total": len(ranked),
            "last_updated": datetime.now().isoformat(),
            "v2_total": len(v2_signals),
        },
    }


# ── CLI entry point ──────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
    output_file = data_dir / "ranking_v3.json"

    result = generate_ranking_v3(data_dir)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)

    signals = result["signals"]
    print(f"\n{'='*55}")
    print(f"V7 Ranking Engine — {len(signals)} tickers ranked")
    print(f"Output: {output_file}")
    print(f"\nTop 15:")
    print(f"{'#':>3}  {'Ticker':<7} {'V7':>5}  {'V2':>5}  {'Dir':<9}  Sources")
    print(f"{'─'*55}")
    for i, s in enumerate(signals[:15], 1):
        sources_str = ",".join(s.get("sources", []))
        print(
            f"{i:>3}. {s['ticker']:<7} {s['score']:>5.1f}  "
            f"{s['v2_score']:>5.1f}  {s['direction']:<9}  {sources_str}"
        )
