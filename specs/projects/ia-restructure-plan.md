# IA Restructure — Implementation Plan

> Created: 2026-02-22 | Follows: Superpowers subagent-driven workflow
> Design spec: `specs/projects/ia-restructure.md`
> Research: `specs/projects/ia-research-findings.md`

## Scope

Phase 1A ONLY — Sidebar restructure + Crypto page-internal tabs.
**No new data collectors. No new API endpoints. No new pages.**
Pure frontend reorganization of existing content.

## Pre-conditions
- [x] Design spec confirmed by Raven
- [x] Research completed (10 platforms analyzed)
- [x] Current sidebar code reviewed
- [x] All existing routes verified

## Current State (Sidebar)
```
Top-level links: Dashboard, Feed, Ranking, Search
Smart Money: Overview, Congress, ARK Invest, Dark Pool, Institutions, Insiders
Market Pulse: Crisis Dashboard, Cross-Asset, Fund Flows
Crypto: Overview, Derivatives, ETF Flows
Research: Reports, Dividend, Knowledge Hub
```

## Target State (Sidebar)
```
Top-level links: Dashboard, Feed
SMART MONEY: Congress Trades, ARK Invest, Institutions (13F), Insiders (Form 4), Dark Pool, Short Interest
MARKET PULSE: Fund Flows (ETF), Crisis Dashboard, Cross-Asset Correlation, Market Regime [coming soon]
CRYPTO: Signals Overview, Derivatives, ETF Flows (+ future tabs in-page)
RESEARCH: Confluence Signals [coming soon], Ticker Lookup, Ranking, Dividend Screener, Knowledge Hub
```

## Key Changes
1. **Rename labels** to be more descriptive (user-facing language, not dev-speak)
2. **Move Ranking & Search into Research group** (from top-level)
3. **Add Short Interest to Smart Money** (from being hidden)
4. **Rename "Search" → "Ticker Lookup"** (clearer intent)
5. **Add "coming soon" placeholder items** for Market Regime, Confluence Signals
6. **Remove Smart Money Overview** (redundant with Dashboard)
7. **Crypto section**: keep 3 sidebar items, future expansion via in-page pill tabs

---

## Tasks

### Task 1: Update Sidebar navSections data (5 min)
**File**: `frontend/sveltekit/src/lib/components/layout/Sidebar.svelte`
**Action**: Replace `navSections` array with new structure.

**Exact changes:**
```typescript
const navSections = [
  {
    title: 'Smart Money',
    items: [
      { href: '/congress', label: 'Congress Trades' },
      { href: '/ark', label: 'ARK Invest' },
      { href: '/institutions', label: 'Institutions (13F)' },
      { href: '/insiders', label: 'Insiders (Form 4)' },
      { href: '/darkpool', label: 'Dark Pool' },
      { href: '/short-interest', label: 'Short Interest', comingSoon: true },
    ]
  },
  {
    title: 'Market Pulse',
    items: [
      { href: '/fund-flows', label: 'Fund Flows (ETF)' },
      { href: '/crisis', label: 'Crisis Dashboard' },
      { href: '/cross-asset', label: 'Cross-Asset' },
      { href: '/market-regime', label: 'Market Regime', comingSoon: true },
    ]
  },
  {
    title: 'Crypto',
    items: [
      { href: '/crypto', label: 'Signals Overview' },
      { href: '/crypto/derivatives', label: 'Derivatives' },
      { href: '/crypto/etf', label: 'ETF Flows' },
    ]
  },
  {
    title: 'Research',
    items: [
      { href: '/confluence', label: 'Confluence Signals', comingSoon: true },
      { href: '/search', label: 'Ticker Lookup' },
      { href: '/ranking', label: 'Ranking' },
      { href: '/dividend', label: 'Dividend Screener' },
      { href: '/knowledge', label: 'Knowledge Hub' },
    ]
  }
];
```

**Top-level links change:**
- Keep: Dashboard, Feed
- Move to Research: Ranking, Search (now "Ticker Lookup")

**Verify:**
- All href routes exist (or have coming-soon handling)
- No broken links

### Task 2: Add "Coming Soon" badge support (5 min)
**File**: `frontend/sveltekit/src/lib/components/layout/Sidebar.svelte`
**Action**: Add visual handling for `comingSoon: true` items.

**Behavior:**
- Show a small "Soon" pill/badge next to the label
- Link still clickable but goes to a placeholder page (or shows tooltip)
- Style: muted text + subtle badge
- Keep it minimal — one line CSS change + template tweak

### Task 3: Create placeholder pages for coming-soon routes (5 min)
**Routes to create:**
- `/short-interest/+page.svelte` — "Short Interest data coming soon. Currently integrated in signal scores."
- `/market-regime/+page.svelte` — "Market Regime indicator coming soon."
- `/confluence/+page.svelte` — "Confluence Signals — multi-source signal crossover analysis coming soon."

Each is a simple centered message page, consistent styling, 20 lines max.

### Task 4: Remove redundant top-level sidebar links (3 min)
**File**: `frontend/sveltekit/src/lib/components/layout/Sidebar.svelte`
**Action**: Remove the standalone top-level `<a>` elements for Ranking and Search.
Keep only Dashboard and Feed as top-level.

### Task 5: Remove Smart Money Overview link (2 min)
The `/smart-money` route was a section overview page. Since Dashboard already serves this purpose,
remove it from sidebar. The route/page can stay but is no longer nav-linked.

### Task 6: Update `isActive()` function if needed (2 min)
Verify that the active state detection still works correctly with the new structure.
The current logic uses `startsWith` which may need adjustment for nested routes.

### Task 7: Rebuild frontend container + verify (3 min)
```bash
cd /home/raven/meridian
docker compose build frontend
docker compose up -d frontend
```
Verify live site shows new sidebar.

---

## Verification Checklist (for Sentinel QA)
- [ ] All 4 sidebar sections visible with correct titles
- [ ] All existing page links work (no 404s)
- [ ] Coming soon items show badge and load placeholder page
- [ ] Dashboard and Feed are top-level (above section groups)
- [ ] Ranking no longer appears as top-level link
- [ ] Search no longer appears as top-level link (now "Ticker Lookup" in Research)
- [ ] Active state highlights correctly for all pages
- [ ] Mobile sidebar works (drawer open/close, all items visible)
- [ ] No regressions on any existing page
- [ ] Smart Money Overview link removed from sidebar

## Commit Plan
Single commit: `refactor: IA restructure — sidebar reorganized by investment decision dimensions`
