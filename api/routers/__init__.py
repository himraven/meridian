"""
Meridian — Router Registration
Registers all API route modules with the main FastAPI app.
"""

from fastapi import FastAPI

from . import (
    us,
    hk,
    cn,
    dividend,
    ticker,
    research,
    data_health,
    system,
    knowledge,
    macro,
    discovery,
)


def register_routers(app: FastAPI) -> None:
    """Register all routers with the FastAPI app."""

    # US market routes (Congress, ARK, DarkPool, 13F, Signals)
    app.include_router(us.router, tags=["us-market"])

    # HK market routes
    app.include_router(hk.router, tags=["hk-market"])

    # CN market routes
    app.include_router(cn.router, tags=["cn-market"])

    # Dividend screener routes
    app.include_router(dividend.router, tags=["dividend"])

    # Ticker lookup routes
    app.include_router(ticker.router, tags=["ticker"])

    # Research report routes
    app.include_router(research.router, tags=["research"])

    # Data health monitoring
    app.include_router(data_health.router, tags=["ops"])

    # System status (DuckDB, etc.)
    app.include_router(system.router, tags=["system"])

    # Knowledge Hub (educational articles)
    app.include_router(knowledge.router, tags=["knowledge"])

    # Macro / Market Regime (Regime Detector, Crisis Dashboard, Cross-Asset)
    app.include_router(macro.router, tags=["macro"])

    # Agent discovery (health, stats, openapi spec)
    app.include_router(discovery.router, tags=["discovery"])
