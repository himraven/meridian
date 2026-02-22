"""
Meridian REST API v1 — x402 Micropayment-Gated Endpoints

Mirrors the 10 MCP tools as standard HTTP REST endpoints, gated by x402 payments
(USDC on Base L2). Each endpoint accepts the same query parameters as the
corresponding MCP tool and returns identical JSON.

Pricing (USDC on Base L2, chain ID 8453):
  GET /api/v1/congress       $0.05  — Congress trades (STOCK Act)
  GET /api/v1/ark/trades     $0.03  — ARK Invest buy/sell activity
  GET /api/v1/ark/holdings   $0.03  — ARK ETF current holdings
  GET /api/v1/insiders       $0.05  — SEC Form 4 insider trades
  GET /api/v1/13f            $0.05  — 13F institutional filings
  GET /api/v1/darkpool       $0.05  — FINRA dark pool anomalies
  GET /api/v1/short-interest $0.03  — FINRA short interest data
  GET /api/v1/superinvestors $0.03  — Superinvestor portfolio changes
  GET /api/v1/confluence     $0.10  — Multi-source confluence signals
  GET /api/v1/regime         FREE   — Market regime (Green/Yellow/Red)

Payment protocol: x402 v2
  - No payment: HTTP 402 with PAYMENT-REQUIRED header (base64 JSON with payment details)
  - With payment: send PAYMENT-SIGNATURE header signed via CDP / x402 client
  - Facilitator: https://x402.org/facilitator (Coinbase hosted)
  - Pay-to: 0xb8280cd9d2a2e7ac3be92c0b5b875c1ca7ab76f4
"""

from typing import Optional

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["v1"])


# ── Congress Trades — $0.05 ────────────────────────────────────────────────

@router.get(
    "/congress",
    summary="Congress trades — $0.05/call",
    description=(
        "US Congress stock trading activity from STOCK Act disclosures. "
        "Requires x402 payment: $0.05 USDC on Base L2."
    ),
)
def v1_congress_trades(
    party: Optional[str] = None,
    chamber: Optional[str] = None,
    trade_type: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
) -> dict:
    """
    Get US Congress stock trading activity (STOCK Act filings).

    **x402 payment required: $0.05 USDC on Base L2.**

    Send the signed payment in the `PAYMENT-SIGNATURE` header.
    Call without payment to receive HTTP 402 with payment instructions.

    Query params match the `get_congress_trades` MCP tool.
    """
    from api.mcp_server import get_congress_trades
    return get_congress_trades(
        party=party,
        chamber=chamber,
        trade_type=trade_type,
        days=days,
        limit=limit,
    )


# ── ARK Invest Trades — $0.03 ─────────────────────────────────────────────

@router.get(
    "/ark/trades",
    summary="ARK Invest trades — $0.03/call",
    description=(
        "ARK Invest buy/sell activity across all ARK ETFs. "
        "Requires x402 payment: $0.03 USDC on Base L2."
    ),
)
def v1_ark_trades(
    trade_type: Optional[str] = None,
    etf: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
) -> dict:
    """
    Get ARK Invest buy/sell activity across ARKK, ARKW, ARKG, ARKQ, ARKF, ARKX.

    **x402 payment required: $0.03 USDC on Base L2.**
    """
    from api.mcp_server import get_ark_trades
    return get_ark_trades(trade_type=trade_type, etf=etf, days=days, limit=limit)


# ── ARK Holdings — $0.03 ──────────────────────────────────────────────────

@router.get(
    "/ark/holdings",
    summary="ARK ETF holdings — $0.03/call",
    description=(
        "Current ARK ETF holdings with portfolio weights. "
        "Requires x402 payment: $0.03 USDC on Base L2."
    ),
)
def v1_ark_holdings(
    etf: Optional[str] = None,
    min_weight: float = 0.0,
    limit: int = 100,
) -> dict:
    """
    Get current ARK ETF holdings with portfolio allocation percentages.

    **x402 payment required: $0.03 USDC on Base L2.**
    """
    from api.mcp_server import get_ark_holdings
    return get_ark_holdings(etf=etf, min_weight=min_weight, limit=limit)


# ── Insider Trades — $0.05 ────────────────────────────────────────────────

@router.get(
    "/insiders",
    summary="Insider trades (SEC Form 4) — $0.05/call",
    description=(
        "SEC Form 4 insider trades with cluster buy detection. "
        "Requires x402 payment: $0.05 USDC on Base L2."
    ),
)
def v1_insider_trades(
    transaction_type: Optional[str] = None,
    ticker: Optional[str] = None,
    days: int = 30,
    cluster_only: bool = False,
    limit: int = 100,
) -> dict:
    """
    Get insider trading data from SEC Form 4 filings.

    **x402 payment required: $0.05 USDC on Base L2.**

    Includes cluster buy detection: multiple insiders buying the same stock.
    """
    from api.mcp_server import get_insider_trades
    return get_insider_trades(
        transaction_type=transaction_type,
        ticker=ticker,
        days=days,
        cluster_only=cluster_only,
        limit=limit,
    )


# ── 13F Filings — $0.05 ───────────────────────────────────────────────────

@router.get(
    "/13f",
    summary="13F institutional filings — $0.05/call",
    description=(
        "13F quarterly holdings from Berkshire, Bridgewater, Citadel, Soros, and 75+ others. "
        "Requires x402 payment: $0.05 USDC on Base L2."
    ),
)
def v1_13f_filings(
    fund: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """
    Get 13F institutional holdings from top hedge funds and asset managers.

    **x402 payment required: $0.05 USDC on Base L2.**
    """
    from api.mcp_server import get_13f_filings
    return get_13f_filings(fund=fund, limit=limit)


# ── Dark Pool Activity — $0.05 ────────────────────────────────────────────

@router.get(
    "/darkpool",
    summary="Dark pool anomalies (FINRA) — $0.05/call",
    description=(
        "FINRA off-exchange dark pool volume anomalies detected by Z-score analysis. "
        "Requires x402 payment: $0.05 USDC on Base L2."
    ),
)
def v1_darkpool_activity(
    min_zscore: float = 2.0,
    min_dpi: float = 0.4,
    days: int = 7,
    limit: int = 100,
) -> dict:
    """
    Get dark pool trading anomalies detected by statistical Z-score analysis.

    **x402 payment required: $0.05 USDC on Base L2.**

    High Z-scores (>2.0) indicate volume significantly above historical norms.
    High DPI (>0.4) means 40%+ of total volume is off-exchange (dark pool).
    """
    from api.mcp_server import get_darkpool_activity
    return get_darkpool_activity(
        min_zscore=min_zscore,
        min_dpi=min_dpi,
        days=days,
        limit=limit,
    )


# ── Short Interest — $0.03 ────────────────────────────────────────────────

@router.get(
    "/short-interest",
    summary="Short interest (FINRA) — $0.03/call",
    description=(
        "FINRA short interest for 8,600+ tickers — shares short, days to cover, % float. "
        "Requires x402 payment: $0.03 USDC on Base L2."
    ),
)
def v1_short_interest(
    ticker: Optional[str] = None,
    min_short_ratio: Optional[float] = None,
    sort_by: str = "short_interest",
    limit: int = 50,
) -> dict:
    """
    Get FINRA short interest data for 8,600+ tickers.

    **x402 payment required: $0.03 USDC on Base L2.**
    """
    from api.mcp_server import get_short_interest
    return get_short_interest(
        ticker=ticker,
        min_short_ratio=min_short_ratio,
        sort_by=sort_by,
        limit=limit,
    )


# ── Superinvestors — $0.03 ────────────────────────────────────────────────

@router.get(
    "/superinvestors",
    summary="Superinvestor activity — $0.03/call",
    description=(
        "Portfolio changes from ~80 legendary investors: Buffett, Soros, Ackman, Icahn, and more. "
        "Requires x402 payment: $0.03 USDC on Base L2."
    ),
)
def v1_superinvestor_activity(
    manager: Optional[str] = None,
    ticker: Optional[str] = None,
    activity_type: Optional[str] = None,
    limit: int = 100,
) -> dict:
    """
    Get superinvestor portfolio changes from 13F filings via Dataroma.

    **x402 payment required: $0.03 USDC on Base L2.**

    Tracks ~80 legendary investors: Buffett, Soros, Ackman, Icahn, Tepper, and more.
    """
    from api.mcp_server import get_superinvestor_activity
    return get_superinvestor_activity(
        manager=manager,
        ticker=ticker,
        activity_type=activity_type,
        limit=limit,
    )


# ── Confluence Signals — $0.10 ────────────────────────────────────────────

@router.get(
    "/confluence",
    summary="Multi-source confluence signals — $0.10/call",
    description=(
        "Stocks where multiple smart money sources agree (Congress + ARK + Dark Pool + Insider + 13F). "
        "Scored 0-100, direction-aware. Requires x402 payment: $0.10 USDC on Base L2."
    ),
)
def v1_confluence_signals(
    min_score: float = 6.0,
    sources: Optional[str] = None,
    days: int = 7,
    limit: int = 100,
) -> dict:
    """
    Get multi-source smart money consensus signals (confluence engine).

    **x402 payment required: $0.10 USDC on Base L2.**

    Scores 0-100 based on how many independent smart money sources agree:
    Congress trades, ARK buys, dark pool anomalies, insider purchases, 13F positions.
    """
    from api.mcp_server import get_confluence_signals
    return get_confluence_signals(
        min_score=min_score,
        sources=sources,
        days=days,
        limit=limit,
    )


# ── Market Regime — FREE ──────────────────────────────────────────────────

@router.get(
    "/regime",
    summary="Market regime — FREE (no payment needed)",
    description=(
        "Current market regime: Green (risk-on) / Yellow (caution) / Red (defensive). "
        "FREE endpoint — no x402 payment required."
    ),
)
def v1_market_regime() -> dict:
    """
    Get current market regime assessment via VIX + SPY 200MA + credit spreads.

    **FREE endpoint — no x402 payment required.**

    Returns Green (risk-on), Yellow (caution), or Red (defensive) regime
    with detailed breakdown of each indicator.
    """
    from api.mcp_server import get_market_regime
    return get_market_regime()
