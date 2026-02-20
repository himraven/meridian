# Meridian Knowledge Hub — Content Production Plan

## Architecture: L1 → L2 → L3

```
L1: Signal Guide (入口层)     — "What & Why" — 3 min read — 引流+SEO
L2: Deep Dive (深入层)        — "How & Evidence" — 10 min read — 建立专业感
L3: Expert Perspectives (大师层) — "Who thinks what" — 5 min read — 权威感
```

Internal linking: L1 ↔ L2 ↔ L3 互相引用，形成网状结构

---

## Content Matrix

### 🏛️ Congress Trading
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `congress-trading-alpha` | Congressional Trading: Information Edge or Insider Advantage? | ✅ Done | — |
| L2 | `congress-disclosure-delay` | The 45-Day Window: Trading the STOCK Act Disclosure Delay | Todo | frameworks/behavioral-finance.md |
| L2 | `congress-committee-alpha` | Committee Alignment: Where the Real Alpha Lives | Todo | smart-money/congressional-trading-alpha.md |
| L3 | `congress-pelosi-effect` | The Pelosi Effect: Tracking the Speaker's Portfolio | Todo | New research |
| L3 | `congress-bipartisan-signals` | When Both Parties Buy: Bipartisan Trading Signals | Todo | New research |

### 👔 Insider Trading
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `insider-buying-signals` | Insider Cluster Buying: When the People Who Know Best Are Buying | ✅ Done | — |
| L2 | `insider-cluster-patterns` | Cluster Buying Patterns: Why Multiple Insiders Matter More | Todo | signals/insider-cluster-patterns.md |
| L2 | `insider-form4-reading` | Reading SEC Form 4: A Practical Guide | Todo | New (technical guide) |
| L3 | `insider-peter-lynch` | Peter Lynch on Insider Buying: "Insiders Buy for Only One Reason" | Todo | masters/peter-lynch.md |
| L3 | `insider-buffett-skin-in-game` | Buffett's Rule: Only Invest Where Management Has Skin in the Game | Todo | masters/warren-buffett.md |

### 🏦 13F Institutional Holdings
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `13f-institutional-tracking` | Following the Giants: A Guide to 13F Institutional Tracking | ✅ Done | — |
| L2 | `13f-ownership-signals` | Institutional Ownership Signals: Concentration, Changes & Crowding | Todo | signals/institutional-ownership-effect.md |
| L2 | `13f-quarterly-lag` | The 45-Day Lag Problem: How to Read Stale 13F Data | Todo | New |
| L3 | `13f-buffett-portfolio` | Inside Berkshire's Portfolio: Lessons from Buffett's 13F | Todo | masters/warren-buffett.md |
| L3 | `13f-dalio-all-weather` | Ray Dalio's All Weather: What 13F Reveals About Risk Parity | Todo | masters/ray-dalio.md |
| L3 | `13f-soros-reflexivity` | Soros's 13F: Trading Reflexivity in Real Time | Todo | masters/george-soros.md |

### 🦅 ARK Invest
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `ark-disruptive-innovation` | ARK Invest: Tracking Cathie Wood's Disruptive Bets | ✅ Done | — |
| L2 | `ark-conviction-scoring` | ARK's Conviction Trades: When Size and Timing Align | Todo | New |
| L2 | `ark-etf-flow-dynamics` | ETF Flow Dynamics: How Fund Flows Create Predictable Patterns | Todo | frameworks/etf-flow-dynamics.md |
| L3 | `ark-cathie-wood-philosophy` | Cathie Wood's Investment Philosophy: 5-Year Time Horizons | Todo | New research |

### 🌑 Dark Pool
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `dark-pool-activity` | Dark Pool Activity: Tracking Institutional Footprints | ✅ Done | — |
| L2 | `dark-pool-microstructure` | Market Microstructure: How Dark Pools Actually Work | Todo | market-structure/us-equity-market-microstructure.md |
| L2 | `dark-pool-zscore-signals` | Z-Score Anomalies: When Dark Pool Volume Screams | Todo | New |
| L3 | `dark-pool-flash-boys` | From Flash Boys to Smart Money: The Evolution of Dark Pools | Todo | market-structure/ |

### 📉 Short Interest
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `short-interest-analysis` | Short Sellers' Conviction: Reading Short Interest Data | ✅ Done | — |
| L2 | `short-squeeze-mechanics` | Short Squeeze Mechanics: DTC, CTB, and the Squeeze Signal | Todo | signals/short-interest-squeeze-signals.md |
| L2 | `short-seller-methodology` | How Professional Short Sellers Think | Todo | frameworks/short-selling-methodology.md |
| L3 | `short-burry-method` | Michael Burry's Short Methodology: The Big Short & Beyond | Todo | masters/michael-burry.md |
| L3 | `short-chanos-fraud` | Jim Chanos: The Art of Forensic Short Selling | Todo | masters/jim-chanos.md |

### 🏆 Superinvestors
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `superinvestor-tracking` | Superinvestors: What Buffett, Dalio & Ackman Are Buying | ✅ Done | — |
| L2 | `superinvestor-cloning` | Portfolio Cloning: How to Follow Superinvestors Systematically | Todo | frameworks/concentrated-portfolio-strategy.md |
| L2 | `superinvestor-overlap` | When Giants Agree: Multi-Superinvestor Overlap Signals | Todo | New |
| L3 | `superinvestor-munger-mental-models` | Charlie Munger's Mental Models for Investment | Todo | masters/charlie-munger.md |
| L3 | `superinvestor-ackman-activist` | Bill Ackman: The Activist Playbook | Todo | masters/bill-ackman.md |

### 🔀 Cross-Signal (Meridian Unique)
| Layer | Slug | Title | Status | Source |
|-------|------|-------|--------|--------|
| L1 | `confluence-signals-explained` | Signal Confluence: When Smart Money Converges | Todo | NEW — Meridian's core differentiator |
| L2 | `conviction-scoring-methodology` | How Meridian Scores Conviction: The V7 Engine | Todo | Technical docs |
| L2 | `multi-source-backtesting` | Multi-Source Signal Backtesting: Does Confluence Work? | Todo | New research |

---

## Recurring Content (Auto-Generated)

| Type | Frequency | Slug Pattern | Generator |
|------|-----------|-------------|-----------|
| Weekly Recap | Mon AM | `weekly-recap-2026-W{XX}` | `scripts/gen_weekly_recap.py` |
| Monthly Top Signals | 1st of month | `monthly-signals-2026-{MM}` | `scripts/gen_monthly_recap.py` |
| Quarterly 13F Review | After 13F deadline | `quarterly-13f-2026-Q{X}` | Manual + data |

---

## Priority Execution Order

### Phase 1: Core L1 + First L2s (Week 1)
1. `confluence-signals-explained` — L1, Meridian's unique value prop, NO competitor has this
2. `congress-committee-alpha` — L2, strongest SEO keyword cluster
3. `insider-cluster-patterns` — L2, actionable + data-backed
4. `short-squeeze-mechanics` — L2, high search volume (WSB audience)
5. `13f-buffett-portfolio` — L3, name recognition = clicks

### Phase 2: Auto-Generation Pipeline (Week 1-2)
6. Weekly Recap generator script + cron
7. Monthly Top Signals generator script + cron

### Phase 3: L3 Masters (Week 2-3)
8-12. Top 5 master articles (Buffett, Lynch, Burry, Soros, Munger)

### Phase 4: Remaining L2s (Week 3-4)
13-20. Fill remaining L2 deep dives

---

## SEO Strategy Per Article

Every article JSON includes:
- `seo.keywords` — 5-8 long-tail keywords
- `seo.description` — 150-160 char meta description
- `content_md` — H2/H3 structure, FAQ sections for featured snippets
- `hero_stat` — Data point for social sharing
- `social.hook_en` / `social.hook_zh` — Pre-written social copy
- `related_articles` — Internal linking to other L1/L2/L3

## GEO (Generative Engine Optimization)
- Every article starts with clear TL;DR
- FAQ-style H2 headings ("Why do congress members outperform?")
- Specific data points with sources (citation-friendly)
- Structured data (Article + FAQ schema) in frontend

---

## Article JSON Template

```json
{
  "slug": "congress-committee-alpha",
  "title": "Committee Alignment: Where the Real Alpha Lives",
  "subtitle": "Congress members trading in their own committee's sector...",
  "category": "deep-dive",
  "signal_source": "congress",
  "layer": "L2",
  "parent_article": "congress-trading-alpha",
  "tldr": "One-paragraph summary...",
  "hero_stat": { "value": "12.4%", "label": "Annual alpha from committee-aligned trades", "source": "Eggers & Hainmueller 2013" },
  "content_md": "## Full markdown content...",
  "key_takeaways": ["...", "...", "..."],
  "related_articles": ["congress-trading-alpha", "congress-pelosi-effect"],
  "seo": { "keywords": [...], "description": "..." },
  "social": { "hook_en": "...", "hook_zh": "...", "hashtags": [...] },
  "updated_at": "2026-02-20"
}
```
