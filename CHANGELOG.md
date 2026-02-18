# Meridian — Changelog

All notable changes to the Meridian platform are documented here.

---

## 2026-02-18 — Data Architecture Overhaul + Scoring Engine Upgrade

### Data Architecture
- **Fixed**: Switched from hardlink-based data sharing to direct bind mount of rsnest data dir
  - Hardlinks break on atomic write (`os.replace`); bind mount is instant and reliable
- **Fixed**: ARK trade data missing — mounted clawd ark-data directory → 1,477 trades + 6 ETFs restored
- **Fixed**: Research reports path — separate mount at `/app/research` with `RESEARCH_DIR` env var
- **Cleaned**: Removed broken symlinks in shared data directory (`json→`, `smartmoney.db→`)
- **Hardened**: signals, research, ark-data mounted as `:ro` (read-only)

### Scoring Engine
- **Upgraded**: `/api/signals/confluence` now reads V2 engine (`signals_v2.json`) with conviction-based scoring
  - V1: 0-4 range, no multi-source detection → V2: 0-100 range, multi-source bonus
  - e.g. GOOG: 3 sources (ARK + Congress + Institution) → score 100
- **Fixed**: V2 engine module (`cross_signal_engine_v2.py`) copied to rsnest so crons generate both v1 + v2

### API Fixes
- **Fixed**: `/api/congress/trades` — `last_updated` was null (wrong nesting path)
- **Fixed**: `/api/congress/trades` — added `buy_count` / `sell_count` to metadata
- **Added**: `/api/data-health` — comprehensive data freshness monitoring (16 sources)
  - Weekend/holiday-aware thresholds
  - Critical vs non-critical classification
  - 🟢🟡🔴 three-level status

### Frontend
- **Added**: Data Health Indicator in sidebar bottom (auto-refreshes every 5 min)
- **Fixed**: Score bars on ticker detail page — changed from `/3` to `/100` scale (V2 engine)
- **Fixed**: Congress buy/sell count — handled both "Buy"/"Purchase" and "Sell"/"Sale" trade types
- **Updated**: CN strategy references from 8x30 → 12x30

### Data Health Sources Monitored
| Source | Schedule | Critical |
|--------|----------|----------|
| Congress Trades | 3x/day | ✅ |
| ARK Trades (JSON) | 4x/day Mon-Fri | ✅ |
| ARK Changes (JSONL) | On activity | ✅ |
| Dark Pool | Daily Tue-Sat | ✅ |
| Confluence Signals | 2x/day | ✅ |
| CN 12x30 Portfolio | Daily (trading days) | ✅ |
| CN Trend State | Daily (trading days) | ✅ |
| HK Daily Signals | Daily (trading days) | ✅ |
| Institution 13F | Weekly Monday | |
| Research Reports | On-demand | |
| SQLite Database | With collectors | |

### Architecture (Final)
```
rsnest crons (smart-money-api)
  └── writes: signals.json + signals_v2.json + congress/ark/darkpool JSON
       │  direct bind mount
       ├── meridian /app/data/:ro
       ├── clawd ark-data → /app/ark-data/:ro  
       ├── data/signals → /app/signals/:ro
       ├── data/research → /app/research/:ro
       └── data/db → /app/db/ (writable)
```

---

*Maintained by Nova*
