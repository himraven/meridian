# Meridian Crypto Expansion — Implementation Spec

> **Goal**: Transform Meridian from US-only smart money tracker into a multi-asset intelligence platform with full crypto derivatives coverage.
> **Data Source**: CoinGlass API (Hobbyist, v2/v4 endpoints)
> **Philosophy**: Data-first. Navigation restructure enables new pages. Pages consume cached data.

---

## 1. Architecture Overview

```
CoinGlass API (30 req/min)
      │
      ▼
rsnest cron collectors (every 15 min)
      │
      ▼
JSON files (/data/coinglass/*.json)
      │ bind mount (read-only)
      ▼
Meridian API endpoints (/api/crypto/*)
      │
      ▼
SvelteKit Frontend (/crypto/*)
```

### CoinGlass API Mapping (Validated)

| Data Type | API Base | Endpoint | Version | Status |
|-----------|----------|----------|---------|--------|
| Open Interest (all coins) | v2 | `/public/v2/open_interest?symbol=BTC` | v2 | ✅ Works |
| Funding Rates (all exchanges) | v2 | `/public/v2/funding?symbol=BTC&time_type=all` | v2 | ✅ Works |
| Options OI | v2 | `/public/v2/option?symbol=BTC` | v2 | ✅ Works |
| Fear & Greed Index | v4 | `/api/index/fear-greed-history?limit=30` | v4 | ✅ Works |
| Supported Coins | v4 | `/api/futures/supported-coins` | v4 | ✅ Works |
| Supported Exchanges | v4 | `/api/futures/supported-exchanges` | v4 | ✅ Works |
| Liquidation Chart | v2 | `/public/v2/liquidation_chart?symbol=BTC&range=24h` | v2 | ❌ Returns null (may need Startup tier) |
| Long/Short Ratio | v2 | `/public/v2/long_short?symbol=BTC&timeType=2` | v2 | ❌ 40001 error (may need Startup tier) |
| Exchange Netflow | v2 | `/public/v2/indicator/exchange_netflow?symbol=BTC` | v2 | ❌ Returns null |

### Available Data Fields (from OI endpoint)
- `openInterest` — Total OI in USD
- `volUsd` — 24h volume in USD
- `avgFundingRateBySymbol` — Weighted avg funding rate
- `h1/h4/h24 OI/Vol ChangePercent` — Time-based changes
- `oiChangePercent 3d/7d/30d` — Longer-term OI trends
- `openInterestByCoinMargin/ByStableCoinMargin` — Margin type breakdown
- `oiVolRadio` — OI/Volume ratio

### Confirmed Working Coins (Top 20)
BTC, ETH, SOL, XRP, HYPE, DOGE, BNB, BCH, SUI, ADA, LINK, AVAX, LTC, PEPE, NEAR, TRX, DOT, UNI, AAVE, ARB

---

## 2. Sidebar Navigation Restructure

### Current Structure
```
Smart Money Signals
├── Overview (/smart-money)
├── Congress (/congress)
├── ARK Invest (/ark)
├── Dark Pool (/darkpool)
├── Institutions (/institutions)
└── Insiders (/insiders)

Market Intelligence
├── Crisis Dashboard (/crisis)
├── Cross-Asset (/cross-asset)
├── Fund Flows (/fund-flows)
└── Crypto Signals (/crypto-signals)

Research
├── Reports (/research)
├── Dividend (/dividend)
└── Knowledge Hub (/knowledge)
```

### New Structure
```
Smart Money               ← Keep as-is, proven
├── Overview (/smart-money)
├── Congress (/congress)
├── ARK Invest (/ark)
├── Dark Pool (/darkpool)
├── Institutions (/institutions)
└── Insiders (/insiders)

Market Pulse              ← Rename from "Market Intelligence"
├── Crisis Dashboard (/crisis)
├── Cross-Asset (/cross-asset)
├── Fund Flows (/fund-flows)
├── Short Interest (/ranking?tab=short)  [future, link to ranking with filter]
└── Market Regime (/regime)  [future, standalone page]

Crypto                    ← NEW section
├── Overview (/crypto)          ← Replaces /crypto-signals
├── Derivatives (/crypto/derivatives)  ← OI + Funding + Options
├── Liquidations (/crypto/liquidations) [placeholder if data unavailable]
├── ETF Flows (/crypto/etf)     ← BTC/ETH ETF flows (from fund-flows data)
└── Exchange (/crypto/exchange) [placeholder]

Research                  ← Keep
├── Reports (/research)
├── Dividend (/dividend)
└── Knowledge Hub (/knowledge)
```

---

## 3. Backend Tasks (rsnest)

### Task B1: CoinGlass Collector — Core
**File**: `api/cron/coinglass_collector.py`
**Schedule**: Every 15 minutes
**Output**: `/data/coinglass/` directory

```python
# Collects from CoinGlass API, outputs JSON files:
# - oi_overview.json      — Top 30 coins OI + Vol + Funding summary
# - funding_rates.json    — All coins funding rates by exchange
# - options_overview.json — BTC/ETH options OI
# - fear_greed.json       — Fear & Greed index (last 90 days)
# - metadata.json         — Collection timestamp, API status, coin count
```

**Priority coins**: BTC, ETH, SOL, XRP, DOGE, BNB, SUI, ADA, LINK, AVAX, PEPE, ARB, OP, NEAR, AAVE, UNI, DOT, MATIC, LTC, BCH

**API calls per run**: ~25 (well within 30/min limit)

### Task B2: CoinGlass Collector — Registration
**File**: Register in rsnest's cron system
**Docker**: Ensure COINGLASS_API_KEY is available in container env

---

## 4. Backend Tasks (meridian)

### Task M1: Crypto API Router
**File**: `api/routers/crypto.py`
**Endpoints**:
```
GET /api/crypto/overview    — Aggregated crypto dashboard data
GET /api/crypto/derivatives — OI + Funding + Options detail
GET /api/crypto/etf         — BTC/ETH ETF flows (reads existing etf_flows.json)
GET /api/crypto/fear-greed  — Fear & Greed history
```

All read from `/app/data/coinglass/*.json` (bind mount from rsnest).

---

## 5. Frontend Tasks

### Task F1: Sidebar Restructure
**File**: `frontend/sveltekit/src/lib/components/layout/Sidebar.svelte`
- Reorganize into 4 sections
- Add Crypto section with sub-items
- Keep existing routes working (no breaking changes)

### Task F2: Crypto Overview Page (`/crypto`)
**Route**: `frontend/sveltekit/src/routes/(app)/crypto/+page.svelte`
**Layout**: 
```
┌─────────────────────────────────────────────────┐
│ Crypto Market Overview                          │
│ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐       │
│ │ BTC   │ │ ETH   │ │ F&G   │ │ Total │       │
│ │$98.2K │ │$3.4K  │ │72 Grd │ │OI $45B│       │
│ │+2.1%  │ │-0.3%  │ │       │ │+0.3%  │       │
│ └───────┘ └───────┘ └───────┘ └───────┘       │
│                                                 │
│ ── Top 20 Coins by OI ──────────────────────── │
│ Table: Coin | OI | Vol 24h | Funding | ΔOI 4h  │
│                                                 │
│ ── Smart Money Crypto Signals ────────────────  │
│ (Existing crypto-signals content, reorganized)  │
│                                                 │
│ ── BTC/ETH ETF Flow Summary ──────────────────  │
│ (Summary cards from fund-flows data)            │
└─────────────────────────────────────────────────┘
```

### Task F3: Derivatives Page (`/crypto/derivatives`)
**Route**: `frontend/sveltekit/src/routes/(app)/crypto/derivatives/+page.svelte`
**Layout**:
```
┌─────────────────────────────────────────────────┐
│ Crypto Derivatives                              │
│ [Open Interest] [Funding Rates] [Options]       │  ← Pill tabs
│                                                 │
│ == Open Interest Tab ==                         │
│ KPI: Total OI | 24h Change | OI/Vol Ratio      │
│ Table: Exchange | OI | Share% | ΔOI 1h/4h/24h  │
│ Mini bar chart: OI by exchange (horizontal)     │
│                                                 │
│ == Funding Rates Tab ==                         │
│ Table: Exchange | Funding % | Next Funding      │
│ Color: Green (positive/long pay) Red (negative) │
│                                                 │
│ == Options Tab ==                               │
│ Table: Exchange | OI | Vol24h | Change          │
└─────────────────────────────────────────────────┘
```

### Task F4: Crypto ETF Page (`/crypto/etf`)
**Route**: `frontend/sveltekit/src/routes/(app)/crypto/etf/+page.svelte`
- Extract BTC/ETH ETF content from existing `/crypto-signals` and `/fund-flows`
- Dedicated page with more detail
- Reuse existing `etfFlows` API

### Task F5: Redirect `/crypto-signals` → `/crypto`
- Add redirect so old URLs don't break
- Update any internal links

---

## 6. Design Guidelines

### Visual Reference
- **Density**: CoinGlass-level data density (lots of numbers, compact tables)
- **Cleanliness**: Stocknear-level visual hierarchy (clear sections, good spacing)
- **Dark theme**: Consistent with existing Meridian dark palette
- **Color coding**: Green/Red for positive/negative values (consistent with existing)

### Component Reuse
- Reuse existing table styles from `/ranking`, `/smart-money`
- Reuse KPI card pattern from `/crisis`
- Pill tab pattern from existing pages
- Percentage change badges (green/red) already exist in CSS

### Responsive
- Desktop: Full tables with all columns
- Mobile: Collapsed columns, horizontal scroll for tables

---

## 7. Execution Order & Dependencies

```
Phase 1 (No dependencies, parallel):
  B1: CoinGlass collector (rsnest)
  F1: Sidebar restructure (meridian frontend)

Phase 2 (Depends on B1):
  B2: Register cron + env setup
  M1: Crypto API router (meridian backend)

Phase 3 (Depends on M1 + F1):
  F2: Crypto Overview page
  F3: Derivatives page
  F4: Crypto ETF page
  F5: Redirect setup

Phase 4 (Polish):
  - Test all pages
  - Deploy + verify
  - Update CHANGELOG
```

---

## 8. Data Bind Mount

Add to meridian's `docker-compose.yml`:
```yaml
volumes:
  - /home/raven/smart-money-platform/data/coinglass:/app/data/coinglass:ro
```

---

## 9. Files Modified/Created

### rsnest (smart-money-platform)
- NEW: `api/cron/coinglass_collector.py`
- EDIT: `docker-compose.yml` (add COINGLASS_API_KEY env)
- EDIT: cron registration

### meridian
- NEW: `api/routers/crypto.py`
- EDIT: `api/routers/__init__.py` (register crypto router)
- EDIT: `frontend/sveltekit/src/lib/components/layout/Sidebar.svelte`
- EDIT: `frontend/sveltekit/src/lib/api.ts` (add crypto API functions)
- NEW: `frontend/sveltekit/src/routes/(app)/crypto/+page.ts` + `+page.svelte`
- NEW: `frontend/sveltekit/src/routes/(app)/crypto/derivatives/+page.ts` + `+page.svelte`
- NEW: `frontend/sveltekit/src/routes/(app)/crypto/etf/+page.ts` + `+page.svelte`
- EDIT: `docker-compose.yml` (add coinglass volume mount)
