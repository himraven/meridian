#!/usr/bin/env python3
"""Patch under-1500-word articles with additional content."""
import json, os

BASE = "/home/raven/meridian/content/knowledge"

# ── helper ───────────────────────────────────
def patch(filename, extra_section):
    path = os.path.join(BASE, filename)
    with open(path) as f:
        d = json.load(f)
    d["content_md"] = d["content_md"] + "\n\n" + extra_section
    with open(path, "w") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    words = len(d["content_md"].split())
    print(f"✓ {filename}: {words} words (after patch)")

# ── 13F: add a Practical Tools section ───────
patch("13f-institutional-tracking.json", """## Practical Tools for Individual Investors

The democratization of 13F data over the past decade has made institutional tracking accessible to any investor willing to spend an afternoon learning a few platforms. Dataroma.com is the simplest starting point: it aggregates the reported holdings of approximately 70 of the most widely followed superinvestors and hedge funds, updated after each quarterly filing deadline. You can see at a glance which stocks are most widely held, which positions were added or increased most recently, and which managers share overlapping views on a given company.

WhaleWisdom offers a more quantitative approach, providing historical 13F data with backtesting capabilities that allow you to validate how specific clone strategies would have performed over prior years. Their "Whalescore" metric ranks funds by historical stock-picking performance, giving you a pre-filtered list of the managers whose disclosures are most worth tracking. For the technically inclined, the SEC's own EDGAR database provides raw 13F XML files accessible via API, making it possible to build custom aggregation and scoring tools in Python with relatively modest effort.

Quiver Quantitative has emerged as one of the most useful platforms for institutional data in a structured, API-accessible format — particularly valuable for quantitative investors who want to incorporate 13F signals into systematic models. The key lesson from practitioners who have used these tools extensively: the quality of your filter matters far more than the breadth of coverage. Tracking 20 high-conviction managers with documented long-term outperformance is more valuable than aggregating signals from all 10,000+ 13F filers, most of whom add no incremental information beyond what passive indices already reflect.""")

# ── ARK: add a Practical Use section ─────────
patch("ark-disruptive-innovation.json", """## Practical Use: Tracking ARK in Real Time

ARK's daily disclosure files are available for free at ark-funds.com/funds, published after 4 PM EST each trading day. Each file lists every holding by ETF (ARKK, ARKG, ARKQ, ARKW, ARKF, ARKX), including shares held, market value, and whether the position increased, decreased, or was unchanged from the prior day. Building a simple monitoring system in Python using these files is a weekend project that provides one of the most transparent windows into an active manager's thinking available anywhere in the market.

The most systematic approach to ARK signal extraction is computing a 20-day rolling net flow for each position: the sum of shares added minus shares removed over the prior 20 trading days, normalized by total position size. A persistently positive rolling flow — ARK consistently adding to a position over multiple weeks — is a stronger signal than a single-day purchase. This persistence filter eliminates the noise of portfolio rebalancing and isolates the names where ARK is expressing genuine conviction growth.

Several free and low-cost platforms have built tools around ARK's daily disclosures. Cathiesark.com and Ark-tracker.com provide real-time alerts when ARK crosses key ownership thresholds in specific companies. For investors focused on specific innovation themes — such as AI infrastructure, genomic medicine, or space exploration — monitoring ARK's activity in those sub-sectors provides an early-warning system for where institutional innovation capital is flowing, often well before traditional analyst coverage or mainstream media attention catches up.""")

# ── Superinvestors: add Accessing the Data ───
patch("superinvestor-tracking.json", """## Accessing Superinvestor Data

The practical infrastructure for superinvestor tracking has become remarkably accessible over the past decade. Dataroma.com is the canonical free starting point: it tracks approximately 70 superinvestors' 13F-reported positions, providing a searchable interface to see current holdings, recent changes, and the "popularity" of specific stocks across the tracked universe. GuruFocus extends this with deeper historical data, valuation metrics, and alerts when tracked managers make portfolio changes.

For a more quantitative approach, WhaleWisdom allows you to construct custom clone portfolios from any combination of tracked managers, backtest them against historical data, and monitor for new position changes as 13F filings are processed. The platform's "clone portfolio" feature is one of the most direct implementations of the academic research literature on institutional tracking — allowing individual investors to construct and monitor the kind of Best Ideas portfolio that Cohen, Polk, and Silli showed generates 1.6–2.1% quarterly alpha.

The key discipline in superinvestor tracking is resisting the temptation to follow every position change. The signal quality is highest in the positions that represent genuine conviction — large holdings that have persisted across multiple quarters, or significant new additions representing a meaningful allocation of the manager's total portfolio. A Buffett position that is 8% of Berkshire's portfolio is worth far more analytical attention than a 0.3% position that may reflect nothing more than a routine cash deployment. Filter for size, filter for persistence, and focus your attention where the concentration of capital signals the concentration of conviction.""")

# ── Congress: add a Policy Sectors section ───
patch("congress-trading-alpha.json", """## Policy-Sensitive Sectors: Where the Signal is Strongest

The congressional trading signal is not uniformly distributed across all sectors. The academic research and empirical data both point to specific industries where the committee structure of Congress creates the most direct information advantage: defense and aerospace (Armed Services Committees), healthcare and pharmaceuticals (Health committees and FDA oversight), energy (Energy committees and EPA regulation), financial services (Banking and Finance committees), and technology regulation (Commerce and Judiciary). In these sectors, the committee-aligned signal is substantially stronger than the market-wide average.

For practical application, the most reliable filter is to match a trading member's committee assignments against the sector of the stock being traded. A member of the Senate Armed Services Committee buying shares in a defense contractor in the weeks before a Pentagon budget announcement is a qualitatively different signal from the same member buying shares in a consumer technology company with no regulatory relevance to their work. The STOCK Act data provides all the information needed to apply this filter — committee assignments are public record, and Quiver Quantitative and Capitol Trades have pre-built this filtering into their platforms.

Geopolitical stress events are another moment when the congressional signal historically strengthens. The 2025 research on Liberation Day tariff trading — 700+ transactions by members and families around the April announcement — illustrates that major policy inflection points are precisely when the information asymmetry between Congress members and the public is greatest. Monitoring congressional disclosure filings in the weeks surrounding major legislative calendars (budget votes, regulatory deadlines, trade policy announcements) provides a higher-signal data environment than passive year-round monitoring.""")

print("\nPatch complete.")
