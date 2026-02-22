# QA Report — Crypto Equity Signals + Short Interest Pages
Date: 2026-02-22 | Build: ac362b5 | Tester: Sentinel

---

## Summary

**FAIL — Confidence: 8/10**

Both pages render, both APIs return valid data, squeeze logic is correct, filters work via URL params, no console errors. However, **3 bugs require fixes before ship**:

1. 🔴 Load More is completely broken — 8,586+ records permanently unreachable
2. 🔴 "Equity Signals" appears twice in the sidebar Crypto section (duplicate entry)
3. 🟠 `sort_by=change_pct` silently falls back to `sort_by=short_interest` — the API doesn't support this sort column

---

## Deployment Verification ✅

```
Container: meridian-frontend — Up 17 minutes (healthy)
Container: meridian-api     — Up 4 hours (healthy)
Container: meridian-nginx   — Up ~1 hour
Latest commit on host: ac362b5 feat: add Crypto Equity Signals page + Short Interest full page
Frontend built: 2026-02-22T14:16:07Z (matches commit timestamp)
```

Container is running the expected code. ✅

---

## Critical Findings (Ship Blockers)

### 🔴 BUG 1: Load More Never Appears (SI Page)

**Evidence:**
```bash
curl "http://localhost:8502/api/us/short-interest?limit=50&sort_by=short_interest"
# Returns: {"data": [...50 items...], "metadata": {"total": 8636, "filtered": 50, ...}}
```

**Root cause:** `metadata.filtered` is set to `len(rows)` (the post-LIMIT count) instead of the total count matching the filter criteria before the LIMIT is applied. The frontend logic:

```js
const hasMore = $derived(() => rows.length < (metadata.filtered ?? metadata.total ?? 0));
// → 50 < 50 = FALSE → Load More never shows
```

With 8,636 total records and a default limit of 50, **8,586 records are permanently unreachable** unless the user manually changes the URL. The "Showing all 50 results" text compounds the problem by implying there's no more data.

**Fix needed in `api/routers/us.py`:** The API must return a separate `total_filtered` count (using a pre-LIMIT `COUNT(*)` query with all WHERE clauses applied) vs `returned` (the actual rows in this response).

---

### 🔴 BUG 2: Duplicate "Equity Signals" in Sidebar

**Evidence:**
```
DOM shows:
  <a href="/crypto/equities">Equity Signals</a>  ← appears twice
  <a href="/crypto/equities">Equity Signals</a>
```

The Crypto section in `Sidebar.svelte` has a copy-paste error at lines 40-41:
```js
{ href: '/crypto/equities', label: 'Equity Signals' },
{ href: '/crypto/equities', label: 'Equity Signals' },  // ← duplicate
```

Visible to every user on every page. Both links work, but the sidebar shows two identical entries.

**Fix needed in `Sidebar.svelte`:** Remove the duplicate entry.

---

## Other Findings

### 🟠 BUG 3: `sort_by=change_pct` Silently Fails

**Evidence:**
```bash
curl "http://localhost:8502/api/us/short-interest?limit=5&sort_by=change_pct"
# Returns results sorted by short_interest, NOT change_pct
# PLUG (SI=348M, change_pct=2.42%) appears #1
# SNPMF (change_pct=56.24%) appears #7
```

The API `sort_col_map` is missing the `change_pct` key:
```python
sort_col_map = {
    "short_ratio": "short_pct_float",
    "days_to_cover": "days_to_cover",
    "short_volume": "short_interest",
    "short_interest": "short_interest",
    # "change_pct" is NOT here → defaults to "short_interest"
}
```

The frontend dropdown offers "Change %" which sends `sort_by=change_pct`. The API echoes `"sort_by": "change_pct"` in the metadata response (making it look like it worked), but the actual data is sorted by `short_interest`. Users who select "Change %" see results sorted incorrectly with no indication of the failure.

**Fix:** Add `"change_pct": "change_pct"` to `sort_col_map` in `api/routers/us.py`.

---

### 🟡 ISSUE 4: Company Name Enrichment Errors (Data Quality)

**Evidence from DOM:**
- `VZ` row shows company = "VIATRIS INC" (VZ is Verizon; VTRS is Viatris)
- `HPQ` row shows company = "HCA HEALTHCARE INC" (HPQ is HP Inc; HCA is HCA Healthcare)

Pre-existing data quality issue in the ticker → company name mapping. Not a code bug in this commit, but visibly wrong to any user who knows these tickers.

---

### 🟡 ISSUE 5: ETF Daily/Weekly Flows Show "—" (Null Data)

**Evidence:**
```json
"crypto_etf_summary": {
    "btc_etf_total_aum": 102830347008.0,
    "eth_etf_total_aum": 3585580032.0,
    "btc_etf_daily_flow": null,
    "btc_etf_weekly_flow": null,
    "eth_etf_daily_flow": null,
    "eth_etf_weekly_flow": null
}
```

The Equity Signals page ETF summary shows `$102.8B` total AUM correctly but displays "—" for all flow values. Individual ETF rows also show "—" for daily flow and flow %. Frontend handles nulls gracefully (no crash), but the feature feels incomplete.

---

### 🟢 ISSUE 6: KPI Cards Reflect Current Page (50 rows), Not Global Data

**Design limitation:** KPI derivations (`kpiMostShorted`, `kpiBiggestIncrease`, `kpiHighestDtc`, `kpiHighestSiFloat`) are computed from the `rows` state — the currently loaded set (default 50). In the default view:

- "Most Shorted" = rows[0] by SI sort → PLUG ✅ (always correct since data is sorted by SI)
- "Biggest SI Increase" = max change_pct among top-50-by-SI → AMXOF +79.45% ✅ (likely correct but not guaranteed globally)
- "Highest DTC" = max DTC among top-50 → GCPEF 999.99d ✅ (tied with many records)
- "Highest SI Float" = max float% among top-50 → ASST 1222.3% ✅ (extreme outlier, likely correct)

Once Load More bug is fixed and users page through data, the KPIs will update to reflect the expanded dataset (which is actually correct behavior for a progressive load model). However, there is ambiguity — the KPIs look like "global maximums" but are computed from the visible subset.

**Note:** ASST (1222.3% float short) and similar extreme outliers appear to have data quality issues (short interest > float by 12x), but that's upstream data, not a frontend bug.

---

## Checklist Results

### API Layer
- [x] All endpoints return 200
- [x] Response schema matches frontend expectations
- [x] Null/empty handling (no 500s on missing data)
- [x] Data freshness (cached_at: 2026-02-22T14:34:37Z)
- [x] Container is running latest code (ac362b5)

### Short Interest Page
- [x] Page renders (HTTP 200)
- [x] KPI cards display correctly from loaded data
- [x] Squeeze highlighting correct (Short% Float >20% AND DTC >5)
- [x] 4 squeeze setups correctly identified: RXRX, MPW, SOUN, IOVA
- [x] No false positives: ABEV (DTC>5 but float<20%) NOT highlighted
- [x] Filter URL params: `sort_by`, `min_short_ratio`, `min_days_to_cover`, `ticker` all work
- [x] Filter state pre-populated from URL on page load
- [x] Filter controls update URL on Apply
- [x] Ticker filter works (TSLA → 1 result)
- [x] SI increase colored red, decrease colored green
- [ ] Load More works **← BROKEN: never shows** 
- [ ] `sort_by=change_pct` works **← BROKEN: silently sorts by SI**
- [x] `comingSoon` removed from sidebar Short Interest entry
- [x] No console errors

### Crypto Equity Signals Page
- [x] Page renders (HTTP 200)
- [x] BTC price card: $67,640 (-0.53%) with 90d sparkline ✅
- [x] ETH price card: $1,951 (-1.13%) with 90d sparkline ✅
- [x] BTC ETF flows: 6 ETFs shown, AUM correct, daily flow null (shows —)
- [x] ETH ETF flows: ETHE + ETHU shown, AUM $3.6B
- [x] Signal Summary: 11 total / 11 bullish / 0 bearish / COIN most active ✅
- [x] Smart Money Composite: 11 rows displayed
- [x] ARK Trades: 35 trades, sentiment bar shows BEARISH
- [x] Insider Activity: 3 trades (MARA, CIFR)
- [x] Short Interest section: 11 crypto stocks
- [x] Dark Pool: 1 row (COIN)
- [x] Congress Trades: empty state displayed correctly
- [x] 13F Holdings: section hidden when empty (no error) ✅
- [x] narrative text rendered in Signal Summary ✅
- [x] No console errors

### Sidebar Navigation
- [x] Short Interest: no `comingSoon` badge ✅
- [x] Equity Signals link exists and navigates correctly ✅
- [ ] Equity Signals appears TWICE in Crypto section **← DUPLICATE BUG**
- [x] Short Interest sidebar link active state correct when on /short-interest ✅

### Regression Pages
- [x] /crypto → 200, "Crypto Overview — Meridian" ✅
- [x] /crypto/derivatives → 200, "Crypto Derivatives — Meridian" ✅
- [x] /crypto/etf → 200, "Crypto ETF Flows — Meridian" ✅

### Mobile/Responsive
- [x] Short Interest: table has `overflow-x-auto min-w-[900px]` — scrolls horizontally ✅
- [x] Short Interest: KPI grid collapses to 2-col on mobile (`grid-cols-2 lg:grid-cols-4`) ✅
- [x] Crypto Equities: BTC/ETH price cards stack vertically on mobile ✅
- [x] Crypto Equities: tables have `overflow-x: auto; -webkit-overflow-scrolling: touch` ✅
- [Note] True 375px viewport test was not achievable (browser minimum ~780px); responsive code reviewed in source and confirmed correct via Tailwind classes

---

## Data Verification

### Short Interest API Schema Matches Frontend ✅
```
API fields:    ticker, short_interest, prior_short_interest, change, change_pct,
               days_to_cover, avg_daily_volume, short_pct_float, float_shares,
               shares_outstanding, settlement_date, company (enriched)

Frontend uses: ticker, short_interest, prior_short_interest, change_pct,
               days_to_cover, short_pct_float, avg_daily_volume, settlement_date, company
```

All fields present and used correctly. ✅

### Crypto Signals API Schema Matches Frontend ✅
```
API top-level keys: crypto_prices, ark_sentiment, ark_trades, insider_trades,
                    darkpool, short_interest, smart_money_signals, congress_trades,
                    institution_holdings, summary, cached_at

All keys accessed safely with optional chaining (?.) and ?? [] fallbacks.
```

### ETF Flows API ✅
```
API: /api/us/etf-flows?category=crypto
Returns: flows (8 items), crypto_etf_summary, sector_rotation, metadata
BTC ETFs (6): IBIT, GBTC, FBTC, ARKB, BITB, BITO — all correctly filtered
ETH ETFs (2): ETHE, ETHU — correctly filtered
```

---

## Recommendation

### ⛔ DO NOT SHIP to production as-is

**Must fix before ship:**
1. 🔴 **Load More broken** — API `filtered` field must return pre-LIMIT count matching filters
2. 🔴 **Duplicate sidebar entry** — remove one `{ href: '/crypto/equities', label: 'Equity Signals' }` from Sidebar.svelte
3. 🟠 **`change_pct` sort silently broken** — add `"change_pct": "change_pct"` to API sort_col_map

**Can ship after the 3 fixes above. Nice-to-haves but not blockers:**
- 🟡 Company name enrichment errors (VZ/HPQ) — pre-existing data issue
- 🟡 ETF daily/weekly flow null data — data pipeline issue, not code
- 🟢 KPI cards global-vs-current-page ambiguity — acceptable design trade-off

---

## Bug Fix Locations

| Bug | File | Fix |
|-----|------|-----|
| Load More | `api/routers/us.py` line ~499 | Add pre-LIMIT `COUNT(*)` with filter WHERE clauses; return as `total_filtered` in metadata |
| Duplicate sidebar | `frontend/sveltekit/src/lib/components/layout/Sidebar.svelte` line 41 | Delete duplicate entry |
| change_pct sort | `api/routers/us.py` line ~469 | Add `"change_pct": "change_pct"` to sort_col_map |

---

*— Sentinel 🛡️*
