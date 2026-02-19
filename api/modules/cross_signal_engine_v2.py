#!/usr/bin/env python3
"""
Smart Money Signal Engine v2 — Conviction-Based Scoring

v1 problem: Multi-source confluence rarely fires (sources don't overlap on same ticker).
v2 solution: Score signal STRENGTH within each source, then aggregate.

Each source gets a conviction score 0-100:
  - Congress:    amount × recency × member count × excess return
  - ARK:         fund count × shares × weight × position type (NEW = bonus)
  - Dark Pool:   z_score × DPI × volume
  - Institutions: position value × change % × fund prestige
  - Insiders:    value × recency × cluster size × title seniority

Final score = max(source_conviction) + multi_source_bonus
Multi-source bonus: 20 points per additional source (still rewarded, not required)

Output: 0-100 scale, meaningful differentiation for single-source signals.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SignalDetail:
    """Individual signal event."""
    source: str
    ticker: str
    direction: str
    date: str
    description: str
    conviction: float  # 0-100 within source
    raw_data: dict = field(default_factory=dict)


@dataclass
class SmartMoneySignal:
    """Scored smart money signal for one ticker."""
    ticker: str
    company: str
    score: float              # 0-100 final score
    direction: str
    sources: List[str]
    source_count: int
    signal_date: str          # Most recent signal date
    
    # Per-source conviction (0-100)
    congress_conviction: float = 0.0
    ark_conviction: float = 0.0
    darkpool_conviction: float = 0.0
    institution_conviction: float = 0.0
    insider_conviction: float = 0.0
    
    # Breakdown
    max_conviction: float = 0.0
    multi_source_bonus: float = 0.0
    recency_factor: float = 0.0
    
    details: List[SignalDetail] = field(default_factory=list)


class SmartMoneyEngineV2:
    """
    v2 engine: conviction-based single-source scoring + multi-source bonus.
    """

    # Amount ranges from congress data → approximate dollar values
    AMOUNT_MAP = {
        "$1,001 - $15,000": 8000,
        "$15,001 - $50,000": 32500,
        "$50,001 - $100,000": 75000,
        "$100,001 - $250,000": 175000,
        "$250,001 - $500,000": 375000,
        "$500,001 - $1,000,000": 750000,
        "$1,000,001 - $5,000,000": 3000000,
        "$5,000,001 - $25,000,000": 15000000,
        "$25,000,001 - $50,000,000": 37500000,
        "Over $50,000,000": 75000000,
    }

    def __init__(self, reference_date: Optional[str] = None):
        if reference_date:
            self.today = datetime.strptime(reference_date, "%Y-%m-%d")
        else:
            self.today = datetime.now()
    
    def _days_ago(self, date_str: str) -> int:
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            return max(0, (self.today - dt).days)
        except (ValueError, TypeError):
            return 9999

    def _recency_decay(self, days: int, half_life: int = 14) -> float:
        """Exponential decay: 1.0 at day 0, 0.5 at half_life, ~0 at 3× half_life."""
        import math
        return math.exp(-0.693 * days / half_life)
    
    def _parse_amount(self, amount_range: str, amount_max: float = 0) -> float:
        """Parse congress amount range to approximate dollar value."""
        if amount_max and amount_max > 0:
            return amount_max
        return self.AMOUNT_MAP.get(amount_range, 0)

    # ── Source-Specific Conviction Scoring ──────────────────────────

    def score_congress(self, trades: list) -> List[SignalDetail]:
        """
        Congress conviction scoring:
        - Amount tier: $15K=10, $50K=25, $100K=40, $250K=55, $500K=70, $1M+=85
        - Recency: exponential decay (14-day half-life)
        - Excess return bonus: up to +15
        - Multiple members buying same stock: +10 per additional member
        """
        if not trades:
            return []
        
        signals_by_ticker: Dict[str, List[dict]] = {}
        for t in trades:
            trade_type = t.get("trade_type", "")
            if "Purchase" not in trade_type and trade_type != "Buy":
                continue
            
            date = t.get("filing_date") or t.get("transaction_date", "")
            if self._days_ago(date) > 60:
                continue
            
            ticker = (t.get("ticker") or "").upper().strip()
            if not ticker:
                continue
            
            if ticker not in signals_by_ticker:
                signals_by_ticker[ticker] = []
            signals_by_ticker[ticker].append(t)
        
        results = []
        for ticker, ticker_trades in signals_by_ticker.items():
            # Best trade (highest amount)
            amounts = []
            for t in ticker_trades:
                amt = self._parse_amount(t.get("amount_range", ""), t.get("amount_max", 0))
                amounts.append(amt)
            
            max_amount = max(amounts) if amounts else 0
            
            # Amount tier score (0-85)
            if max_amount >= 5_000_000: amount_score = 85
            elif max_amount >= 1_000_000: amount_score = 70
            elif max_amount >= 500_000: amount_score = 55
            elif max_amount >= 250_000: amount_score = 45
            elif max_amount >= 100_000: amount_score = 35
            elif max_amount >= 50_000: amount_score = 25
            elif max_amount >= 15_000: amount_score = 15
            else: amount_score = 10
            
            # Recency
            dates = [t.get("transaction_date") or t.get("filing_date", "") for t in ticker_trades]
            days = min(self._days_ago(d) for d in dates if d)
            recency = self._recency_decay(days)
            
            # Excess return bonus
            excess_bonus = 0
            for t in ticker_trades:
                er = t.get("excess_return_pct")
                if er and er > 0:
                    excess_bonus = max(excess_bonus, min(er * 1.5, 15))
            
            # Multi-member bonus
            unique_members = len(set(t.get("representative", "") for t in ticker_trades))
            member_bonus = min((unique_members - 1) * 10, 20)
            
            conviction = min(100, (amount_score * recency) + excess_bonus + member_bonus)
            
            # Build description
            best_trade = max(ticker_trades, key=lambda t: self._parse_amount(t.get("amount_range", ""), t.get("amount_max", 0)))
            rep = best_trade.get("representative", "Unknown")
            party = best_trade.get("party", "")
            amt_range = best_trade.get("amount_range", "")
            desc = f"{rep} ({party[0] if party else '?'}) bought {amt_range}"
            if unique_members > 1:
                desc += f" + {unique_members - 1} more"
            
            results.append(SignalDetail(
                source="congress",
                ticker=ticker,
                direction="Bullish",
                date=best_trade.get("transaction_date", ""),
                description=desc,
                conviction=round(conviction, 1),
                raw_data={
                    "amount_score": amount_score,
                    "recency": round(recency, 3),
                    "excess_bonus": round(excess_bonus, 1),
                    "member_bonus": member_bonus,
                    "member_count": unique_members,
                    "max_amount": max_amount,
                    "company": best_trade.get("company", ""),
                }
            ))
        
        return results

    def score_ark(self, trades: list, holdings: list = None) -> List[SignalDetail]:
        """
        ARK conviction scoring:
        - Fund count: 1=20, 2=40, 3=60, 4=75, 5=85
        - Position type: NEW=+15, increase=+5
        - Weight in fund: >5%=+10, >2%=+5
        - Recency decay
        """
        if not trades:
            return []
        
        signals_by_ticker: Dict[str, List[dict]] = {}
        for t in trades:
            if t.get("trade_type") != "Buy":
                continue
            date = t.get("date", "")
            if self._days_ago(date) > 30:
                continue
            ticker = (t.get("ticker") or "").upper().strip()
            if not ticker:
                continue
            if ticker not in signals_by_ticker:
                signals_by_ticker[ticker] = []
            signals_by_ticker[ticker].append(t)
        
        # Holdings lookup for weight info
        holdings_map: Dict[str, list] = {}
        if holdings:
            for h in holdings:
                t = (h.get("ticker") or "").upper().strip()
                if t not in holdings_map:
                    holdings_map[t] = []
                holdings_map[t].append(h)
        
        results = []
        for ticker, ticker_trades in signals_by_ticker.items():
            # Unique funds buying
            funds = set(t.get("etf", "") for t in ticker_trades)
            fund_count = len(funds)
            
            # Fund count score
            if fund_count >= 5: fund_score = 85
            elif fund_count >= 4: fund_score = 75
            elif fund_count >= 3: fund_score = 60
            elif fund_count >= 2: fund_score = 40
            else: fund_score = 20
            
            # Position type bonus
            new_position = any(t.get("change_type") == "NEW_POSITION" for t in ticker_trades)
            type_bonus = 15 if new_position else 5
            
            # Weight bonus
            weight_bonus = 0
            ticker_holdings = holdings_map.get(ticker, [])
            if ticker_holdings:
                max_weight = max(h.get("weight_pct", 0) for h in ticker_holdings)
                if max_weight > 5: weight_bonus = 10
                elif max_weight > 2: weight_bonus = 5
            
            # Total shares
            total_shares = sum(t.get("shares", 0) for t in ticker_trades)
            
            # Recency
            dates = [t.get("date", "") for t in ticker_trades]
            days = min(self._days_ago(d) for d in dates if d)
            recency = self._recency_decay(days)
            
            conviction = min(100, (fund_score * recency) + type_bonus + weight_bonus)
            
            desc_parts = [f"ARK {'|'.join(sorted(funds))}"]
            if new_position:
                desc_parts.append("NEW")
            desc_parts.append(f"bought {total_shares:,} shares")
            
            results.append(SignalDetail(
                source="ark",
                ticker=ticker,
                direction="Bullish",
                date=max(dates),
                description=" ".join(desc_parts),
                conviction=round(conviction, 1),
                raw_data={
                    "fund_count": fund_count,
                    "funds": sorted(funds),
                    "total_shares": total_shares,
                    "new_position": new_position,
                    "weight_bonus": weight_bonus,
                    "recency": round(recency, 3),
                    "company": ticker_trades[0].get("company", ""),
                }
            ))
        
        return results

    def score_darkpool(self, data: list) -> List[SignalDetail]:
        """
        Dark pool conviction scoring:
        - Z-score: 2σ=30, 3σ=50, 4σ=70, 5σ+=85
        - DPI bonus: >0.6=+10, >0.8=+15
        - Volume bonus: >1M=+5, >5M=+10, >10M=+15
        - Recency decay (7-day half-life, fast decay)
        """
        if not data:
            return []
        
        signals_by_ticker: Dict[str, dict] = {}
        for entry in data:
            date = entry.get("date", "")
            if self._days_ago(date) > 14:
                continue
            
            z_score = entry.get("z_score", 0)
            if z_score < 2.0:
                continue
            
            dpi = entry.get("dpi", 0)
            if dpi > 1:
                dpi = dpi / 100.0
            
            ticker = (entry.get("ticker") or "").upper().strip()
            if not ticker:
                continue
            
            # Keep strongest signal per ticker
            if ticker not in signals_by_ticker or entry.get("z_score", 0) > signals_by_ticker[ticker].get("z_score", 0):
                signals_by_ticker[ticker] = entry
        
        results = []
        for ticker, entry in signals_by_ticker.items():
            z_score = entry.get("z_score", 0)
            dpi = entry.get("dpi", 0)
            if dpi > 1:
                dpi = dpi / 100.0
            volume = entry.get("total_volume", 0)
            
            # Z-score tier
            if z_score >= 5: z_tier = 85
            elif z_score >= 4: z_tier = 70
            elif z_score >= 3: z_tier = 50
            else: z_tier = 30
            
            # DPI bonus
            dpi_bonus = 0
            if dpi >= 0.8: dpi_bonus = 15
            elif dpi >= 0.6: dpi_bonus = 10
            elif dpi >= 0.4: dpi_bonus = 5
            
            # Volume bonus
            vol_bonus = 0
            if volume >= 10_000_000: vol_bonus = 15
            elif volume >= 5_000_000: vol_bonus = 10
            elif volume >= 1_000_000: vol_bonus = 5
            
            # Recency (faster decay for darkpool)
            days = self._days_ago(entry.get("date", ""))
            recency = self._recency_decay(days, half_life=7)
            
            conviction = min(100, (z_tier * recency) + dpi_bonus + vol_bonus)
            
            results.append(SignalDetail(
                source="darkpool",
                ticker=ticker,
                direction="Bullish",
                date=entry.get("date", ""),
                description=f"DPI {dpi:.0%}, Z-score {z_score:.1f}σ, Vol {volume:,.0f}",
                conviction=round(conviction, 1),
                raw_data={
                    "z_score": z_score,
                    "dpi": round(dpi, 4),
                    "total_volume": volume,
                    "z_tier": z_tier,
                    "dpi_bonus": dpi_bonus,
                    "vol_bonus": vol_bonus,
                    "recency": round(recency, 3),
                    "company": entry.get("company", ""),
                }
            ))
        
        return results

    def score_institutions(self, filings: list) -> List[SignalDetail]:
        """
        13F institution conviction scoring:
        - Position value: $50M=20, $100M=35, $500M=55, $1B+=75
        - Fund prestige: top-tier (Berkshire, Citadel, Renaissance)=+15
        - Change magnitude: new=+15, increased >20%=+10, >10%=+5
        - Multi-fund: +10 per additional fund holding
        """
        if not filings:
            return []
        
        PRESTIGE_FUNDS = {"berkshire", "citadel", "renaissance", "bridgewater", "two sigma", "de shaw", "millennium", "point72", "soros"}
        
        signals_by_ticker: Dict[str, List[dict]] = {}
        for filing in filings:
            filing_date = filing.get("filing_date", "")
            if self._days_ago(filing_date) > 120:
                continue
            
            fund_name = filing.get("fund_name", "")
            is_prestige = any(p in fund_name.lower() for p in PRESTIGE_FUNDS)
            
            for holding in filing.get("holdings", []):
                value = holding.get("value", 0)
                if value < 50_000_000:
                    continue
                
                ticker = (holding.get("ticker") or "").upper().strip()
                if not ticker:
                    continue
                
                if ticker not in signals_by_ticker:
                    signals_by_ticker[ticker] = []
                
                signals_by_ticker[ticker].append({
                    **holding,
                    "fund_name": fund_name,
                    "filing_date": filing_date,
                    "is_prestige": is_prestige,
                })
        
        results = []
        for ticker, holdings in signals_by_ticker.items():
            # Best holding
            best = max(holdings, key=lambda h: h.get("value", 0))
            max_value = best.get("value", 0)
            
            # Value tier
            if max_value >= 1_000_000_000: val_tier = 75
            elif max_value >= 500_000_000: val_tier = 55
            elif max_value >= 100_000_000: val_tier = 35
            else: val_tier = 20
            
            # Prestige bonus
            prestige_bonus = 15 if any(h.get("is_prestige") for h in holdings) else 0
            
            # Change bonus
            change_bonus = 0
            for h in holdings:
                ct = h.get("change_type", "")
                cp = abs(h.get("change_pct", 0))
                if ct == "New":
                    change_bonus = max(change_bonus, 15)
                elif cp >= 20:
                    change_bonus = max(change_bonus, 10)
                elif cp >= 10:
                    change_bonus = max(change_bonus, 5)
            
            # Multi-fund bonus
            unique_funds = len(set(h.get("fund_name", "") for h in holdings))
            fund_bonus = min((unique_funds - 1) * 10, 20)
            
            # Recency
            dates = [h.get("filing_date", "") for h in holdings]
            days = min(self._days_ago(d) for d in dates if d)
            recency = self._recency_decay(days, half_life=30)
            
            conviction = min(100, (val_tier * recency) + prestige_bonus + change_bonus + fund_bonus)
            
            ct = best.get("change_type", "held")
            desc = f"{best['fund_name']} {ct} ${max_value/1e6:.0f}M"
            if unique_funds > 1:
                desc += f" + {unique_funds - 1} more funds"
            
            results.append(SignalDetail(
                source="institution",
                ticker=ticker,
                direction="Bullish",
                date=best.get("filing_date", ""),
                description=desc,
                conviction=round(conviction, 1),
                raw_data={
                    "max_value": max_value,
                    "val_tier": val_tier,
                    "prestige_bonus": prestige_bonus,
                    "change_bonus": change_bonus,
                    "fund_bonus": fund_bonus,
                    "fund_count": unique_funds,
                    "recency": round(recency, 3),
                    "company": best.get("issuer", ""),
                }
            ))
        
        return results

    def score_insiders(self, trades: list, clusters: list = None) -> List[SignalDetail]:
        """
        Insider trading conviction scoring:
        - Value tier: $50K=15, $100K=30, $500K=50, $1M=65, $5M+=80
        - Cluster bonus: 3 insiders=+15, 4=+20, 5+=+25
        - Title seniority: CEO/CFO/COO=+10, VP/Director=+5
        - Recency: exponential decay (14-day half-life)
        """
        if not trades:
            return []

        # Build cluster lookup
        cluster_map: Dict[str, dict] = {}
        if clusters:
            for c in clusters:
                ticker = (c.get("ticker") or "").upper().strip()
                if ticker:
                    cluster_map[ticker] = c

        signals_by_ticker: Dict[str, List[dict]] = {}
        for t in trades:
            if t.get("transaction_type") != "Buy":
                continue

            date = t.get("filing_date") or t.get("trade_date", "")
            if self._days_ago(date) > 45:
                continue

            value = t.get("value", 0)
            if value < 10_000:  # Very small buys less meaningful
                continue

            ticker = (t.get("ticker") or "").upper().strip()
            if not ticker:
                continue

            if ticker not in signals_by_ticker:
                signals_by_ticker[ticker] = []
            signals_by_ticker[ticker].append(t)

        results = []
        SENIOR_TITLES = {"ceo", "cfo", "coo", "cto", "president", "chairman", "chief"}

        for ticker, ticker_trades in signals_by_ticker.items():
            # Max value
            max_value = max(t.get("value", 0) for t in ticker_trades)

            # Value tier (0-80)
            if max_value >= 5_000_000: val_tier = 80
            elif max_value >= 1_000_000: val_tier = 65
            elif max_value >= 500_000: val_tier = 50
            elif max_value >= 100_000: val_tier = 30
            elif max_value >= 50_000: val_tier = 15
            else: val_tier = 10

            # Cluster bonus
            unique_insiders = set(t.get("insider_name", "") for t in ticker_trades)
            insider_count = len(unique_insiders)
            cluster_info = cluster_map.get(ticker, {})
            # Use the larger of detected vs cluster page count
            cluster_count = max(insider_count, cluster_info.get("insider_count", 0))

            cluster_bonus = 0
            if cluster_count >= 5: cluster_bonus = 25
            elif cluster_count >= 4: cluster_bonus = 20
            elif cluster_count >= 3: cluster_bonus = 15

            # Title seniority bonus
            title_bonus = 0
            for t in ticker_trades:
                title = (t.get("title") or "").lower()
                if any(s in title for s in SENIOR_TITLES):
                    title_bonus = max(title_bonus, 10)
                elif any(s in title for s in ("vp", "vice president", "director", "svp")):
                    title_bonus = max(title_bonus, 5)

            # Recency
            dates = [t.get("trade_date") or t.get("filing_date", "") for t in ticker_trades]
            days = min(self._days_ago(d) for d in dates if d)
            recency = self._recency_decay(days)

            conviction = min(100, (val_tier * recency) + cluster_bonus + title_bonus)

            # Build description
            best_trade = max(ticker_trades, key=lambda t: t.get("value", 0))
            name = best_trade.get("insider_name", "Unknown")
            title_str = best_trade.get("title", "")
            desc = f"{name}"
            if title_str:
                desc += f" ({title_str})"
            desc += f" bought ${max_value:,.0f}"
            if cluster_count >= 3:
                desc += f" [{cluster_count} insiders cluster]"
            elif insider_count > 1:
                desc += f" + {insider_count - 1} more"

            results.append(SignalDetail(
                source="insider",
                ticker=ticker,
                direction="Bullish",
                date=best_trade.get("trade_date", ""),
                description=desc,
                conviction=round(conviction, 1),
                raw_data={
                    "max_value": max_value,
                    "val_tier": val_tier,
                    "cluster_bonus": cluster_bonus,
                    "title_bonus": title_bonus,
                    "insider_count": insider_count,
                    "cluster_count": cluster_count,
                    "recency": round(recency, 3),
                    "company": best_trade.get("company", ""),
                }
            ))

        return results

    # ── Aggregation ────────────────────────────────────────────────

    def generate(
        self,
        congress_data: dict = None,
        ark_data: dict = None,
        darkpool_data: dict = None,
        institution_data: dict = None,
        insider_data: dict = None,
        ark_holdings: list = None,
        min_score: float = 0,
    ) -> List[SmartMoneySignal]:
        """
        Main pipeline:
        1. Score each source independently
        2. Merge by ticker
        3. Final score = max(source conviction) + multi_source_bonus
        4. Sort by score descending
        """
        # Step 1: Score each source
        all_details: Dict[str, List[SignalDetail]] = {}
        
        if congress_data:
            for s in self.score_congress(congress_data.get("trades", congress_data.get("data", []))):
                all_details.setdefault(s.ticker, []).append(s)
        
        if ark_data:
            for s in self.score_ark(
                ark_data.get("trades", ark_data.get("data", [])),
                ark_holdings or ark_data.get("holdings", {}).get("data", [])
            ):
                all_details.setdefault(s.ticker, []).append(s)
        
        if darkpool_data:
            for s in self.score_darkpool(darkpool_data.get("tickers", darkpool_data.get("data", []))):
                all_details.setdefault(s.ticker, []).append(s)
        
        if institution_data:
            for s in self.score_institutions(institution_data.get("filings", institution_data.get("data", []))):
                all_details.setdefault(s.ticker, []).append(s)
        
        if insider_data:
            for s in self.score_insiders(
                insider_data.get("trades", insider_data.get("data", [])),
                insider_data.get("clusters", [])
            ):
                all_details.setdefault(s.ticker, []).append(s)
        
        # Step 2 & 3: Merge and score
        results = []
        for ticker, details in all_details.items():
            source_convictions = {}
            for d in details:
                source_convictions[d.source] = max(
                    source_convictions.get(d.source, 0),
                    d.conviction
                )
            
            max_conviction = max(source_convictions.values())
            source_count = len(source_convictions)
            multi_bonus = min((source_count - 1) * 20, 40)  # +20 per extra source, cap 40
            
            # Source diversity cap — single source can't hit 100
            # Forces multi-source confluence to rank highest
            if source_count == 1:
                source_cap = 0.75   # max 75
            elif source_count == 2:
                source_cap = 0.85   # max ~92 with bonus
            elif source_count == 3:
                source_cap = 0.90   # max ~100 with bonus
            else:
                source_cap = 1.0    # 4+ sources uncapped
            
            # Most recent date
            dates = [d.date for d in details if d.date]
            signal_date = max(dates) if dates else ""
            recency_days = self._days_ago(signal_date) if signal_date else 30
            
            final_score = min(100, (max_conviction * source_cap) + multi_bonus)
            
            # Get company name from any detail
            company = ""
            for d in details:
                company = d.raw_data.get("company", "")
                if company:
                    break
            
            results.append(SmartMoneySignal(
                ticker=ticker,
                company=company,
                score=round(final_score, 1),
                direction="Bullish",
                sources=sorted(source_convictions.keys()),
                source_count=source_count,
                signal_date=signal_date,
                congress_conviction=round(source_convictions.get("congress", 0), 1),
                ark_conviction=round(source_convictions.get("ark", 0), 1),
                darkpool_conviction=round(source_convictions.get("darkpool", 0), 1),
                institution_conviction=round(source_convictions.get("institution", 0), 1),
                insider_conviction=round(source_convictions.get("insider", 0), 1),
                max_conviction=round(max_conviction, 1),
                multi_source_bonus=round(multi_bonus, 1),
                recency_factor=round(self._recency_decay(recency_days), 3),
                details=details,
            ))
        
        # Step 4: Filter and sort
        results = [r for r in results if r.score >= min_score]
        results.sort(key=lambda r: (-r.score, -r.source_count, r.ticker))
        
        logger.info(f"SmartMoney v2: {len(results)} signals from {len(all_details)} tickers")
        return results
    
    def to_json(self, results: List[SmartMoneySignal]) -> List[dict]:
        """Serialize for API response."""
        return [
            {
                "ticker": r.ticker,
                "company": r.company,
                "score": r.score,
                "direction": r.direction,
                "sources": r.sources,
                "source_count": r.source_count,
                "signal_date": r.signal_date,
                "congress_score": r.congress_conviction,
                "ark_score": r.ark_conviction,
                "darkpool_score": r.darkpool_conviction,
                "institution_score": r.institution_conviction,
                "insider_score": r.insider_conviction,
                "max_conviction": r.max_conviction,
                "multi_source_bonus": r.multi_source_bonus,
                "details": [
                    {
                        "source": d.source,
                        "description": d.description,
                        "date": d.date,
                        "conviction": d.conviction,
                    }
                    for d in r.details
                ],
            }
            for r in results
        ]
