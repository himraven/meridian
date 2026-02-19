# Meridian Knowledge Hub — Content

## Article Format (JSON)
Each article is a JSON file: `{slug}.json`

```json
{
  "slug": "congress-trading-alpha",
  "title": "Congressional Trading: Information Edge or Insider Advantage?",
  "subtitle": "Why Congress members' stock trades consistently beat the market",
  "category": "signal-guide",
  "signal_source": "congress",
  "tldr": "U.S. Congress members' stock trades have outperformed the S&P 500 by an average of 6% over 30 days, driven by information asymmetry from committee hearings and policy access.",
  "hero_stat": {
    "value": "+6%",
    "label": "Average 30-day excess return",
    "source": "2025 International Review of Economics & Finance"
  },
  "content_md": "... full markdown content (English) ...",
  "content_zh": null,  // Chinese version — null for now, Phase 1 add later
  "key_takeaways": [
    "Congress trades outperform by 6% on average over 30 days",
    "Trading volume increases 50% during congressional sessions",
    "STOCK Act disclosure lag (45 days) creates actionable window"
  ],
  "related_articles": ["insider-buying-signals", "13f-institutional-tracking"],
  "related_masters": ["warren-buffett", "peter-lynch"],
  "academic_references": [
    {
      "title": "Congressional Trading and Information Asymmetry",
      "journal": "International Review of Economics & Finance",
      "year": 2025,
      "key_finding": "Trading volume increases ~50% during sessions"
    }
  ],
  "seo": {
    "keywords": ["congress stock trading", "congressional trading", "STOCK Act", "political trading alpha"],
    "description": "Learn why U.S. Congress members' stock trades consistently outperform the market and how Meridian tracks this signal."
  },
  "social": {
    "hook_zh": "美国国会议员炒股，年化跑赢标普30%",
    "hook_en": "Congress members beat the S&P 500 by 30% annually. Here's why.",
    "hashtags": ["#CongressTrading", "#SmartMoney", "#InvestmentSignals"]
  },
  "updated_at": "2026-02-19"
}
```

## Signal Source Mapping
- congress → Congress Trading
- insiders → Insider Trading  
- ark → ARK Invest
- institutions → 13F Institutional Holdings
- darkpool → Dark Pool Activity
- short_interest → Short Interest
- superinvestors → Superinvestor Tracking

## Content Guidelines
- Language: English (primary), Chinese hooks for social media
- Tone: Authoritative but accessible. Like a smart friend explaining finance.
- Length: L1 articles ~1500-2000 words
- Always include: specific numbers, academic citations, "How Meridian Uses It"
- Never: investment advice, guaranteed returns, fear-mongering
