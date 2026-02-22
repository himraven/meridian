# Crypto Overview Enhancement — Implementation Plan

## Goal
Enrich `/crypto` overview page with richer data: Fear & Greed gauge with history, BTC/ETH price cards, ETF flow summary improvement, and Smart Money highlight from crypto-signals.

## Current State
- Page is 650 lines, has: 4 KPI cards (BTC OI, ETH OI, F&G value, Total OI) + OI table + ETF summary
- Data: loads `api.crypto.overview()` + `api.macro.etfFlows({ category: 'crypto' })`
- F&G is just a number in a KPI card — no gauge, no history
- No BTC/ETH price (only OI)
- No smart money signals from crypto stocks

## Enhancement Tasks

### Task 1: Update data loader (+page.ts)
- Add `api.crypto.fearGreed({ limit: 30 })` for F&G history (30 days)
- Add `api.macro.cryptoSignals()` for BTC/ETH prices + smart money highlights
- Use `Promise.allSettled` for graceful failure handling

### Task 2: Add BTC/ETH Price Row (new section, above KPI cards)
- Two-column: BTC price card + ETH price card
- Each shows: large price, 24h change %, 90-day sparkline (LWLineChart)
- Data source: `cryptoSignals.crypto_prices.btc/eth`
- Pattern: Same as `/crypto/equities` price cards

### Task 3: Enhance Fear & Greed card → full section
- Replace the small F&G KPI card with a dedicated F&G section
- Show: current value (large, color-coded) + label + BTC price at that moment
- Add mini sparkline of F&G history (30 days) using LWLineChart
- Color coding: ≤20 red (Extreme Fear), ≤40 orange (Fear), ≤60 yellow (Neutral), ≤80 green (Greed), >80 bright green (Extreme Greed)

### Task 4: Add Smart Money Highlight section
- Below F&G, above OI table
- Show top 3 crypto stock signals from cryptoSignals.smart_money_signals
- Compact card: Ticker + Score (color-coded) + Direction badge
- Link "View all →" to `/crypto/equities`

### Task 5: Improve ETF Flow section
- Keep existing BTC/ETH ETF cards but make them more compact
- The detailed ETF tables are already on `/crypto/etf`, so overview just needs summary KPIs

### Layout Order (top to bottom)
1. Header (existing)
2. **NEW: BTC/ETH Price Cards** (2-col with sparklines)
3. **ENHANCED: F&G Section** (gauge + 30d sparkline)
4. KPI Cards (BTC OI, ETH OI, Total OI — remove F&G from here since it has its own section)
5. **NEW: Smart Money Highlight** (top 3 crypto stocks)
6. OI Table (existing, keep as-is)
7. ETF Flow Summary (existing, keep as-is)

## Files to Modify
1. `src/routes/(app)/crypto/+page.ts` — Add fearGreed + cryptoSignals data loading
2. `src/routes/(app)/crypto/+page.svelte` — All UI changes

## NOT Changing
- API endpoints (all exist already)
- Other crypto subpages
- OI table structure
