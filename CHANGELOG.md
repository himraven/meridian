# Meridian — Changelog

All notable changes to the Meridian platform are documented here.

---

## 2026-02-22 — ETF Flow Integration (Phase 2) — Frontend Pages

**FEAT: Fund Flows page + Crypto Signals ETF cards**

- NEW `/fund-flows` page — full ETF flow dashboard
  - Risk Sentiment Gauge: visual -1→+1 gradient bar with live needle
  - Sector Rotation: 11-cell heatmap (color-coded by flow magnitude) + detail table
  - Crypto ETFs: BTC (6 ETFs) + ETH (2 ETFs) with AUM, daily/weekly flow, streak
  - Mega ETFs: SPY, QQQ, IWM, DIA, EEM, EFA, VTI, VOO — 1d/5d/20d flow table
  - Cross-Asset: GLD, TLT, HYG, LQD, UUP, TIP — risk appetite rotation
  - Asia/China: FXI, KWEB, EWJ, VNM
  - Graceful null handling: shows "—" for first-day zero flow, "collecting" note
- UPDATED `/crypto-signals` — BTC ETF FLOWS + ETH ETF FLOWS cards inserted between price and summary
  - Summary stats (AUM, daily flow, weekly flow) from `crypto_etf_summary`
  - Individual ETF breakdown tables
- UPDATED `Sidebar.svelte` — added Fund Flows link under Market Intelligence
- Files: `frontend/sveltekit/src/routes/(app)/fund-flows/+page.ts`, `+page.svelte`
- Files: `frontend/sveltekit/src/routes/(app)/crypto-signals/+page.ts`, `+page.svelte`
- Files: `frontend/sveltekit/src/lib/components/layout/Sidebar.svelte`

---

## 2026-02-22 — ETF Flow Integration (Phase 1)

**FEAT: ETF Fund Flow API + Frontend Client**

- Added `GET /api/us/etf-flows` endpoint to `api/routers/macro.py`
  - Reads `etf_flows.json` from shared data mount (written by rsnest cron)
  - Optional `?category=crypto|sector|mega|cross_asset|asia` filter
  - 30-min in-memory cache
  - Returns: flows[], sector_rotation, crypto_etf_summary, metadata
- Added `api.macro.etfFlows(params?)` to `frontend/sveltekit/src/lib/api.ts`
- Data source: rsnest `etf_flow_collector.py` → `/app/data/etf_flows.json` → bind mount → meridian reads

---

## 2026-02-21 — Crisis Dashboard UI Fix

**FIX: SMART MONEY CRISIS BEHAVIOR 卡片分行不一致**

- 为 `signal-buy-count` / `signal-sell-count` span 加了 `white-space: nowrap`，防止数字与标签（如 "239" / "buys"）被拆分到不同行
- `signal-counts` 容器改为 `flex-wrap: wrap` + `gap: 4px 12px`，保证在卡片较窄时整组数字仍换行一致
- 修改文件：`frontend/sveltekit/src/routes/(app)/crisis/+page.svelte`

---

## 2026-02-21 — MCP Server (Model Context Protocol)

**NEW: AI Agent API via MCP Protocol**

Meridian now exposes a fully compliant MCP Server at `meridianfin.io/mcp`, enabling AI agents (Claude, ChatGPT, custom agents) to query smart money data programmatically.

**10 MCP Tools:**
| Tool | Description |
|------|-------------|
| `get_congress_trades` | Congress trading activity (STOCK Act filings) |
| `get_ark_trades` | ARK Invest buy/sell trades across all ETFs |
| `get_ark_holdings` | Current ARK ETF holdings with weights |
| `get_insider_trades` | SEC Form 4 insider trading + cluster detection |
| `get_13f_filings` | 13F institutional holdings (Buffett, Dalio, Soros, etc.) |
| `get_darkpool_activity` | Dark pool anomalies (FINRA, z-score filtered) |
| `get_short_interest` | Short interest data (FINRA) |
| `get_superinvestor_activity` | Superinvestor portfolio changes (Dataroma) |
| `get_confluence_signals` | Multi-source smart money consensus signals |
| `get_market_regime` | Market regime (Green/Yellow/Red) via VIX, MA200, credit spreads |

**Technical:**
- Streamable HTTP transport (stateless), mounted inside existing FastAPI app
- DuckDB fast path → JSON fallback for all data queries
- Zero extra memory (no new container, shared process)
- 65 tests (unit + integration), all passing
- nginx configured with streaming proxy support, no caching
- Cloudflare tunnel passes through cleanly

**Usage:** `claude mcp add --transport http meridian https://meridianfin.io/mcp`

---

## 2026-02-21 — Market Intelligence Suite: Regime Detector + Crisis Dashboard + Cross-Asset Signals

### Feature 1: Regime Detector Widget (Dashboard)
- **API**: `GET /api/us/regime` — Returns Green/Yellow/Red market regime status
  - **VIX level**: Live from Yahoo Finance (`^VIX`) — Green (<20), Yellow (20-30), Red (>30)
  - **SPY vs MA200**: 200-day moving average calculation — Bullish/Bearish with % above/below
  - **Credit Spread**: ICE BofA High Yield OAS (FRED `BAMLH0A0HYM2`) — Normal/Elevated/Crisis
  - **Overall regime**: Composite traffic-light from all 3 components
  - **Cache**: 1-hour in-memory TTL
- **Dashboard widget**: Compact regime strip above the signal feed
  - Pulsing color dot (green/yellow/red glow animation)
  - Component values: VIX, SPY/MA200 pct, HY Spread
  - Direct link to Crisis Dashboard

### Feature 2: Crisis Dashboard (`/crisis`)
- **API**: `GET /api/us/crisis` — Crisis intelligence aggregator
  - VIX stats: current, 1Y avg, 5Y avg, regime classification (calm/elevated/fearful/crisis)
  - Smart Money crisis signals from 5 sources: Congress, Insiders, ARK, Institutions (13F), Dark Pool
  - **Crisis Conviction Score** (0–100): Weighted composite — Congress 25, Insider 25, 13F 20, ARK 15, Dark Pool 15
  - Historical Crisis Playbook: 5 events (COVID 2020, Rate Shock 2022, Aug 2024 spike, GFC 2009, 2018 Q4)
  - **Cache**: 30-minute TTL
- **Frontend page** at `/crisis`:
  - VIX hero number with regime label and 1Y/5Y comparison
  - Conviction score ring (0–100) with color-coded label
  - Smart money signals grid (per-source buy/sell counts + net direction)
  - Historical playbook table with VIX peaks, drawdowns, and forward returns
- **Sidebar**: "Crisis Dashboard" added under new "Market Intelligence" section

### Feature 3: Cross-Asset Signal Dashboard (`/cross-asset`)
- **API**: `GET /api/us/cross-asset` — Cross-asset macro signals
  - **Gold vs BTC correlation**: Rolling 30/90/180 day Pearson correlation (GLD vs BTC-USD)
  - **M2 Money Supply**: FRED `M2SL` — current level ($22.4T) + YoY growth rate (4.6%)
  - **Treasury Yield Curve**: 2Y (`GS2`) and 10Y (`GS10`) yields + spread, inversion detection
  - **Fear & Greed proxy**: VIX-derived score (0–100) with narrative
  - All series include 90-day chart data for mini sparklines
  - **Cache**: 1-hour TTL
- **Frontend page** at `/cross-asset`:
  - Gold vs BTC correlation cards (30d/90d/180d with color coding)
  - BTC and Gold mini charts (LWLineChart — lightweight-charts)
  - M2 supply hero stat + YoY growth + 36-month trend chart
  - Treasury yield stats + 24-month 10Y-2Y spread chart with inversion alert
  - Fear & Greed gauge bar with needle indicator
- **Sidebar**: "Cross-Asset" added under "Market Intelligence" section

### Backend
- New router: `api/routers/macro.py` (registered in `__init__.py`)
- All endpoints use `yfinance` for live price data + FRED CSV API for macro series
- In-memory TTL cache (no Redis dependency) — avoids hammering external APIs
- Graceful fallback values on data fetch failures

### Frontend
- API client (`api.ts`): Added `macro.regime()`, `macro.crisis()`, `macro.crossAsset()`
- Sidebar: New "Market Intelligence" collapsible section with Crisis + Cross-Asset links

---

## 2026-02-19 — Knowledge Hub Launch

### New Feature: Knowledge Hub
- **API**: `GET /api/knowledge` — lists all articles (slug, title, tldr, hero_stat, etc.)
- **API**: `GET /api/knowledge/{slug}` — full article with `content_md`, academic references, SEO
- **Content**: 3 seed articles in `content/knowledge/` (JSON schema):
  - `congress-trading-alpha.json` — Congressional trading alpha (+6% 30-day)
  - `insider-buying-signals.json` — Insider cluster buying (+8.9% 12-month)
  - `dark-pool-activity.json` — Dark pool volume anomalies (~40% of US equity volume)
- **Docker**: Mounted `./content:/app/content:ro` in API service
- **Cache**: In-memory cache with 60s mtime-based file refresh (no restart needed)

### Frontend: Knowledge Hub Pages
- `/knowledge` — Index page: hero section, category filter pills, responsive card grid
  - Category filter: All | Signal Guides | Deep Dives | Masters
  - Each card: badge, title, tldr, hero_stat number, "Read →" link
- `/knowledge/[slug]` — Article page:
  - Auto-generated table of contents from h2 headings
  - Rendered markdown via `marked` library
  - Hero stat (big featured number), TL;DR callout
  - Key takeaways sidebar (desktop) + mobile collapsible
  - Academic references section
  - Related articles (card links)
  - "How Meridian Uses This Signal" section
  - Full SEO meta tags (title, description, keywords, og:*)
- Sidebar: Added "Knowledge Hub" under Research section
- Synced `knowledge.py` router to rsnest

### Ranking Page Enhancements
- Signal badges (GOV, ARK, DP, 13F, INS) now **clickable** → `/knowledge/{slug}`
- Hover tooltip on badges shows signal tldr + "Click to learn more"
- Scoring table source labels now link to corresponding knowledge articles
- Footer tip: "Click any signal badge to learn how that signal works" + Knowledge Hub link

---

## 2026-02-18 — Data Architecture Overhaul + Scoring Engine Upgrade

### Data Architecture
- **Fixed**: Switched from hardlink-based data sharing to direct bind mount of rsnest data dir
  - Hardlinks break on atomic write (`os.replace`); bind mount is instant and reliable
- **Fixed**: ARK trade data missing — mounted clawd ark-data directory → 1,477 trades + 6 ETFs restored
- **Fixed**: Research reports path — separate mount at `/app/research` with `RESEARCH_DIR` env var
- **Cleaned**: Removed broken symlinks in shared data directory (`json→`, `smartmoney.db→`)
- **Hardened**: signals, research, ark-data mounted as `:ro` (read-only)

### Scoring Engine
- **Upgraded**: `/api/signals/confluence` now reads V2 engine (`signals_v2.json`) with conviction-based scoring
  - V1: 0-4 range, no multi-source detection → V2: 0-100 range, multi-source bonus
  - e.g. GOOG: 3 sources (ARK + Congress + Institution) → score 100
- **Fixed**: V2 engine module (`cross_signal_engine_v2.py`) copied to rsnest so crons generate both v1 + v2

### API Fixes
- **Fixed**: `/api/congress/trades` — `last_updated` was null (wrong nesting path)
- **Fixed**: `/api/congress/trades` — added `buy_count` / `sell_count` to metadata
- **Added**: `/api/data-health` — comprehensive data freshness monitoring (16 sources)
  - Weekend/holiday-aware thresholds
  - Critical vs non-critical classification
  - 🟢🟡🔴 three-level status

### Frontend
- **Added**: Data Health Indicator in sidebar bottom (auto-refreshes every 5 min)
- **Fixed**: Score bars on ticker detail page — changed from `/3` to `/100` scale (V2 engine)
- **Fixed**: Congress buy/sell count — handled both "Buy"/"Purchase" and "Sell"/"Sale" trade types
- **Updated**: CN strategy references from 8x30 → 12x30

### Data Health Sources Monitored
| Source | Schedule | Critical |
|--------|----------|----------|
| Congress Trades | 3x/day | ✅ |
| ARK Trades (JSON) | 4x/day Mon-Fri | ✅ |
| ARK Changes (JSONL) | On activity | ✅ |
| Dark Pool | Daily Tue-Sat | ✅ |
| Confluence Signals | 2x/day | ✅ |
| CN 12x30 Portfolio | Daily (trading days) | ✅ |
| CN Trend State | Daily (trading days) | ✅ |
| HK Daily Signals | Daily (trading days) | ✅ |
| Institution 13F | Weekly Monday | |
| Research Reports | On-demand | |
| SQLite Database | With collectors | |

### Architecture (Final)
```
rsnest crons (smart-money-api)
  └── writes: signals.json + signals_v2.json + congress/ark/darkpool JSON
       │  direct bind mount
       ├── meridian /app/data/:ro
       ├── clawd ark-data → /app/ark-data/:ro  
       ├── data/signals → /app/signals/:ro
       ├── data/research → /app/research/:ro
       └── data/db → /app/db/ (writable)
```

---

*Maintained by Nova*
