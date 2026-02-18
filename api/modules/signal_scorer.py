#!/usr/bin/env python3
"""
Signal Scoring System - 信号评分系统

综合多个维度对交易信号打分:
1. 来源权重 (谁在买)
2. 信号强度 (买多少)
3. 信号一致性 (多少人在买)
4. 时效性 (信息新鲜度)
5. 股票质量 (基本面)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class SignalSource(Enum):
    """信号来源"""
    ARK = "ark"
    CONGRESS = "congress"
    F13 = "13f"
    INSIDER = "insider"
    OPTIONS = "options"


@dataclass
class Signal:
    """单个信号"""
    source: SignalSource
    actor: str              # 具体来源人/机构
    ticker: str
    action: str             # BUY / SELL
    date: str
    amount: float = 0       # 金额
    weight: float = 0       # 占总仓位比例
    
    # 计算后的分数
    raw_score: float = 0
    factors: Dict = field(default_factory=dict)


@dataclass
class ScoredStock:
    """评分后的股票"""
    ticker: str
    signals: List[Signal]
    
    # 各维度得分
    source_score: float = 0     # 来源得分
    strength_score: float = 0   # 强度得分
    consensus_score: float = 0  # 共识得分
    freshness_score: float = 0  # 时效得分
    
    # 总分
    total_score: float = 0
    confidence: str = ""        # HIGH / MEDIUM / LOW
    
    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "total_score": round(self.total_score, 2),
            "confidence": self.confidence,
            "source_score": round(self.source_score, 2),
            "strength_score": round(self.strength_score, 2),
            "consensus_score": round(self.consensus_score, 2),
            "freshness_score": round(self.freshness_score, 2),
            "signal_count": len(self.signals),
            "sources": list(set(s.source.value for s in self.signals)),
        }


class SignalScorer:
    """信号评分器"""
    
    def __init__(self):
        # 来源权重 (基于回测结果调整)
        self.source_weights = {
            SignalSource.CONGRESS: 2.0,    # 国会交易最强
            SignalSource.F13: 1.5,         # 13F 大佬次之
            SignalSource.ARK: 1.0,         # ARK 中等
            SignalSource.INSIDER: 1.2,     # 内部人交易
            SignalSource.OPTIONS: 0.8,     # 期权信号较弱
        }
        
        # 演员权重 (具体人物)
        self.actor_weights = {
            # 国会
            "pelosi": 2.5,          # Pelosi 最强
            "nancy pelosi": 2.5,
            "tuberville": 1.8,
            "crenshaw": 1.5,
            "ossoff": 1.5,
            
            # ARK
            "arkk": 1.2,
            "arkw": 1.0,
            "arkg": 0.9,
            
            # 13F
            "buffett": 2.0,
            "berkshire": 2.0,
            "dalio": 1.5,
            "ackman": 1.5,
            "soros": 1.3,
        }
        
        # 信号衰减 (天数 -> 衰减系数)
        self.freshness_decay = {
            1: 1.0,     # 1天内
            3: 0.9,
            7: 0.7,
            14: 0.5,
            30: 0.3,
            45: 0.1,    # 超过45天几乎无效
        }
    
    def calculate_source_score(self, signal: Signal) -> float:
        """计算来源得分"""
        base = self.source_weights.get(signal.source, 1.0)
        
        # 检查演员加权
        actor_lower = signal.actor.lower()
        actor_weight = 1.0
        for name, weight in self.actor_weights.items():
            if name in actor_lower:
                actor_weight = max(actor_weight, weight)
        
        return base * actor_weight
    
    def calculate_strength_score(self, signal: Signal) -> float:
        """计算强度得分 (交易规模)"""
        # 基于金额
        if signal.amount > 0:
            if signal.amount >= 5_000_000:
                return 2.0
            elif signal.amount >= 1_000_000:
                return 1.5
            elif signal.amount >= 500_000:
                return 1.2
            elif signal.amount >= 100_000:
                return 1.0
            else:
                return 0.5
        
        # 基于仓位权重
        if signal.weight > 0:
            if signal.weight >= 5:   # 5%+ 重仓
                return 1.8
            elif signal.weight >= 2:  # 2%+
                return 1.3
            else:
                return 1.0
        
        return 1.0
    
    def calculate_freshness_score(self, signal: Signal) -> float:
        """计算时效得分"""
        try:
            signal_date = datetime.strptime(signal.date, "%Y-%m-%d")
            days_ago = (datetime.now() - signal_date).days
            
            for days, decay in sorted(self.freshness_decay.items()):
                if days_ago <= days:
                    return decay
            
            return 0.05  # 非常旧的信号
        except:
            return 0.5  # 默认中等
    
    def score_signals(self, signals: List[Signal]) -> List[ScoredStock]:
        """对信号列表打分并汇总"""
        # 按 ticker 分组
        by_ticker = {}
        for s in signals:
            if s.ticker not in by_ticker:
                by_ticker[s.ticker] = []
            by_ticker[s.ticker].append(s)
        
        scored_stocks = []
        
        for ticker, ticker_signals in by_ticker.items():
            stock = ScoredStock(ticker=ticker, signals=ticker_signals)
            
            # 计算各维度得分
            source_scores = [self.calculate_source_score(s) for s in ticker_signals]
            strength_scores = [self.calculate_strength_score(s) for s in ticker_signals]
            freshness_scores = [self.calculate_freshness_score(s) for s in ticker_signals]
            
            stock.source_score = max(source_scores) if source_scores else 0
            stock.strength_score = max(strength_scores) if strength_scores else 0
            stock.freshness_score = max(freshness_scores) if freshness_scores else 0
            
            # 共识得分 (多少独立来源)
            unique_sources = set(s.source for s in ticker_signals)
            unique_actors = set(s.actor.lower() for s in ticker_signals)
            stock.consensus_score = min(2.0, 0.5 * len(unique_sources) + 0.3 * len(unique_actors))
            
            # 总分 = 加权平均，归一化到 0-10
            raw_score = (
                stock.source_score * 0.35 +
                stock.strength_score * 0.25 +
                stock.consensus_score * 0.25 +
                stock.freshness_score * 0.15
            )
            # 归一化: 理论最高约 5 分，映射到 10
            stock.total_score = min(10, raw_score * 2)
            
            # 信心等级
            if stock.total_score >= 7:
                stock.confidence = "HIGH"
            elif stock.total_score >= 4:
                stock.confidence = "MEDIUM"
            else:
                stock.confidence = "LOW"
            
            scored_stocks.append(stock)
        
        # 按总分排序
        scored_stocks.sort(key=lambda x: x.total_score, reverse=True)
        
        return scored_stocks


def format_scored_stocks(stocks: List[ScoredStock], top_n: int = 10) -> str:
    """格式化评分结果"""
    lines = [
        "🎯 **Smart Money Signal Ranking**",
        "",
        f"Top {min(top_n, len(stocks))} stocks by composite score:",
        "",
    ]
    
    for i, stock in enumerate(stocks[:top_n], 1):
        emoji = "🔥" if stock.confidence == "HIGH" else ("⚡" if stock.confidence == "MEDIUM" else "💤")
        sources = "/".join(sorted(set(s.source.value for s in stock.signals)))
        
        lines.append(f"{i}. **{stock.ticker}** {emoji} Score: {stock.total_score:.1f}/10")
        lines.append(f"   Sources: {sources} | Signals: {len(stock.signals)}")
        lines.append(f"   来源{stock.source_score:.1f} 强度{stock.strength_score:.1f} "
                    f"共识{stock.consensus_score:.1f} 时效{stock.freshness_score:.1f}")
        lines.append("")
    
    return "\n".join(lines)


# 示例使用
if __name__ == "__main__":
    scorer = SignalScorer()
    
    # 模拟信号
    test_signals = [
        Signal(SignalSource.CONGRESS, "Nancy Pelosi", "NVDA", "BUY", "2026-01-15", amount=1_500_000),
        Signal(SignalSource.ARK, "ARKK", "NVDA", "BUY", "2026-01-20", weight=5.2),
        Signal(SignalSource.F13, "Berkshire Hathaway", "NVDA", "BUY", "2026-01-25"),
        Signal(SignalSource.CONGRESS, "Tommy Tuberville", "AAPL", "BUY", "2026-01-18", amount=500_000),
        Signal(SignalSource.ARK, "ARKW", "COIN", "BUY", "2026-02-01", weight=3.1),
        Signal(SignalSource.CONGRESS, "Dan Crenshaw", "MSFT", "BUY", "2026-01-10", amount=250_000),
    ]
    
    # 评分
    scored = scorer.score_signals(test_signals)
    
    # 输出
    print(format_scored_stocks(scored))
