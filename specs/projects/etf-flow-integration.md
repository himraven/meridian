# ETF Flow Integration — Spec & Plan

> Created: 2026-02-22 | Status: **PLANNING** | Priority: HIGH
> Requested by Raven: "正式排一下，准备充分后安排开工"

## 目标

将 ETF 资金流数据引入 Meridian，作为新的信号源，平衡现有引擎对 ARK/Superinvestor/Short Interest 的过度依赖。

### 两个维度：
1. **Crypto 板块**: BTC/ETH ETF 资金流（IBIT, GBTC, FBTC, ETHE 等）
2. **全站**: Sector ETF 资金流（XLK, XLF, XLE 等）+ Mega ETF（SPY, QQQ）

---

## Phase 0: 数据源调研 (MUST DO FIRST)

### 免费可用数据源

| 来源 | 数据 | 更新频率 | 可行性 | 备注 |
|------|------|----------|--------|------|
| **yfinance** (sharesOutstanding + totalAssets) | 当前快照 | 实时 | ✅ 可用 | 需要每日采集快照，自己算 delta |
| **ETF.com** (Fund Flows Tool) | 日度 net flow | 日度 | ⚠️ 需爬虫 | 有反爬，不太稳定 |
| **EODHD** (free tier) | ETF fundamentals | 日度 | ✅ 20 calls/day free | 够核心 ETF 用 |
| **Alpha Vantage** (free tier) | ETF data | 日度 | ✅ 25 calls/day free | 有 ETF profile 端点 |
| **FINRA ADF** | 暗池数据 | 已有 | ✅ 已接入 | 可扩展到 ETF |
| **SEC EDGAR N-PORT** | ETF 持仓 | 月度 | ⚠️ 复杂 | Phase 2+ |

### 推荐方案: yfinance daily snapshot + 自算 flow

**原理:**
```
Daily Net Flow ≈ Δ(Shares Outstanding) × NAV
```

- yfinance 免费、无限调用、数据可靠
- 每天采集一次 ~40 只 ETF 的 sharesOutstanding + totalAssets
- 存储 daily snapshot，自动计算 Δshares × NAV = net flow
- 与我们现有 cron 体系完全兼容

**局限:**
- yfinance sharesOutstanding 不是每只 ETF 都有（IBIT 返回 None）
- totalAssets 可用但精度不如 sharesOutstanding
- 需要 fallback: `flow ≈ Δ(totalAssets) - (price_return × prev_totalAssets)`

### 待验证 (Phase 0 必做)

- [ ] 测试 40 只目标 ETF 的 yfinance 数据可用性
- [ ] 对比 yfinance vs EODHD vs Alpha Vantage 的 ETF 数据质量
- [ ] 确认 BTC ETF (IBIT/GBTC/FBTC) 的 sharesOutstanding 是否可用
- [ ] 如果 sharesOutstanding 不可用，验证 totalAssets delta 方法的准确性
- [ ] 调研 iShares 官网是否有 IBIT 每日 shares outstanding 公开数据

---

## Phase 1: ETF Flow Collector (数据采集层)

### 目标 ETF 列表 (~40 只)

**Crypto ETFs (11 只):**
```
IBIT  - iShares Bitcoin Trust (BlackRock)
GBTC  - Grayscale Bitcoin Trust
FBTC  - Fidelity Wise Origin Bitcoin Fund
ARKB  - ARK 21Shares Bitcoin ETF
BITB  - Bitwise Bitcoin ETF
BITO  - ProShares Bitcoin Strategy ETF
ETHE  - Grayscale Ethereum Trust
ETHU  - ProShares Ultra Ether ETF
```

**US Sector SPDRs (11 只):**
```
XLK  - Technology         XLV  - Health Care
XLF  - Financials         XLI  - Industrials
XLE  - Energy             XLB  - Materials
XLY  - Consumer Disc.     XLP  - Consumer Staples
XLU  - Utilities          XLRE - Real Estate
XLC  - Communication
```

**Mega / Benchmark (8 只):**
```
SPY  - S&P 500            QQQ  - Nasdaq 100
IWM  - Russell 2000       DIA  - Dow Jones
EEM  - Emerging Markets   EFA  - Developed ex-US
VTI  - Total Market       VOO  - S&P 500 (Vanguard)
```

**Cross-Asset Sentiment (6 只):**
```
GLD  - Gold               TLT  - 20yr Treasury
HYG  - High Yield Corp    LQD  - Investment Grade
UUP  - US Dollar          TIP  - TIPS (Inflation)
```

**China/Asia (4 只):**
```
FXI  - China Large Cap    KWEB - China Internet
EWJ  - Japan              VNM  - Vietnam
```

### 数据结构

```json
// etf_flows.json (daily output)
{
  "flows": [
    {
      "ticker": "IBIT",
      "name": "iShares Bitcoin Trust",
      "category": "crypto",      // crypto | sector | mega | cross_asset | asia
      "date": "2026-02-21",
      "total_assets": 64803766272,
      "shares_outstanding": null,
      "nav": 38.37,
      "price": 38.61,
      "net_flow_usd": 245000000,
      "flow_pct_aum": 0.38,
      "flow_5d_usd": 1200000000,
      "flow_20d_usd": 3500000000,
      "flow_streak": 5            // 连续流入天数 (负=流出)
    }
  ],
  "sector_rotation": {
    "top_inflows": ["XLK", "XLF"],
    "top_outflows": ["XLE", "XLU"],
    "risk_sentiment": 0.65        // -1 (risk-off) to +1 (risk-on)
  },
  "crypto_etf_summary": {
    "btc_etf_total_aum": 120000000000,
    "btc_etf_daily_flow": 345000000,
    "btc_etf_weekly_flow": 1500000000,
    "eth_etf_daily_flow": -50000000
  },
  "metadata": {
    "etf_count": 40,
    "last_updated": "2026-02-21T22:00:00Z",
    "data_source": "yfinance"
  }
}
```

### Cron 设计

- **Schedule**: Daily, 22:30 ET (市场收盘后)
- **Runtime**: ~2-3 min (40 只 ETF × yfinance)
- **History**: 保留 90 天 daily snapshots → `etf_flow_history.json`
- **容错**: 单只 ETF 失败不影响其他，重试 3 次

---

## Phase 2: 前端展示

### Crypto Signals 页面新增

**新卡片: "BTC ETF FLOWS"**
- Daily/Weekly/Monthly net flow 数字
- 5 只主要 BTC ETF 的流入流出柱状图
- 连续流入/流出天数 streak
- 放在 BTC 价格卡片下方

**新卡片: "ETH ETF FLOWS"**
- 同上，ETH 版本

### 全站新页面: "Fund Flows" (or "资金流向")

**Sector Rotation 热力图**
- 11 个 sector ETF 的 1d/5d/20d flow 热力图
- 颜色: 绿=净流入, 红=净流出
- 直观展示板块轮动

**Risk Sentiment Gauge**
- 基于 risk-on vs risk-off ETF flow 比率
- -1 (极度避险) → +1 (极度追险)
- 参考 ETF: SPY/QQQ/HYG (risk-on) vs GLD/TLT/UUP (risk-off)

**ETF Flow Ranking Table**
- 按 net flow 排序的完整 ETF 列表
- 列: Ticker, Name, AUM, 1d Flow, 5d Flow, 20d Flow, Streak

### Dashboard 集成

- Dashboard 页面加一个 "Fund Flow Highlights" 迷你卡片
- 显示当日最大流入/流出 + risk sentiment

---

## Phase 3: 信号引擎集成

### 新增 Signal Source: `etf_flow`

在 `cross_signal_engine_v2.py` 新增 `score_etf_flow()`:

**Crypto 信号:**
- BTC ETF 周净流入 > $1B → bullish signal for COIN/MSTR/MARA 等
- BTC ETF 连续流出 > 5 天 → bearish signal
- 特定 ETF 异常流动 (>2σ) → alert

**全站信号:**
- Sector ETF 极端流入 (>2σ) → bullish signal for sector top stocks
- Sector 轮动方向 → 增强/削弱该 sector 股票的信号评分

**权重定位:**
- `etf_flow` 作为 "active" source (非 passive)
- 与 ark/congress/darkpool 同级
- 可以有效 balance ARK 的权重

---

## Phase 4: Superinvestor Crypto 覆盖增强

### 目标
现有 superinvestor 数据对 crypto stocks 覆盖不足。增强方式：

1. **13F 过滤**: 从现有 13F 数据中提取持有 crypto stocks 的机构
2. **Saylor Tracker**: MicroStrategy 的 BTC 购买记录是公开的
3. **Crypto Fund Holdings**: Galaxy Digital, Grayscale 等 crypto-native 机构

### 数据来源
- 现有 13F 数据已有覆盖（只是没有在 crypto 页面突出展示）
- MicroStrategy BTC purchases: 公开 press releases
- 可以先做 UI 层面的增强，把现有数据更好地呈现

---

## 开发计划

| Phase | 内容 | 预估时间 | 前置条件 |
|-------|------|----------|----------|
| **0** | 数据源验证 | 2-3 小时 | 无 |
| **1** | ETF Flow Collector (cron) | 1 天 | Phase 0 通过 |
| **2** | 前端展示 (crypto + 全站) | 1-2 天 | Phase 1 完成 |
| **3** | 信号引擎集成 | 半天 | Phase 1+2 完成 |
| **4** | Superinvestor crypto 增强 | 半天 | 独立，可并行 |

**总计: ~4 天工作量**

---

## 上次教训 (Lessons Learned)

基于 2026-02-20 Meridian 全站修复的经验：

1. **数据验证先行**: 上次 Feed 页面多个 tab 空数据，是因为时间窗口设计没考虑数据实际更新频率。这次必须先验证每只 ETF 的数据可用性。
2. **不要假设数据存在**: yfinance 对 IBIT 的 sharesOutstanding 返回 None。每个字段都要测。
3. **前端不要硬编码时间窗口**: 要根据数据实际频率动态适配。
4. **先跑 collector，有数据了再写前端**: 不要前后端同时开发，避免 mock 数据和真实数据不匹配。
5. **部署后必跑 health check**: `python3 scripts/meridian_health_check.py`。

---

## 开工条件

Phase 0 数据验证全部通过后，由 Raven 确认开工。
不 rush，不跳步骤。
