#!/usr/bin/env python3
"""
Cross-Signal Confluence Engine — PRD §2.3 Implementation

Core algorithm that detects when multiple smart money sources 
align on the same ticker within a time window (±7 days).

Signal Sources:
  1. Congress trades (Buy, amount ≥$15K, filed ≤45 days)    weight=1.0
  2. ARK trades (Buy, weight ≥1%, traded ≤30 days)          weight=1.0
  3. Dark Pool anomalies (Z≥2, DPI≥0.4, vol≥500K, ≤7 days)  weight=0.8
  4. 13F Institutions (New/Increased ≥10%, value≥$50M, ≤90d) weight=0.6

Scoring (PRD §2.3):
  Base_Score          = Σ(signal weights)
  Recency_Multiplier  = 1.0 - (days_since_last / 30)
  Signal_Count_Bonus  = 0.5 × (count - 1)
  Excess_Return_Bonus = min(congress_excess / 10, 2.0)
  Confluence_Score    = (Base × Recency) + Count_Bonus + Excess_Bonus
  Normalized_Score    = min(Confluence_Score / 5.0 × 10, 10)

Verification: PRD example → score = 8.46
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── Signal Definition ──────────────────────────────────────────────────


@dataclass
class RawSignal:
    """A single extracted signal from any source."""
    ticker: str
    source: str           # "congress" | "ark" | "darkpool" | "institution"
    direction: str        # "Bullish" | "Bearish"
    date: str             # YYYY-MM-DD
    weight: float         # Source weight (1.0, 0.8, 0.6)
    description: str      # Human-readable description
    raw_data: dict = field(default_factory=dict)  # Full original record


@dataclass
class ConfluenceResult:
    """A scored confluence signal for one ticker."""
    ticker: str
    score: float                    # Normalized 0-10
    direction: str                  # "Bullish" | "Bearish"
    sources: List[str]              # ["congress", "ark", "darkpool"]
    source_count: int
    signals: List[RawSignal]
    signal_date: str                # Date of most recent signal
    congress_score: float = 0.0
    ark_score: float = 0.0
    darkpool_score: float = 0.0
    institution_score: float = 0.0
    # Scoring breakdown
    base_score: float = 0.0
    recency_multiplier: float = 0.0
    signal_count_bonus: float = 0.0
    excess_return_bonus: float = 0.0
    raw_score: float = 0.0


# ── Signal Extraction ──────────────────────────────────────────────────


class SignalExtractor:
    """
    Extract qualifying signals from each data source.
    
    Each method reads the cached data and returns RawSignal objects
    that meet the PRD-defined criteria.
    """

    def __init__(self, reference_date: Optional[str] = None):
        """
        Args:
            reference_date: YYYY-MM-DD to use as "today". 
                          Defaults to actual today. Useful for testing.
        """
        if reference_date:
            self.today = datetime.strptime(reference_date, "%Y-%m-%d")
        else:
            self.today = datetime.now()

    def _days_ago(self, date_str: str) -> int:
        """Calculate days between date_str and today."""
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return (self.today - dt).days
        except (ValueError, TypeError):
            return 9999

    def extract_congress(self, data: dict) -> List[RawSignal]:
        """
        Extract Congress buy signals.
        
        Criteria (PRD §2.1):
        - trade_type == "Buy" (not Sell)
        - amount_max >= $15,000
        - Filed within last 45 days
        """
        signals = []
        for trade in data.get("trades", []):
            # Must be a buy
            if trade.get("trade_type") != "Buy":
                continue
            
            # Amount threshold
            amount_max = trade.get("amount_max", 0)
            if amount_max < 15000:
                continue
            
            # Recency: use filing_date if available, else transaction_date
            date = trade.get("filing_date") or trade.get("transaction_date", "")
            if self._days_ago(date) > 45:
                continue

            excess = trade.get("excess_return_pct")
            amount_range = trade.get("amount_range", "")
            rep = trade.get("representative", "")
            party = trade.get("party", "")
            
            signals.append(RawSignal(
                ticker=trade["ticker"],
                source="congress",
                direction="Bullish",
                date=trade.get("transaction_date", date),
                weight=1.0,
                description=f"{rep} ({party}) bought {amount_range}",
                raw_data={
                    "representative": rep,
                    "party": party,
                    "chamber": trade.get("chamber"),
                    "amount_min": trade.get("amount_min"),
                    "amount_max": amount_max,
                    "excess_return_pct": excess,
                },
            ))
        
        return signals

    def extract_ark(self, data: dict) -> List[RawSignal]:
        """
        Extract ARK buy signals.
        
        Criteria (PRD §2.1):
        - trade_type == "Buy"
        - weight_pct >= 1.0 (if available)
        - Trade within last 30 days
        """
        signals = []
        for trade in data.get("trades", []):
            if trade.get("trade_type") != "Buy":
                continue
            
            date = trade.get("date", "")
            if self._days_ago(date) > 30:
                continue

            # Weight threshold (skip if weight not available)
            weight = trade.get("weight_pct")
            if weight is not None and weight < 1.0:
                continue

            etf = trade.get("etf", "")
            shares = trade.get("shares", 0)
            change_type = trade.get("change_type", "")
            
            desc = f"ARK {etf} bought"
            if change_type == "NEW_POSITION":
                desc = f"ARK {etf} NEW position"
            
            signals.append(RawSignal(
                ticker=trade["ticker"],
                source="ark",
                direction="Bullish",
                date=date,
                weight=1.0,
                description=f"{desc} ({shares:,} shares)",
                raw_data={
                    "etf": etf,
                    "shares": shares,
                    "weight_pct": weight,
                    "change_type": change_type,
                    "change_pct": trade.get("change_pct"),
                },
            ))
        
        return signals

    def extract_darkpool(self, data: dict) -> List[RawSignal]:
        """
        Extract dark pool anomaly signals.
        
        Criteria (PRD §2.1):
        - Z-Score >= 2.0
        - DPI >= 0.4
        - Volume >= 500K shares/day
        - Anomaly within last 7 days
        """
        signals = []
        for entry in data.get("tickers", data.get("anomalies", [])):
            date = entry.get("date", "")
            if self._days_ago(date) > 7:
                continue
            
            z_score = entry.get("z_score", 0)
            if z_score < 2.0:
                continue
            
            dpi = entry.get("dpi", entry.get("off_exchange_pct", 0))
            # Normalize: if stored as percentage, convert
            if dpi and dpi > 1:
                dpi = dpi / 100.0
            if dpi < 0.4:
                continue
            
            volume = entry.get("total_volume", entry.get("off_exchange_volume", 0))
            if volume < 500_000:
                continue

            signals.append(RawSignal(
                ticker=entry.get("ticker", ""),
                source="darkpool",
                direction="Bullish",
                date=date,
                weight=0.8,
                description=f"DPI {dpi:.2f} (Z-score {z_score:.1f}σ)",
                raw_data={
                    "dpi": round(dpi, 4),
                    "z_score": round(z_score, 2),
                    "total_volume": volume,
                    "off_exchange_volume": entry.get("off_exchange_volume"),
                },
            ))
        
        return signals

    def extract_institutions(self, data: dict) -> List[RawSignal]:
        """
        Extract 13F institutional signals.
        
        Criteria (PRD §2.1):
        - New position OR increased >= 10% QoQ
        - Position value >= $50M
        - Filing within last 90 days
        """
        signals = []
        for filing in data.get("filings", []):
            filing_date = filing.get("filing_date", "")
            if self._days_ago(filing_date) > 90:
                continue
            
            fund_name = filing.get("fund_name", "")
            
            for holding in filing.get("holdings", []):
                value = holding.get("value", 0)
                if value < 50_000_000:
                    continue
                
                change_type = holding.get("change_type", "")
                change_pct = holding.get("change_pct", 0)
                
                # Only new positions or significant increases
                if change_type == "New":
                    pass  # Always include new positions
                elif change_type == "Increased" and abs(change_pct) >= 10:
                    pass  # Significant increase
                else:
                    continue
                
                ticker = holding.get("ticker") or ""
                issuer = holding.get("issuer", "")
                display = ticker or issuer
                
                if not display:
                    continue
                
                desc_action = "NEW position" if change_type == "New" else f"increased {change_pct:+.0f}%"
                
                signals.append(RawSignal(
                    ticker=ticker if ticker else issuer[:10],
                    source="institution",
                    direction="Bullish",
                    date=filing_date,
                    weight=0.6,
                    description=f"{fund_name} {desc_action} (${value/1e6:.0f}M)",
                    raw_data={
                        "fund_name": fund_name,
                        "value": value,
                        "shares": holding.get("shares"),
                        "change_type": change_type,
                        "change_pct": change_pct,
                        "pct_portfolio": holding.get("pct_portfolio"),
                    },
                ))
        
        return signals


# ── Confluence Engine ──────────────────────────────────────────────────


class CrossSignalEngine:
    """
    Core confluence detection and scoring engine.
    
    Pipeline:
    1. Extract signals from all sources
    2. Group by ticker
    3. Find tightest cluster within ±window_days
    4. Score using PRD §2.3 formula
    5. Return sorted ConfluenceResult list
    """

    def __init__(
        self,
        window_days: int = 7,
        max_possible_score: float = 5.0,
        min_score: float = 6.0,
        reference_date: Optional[str] = None,
    ):
        self.window_days = window_days
        self.max_possible_score = max_possible_score
        self.min_score = min_score
        self.extractor = SignalExtractor(reference_date=reference_date)
        self._reference_date = reference_date

    def _today(self) -> datetime:
        if self._reference_date:
            return datetime.strptime(self._reference_date, "%Y-%m-%d")
        return datetime.now()

    def extract_all_signals(
        self,
        congress_data: Optional[dict] = None,
        ark_data: Optional[dict] = None,
        darkpool_data: Optional[dict] = None,
        institution_data: Optional[dict] = None,
    ) -> List[RawSignal]:
        """Extract qualifying signals from all available sources."""
        all_signals = []
        
        if congress_data:
            signals = self.extractor.extract_congress(congress_data)
            logger.info(f"Congress: {len(signals)} qualifying signals")
            all_signals.extend(signals)
        
        if ark_data:
            signals = self.extractor.extract_ark(ark_data)
            logger.info(f"ARK: {len(signals)} qualifying signals")
            all_signals.extend(signals)
        
        if darkpool_data:
            signals = self.extractor.extract_darkpool(darkpool_data)
            logger.info(f"Dark Pool: {len(signals)} qualifying signals")
            all_signals.extend(signals)
        
        if institution_data:
            signals = self.extractor.extract_institutions(institution_data)
            logger.info(f"Institutions: {len(signals)} qualifying signals")
            all_signals.extend(signals)
        
        logger.info(f"Total: {len(all_signals)} signals from all sources")
        return all_signals

    def group_by_ticker(self, signals: List[RawSignal]) -> Dict[str, List[RawSignal]]:
        """Group signals by ticker symbol."""
        groups: Dict[str, List[RawSignal]] = {}
        for s in signals:
            ticker = s.ticker.upper().strip()
            if not ticker:
                continue
            if ticker not in groups:
                groups[ticker] = []
            groups[ticker].append(s)
        return groups

    def find_best_cluster(
        self, signals: List[RawSignal]
    ) -> List[RawSignal]:
        """
        Find the tightest cluster of signals within ±window_days.
        
        Strategy: Use each signal's date as an anchor, find which other
        signals fall within ±window_days. Return the cluster with the
        highest total weight.
        """
        if len(signals) <= 1:
            return signals

        best_cluster = signals[:1]
        best_weight = signals[0].weight

        for anchor in signals:
            try:
                anchor_dt = datetime.strptime(anchor.date[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
            
            cluster = []
            total_weight = 0
            for s in signals:
                try:
                    s_dt = datetime.strptime(s.date[:10], "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue
                
                if abs((s_dt - anchor_dt).days) <= self.window_days:
                    cluster.append(s)
                    total_weight += s.weight
            
            if total_weight > best_weight:
                best_cluster = cluster
                best_weight = total_weight

        return best_cluster

    def deduplicate_sources(self, signals: List[RawSignal]) -> List[RawSignal]:
        """
        Deduplicate signals of the same type.
        
        If multiple Congress members bought the same stock,
        keep the one with highest excess return (or most recent).
        Same for multiple ARK ETFs, etc.
        """
        by_source: Dict[str, List[RawSignal]] = {}
        for s in signals:
            if s.source not in by_source:
                by_source[s.source] = []
            by_source[s.source].append(s)
        
        deduped = []
        for source, source_signals in by_source.items():
            if source == "congress":
                # Keep all congress signals (multiple members = stronger signal)
                # but we'll only count weight once for scoring
                deduped.extend(source_signals)
            elif source == "ark":
                # Keep all ARK signals (different ETFs = independent decisions)
                deduped.extend(source_signals)
            else:
                # For darkpool/institution, keep the strongest signal
                best = max(source_signals, key=lambda s: s.raw_data.get("z_score", 0) or s.raw_data.get("value", 0) or 0)
                deduped.append(best)
        
        return deduped

    def score_cluster(self, ticker: str, signals: List[RawSignal]) -> ConfluenceResult:
        """
        Score a cluster of signals for one ticker using PRD §2.3 formula.
        
        Base_Score          = Σ(unique source weights)
        Recency_Multiplier  = 1.0 - (days_since_last / 30)
        Signal_Count_Bonus  = 0.5 × (unique_source_count - 1)
        Excess_Return_Bonus = min(max_congress_excess / 10, 2.0)
        Confluence_Score    = (Base × Recency) + Count_Bonus + Excess_Bonus
        Normalized_Score    = min(Score / max_possible × 10, 10)
        """
        today = self._today()

        # Unique sources and their weights
        source_weights = {}
        for s in signals:
            if s.source not in source_weights:
                source_weights[s.source] = s.weight
        
        # Base Score = sum of unique source weights
        base_score = sum(source_weights.values())

        # Days since most recent signal
        dates = []
        for s in signals:
            try:
                dates.append(datetime.strptime(s.date[:10], "%Y-%m-%d"))
            except (ValueError, TypeError):
                pass
        
        if dates:
            most_recent = max(dates)
            days_since_last = (today - most_recent).days
            signal_date = most_recent.strftime("%Y-%m-%d")
        else:
            days_since_last = 30
            signal_date = ""
        
        # Recency Multiplier (clamp to [0, 1])
        recency_multiplier = max(0, 1.0 - (days_since_last / 30))

        # Signal Count Bonus (based on unique source count)
        unique_source_count = len(source_weights)
        signal_count_bonus = 0.5 * (unique_source_count - 1)

        # Excess Return Bonus (from Congress data)
        congress_excess = 0.0
        for s in signals:
            if s.source == "congress":
                er = s.raw_data.get("excess_return_pct")
                if er is not None and er > congress_excess:
                    congress_excess = er
        excess_return_bonus = min(congress_excess / 10, 2.0)

        # Confluence Score
        raw_score = (base_score * recency_multiplier) + signal_count_bonus + excess_return_bonus
        
        # Normalized Score (0-10)
        normalized = min(raw_score / self.max_possible_score * 10, 10.0)

        # Per-source scores (for display)
        congress_score = source_weights.get("congress", 0.0) * recency_multiplier
        ark_score = source_weights.get("ark", 0.0) * recency_multiplier
        darkpool_score = source_weights.get("darkpool", 0.0) * recency_multiplier
        institution_score = source_weights.get("institution", 0.0) * recency_multiplier

        # Direction: mostly Bullish for buy signals
        direction = "Bullish"
        sources = sorted(source_weights.keys())

        return ConfluenceResult(
            ticker=ticker,
            score=round(normalized, 2),
            direction=direction,
            sources=sources,
            source_count=unique_source_count,
            signals=signals,
            signal_date=signal_date,
            congress_score=round(congress_score, 2),
            ark_score=round(ark_score, 2),
            darkpool_score=round(darkpool_score, 2),
            institution_score=round(institution_score, 2),
            base_score=round(base_score, 2),
            recency_multiplier=round(recency_multiplier, 3),
            signal_count_bonus=round(signal_count_bonus, 2),
            excess_return_bonus=round(excess_return_bonus, 2),
            raw_score=round(raw_score, 2),
        )

    def generate_signals(
        self,
        congress_data: Optional[dict] = None,
        ark_data: Optional[dict] = None,
        darkpool_data: Optional[dict] = None,
        institution_data: Optional[dict] = None,
        min_score: Optional[float] = None,
    ) -> List[ConfluenceResult]:
        """
        Main entry point — full pipeline.
        
        1. Extract signals from all sources
        2. Group by ticker
        3. Find best cluster per ticker
        4. Score each cluster
        5. Filter by min_score
        6. Return sorted by score descending
        """
        if min_score is None:
            min_score = self.min_score

        # Step 1: Extract
        all_signals = self.extract_all_signals(
            congress_data=congress_data,
            ark_data=ark_data,
            darkpool_data=darkpool_data,
            institution_data=institution_data,
        )

        if not all_signals:
            return []

        # Step 2: Group by ticker
        groups = self.group_by_ticker(all_signals)

        # Step 3 & 4: Cluster and score each ticker
        results = []
        for ticker, signals in groups.items():
            cluster = self.find_best_cluster(signals)
            cluster = self.deduplicate_sources(cluster)
            
            # Only score if >= 1 signal (single signals still get scored)
            if cluster:
                result = self.score_cluster(ticker, cluster)
                results.append(result)

        # Step 5: Filter by minimum score
        results = [r for r in results if r.score >= min_score]

        # Step 6: Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        
        logger.info(
            f"Generated {len(results)} confluence signals "
            f"(from {len(groups)} tickers, min_score={min_score})"
        )

        return results

    def to_json(self, results: List[ConfluenceResult]) -> dict:
        """Convert results to JSON-serializable dict for cache."""
        signals_out = []
        for r in results:
            signals_out.append({
                "ticker": r.ticker,
                "score": r.score,
                "direction": r.direction,
                "sources": r.sources,
                "source_count": r.source_count,
                "signal_date": r.signal_date,
                "congress_score": r.congress_score,
                "ark_score": r.ark_score,
                "darkpool_score": r.darkpool_score,
                "institution_score": r.institution_score,
                "details": [
                    {
                        "source": s.source,
                        "description": s.description,
                        "date": s.date,
                        "weight": s.weight,
                    }
                    for s in r.signals
                ],
                "scoring": {
                    "base_score": r.base_score,
                    "recency_multiplier": r.recency_multiplier,
                    "signal_count_bonus": r.signal_count_bonus,
                    "excess_return_bonus": r.excess_return_bonus,
                    "raw_score": r.raw_score,
                },
            })

        return {
            "signals": signals_out,
            "metadata": {
                "schema_version": "1.0.0",
                "total_count": len(signals_out),
                "high_confidence": sum(1 for r in results if r.score >= 8),
                "avg_score": round(
                    sum(r.score for r in results) / len(results), 2
                ) if results else 0,
                "last_updated": datetime.now().isoformat(),
            },
        }
