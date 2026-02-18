#!/usr/bin/env python3
"""
ARK Invest Daily Trades Collector

数据源: cathiesark.com (免费, 每日更新)
功能: 获取ARK ETF每日交易，检测变化，存储历史
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR, ARK_ETFS

# cathiesark.com endpoints
TRADES_URL = "https://cathiesark.com/ark-funds-combined/trades"
HOLDINGS_API = "https://arkfunds.io/api/v2/etf/holdings"


class ARKCollector:
    """ARK Invest 数据采集器"""
    
    def __init__(self):
        self.data_file = DATA_DIR / "ark_trades.json"
        self.holdings_dir = DATA_DIR / "ark_holdings"
        self.holdings_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; SmartMoneyTracker/1.0)"
        })
    
    def fetch_trades_from_arkfunds_io(self, symbol: str = "ARKK") -> Optional[dict]:
        """从 arkfunds.io API 获取持仓数据"""
        url = f"{HOLDINGS_API}?symbol={symbol}"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[ARK] Error fetching {symbol}: {e}")
            return None
    
    def fetch_all_holdings(self) -> dict:
        """获取所有 ARK ETF 的当前持仓"""
        all_holdings = {}
        for etf in ARK_ETFS.keys():
            data = self.fetch_trades_from_arkfunds_io(etf)
            if data and "holdings" in data:
                all_holdings[etf] = {
                    "date": data.get("date"),
                    "holdings": data["holdings"]
                }
                print(f"[ARK] {etf}: {len(data['holdings'])} holdings")
        return all_holdings
    
    def load_previous_holdings(self, etf: str) -> Optional[dict]:
        """加载上次的持仓数据"""
        filepath = self.holdings_dir / f"{etf}_latest.json"
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return None
    
    def save_holdings(self, etf: str, data: dict):
        """保存持仓数据"""
        filepath = self.holdings_dir / f"{etf}_latest.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        # 同时保存历史快照
        if data.get("date"):
            history_file = self.holdings_dir / f"{etf}_{data['date']}.json"
            if not history_file.exists():
                with open(history_file, "w") as f:
                    json.dump(data, f, indent=2)
    
    def detect_changes(self, etf: str, current: dict) -> list:
        """检测持仓变化 (买入/卖出)"""
        changes = []
        previous = self.load_previous_holdings(etf)
        
        if not previous:
            print(f"[ARK] {etf}: 首次运行，无历史数据")
            return changes
        
        # 构建 ticker -> shares 映射
        prev_map = {h["ticker"]: h for h in previous.get("holdings", [])}
        curr_map = {h["ticker"]: h for h in current.get("holdings", [])}
        
        # 检测新增 (买入)
        for ticker, holding in curr_map.items():
            if ticker not in prev_map:
                changes.append({
                    "type": "NEW_POSITION",
                    "etf": etf,
                    "ticker": ticker,
                    "company": holding.get("company"),
                    "shares": holding.get("shares"),
                    "weight": holding.get("weight"),
                })
            else:
                # 检测加仓/减仓
                prev_shares = prev_map[ticker].get("shares", 0)
                curr_shares = holding.get("shares", 0)
                
                if curr_shares > prev_shares * 1.01:  # 加仓超过1%
                    changes.append({
                        "type": "INCREASED",
                        "etf": etf,
                        "ticker": ticker,
                        "company": holding.get("company"),
                        "prev_shares": prev_shares,
                        "curr_shares": curr_shares,
                        "change_pct": (curr_shares - prev_shares) / prev_shares * 100 if prev_shares else 0,
                    })
                elif curr_shares < prev_shares * 0.99:  # 减仓超过1%
                    changes.append({
                        "type": "DECREASED",
                        "etf": etf,
                        "ticker": ticker,
                        "company": holding.get("company"),
                        "prev_shares": prev_shares,
                        "curr_shares": curr_shares,
                        "change_pct": (prev_shares - curr_shares) / prev_shares * 100 if prev_shares else 0,
                    })
        
        # 检测清仓
        for ticker, holding in prev_map.items():
            if ticker not in curr_map:
                changes.append({
                    "type": "SOLD_OUT",
                    "etf": etf,
                    "ticker": ticker,
                    "company": holding.get("company"),
                    "prev_shares": holding.get("shares"),
                })
        
        return changes
    
    def run(self) -> list:
        """运行采集，返回所有变化"""
        print(f"[ARK] Starting collection at {datetime.now()}")
        all_changes = []
        
        all_holdings = self.fetch_all_holdings()
        
        for etf, data in all_holdings.items():
            changes = self.detect_changes(etf, data)
            if changes:
                all_changes.extend(changes)
                print(f"[ARK] {etf}: {len(changes)} changes detected")
            
            # 保存最新数据
            self.save_holdings(etf, data)
        
        # 保存变化日志
        if all_changes:
            self.save_changes_log(all_changes)
        
        # Dual-write to SQLite
        self._save_to_db(all_holdings)
        
        print(f"[ARK] Done. Total changes: {len(all_changes)}")
        return all_changes
    
    def _save_to_db(self, all_holdings: dict):
        """Write holdings to SQLite database (dual-write)."""
        try:
            from api.database import SessionLocal
            from api.crud import upsert_ark_holdings, log_refresh
            import time
            db = SessionLocal()
            t0 = time.time()
            total = 0
            for etf, data in all_holdings.items():
                holdings = data.get("holdings", [])
                for h in holdings:
                    h.setdefault("etf", etf)
                    h.setdefault("fund", etf)
                count = upsert_ark_holdings(db, holdings)
                total += count
            ms = int((time.time() - t0) * 1000)
            log_refresh(db, "ark", "success", total, ms)
            db.close()
            print(f"[ARK] SQLite: {total} holdings written ({ms}ms)")
        except Exception as e:
            print(f"[ARK] SQLite write failed (JSON still saved): {e}")
    
    def save_changes_log(self, changes: list):
        """保存变化日志"""
        log_file = DATA_DIR / "ark_changes.jsonl"
        with open(log_file, "a") as f:
            for change in changes:
                change["timestamp"] = datetime.now().isoformat()
                f.write(json.dumps(change) + "\n")


def format_changes_message(changes: list) -> str:
    """格式化变化为消息"""
    if not changes:
        return "No changes detected."
    
    lines = ["🦅 **ARK Trades Detected**\n"]
    
    for c in changes:
        emoji = {
            "NEW_POSITION": "🟢 NEW",
            "INCREASED": "📈 ADD",
            "DECREASED": "📉 TRIM",
            "SOLD_OUT": "🔴 SOLD",
        }.get(c["type"], "•")
        
        if c["type"] == "NEW_POSITION":
            lines.append(f"{emoji} **{c['ticker']}** ({c['etf']})")
            lines.append(f"   {c['company']}")
            lines.append(f"   Shares: {c['shares']:,} | Weight: {c.get('weight', 'N/A')}%")
        elif c["type"] == "SOLD_OUT":
            lines.append(f"{emoji} **{c['ticker']}** ({c['etf']})")
            lines.append(f"   {c['company']} - Position closed")
        else:
            direction = "+" if c["type"] == "INCREASED" else "-"
            lines.append(f"{emoji} **{c['ticker']}** ({c['etf']}) {direction}{c.get('change_pct', 0):.1f}%")
            lines.append(f"   {c.get('prev_shares', 0):,} → {c.get('curr_shares', 0):,} shares")
        
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    collector = ARKCollector()
    changes = collector.run()
    
    if changes:
        msg = format_changes_message(changes)
        print("\n" + "="*50)
        print(msg)
    else:
        print("\n[ARK] No changes detected.")
