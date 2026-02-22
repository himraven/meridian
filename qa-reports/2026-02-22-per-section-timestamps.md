# QA Report — Per-Section Data Freshness Timestamps
Date: 2026-02-22 | Build: `c1044f2` | Tester: Sentinel

---

## Summary

**PASS — Confidence: 9/10**

All four per-section timestamps render correctly. Global "Updated X ago" header label successfully removed. No NaN/undefined/null rendering. No console errors. No regressions on other pages.

---

## Deployment Verification

```
Container:     meridian-frontend — Up (healthy), started 15:47:06 UTC
Container:     meridian-api — Up (healthy), port 8502
Commit on disk: c1044f2 (verified via git log)
Build timing:  Container started 11s before commit timestamp — code was staged before commit
```

**Note on initial screenshot:** First browser screenshot showed "Updated 13m ago" in the header (stale browser cache from prior build). Curl of `http://localhost:3001/crypto` confirmed the live HTML has no such header label. Fresh page load confirmed clean.

---

## Checklist Results

### ✅ Spec Requirements

| Check | Result | Evidence |
|-------|--------|----------|
| Global "Updated X ago" REMOVED from header | ✅ PASS | Header DOM: only `<h1>` + `<p class="page-subtitle">`, no timestamp element |
| Prices · Xm ago above BTC/ETH cards | ✅ PASS | aria `[ref=e83]: Prices` + `[ref=e84]: just now` |
| F&G timestamp next to label | ✅ PASS | aria `[ref=e154]: FEAR & GREED INDEX` + `[ref=e155]: 5m ago` |
| OI table timestamp next to label | ✅ PASS | aria `[ref=e244]: Top 20 Coins by Open Interest` + `[ref=e245]: 5m ago` |
| ETF timestamp before "Full ETF details →" | ✅ PASS | aria `[ref=e464]: 3h ago` + `[ref=e465]: Full ETF details →` (order confirmed) |
| All timestamps in relative format | ✅ PASS | Values: "just now", "5m ago", "5m ago", "3h ago" |
| Null timestamps don't render (no NaN/undefined) | ✅ PASS | grep for NaN/undefined/null → 0 results in rendered HTML |

### ✅ API Layer

| Endpoint | Status | Timestamp Field |
|----------|--------|----------------|
| `/api/crypto/overview` | 200 | `metadata.oi_collected_at: "2026-02-22T15:45:29"` |
| `/api/crypto/fear-greed?limit=30` | 200 | `metadata.collected_at: "2026-02-22T15:45:34"` |
| `/api/us/crypto-signals` | 200 | `cached_at: "2026-02-22T15:48:46"` |
| `/api/us/etf-flows?category=crypto` | 200 | `metadata.last_updated: "2026-02-22T12:12:08"` |

### ✅ Frontend — Data Integrity

- `[x]` Numbers displayed match raw API values
- `[x]` No "NaN", "undefined", or raw "null" rendered to users
- `[x]` ETF null flow values correctly show "—" (from `fmtFlow()`)
- `[x]` `collectedAt()` function has try/catch — safe against malformed timestamps
- `[x]` `{#if cryptoSignals.cached_at}` guard prevents orphan timestamp elements
- `[x]` `{#if fgData?.metadata?.collected_at}` guard — correct null check
- `[x]` `{#if etfData?.metadata?.last_updated}` guard — correct null check
- `[x]` `{#if meta?.oi_collected_at}` guard — correct null check

### ✅ Frontend — Visual/UX

- `[x]` Page renders without console errors (0 errors logged)
- `[x]` Mobile 375px — layout intact, timestamps visible, no overflow breaks
- `[x]` Desktop — all sections render correctly
- `[x]` "Full ETF details →" link preserved and correctly positioned after timestamp
- `[x]` Timestamp styling: dimmed, monospace, 10px — non-intrusive per design intent

### ✅ Integration / Regression

- `[x]` `/crypto/derivatives` — 200 OK
- `[x]` `/crypto/etf` — 200 OK  
- `[x]` `/crypto/equities` — 200 OK
- `[x]` `/dashboard` — 200 OK

---

## Findings

### 🟢 LOW — Dead CSS class `.cache-label` in crypto +page.svelte

**Location:** `/frontend/sveltekit/src/routes/(app)/crypto/+page.svelte` — `style` block, line 495
**Issue:** `.cache-label` CSS rule still present from old implementation, no longer referenced by any HTML element in the template.
**Impact:** Zero user impact. Minor style bundle bloat.
**Recommendation:** Remove in a future cleanup pass (not a ship blocker).

---

## Timestamp Source Map (Verified)

```
Section         → Data Source                  → Field                        → Value
──────────────────────────────────────────────────────────────────────────────────────
Prices          → /api/us/crypto-signals       → .cached_at                   → just now
Fear & Greed    → /api/crypto/fear-greed       → .metadata.collected_at       → 5m ago
OI Table        → /api/crypto/overview         → .metadata.oi_collected_at    → 5m ago
ETF Summary     → /api/us/etf-flows            → .metadata.last_updated       → 3h ago
```

Each section correctly represents its OWN data freshness. The original problem (single OI timestamp misleading users about price freshness) is resolved.

---

## Edge Case Verification

**Null timestamp handling:**
- Template guards (`{#if field}`) prevent rendering when timestamp is null/undefined
- `collectedAt()` function: `if (!ts) return ''` — safe for all falsy inputs
- `collectedAt()` has try/catch on `new Date(ts)` — safe against unparseable strings
- ETF `daily_flow` and `weekly_flow` are currently null → correctly renders "—" via `fmtFlow()`

**"just now" threshold:**
- `collectedAt()` returns "just now" when `diffMin < 1` — correct UX for very fresh data

---

## Recommendation

**✅ SHIP**

The per-section timestamps feature works exactly as specified. Data freshness is now honestly represented per section. No regressions found. One dead CSS class is the only finding and it's cosmetic.
