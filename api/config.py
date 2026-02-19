"""
Smart Money Intelligence Platform — Configuration

All paths, weights, thresholds, and API settings in one place.
Environment variables override defaults where applicable.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict


# ── Paths ──────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent  # smart-money-platform/
API_ROOT = Path(__file__).parent             # smart-money-platform/api/
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "static"


# ── Cache Filenames ────────────────────────────────────────────────────────

CACHE_FILES = {
    "congress": "congress.json",
    "darkpool": "darkpool.json",
    "ark_trades": "ark_trades.json",
    "ark_holdings": "ark_holdings.json",
    "institutions": "institutions.json",
    "insiders": "insiders.json",
    "superinvestors": "superinvestors.json",
    "signals": "signals.json",
    "congress_backtest": "congress_backtest.json",
    "ticker_metadata": "ticker_metadata.json",
    "short_interest": "short_interest.json",
}


# ── Signal Weights (PRD §2.3) ─────────────────────────────────────────────

SIGNAL_WEIGHTS: Dict[str, float] = {
    "congress": 1.0,
    "ark": 1.0,
    "darkpool": 0.8,
    "institutions": 0.6,
}


# ── Signal Thresholds (PRD §2.1) ──────────────────────────────────────────

@dataclass(frozen=True)
class CongressThresholds:
    """PRD: Congress signal criteria."""
    min_amount: float = 15_000       # Minimum trade amount ($)
    max_age_days: int = 45           # Regulatory filing limit
    signal_lookback_days: int = 30   # For confluence window


@dataclass(frozen=True)
class DarkPoolThresholds:
    """PRD: DPI anomaly criteria."""
    min_dpi: float = 0.4             # Minimum Dark Pool Index
    z_score_threshold: float = 2.0   # 95% confidence (2σ)
    min_volume: int = 500_000        # Minimum daily volume (shares)
    rolling_window_days: int = 30    # For Z-score calculation
    history_days: int = 90           # Days of history to fetch
    signal_lookback_days: int = 7    # Anomaly recency window


@dataclass(frozen=True)
class ArkThresholds:
    """PRD: ARK signal criteria."""
    min_weight_pct: float = 1.0      # Min % of ETF portfolio
    signal_lookback_days: int = 30   # For confluence window


@dataclass(frozen=True)
class InstitutionThresholds:
    """PRD: 13F signal criteria."""
    min_value: float = 50_000_000    # Minimum position value ($)
    min_change_pct: float = 10.0     # Minimum QoQ change (%)
    signal_lookback_days: int = 90   # Quarterly cadence


@dataclass(frozen=True)
class ConfluenceThresholds:
    """PRD: Confluence scoring parameters."""
    time_window_days: int = 7        # ±7 days for signal grouping
    max_possible_score: float = 5.0  # For normalization
    min_signals_for_confluence: int = 2  # Require ≥2 signals
    default_min_score: float = 6.0   # Default score filter


CONGRESS = CongressThresholds()
DARKPOOL = DarkPoolThresholds()
ARK = ArkThresholds()
INSTITUTIONS = InstitutionThresholds()
CONFLUENCE = ConfluenceThresholds()


# ── ARK ETFs ───────────────────────────────────────────────────────────────

ARK_ETFS: Dict[str, str] = {
    "ARKK": "ARK Innovation ETF",
    "ARKW": "ARK Next Generation Internet ETF",
    "ARKQ": "ARK Autonomous Tech & Robotics ETF",
    "ARKG": "ARK Genomic Revolution ETF",
    "ARKF": "ARK Fintech Innovation ETF",
    "ARKX": "ARK Space Exploration ETF",
}


# ── External APIs ─────────────────────────────────────────────────────────

# Quiver Quantitative
QUIVER_API_KEY = os.getenv("QUIVER_API_KEY", "")
QUIVER_BASE_URL = "https://api.quiverquant.com/beta"
QUIVER_RATE_LIMIT_PER_MIN = 30  # Free tier: ~30 req/min
QUIVER_DAILY_LIMIT = 2000       # Free tier: 2000 req/day

# Quiver Endpoints
QUIVER_ENDPOINTS = {
    "congress_house": f"{QUIVER_BASE_URL}/historical/housetrading",
    "congress_senate": f"{QUIVER_BASE_URL}/historical/senatetrading",
    "darkpool": f"{QUIVER_BASE_URL}/historical/offexchange",
    "ark_trades": f"{QUIVER_BASE_URL}/historical/ark",
    # 13F uses SEC EDGAR, not Quiver
}

# ARK direct data
ARK_HOLDINGS_URL = "https://ark-funds.com/wp-content/uploads/funds-etf-csv/ARK_{fund}_ETF_{ticker}_HOLDINGS.csv"
CATHIES_ARK_API = "https://cathiesark.com/api"


# ── Notification ───────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


# ── Existing Data Paths (backward compat with rsnest) ─────────────────────
# These paths use environment variables for Docker compatibility

LEGACY_ARK_DATA_DIR = os.getenv(
    "CLAWD_ARK_DATA_DIR",
    "/home/raven/clawd/projects/quant-engine/us-signals/smart-money-tracker/data"
)
LEGACY_SIGNAL_LOG = os.getenv(
    "CLAWD_SIGNALS_DIR",
    "/home/raven/clawd/shared/signals"
) + "/signal_log.jsonl"


# ── Sectors ────────────────────────────────────────────────────────────────

SECTORS = [
    "Technology",
    "Healthcare",
    "Finance",
    "Energy",
    "Consumer Discretionary",
    "Consumer Staples",
    "Industrials",
    "Materials",
    "Real Estate",
    "Utilities",
    "Communication Services",
]


# ── Tracked Institutions (13F) ─────────────────────────────────────────────

# CIK → {name, manager} for display and lookup
TRACKED_INSTITUTIONS: Dict[str, Dict[str, str]] = {
    "0001067983": {"name": "Berkshire Hathaway", "manager": "Warren Buffett"},
    "0001350694": {"name": "Bridgewater Associates", "manager": "Ray Dalio"},
    "0001037389": {"name": "Renaissance Technologies", "manager": "Jim Simons"},
    "0001423053": {"name": "Citadel Advisors", "manager": "Ken Griffin"},
    "0001656456": {"name": "Appaloosa Management", "manager": "David Tepper"},
    "0001336528": {"name": "Pershing Square Capital", "manager": "Bill Ackman"},
    "0001029160": {"name": "Soros Fund Management", "manager": "George Soros"},
}
