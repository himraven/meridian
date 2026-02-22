# QA Report — IA Sidebar Restructure Phase 1A

**Date:** 2026-02-22 | **Build:** `3d8b2eb` | **Tester:** Sentinel 🛡️

---

## Summary

**PASS** — Confidence: **9/10**

Sidebar restructure is clean, correct, and complete. All 20 routes return 200. Labels, section grouping, item counts, "Soon" badges, and active state highlighting all match spec. One medium finding in the Navbar (not sidebar) that references the old `/smart-money` route. No regressions detected on existing pages.

---

## Critical Findings (Ship Blockers)

None.

---

## Other Findings

### 🟡 MEDIUM — Navbar still references `/smart-money` route

The top Navbar component (`Navbar.svelte`) still contains desktop nav links from the old IA:

```html
<a href="/smart-money" class="nav-link ...">Markets</a>
<a href="/research" class="nav-link ...">Research</a>
```

**Impact:** The `/smart-money` route still renders (200 — shows the old dashboard), so it's not broken. But it's conceptually stale — the sidebar no longer links there, and the Navbar's "Markets" / "Research" grouping doesn't match the new 4-section model. This is desktop-only (`hidden lg:flex`).

**Evidence:** `curl -s http://localhost:3001/dashboard | grep '/smart-money'` returns the Navbar link.

**Recommendation:** Update Navbar to either remove desktop nav links (since sidebar is primary nav) or align them with the new section titles. Not a blocker — sidebar is the primary navigation and it's correct.

### 🟢 LOW — `/crypto` parent highlights when on sub-routes

When on `/crypto/derivatives`, both `/crypto` and `/crypto/derivatives` show active state. This is the `isActive()` `startsWith` logic — technically correct behavior (parent route matches prefix), but worth noting. Consistent UX — not a bug.

---

## Checklist Results

### Deployment Verification
- [x] Commit `3d8b2eb` is HEAD on main in `/home/raven/meridian`
- [x] `meridian-frontend` container is healthy and recently rebuilt
- [x] Container serves the new sidebar (SSR HTML matches source code)

### Sidebar Structure
- [x] Exactly 4 section groups: Smart Money, Market Pulse, Crypto, Research
- [x] Section headers are uppercase styled labels
- [x] All sections expanded by default
- [x] Collapsible chevrons present on each section

### Section Item Counts
- [x] Smart Money: 6 items (1 coming soon) ✅
- [x] Market Pulse: 4 items (1 coming soon) ✅
- [x] Crypto: 3 items (0 coming soon) ✅
- [x] Research: 5 items (1 coming soon) ✅
- [x] Total sidebar links: 20 (2 top-level + 18 in sections)

### Top-Level Links
- [x] Only Dashboard and Feed appear above the 4 sections
- [x] Ranking is NOT top-level (moved to Research section)
- [x] Search/Ticker Lookup is NOT top-level (moved to Research section)

### Labels (Exact Match)
- [x] "Congress Trades" (not "Congress")
- [x] "ARK Invest" (not "ARK")
- [x] "Institutions (13F)" (not "Institutions")
- [x] "Insiders (Form 4)" (not "Insiders")
- [x] "Dark Pool"
- [x] "Short Interest"
- [x] "Fund Flows (ETF)"
- [x] "Crisis Dashboard"
- [x] "Cross-Asset"
- [x] "Market Regime"
- [x] "Signals Overview"
- [x] "Derivatives"
- [x] "ETF Flows"
- [x] "Confluence Signals"
- [x] "Ticker Lookup"
- [x] "Ranking"
- [x] "Dividend Screener"
- [x] "Knowledge Hub"

### "Soon" Badges
- [x] Short Interest — has `sidebar-link-soon` class + `<span class="soon-badge">Soon</span>`
- [x] Market Regime — has `sidebar-link-soon` class + `<span class="soon-badge">Soon</span>`
- [x] Confluence Signals — has `sidebar-link-soon` class + `<span class="soon-badge">Soon</span>`
- [x] No other items have Soon badges

### Placeholder Pages (NEW Routes)
- [x] `/short-interest` — 200, "Coming Soon" header, descriptive paragraph about short interest data
- [x] `/market-regime` — 200, "Coming Soon" header, descriptive paragraph about regime identification
- [x] `/confluence` — 200, "Coming Soon" header, descriptive paragraph about multi-source signals

### Active State Highlighting
- [x] `/dashboard` page → "Dashboard" link has `sidebar-link-active`
- [x] `/congress` page → "Congress Trades" link has `sidebar-link-active`, Dashboard does NOT
- [x] `/short-interest` page → has both `sidebar-link-active` AND `sidebar-link-soon`
- [x] `/crypto/derivatives` page → "Derivatives" link has active state

### No Regression on Existing Pages
- [x] `/congress` — 25KB, renders with real data (Congress, trades, Representative markers)
- [x] `/ark` — 556KB, full content
- [x] `/crypto` — 28KB, renders
- [x] `/crypto/derivatives` — 28KB, renders
- [x] `/crypto/etf` — 20KB, renders
- [x] `/fund-flows` — 30KB, renders
- [x] `/crisis` — 19KB, renders
- [x] `/cross-asset` — 16KB, renders
- [x] `/search` — 16KB, renders
- [x] `/ranking` — 678KB, full content
- [x] `/dividend` — 83KB, renders
- [x] `/knowledge` — 37KB, renders
- [x] `/feed` — 14KB, renders

### Old Routes
- [x] `/smart-money` is NOT in the sidebar
- [ ] `/smart-money` still exists as a Navbar link (see MEDIUM finding above)

### Mobile Sidebar
- [x] Mobile close button present (`aria-label="Close sidebar"`)
- [x] Close row has `md:hidden` (visible only on mobile)
- [x] Hamburger toggle button in Navbar (`aria-label="Toggle menu"`)
- [x] Mobile backdrop renders conditionally via `{#if open}` (correct pattern)
- [x] Sidebar uses `transform: translateX(-100%)` for mobile hiding, `translateX(0)` on md+

---

## Recommendation

**SHIP ✅** — Sidebar restructure is complete and correct. The Navbar `/smart-money` reference is cosmetic/minor and can be cleaned up in a follow-up pass (Phase 1B or separate cleanup task). No regressions, no data issues, no broken links.
