# Meridian IA 调研报告 — 复杂信息架构平台对比分析

> 调研日期: 2026-02-22 | 目的: 为 Sidebar 重构提供设计依据
> 调研范围: 金融数据平台 + 复杂 SaaS + Crypto-native 平台

---

## 一、调研对象概览

### 1. 金融数据平台（直接竞品）

#### Unusual Whales（最相似，Smart Money + Options Flow）
**导航结构:** 顶部 mega menu，分两大入口
- **Options Tools**: Flow Feed, 0DTE Flow, Net Flow, Hottest Contracts
- **Market Data**: Market Overview, Stock Screener, Sector/ETF Flow, News
- **Stock Data**: Halt Feed, Dark Pool Feed, Whale Feed
- **Ticker Explorer**: Overview → Chart → Volatility → GEX → Greeks → Earnings → Shorts → Insider（逐 tab 深入）
- **Portfolios**: Congress trades, Hedge funds, Celebrity portfolios
- **Super Dashboard**: 可配置的 all-in-one 面板

**IA 特点:**
- 按**工具类型**分，不是按数据源分
- Ticker Explorer 是独立入口：搜一只股 → 看所有维度（和我们的 Search 概念一致）
- "Super Dashboard" 是高级用户的可定制聚合面板
- 顶部 nav 用 mega menu（hover 展开），不是 sidebar

**值得学的:** 
- Ticker Explorer 作为独立核心功能，每只股票有完整多 tab 视图
- 按工具类型/用户意图分，不按数据源分
- Super Dashboard 让用户自定义布局

**不学的:**
- Mega menu hover 展开 — 在移动端体验差
- 功能太多导致 nav 项 30+ 个，新用户迷路

#### Koyfin（专业级金融分析终端）
**导航结构:** 左侧 sidebar + 右侧 sidebar + 顶部 command bar
- **左侧 sidebar（主导航）:**
  - My Watchlists / My Screens / My Portfolio / My Dashboards（用户自定义区）
  - Market Dashboards（Koyfin 预建的主题面板）
  - Analytics（分析工具集）
  - Security Analysis（个股深度页）
- **右侧 sidebar:** Watchlists, Movers, News（实时信息流）
- **顶部 Command Bar:** 快捷键 `/` 激活，类似 Bloomberg 终端

**IA 特点:**
- **双 sidebar**: 左侧导航 + 右侧信息流，互不干扰
- **Command Bar** 是核心交互方式（和 Bloomberg 学的）
- 每个功能都有 2-3 字母快捷键（如 G = Graph, FA = Fundamentals）
- 用户自定义内容放在最上面（My Dashboards, My Screens）
- 预建 vs 自定义 分离清楚

**值得学的:**
- 用户自定义区域放顶部（人性化，高频使用）
- Command Bar / 全局搜索作为一等公民
- 左侧导航按"功能类型"而非"数据源"

**不学的:**
- 双 sidebar 太重，Meridian 用不着
- 快捷键系统开发成本高，MVP 阶段不需要

#### Stocknear（技术栈相同：SvelteKit + Tailwind）
**导航结构:** 顶部 nav bar（mobile: Sheet/Drawer）
- **Stocks**: By Industry, Market Mover, Heatmap, Stock Lists
- **ETFs**: New Launches, ETF Providers
- **Analysts**: Top Analysts, Top Stocks, Analyst Flow
- **Calendar**: Dividends, Earnings, IPO, Economic
- **Flow**: Options Flow, Market Flow, Unusual Order Flow, News Flow
- **Smart Money**: Congress, Hedge Funds, Insider Tracker, POTUS Tracker
- **Screener**: Stock Screener, Options Screener, Covered Call Screener
- **Tools**: Compare, Chart, Calculator, Portfolio, Watchlist, AI Chat
- **News/Education**: Market News, Learning Center, Reddit Tracker

**IA 特点:**
- **Accordion/折叠式** mobile menu — 每组可展开收起
- 分组非常细（9 个大组，每组 2-5 项）
- Smart Money 单独一组，和 Flow 分开
- Ticker 详情页用 tab 切换（Financials → Statistics → Dark Pool → Options → Insider → Dividends）

**值得学的:**
- Accordion 分组在 mobile 上体验很好
- Smart Money 独立分组 ← 和我们方案一致
- Ticker 页的 tab 结构清晰

**不学的:**
- 9 组太多了，认知负担重
- 没有 sidebar（纯顶栏 + drawer），桌面端空间利用率低

#### Finviz
- 极简顶栏：Home | News | Screener | Maps | Groups | Portfolio | Futures | Forex | Crypto
- 9 个入口，零嵌套
- 每个页面内用 tab/filter 进一步分层
- **启发:** 顶层越少越好，深度留给页面内部

### 2. Crypto-native 平台

#### CoinGlass
**导航结构:** 顶部 nav bar
- **Market**: 首页（综合仪表盘）
- **Exchanges**: 交易所数据
- **Open Interest**: BTC/ETH OI 数据
- **Funding Rate**: 资费率
- **Liquidation**: 爆仓数据
- **Data**: 更多数据工具
- **Supercharts**: 图表工具
- **Quick Access 条:** OI%, Liquidation%, AVG RSI, Altcoin Season, CGDI
- **首页 tab 切换:** Index | Top Gainers | OI Change | Long/Short | Derivatives | Funding Rate | RSI | Liquidation

**IA 特点:**
- **扁平到极致** — 每个大功能就是一个顶部 nav 项
- 首页用 pill tabs 做水平切换（非常密集）
- 顶部 quick access 条显示关键 KPI
- 没有 sidebar，没有嵌套

**值得学的:**
- KPI 快速访问条（OI, Liquidation 等实时数据一行展示）
- Pill tabs 在页面内切换子视图
- 首页做综合仪表盘，多 tab 覆盖不同维度

**不学的:**
- 配色混乱（你已经指出）
- 信息层级弱（所有数据平铺，没有视觉重心）
- 纯顶栏在内容多的时候不够用

#### DeFiLlama
**导航结构:** 左侧 sidebar（非常深的层级）
- **顶层:** Home, Metrics, Tools, Chains, Yields, Stablecoins, RWA
- **Old Menu 展开后有 15+ 个大组:**
  - Market Overview (7 sub): Overview, Chains, Categories, Oracles, Top Protocols, Bridged TVL, Forks
  - Yields (9 sub): Overview, Stablecoin Pools, Leveraged Lending, Halal, Delta Neutral, Long/Short...
  - Fees & Revenue (9 sub): Revenue, Fees, Holders Revenue, Fees(Chains), Revenue(Chains)...
  - Volume (10 sub): Perps, DEXs, Bridge Aggregators, Open Interest, Options...
  - Stablecoins (2 sub)
  - Airdrops, NFTs, DATs, ETFs, Hacks, Bridges, Unlocks, Treasuries, Raises...
  - 还有: CEX Transparency, Narrative Tracker, Governance, Correlations, Watchlist, Token Liquidity...

**IA 特点:**
- **层级最深** — sidebar 有 15+ 组，总共 60+ 个页面
- 但用折叠来管理复杂度，默认只看到大组名
- Premium 功能区独立在最上方
- 最近加了全局搜索 `⌘K`
- 新旧导航并存（"Old Menu" 仍然存在）

**值得学的:**
- 折叠式 sidebar 处理大量页面的方式
- 按**功能域**分组（Volume, Yields, Fees）而非按链或协议
- 全局搜索 `⌘K`

**不学的:**
- 60+ 页面对新用户来说太压倒性
- 新旧 nav 并存造成混乱
- 没有"用户自定义"区域

#### Arkham Intelligence
- 极简结构：Exchange | Intel | Swap
- Intel 平台内用搜索为主导航
- 核心交互：搜一个地址/实体 → 看所有链上行为
- **启发:** 搜索驱动的 IA 在数据密集型产品中极为有效

### 3. 复杂 SaaS（非金融）

#### Datadog（最成功的复杂导航重设计）
**2024 导航重设计核心原则:**
1. **最常用功能放最上和最下** — Search + Recent Pages 在顶部，Logs/Metrics 在底部
2. **中间按产品域分组** — Infrastructure, APM, Digital Experience, Software Delivery, Security
3. **每组 hover 展开二级面板** — 左列核心功能，右列配置选项
4. **组内按使用频率排序** + 按功能相关性分组
5. **底部放"底层功能"** — Logs, Metrics, Integrations（跨域通用的基础数据）
6. **增强可读性** — 高对比度、Favorites 区域加宽

**核心设计思想:**
> "A major goal was to organize features in a way that better reflects how users actually interact with Datadog"
> — 按用户行为模式组织，不按产品技术架构

**值得学的:**
- 高频功能放最上/最下（人眼 F 型阅读模式）
- 按用户场景分组，不按技术分类
- Favorites / Recent Pages 作为快速跳转
- 底层通用功能沉底（Logs = 我们的 Ranking/Search）

#### Linear
**设计原则:**
- "减少视觉噪音，增加导航层级和密度"
- Sidebar 极简：只有 Issues, Projects, Views, Settings
- 所有复杂性通过 filter/view 在页面内处理
- Mobile tab bar 限制 5 个项

**值得学的:**
- 顶层入口要克制（5个以内）
- 复杂度留给页面内部，不堆在导航上

---

## 二、关键 IA 模式总结

### 模式 A: 按数据源/来源分（❌ 我们要避免的）
```
Congress | ARK | 13F | Insider | Dark Pool | Short Interest | OI | Funding
```
- 问题：用户不关心数据从哪来，关心数据说明什么
- 谁在用：早期 CoinGlass

### 模式 B: 按资产类型分（⚠️ 部分可用）
```
Stocks | ETFs | Crypto | Forex | Futures
```
- 适合多资产平台（TradingView, Koyfin）
- 对 Meridian 来说，Crypto 确实值得独立

### 模式 C: 按用户决策意图分（✅ 你的方向）
```
"聪明钱在干嘛?" | "市场情绪怎样?" | "Crypto有什么信号?" | "我该研究什么?"
```
- Smart Money → Market Pulse → Crypto → Research
- 最贴近用户真实思维方式
- Unusual Whales 和 Stocknear 都在往这个方向走

### 模式 D: 按功能类型分（Datadog / Koyfin）
```
监控 | 分析 | 配置 | 基础数据
```
- 适合大型 SaaS，对 Meridian 可能还太早

---

## 三、对 Meridian 当前方案的优化建议

### ✅ 已确认的好决策
1. **四大板块分组** — Smart Money / Market Pulse / Crypto / Research — 完全符合模式 C
2. **Crypto 独立** — 所有调研对象都这么做
3. **Dashboard/Feed/Ranking 作为顶层入口** — 和用户 4 场景完美对应

### 🔧 建议优化

#### 1. 考虑加入 Favorites/Recent 快速跳转区
- **参考:** Datadog, Koyfin
- **做法:** sidebar 最顶部加一个小区域，显示用户最近访问的 3-5 个页面
- **价值:** 高频用户不需要每次点开 Smart Money → Congress，直接从 Recent 跳转
- **优先级:** Phase 2+（先把基础框架搞好）

#### 2. 全局搜索 `⌘K` / `/` 快捷键
- **参考:** Koyfin, DeFiLlama, Linear
- **做法:** 顶部搜索框，`/` 或 `⌘K` 激活，搜 ticker + 功能页面
- **价值:** 复杂导航的安全网 — 找不到就搜
- **优先级:** 高，但可以和 Ticker Lookup 合并考虑

#### 3. Sidebar 底部放通用工具
- **参考:** Datadog 把 Logs/Metrics 放底部
- **做法:** Knowledge Hub, Dividend Screener 这种低频但通用的放最下面
- **当前方案:** Research 组已经在最下面了 — ✅ 吻合

#### 4. Market Pulse 分组可以更精炼
- **当前:** Fund Flows, Short Interest, Crisis Dashboard, Cross-Asset, Market Regime（5项）
- **建议:** 考虑 Short Interest 是否更适合放 Smart Money？它本质上是机构行为信号
  - Short Interest 从行为角度是 "聪明钱在做空什么" → 可归入 Smart Money
  - 如果这样，Market Pulse 变成 4 项：Fund Flows, Crisis, Cross-Asset, Market Regime
  - Smart Money 变成 7 项：Congress, ARK, 13F, Superinvestors, Insiders, Dark Pool, Short Interest
  - **但:** Smart Money 7 项可能太多 → 可以考虑合并 Institutions(13F) + Superinvestors 
- **最终建议:** 先按你当前方案走，上线后观察用户点击数据再调整

#### 5. Crypto 子页面数量预警
- **当前规划:** 6-7 个子页面
- **参考:** CoinGlass 用 pill tabs 在页面内切换，而非 sidebar 里列出来
- **建议:** 考虑 Crypto 板块用页面内 pill tabs 替代 sidebar 子项
  - Sidebar 只放一个 "Crypto" 入口
  - 进入 Crypto 后，页面内用 pill tabs: Overview | Derivatives | Liquidations | L/S Ratio | ETF Flows | Exchange
  - **好处:** sidebar 不会太长，Crypto 作为一个"子应用"有自己的内导航
  - **参考案例:** Stocknear 的 ticker 页面就是这么做的
  - **当前方案已经部分这样做了** — crypto 有 Overview/Derivatives/ETF 三个 pill tab

#### 6. "Coming Soon" 占位策略
- **好做法:** DeFiLlama 会在新功能旁加 "New" 标记
- **建议:** 
  - 已有数据的页面正常显示
  - 无数据的新页面用 "Coming Soon" + 简介 + 预期上线时间
  - **不要** 在 sidebar 里放太多 coming soon — 会让产品看起来空壳
  - 建议只放 1-2 个 coming soon，其余等数据到了再加

---

## 四、最终结论

你的四大板块框架方向**完全正确**，和业界最佳实践高度一致。主要优化空间在：

1. **Crypto 考虑页内 tab 导航**，减少 sidebar 长度
2. **Short Interest 归属再考虑**（Smart Money vs Market Pulse）
3. **全局搜索 `⌘K`** 是复杂导航的标配
4. **控制 coming soon 数量**，避免空壳感
5. **Future: Favorites/Recent** 快速跳转

框架没问题，可以动手了。

---

*调研来源: Unusual Whales, Koyfin, Stocknear (源码), CoinGlass, DeFiLlama, Finviz, Arkham Intelligence, Datadog (blog), Linear, UX Planet, Pencil & Paper*
