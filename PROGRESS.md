# Meridian Progress & Lessons Learned

## 2026-02-22

### Crypto Signals Page Fixes
**Issues found by Raven (live QA):**
1. ARK sentiment "BEARISH" displayed as overall signal verdict — but 11/11 signals were Bullish
   - Root cause: ARK buy/sell ratio (5B/13S) was visually positioned as main verdict
   - Fix: Moved ARK sentiment to ARK Invest card, away from signal summary
2. Missing company names for WULF, MARA, CIFR, HUT, BTBT, CLSK, IREN
   - Root cause: These tickers only had `short_interest` source, which doesn't carry company names
   - Fix: Added `CRYPTO_STOCK_NAMES` hardcoded fallback in `macro.py`
3. Missing % Float for most crypto stocks
   - Root cause: Short interest collector's `PRIORITY_TICKERS` didn't include all crypto miners → yfinance float enrichment skipped them
   - Fix: (a) Added miners to PRIORITY_TICKERS in rsnest collector, (b) Added `CRYPTO_FLOAT_SHARES` fallback in Meridian API layer
   - Commits: `9ea676e`, `3eb7fdd`, `e30a0fa`

### Signal Weight Analysis (Raven's feedback)
**Problem**: Raven noticed ARK influence felt disproportionate in crypto section.
**Actual data analysis** (全站 2543 signals):
- Short Interest: 61% primary driver (passive, most stocks have this)
- Superinvestor: 32% primary driver
- Insider: 4.7%
- ARK: 1.2% (only 66 tickers)
- Institution: 0.5%
- Congress: 0.3%
- Dark Pool: 0.2%

**Insight**: ARK isn't overweighted globally — but in crypto-specific context, ARK is amplified because it's the most active ETF buyer of crypto stocks. Other signal sources don't cover crypto miners well.

**Solution planned**: ETF Flow Integration (see `specs/projects/etf-flow-integration.md`)
- Add BTC/ETH ETF flow data as new signal source
- Add sector ETF flows for entire platform
- Enhance superinvestor crypto coverage

### Lessons
- **Always test on mobile** — layout issues Raven caught were mobile-specific UX problems
- **Data fallbacks matter** — upstream data gaps (Quiver missing float, signal engine missing company names) need fallback layers
- **Signal source diversity** — single-source dominance in a sector creates contradictory UX. Need balanced multi-source coverage.
- **Don't ship then pray** — check the live site yourself before telling Raven it's done
