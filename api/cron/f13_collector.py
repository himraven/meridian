#!/usr/bin/env python3
"""
13F Filings Collector

数据源: SEC EDGAR (免费)
追踪: Berkshire Hathaway (Buffett), Bridgewater, Renaissance, etc.

13F 披露: 季度结束后 45 天内
"""

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import xml.etree.ElementTree as ET
import sys

sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_DIR

# 追踪的机构 (CIK 号)
TRACKED_FUNDS = {
    "0001067983": {"name": "Berkshire Hathaway", "alias": "Buffett"},
    "0001350694": {"name": "Bridgewater Associates", "alias": "Dalio"},
    "0001037389": {"name": "Renaissance Technologies", "alias": "Simons"},
    "0001423053": {"name": "Citadel Advisors", "alias": "Griffin"},
    "0001336528": {"name": "Pershing Square", "alias": "Ackman"},
    "0001649339": {"name": "Appaloosa Management", "alias": "Tepper"},
    "0001029160": {"name": "Soros Fund Management", "alias": "Soros"},
}

# SEC EDGAR URLs
SEC_BASE = "https://www.sec.gov"
SEC_FILINGS_API = f"{SEC_BASE}/cgi-bin/browse-edgar"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions"


class F13Collector:
    """13F 文件采集器"""
    
    def __init__(self):
        self.data_dir = DATA_DIR / "13f_filings"
        self.data_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SmartMoneyTracker/1.0 (contact@example.com)",  # SEC requires this
            "Accept-Encoding": "gzip, deflate",
        })
    
    def get_latest_13f(self, cik: str) -> Optional[Dict]:
        """获取最新的 13F 提交"""
        # 使用 SEC 的 submissions API
        url = f"{SEC_SUBMISSIONS}/CIK{cik.zfill(10)}.json"
        
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            # 查找最新的 13F-HR 文件
            filings = data.get("filings", {}).get("recent", {})
            forms = filings.get("form", [])
            accessions = filings.get("accessionNumber", [])
            filing_dates = filings.get("filingDate", [])
            
            for i, form in enumerate(forms):
                if form in ["13F-HR", "13F-HR/A"]:
                    return {
                        "cik": cik,
                        "form": form,
                        "accession": accessions[i],
                        "filing_date": filing_dates[i],
                        "company": data.get("name", ""),
                    }
            
            return None
            
        except Exception as e:
            print(f"[13F] Error fetching {cik}: {e}")
            return None
    
    def get_13f_holdings(self, cik: str, accession: str) -> List[Dict]:
        """解析 13F 持仓数据"""
        holdings = []
        
        # 构建 holdings XML URL
        accession_clean = accession.replace("-", "")
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_clean}"
        
        try:
            # 先获取文件列表找到 holdings XML
            index_url = f"{url}/index.json"
            resp = self.session.get(index_url, timeout=30)
            resp.raise_for_status()
            
            files = resp.json().get("directory", {}).get("item", [])
            holdings_file = None
            
            # Strategy: find the XML file that contains the holdings info table
            # Different filers use different naming conventions:
            #   - Most common: "infotable.xml" or "*infotable*.xml"
            #   - Some use: "*holding*.xml"
            #   - Others use numeric names: "46994.xml"
            # We exclude "primary_doc.xml" (the cover page) and index files
            xml_candidates = []
            for f in files:
                name = f.get("name", "")
                name_lower = name.lower()
                if not name_lower.endswith(".xml"):
                    continue
                if name_lower == "primary_doc.xml":
                    continue
                if "index" in name_lower:
                    continue
                # Prefer files with known patterns, but collect all XML candidates
                size = f.get("size", "")
                xml_candidates.append((name, size))
            
            # Pick best candidate: prefer "infotable", then "holding", then largest XML
            for name, size in xml_candidates:
                if "infotable" in name.lower():
                    holdings_file = name
                    break
            
            if not holdings_file:
                for name, size in xml_candidates:
                    if "holding" in name.lower():
                        holdings_file = name
                        break
            
            if not holdings_file and xml_candidates:
                # Fall back to the first non-primary XML (often the only one)
                holdings_file = xml_candidates[0][0]
            
            if not holdings_file:
                print(f"[13F] No holdings file found for {cik}")
                return holdings
            
            # 获取并解析 holdings XML
            holdings_url = f"{url}/{holdings_file}"
            resp = self.session.get(holdings_url, timeout=30)
            resp.raise_for_status()
            
            # 解析 XML
            root = ET.fromstring(resp.content)
            ns = {"ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}
            
            for info in root.findall(".//ns:infoTable", ns):
                holding = {
                    "issuer": info.findtext("ns:nameOfIssuer", "", ns),
                    "class": info.findtext("ns:titleOfClass", "", ns),
                    "cusip": info.findtext("ns:cusip", "", ns),
                    "value": int(info.findtext("ns:value", "0", ns)) * 1000,  # 单位是千美元
                    "shares": int(info.findtext(".//ns:sshPrnamt", "0", ns)),
                    "put_call": info.findtext(".//ns:putCall", "", ns),
                }
                holdings.append(holding)
            
            print(f"[13F] Parsed {len(holdings)} holdings from {cik}")
            
        except Exception as e:
            print(f"[13F] Error parsing holdings for {cik}: {e}")
        
        return holdings
    
    def load_previous_filing(self, cik: str) -> Optional[Dict]:
        """加载之前的 filing 数据"""
        filepath = self.data_dir / f"{cik}_latest.json"
        if filepath.exists():
            with open(filepath) as f:
                return json.load(f)
        return None
    
    def save_filing(self, cik: str, data: Dict):
        """保存 filing 数据"""
        filepath = self.data_dir / f"{cik}_latest.json"
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        # 保存历史版本
        if data.get("filing_date"):
            history_file = self.data_dir / f"{cik}_{data['filing_date']}.json"
            if not history_file.exists():
                with open(history_file, "w") as f:
                    json.dump(data, f, indent=2)
    
    def detect_changes(self, cik: str, current: Dict, previous: Dict) -> List[Dict]:
        """检测持仓变化"""
        changes = []
        fund_info = TRACKED_FUNDS.get(cik, {})
        fund_name = fund_info.get("alias", fund_info.get("name", cik))
        
        curr_holdings = {h["cusip"]: h for h in current.get("holdings", [])}
        prev_holdings = {h["cusip"]: h for h in previous.get("holdings", [])}
        
        # 新建仓位
        for cusip, h in curr_holdings.items():
            if cusip not in prev_holdings:
                changes.append({
                    "type": "NEW_POSITION",
                    "fund": fund_name,
                    "issuer": h["issuer"],
                    "cusip": cusip,
                    "shares": h["shares"],
                    "value": h["value"],
                })
        
        # 清仓
        for cusip, h in prev_holdings.items():
            if cusip not in curr_holdings:
                changes.append({
                    "type": "SOLD_OUT",
                    "fund": fund_name,
                    "issuer": h["issuer"],
                    "cusip": cusip,
                    "prev_shares": h["shares"],
                })
        
        # 加仓/减仓 (变化超过10%)
        for cusip, curr in curr_holdings.items():
            if cusip in prev_holdings:
                prev = prev_holdings[cusip]
                if prev["shares"] > 0:
                    change_pct = (curr["shares"] - prev["shares"]) / prev["shares"] * 100
                    
                    if abs(change_pct) > 10:
                        changes.append({
                            "type": "INCREASED" if change_pct > 0 else "DECREASED",
                            "fund": fund_name,
                            "issuer": curr["issuer"],
                            "cusip": cusip,
                            "prev_shares": prev["shares"],
                            "curr_shares": curr["shares"],
                            "change_pct": change_pct,
                        })
        
        return changes
    
    def run(self) -> List[Dict]:
        """运行采集"""
        print(f"[13F] Starting collection at {datetime.now()}")
        all_changes = []
        
        for cik, info in TRACKED_FUNDS.items():
            print(f"[13F] Checking {info['name']}...")
            
            # 获取最新 filing
            latest = self.get_latest_13f(cik)
            if not latest:
                continue
            
            # 检查是否有新 filing
            previous = self.load_previous_filing(cik)
            if previous and previous.get("accession") == latest["accession"]:
                print(f"[13F] {info['name']}: No new filing")
                continue
            
            print(f"[13F] {info['name']}: New filing {latest['filing_date']}")
            
            # 获取持仓数据
            holdings = self.get_13f_holdings(cik, latest["accession"])
            latest["holdings"] = holdings
            
            # 检测变化
            if previous:
                changes = self.detect_changes(cik, latest, previous)
                if changes:
                    all_changes.extend(changes)
                    print(f"[13F] {info['name']}: {len(changes)} changes")
            
            # 保存
            self.save_filing(cik, latest)
            
            # Dual-write to SQLite
            self._save_to_db(cik, latest, holdings)
        
        print(f"[13F] Done. Total changes: {len(all_changes)}")
        return all_changes
    
    def _save_to_db(self, cik: str, filing: Dict, holdings: list):
        """Write filing to SQLite database (dual-write)."""
        try:
            from api.database import SessionLocal
            from api.crud import upsert_institution_filing, log_refresh
            import time
            db = SessionLocal()
            t0 = time.time()
            info = TRACKED_FUNDS.get(cik, {})
            filing_data = {
                "cik": cik,
                "fund_name": info.get("alias", info.get("name")),
                "company_name": info.get("name"),
                "filing_date": filing.get("filing_date"),
                "quarter": filing.get("quarter"),
                "accession": filing.get("accession"),
                "total_value": sum(h.get("value", 0) for h in holdings),
                "holdings_count": len(holdings),
            }
            count = upsert_institution_filing(db, filing_data, holdings)
            ms = int((time.time() - t0) * 1000)
            log_refresh(db, "13f", "success", count, ms)
            db.close()
            print(f"[13F] SQLite: {cik} — {count} holdings written ({ms}ms)")
        except Exception as e:
            print(f"[13F] SQLite write failed (JSON still saved): {e}")


def format_13f_changes(changes: List[Dict]) -> str:
    """格式化 13F 变化为消息"""
    if not changes:
        return ""
    
    lines = ["📊 **13F 大佬持仓变化**\n"]
    
    # 按基金分组
    by_fund = {}
    for c in changes:
        fund = c["fund"]
        if fund not in by_fund:
            by_fund[fund] = []
        by_fund[fund].append(c)
    
    for fund, fund_changes in by_fund.items():
        lines.append(f"**{fund}**")
        
        for c in fund_changes[:10]:
            emoji = {
                "NEW_POSITION": "🟢 新建仓",
                "SOLD_OUT": "🔴 清仓",
                "INCREASED": "📈 加仓",
                "DECREASED": "📉 减仓",
            }.get(c["type"], "•")
            
            if c["type"] == "NEW_POSITION":
                value_m = c.get("value", 0) / 1_000_000
                lines.append(f"  {emoji} {c['issuer']} ${value_m:.1f}M")
            elif c["type"] == "SOLD_OUT":
                lines.append(f"  {emoji} {c['issuer']}")
            else:
                lines.append(f"  {emoji} {c['issuer']} {c.get('change_pct', 0):+.1f}%")
        
        if len(fund_changes) > 10:
            lines.append(f"  ... 还有 {len(fund_changes)-10} 条")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    collector = F13Collector()
    changes = collector.run()
    
    if changes:
        msg = format_13f_changes(changes)
        print("\n" + "="*50)
        print(msg)
    else:
        print("\n[13F] No new filings or changes detected")
