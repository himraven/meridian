"""
Meridian — Smart Money Intelligence Platform
FastAPI Backend serving APIs for multi-market signal analysis.

Routers: US (ARK, Congress, DarkPool, 13F), CN, HK, Ticker, Dividend
"""

import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

import threading

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from fastapi.responses import ORJSONResponse
    DEFAULT_RESPONSE_CLASS = ORJSONResponse
except ImportError:
    from fastapi.responses import JSONResponse
    DEFAULT_RESPONSE_CLASS = JSONResponse

from api.shared import smart_money_cache, ticker_names

# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Meridian — Smart Money Intelligence Platform",
    description="Where smart money signals converge. Multi-market signal analysis across US, CN, and HK markets.",
    version="1.0.0",
    default_response_class=DEFAULT_RESPONSE_CLASS,
)

# ── Middleware ─────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)

import os
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SmartCacheMiddleware(BaseHTTPMiddleware):
    """Tiered cache-control for API endpoints."""

    CACHE_MEDIUM = {
        "/api/us/13f", "/api/us/ark", "/api/congress/trades",
        "/api/signals/confluence", "/api/dividend-screener",
        "/api/cn/8x30/portfolio", "/api/cn/8x30/nav", "/api/cn/8x30/metrics",
        "/api/hk/signals",
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path

        if not path.startswith("/api/"):
            return response

        if path in ("/health", "/api/health"):
            response.headers["Cache-Control"] = "no-cache"
        elif any(path.startswith(p) for p in self.CACHE_MEDIUM):
            response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


app.add_middleware(SmartCacheMiddleware)


# ── Lightweight API Metrics (no Prometheus, just in-memory + log slow requests) ──
import time
import logging
from collections import deque

logger = logging.getLogger(__name__)

_request_metrics: deque = deque(maxlen=5000)  # rolling window
_SLOW_THRESHOLD_MS = 300  # log requests slower than this

class MetricsMiddleware(BaseHTTPMiddleware):
    """Track request latency, log slow requests, expose /api/metrics."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/api/metrics", "/health", "/api/health"):
            return await call_next(request)
        
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        path = request.url.path
        if path.startswith("/api/"):
            _request_metrics.append({
                "path": path,
                "method": request.method,
                "status": response.status_code,
                "ms": round(elapsed_ms, 1),
                "ts": time.time(),
            })
            if elapsed_ms > _SLOW_THRESHOLD_MS:
                logger.warning(f"[slow] {request.method} {path} → {elapsed_ms:.0f}ms (status {response.status_code})")
        
        response.headers["X-Response-Time"] = f"{elapsed_ms:.0f}ms"
        return response


app.add_middleware(MetricsMiddleware)


# ── x402 Payment Middleware ────────────────────────────────────────────────
# Gates the paid REST v1 endpoints (see /api/v1/*).
# Free routes (/api/v1/regime and all non-v1 routes) pass through unchanged.
# The MCP server at /mcp is NOT affected — it remains free.
try:
    from x402.http import HTTPFacilitatorClient
    from x402.http.middleware.fastapi import payment_middleware
    from x402 import x402ResourceServer
    from x402.mechanisms.evm.exact import ExactEvmServerScheme

    _X402_PAY_TO = "0xb8280cd9d2a2e7ac3be92c0b5b875c1ca7ab76f4"
    _X402_NETWORK = "eip155:8453"  # Base mainnet

    # Route → payment config. /api/v1/regime intentionally absent (FREE).
    _X402_ROUTES = {
        "GET /api/v1/congress":       {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.05", "network": _X402_NETWORK}},
        "GET /api/v1/ark/trades":     {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.03", "network": _X402_NETWORK}},
        "GET /api/v1/ark/holdings":   {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.03", "network": _X402_NETWORK}},
        "GET /api/v1/insiders":       {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.05", "network": _X402_NETWORK}},
        "GET /api/v1/13f":            {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.05", "network": _X402_NETWORK}},
        "GET /api/v1/darkpool":       {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.05", "network": _X402_NETWORK}},
        "GET /api/v1/short-interest": {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.03", "network": _X402_NETWORK}},
        "GET /api/v1/superinvestors": {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.03", "network": _X402_NETWORK}},
        "GET /api/v1/confluence":     {"accepts": {"scheme": "exact", "payTo": _X402_PAY_TO, "price": "$0.10", "network": _X402_NETWORK}},
    }

    _x402_facilitator = HTTPFacilitatorClient({"url": "https://x402.org/facilitator"})
    _x402_server = x402ResourceServer(_x402_facilitator)
    _x402_server.register(_X402_NETWORK, ExactEvmServerScheme())

    # Create middleware function once (holds initialization state in closure).
    # sync_facilitator_on_start=False: don't block on startup; the facilitator
    # is only needed when verifying actual payments, not for returning 402s.
    _x402_middleware_fn = payment_middleware(
        _X402_ROUTES,
        _x402_server,
        sync_facilitator_on_start=False,
    )

    @app.middleware("http")
    async def x402_payment_middleware(request: Request, call_next):
        """Intercept paid v1 routes — return 402 or verify payment before routing."""
        try:
            return await _x402_middleware_fn(request, call_next)
        except Exception as exc:
            # Fail closed: never expose paid content on middleware crash
            logger.error(f"[x402] Middleware error on {request.url.path}: {exc}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content={"error": "payment_service_unavailable"},
                status_code=503,
            )

    print("[x402] Payment middleware registered — 9 paid v1 endpoints (USDC on Base L2, eip155:8453)")

except ImportError as exc:
    print(f"[x402] Package not installed ({exc}) — payment gating disabled")
except Exception as exc:
    print(f"[x402] Middleware setup failed ({exc}) — payment gating disabled")


@app.get("/api/metrics")
def api_metrics():
    """Lightweight request metrics — no external dependencies."""
    now = time.time()
    recent = [m for m in _request_metrics if now - m["ts"] < 3600]  # last hour
    
    if not recent:
        return {"requests_1h": 0, "avg_ms": 0, "slow_requests": [], "top_endpoints": []}
    
    # Aggregate by endpoint
    endpoints: dict = {}
    for m in recent:
        p = m["path"]
        if p not in endpoints:
            endpoints[p] = {"count": 0, "total_ms": 0, "max_ms": 0, "errors": 0}
        endpoints[p]["count"] += 1
        endpoints[p]["total_ms"] += m["ms"]
        endpoints[p]["max_ms"] = max(endpoints[p]["max_ms"], m["ms"])
        if m["status"] >= 400:
            endpoints[p]["errors"] += 1
    
    top = sorted(
        [{"path": k, "count": v["count"], "avg_ms": round(v["total_ms"]/v["count"], 1), 
          "max_ms": v["max_ms"], "errors": v["errors"]} 
         for k, v in endpoints.items()],
        key=lambda x: x["count"], reverse=True
    )[:20]
    
    slow = [m for m in recent if m["ms"] > _SLOW_THRESHOLD_MS][-20:]
    
    return {
        "requests_1h": len(recent),
        "avg_ms": round(sum(m["ms"] for m in recent) / len(recent), 1),
        "p95_ms": round(sorted(m["ms"] for m in recent)[int(len(recent)*0.95)], 1) if len(recent) > 1 else 0,
        "slow_requests": len(slow),
        "top_endpoints": top,
        "recent_slow": slow,
    }


# ── Startup Event ──────────────────────────────────────────────────────────
@app.on_event("startup")
def init_database():
    """Initialize SQLite database tables on startup."""
    try:
        from api.database import init_db
        init_db()
        print("[database] SQLite tables initialized")
    except Exception as e:
        print(f"[database] Init failed (falling back to JSON): {e}")


@app.on_event("startup")
def init_duckdb():
    """Initialize DuckDB query layer on startup (runs in background thread)."""
    def _run():
        try:
            from api.modules.db_init import init_duckdb as _init
            _init()
        except Exception as e:
            print(f"[duckdb] Startup init failed (API will use JSON fallback): {e}")

    threading.Thread(target=_run, daemon=True, name="duckdb-init").start()


@app.on_event("startup")
def bootstrap_ticker_names():
    """Pre-populate ticker names from all data sources + yfinance on startup."""
    def _bootstrap():
        ticker_names._ensure_initialized()
        all_tickers = set()
        for src in ["congress.json", "ark_trades.json", "ark_holdings.json", "darkpool.json"]:
            data = smart_money_cache.read(src)
            if isinstance(data, dict):
                for item in data.get("trades", []) + data.get("holdings", []) + data.get("tickers", []):
                    tk = item.get("ticker", "").strip()
                    if tk:
                        all_tickers.add(tk)

        missing = [t for t in all_tickers if t not in ticker_names._names]
        if missing:
            print(f"[ticker_lookup] Resolving {len(missing)} missing ticker names via yfinance...")
            ticker_names.bulk_resolve(missing)
            print(f"[ticker_lookup] Done. Total: {ticker_names.count} tickers mapped.")

    threading.Thread(target=_bootstrap, daemon=True).start()


# ── Health Check (Docker / load-balancer) ─────────────────────────────────
@app.get("/health")
def health_check():
    """Minimal health check for Docker / Cloudflare health monitors."""
    return {"status": "ok", "service": "meridian-api"}


# ── Agent Discovery — root-level static endpoints ─────────────────────────

_LLMS_TXT = """\
# Meridian — Smart Money Intelligence API
# https://meridianfin.io
# MCP Server: https://meridianfin.io/mcp
# Pay-per-call via x402 (USDC on Base L2). No API keys or subscriptions needed.
#
# Meridian tracks smart money activity across US markets: Congress trades (STOCK Act),
# ARK Invest, dark pool anomalies (FINRA), SEC insider filings, 13F institutional
# holdings, superinvestors (Buffett, Soros, Ackman, ...), short interest, multi-source
# confluence signals, and market regime.

## MCP Tools (10 tools) — transport: Streamable HTTP at /mcp

### Smart Money — Government
- get_congress_trades ($0.05) — US Congress trading activity (STOCK Act filings). Filter by party, chamber, trade_type, days.

### Smart Money — Institutional
- get_ark_trades     ($0.03) — ARK Invest buy/sell activity across ARKK/ARKW/ARKG/ARKQ/ARKF/ARKX. Filter by etf, trade_type, days.
- get_ark_holdings   ($0.03) — Current ARK ETF portfolio holdings with weight percentages.
- get_13f_filings    ($0.05) — 13F quarterly holdings from Berkshire, Bridgewater, Citadel, Soros, Renaissance, and 75+ others.

### Smart Money — Insiders
- get_insider_trades ($0.05) — SEC Form 4 insider trades. Includes cluster buy detection (multiple insiders buying same stock).

### Smart Money — Dark Pool
- get_darkpool_activity ($0.05) — FINRA off-exchange dark pool anomalies. Statistical Z-score detection of unusual volume.

### Smart Money — Short Selling
- get_short_interest ($0.03) — FINRA short interest for 8,600+ tickers. Shares short, days to cover, % of float.

### Smart Money — Superinvestors
- get_superinvestor_activity ($0.05) — Portfolio changes from ~80 legendary investors (Dataroma). Tracks buys, sells, adds, reduces.

### Signals — Multi-Source
- get_confluence_signals ($0.10) — Stocks where multiple smart money sources agree. Scored 0-100, direction-aware (bullish/bearish).

### Signals — Macro
- get_market_regime (FREE) — Market regime: Green/Yellow/Red via VIX + SPY 200MA + credit spreads (FRED). Cached 1h.

## REST API v1 Endpoints (x402-gated, same data as MCP tools)

### Paid endpoints (USDC on Base L2, eip155:8453)
- GET /api/v1/congress?party=&chamber=&trade_type=&days=30&limit=100   ($0.05)
- GET /api/v1/ark/trades?trade_type=&etf=&days=30&limit=100            ($0.03)
- GET /api/v1/ark/holdings?etf=&min_weight=0&limit=100                 ($0.03)
- GET /api/v1/insiders?transaction_type=&ticker=&days=30&cluster_only=false ($0.05)
- GET /api/v1/13f?fund=&limit=50                                       ($0.05)
- GET /api/v1/darkpool?min_zscore=2.0&min_dpi=0.4&days=7&limit=100     ($0.05)
- GET /api/v1/short-interest?ticker=&min_short_ratio=&sort_by=short_interest ($0.03)
- GET /api/v1/superinvestors?manager=&ticker=&activity_type=&limit=100 ($0.03)
- GET /api/v1/confluence?min_score=6.0&sources=&days=7&limit=100       ($0.10)

### Free endpoint (no payment)
- GET /api/v1/regime                                                    (FREE)

## Free Endpoints (no auth)
- GET /api/health       — Service health check, version, capabilities
- GET /api/stats        — Data freshness per source, total tickers tracked, sample confluence signal
- GET /api/openapi.json — OpenAPI 3.1 spec with x-x402 pricing extensions
- GET /llms.txt         — This file
- GET /.well-known/agents.json — Agent discovery metadata (JSON)
- GET /api/data-health  — Detailed data freshness monitoring
- GET /api/v1/regime    — Market regime (free)

## Payment
REST v1 endpoints require x402 payment (USDC on Base L2, Coinbase).
MCP tools at /mcp are also available (same data, same pricing via x402).
No subscriptions, no API keys. Pay only for what you use.
Minimum per-call cost: $0.03. Max: $0.10 (get_confluence_signals).

## Integration Example (REST v1 with x402)
```
# 1. First call — receive 402 with payment instructions
GET https://meridianfin.io/api/v1/congress
→ HTTP 402
→ Header: PAYMENT-REQUIRED: <base64-encoded payment requirements>

# 2. Create payment via CDP / x402 client, then retry with header
GET https://meridianfin.io/api/v1/congress
Header: PAYMENT-SIGNATURE: <base64-encoded signed payment payload>
→ HTTP 200 with Congress trade data
```

## Integration Example (MCP)
```
POST https://meridianfin.io/mcp
Content-Type: application/json

{"method": "tools/call", "params": {"name": "get_confluence_signals", "arguments": {"min_score": 7, "days": 7}}}
```

## Data Sources
- SEC EDGAR (Form 4 insider filings, 13F institutional holdings)
- US Congress STOCK Act disclosure portal (via Quiver Quantitative)
- FINRA (daily dark pool volume, bi-monthly short interest)
- ARK Invest (daily ETF trade disclosures)
- Dataroma (superinvestor 13F aggregation)
- Yahoo Finance / FRED (VIX, SPY, HY credit spreads)

## Update Cadence
- Congress trades: 3× daily
- ARK trades/holdings: 4× daily (Mon-Fri)
- Dark pool: daily (Tue-Sat, after FINRA publish)
- Insider trades: 2× daily
- 13F / Superinvestors: weekly (SEC quarterly cadence)
- Confluence signals: 2× daily
- Market regime: live (1h cache)
"""

_AGENTS_JSON = {
    "schema_version": "1.0",
    "name": "Meridian Smart Money Intelligence",
    "description": (
        "Real-time smart money intelligence API for US markets. Tracks Congress trades, "
        "ARK Invest, dark pool anomalies, SEC insider filings, 13F institutional holdings, "
        "superinvestors, short interest, confluence signals, and market regime. "
        "Pay-per-call via x402 (USDC on Base L2). No API keys needed."
    ),
    "url": "https://meridianfin.io",
    "api_base": "https://meridianfin.io",
    "mcp_url": "https://meridianfin.io/mcp",
    "rest_api_base": "https://meridianfin.io/api/v1",
    "openapi_url": "https://meridianfin.io/api/openapi.json",
    "llms_txt_url": "https://meridianfin.io/llms.txt",
    "version": "1.0.0",
    "categories": ["finance", "trading", "smart-money", "market-intelligence"],
    "capabilities": [
        "congress_trades",
        "ark_invest_tracking",
        "dark_pool_analysis",
        "insider_trading",
        "institutional_13f",
        "superinvestor_tracking",
        "short_interest",
        "confluence_signals",
        "market_regime",
    ],
    "payment": {
        "protocol": "x402",
        "currency": "USDC",
        "network": "base",
        "chain_id": 8453,
        "caip2": "eip155:8453",
        "facilitator": "https://x402.org/facilitator",
        "pay_to": "0xb8280cd9d2a2e7ac3be92c0b5b875c1ca7ab76f4",
        "description": "Pay-per-call. No subscriptions. USDC on Base L2 (Coinbase).",
        "price_range": {"min_usd": 0.03, "max_usd": 0.10},
    },
    "tools": [
        {"name": "get_congress_trades",       "price_usd": 0.05, "rest_path": "/api/v1/congress"},
        {"name": "get_ark_trades",            "price_usd": 0.03, "rest_path": "/api/v1/ark/trades"},
        {"name": "get_ark_holdings",          "price_usd": 0.03, "rest_path": "/api/v1/ark/holdings"},
        {"name": "get_insider_trades",        "price_usd": 0.05, "rest_path": "/api/v1/insiders"},
        {"name": "get_13f_filings",           "price_usd": 0.05, "rest_path": "/api/v1/13f"},
        {"name": "get_darkpool_activity",     "price_usd": 0.05, "rest_path": "/api/v1/darkpool"},
        {"name": "get_short_interest",        "price_usd": 0.03, "rest_path": "/api/v1/short-interest"},
        {"name": "get_superinvestor_activity","price_usd": 0.03, "rest_path": "/api/v1/superinvestors"},
        {"name": "get_confluence_signals",    "price_usd": 0.10, "rest_path": "/api/v1/confluence"},
        {"name": "get_market_regime",         "price_usd": 0.00, "rest_path": "/api/v1/regime", "free": True},
    ],
    "free_endpoints": [
        {"path": "/api/health",             "description": "Service health check"},
        {"path": "/api/stats",              "description": "Data freshness and coverage stats"},
        {"path": "/api/openapi.json",       "description": "OpenAPI 3.1 spec with x-x402 extensions"},
        {"path": "/llms.txt",               "description": "LLM-readable endpoint guide"},
        {"path": "/.well-known/agents.json","description": "Agent discovery metadata"},
        {"path": "/api/v1/regime",          "description": "Market regime: Green/Yellow/Red (FREE)"},
    ],
    "data_sources": [
        "SEC EDGAR (Form 4, 13F)",
        "US Congress STOCK Act (Quiver Quantitative)",
        "FINRA (Dark Pool, Short Interest)",
        "ARK Invest daily disclosures",
        "Dataroma (Superinvestors)",
        "Yahoo Finance / FRED",
    ],
}


from fastapi.responses import PlainTextResponse


@app.get("/llms.txt", include_in_schema=False)
def serve_llms_txt():
    """LLM-readable guide to all Meridian endpoints and tools."""
    return PlainTextResponse(content=_LLMS_TXT, media_type="text/plain; charset=utf-8")


@app.get("/.well-known/agents.json", include_in_schema=False)
def serve_agents_json():
    """Agent discovery metadata — standard /.well-known/agents.json."""
    from fastapi.responses import JSONResponse
    return JSONResponse(content=_AGENTS_JSON)


# ── Router Registration ────────────────────────────────────────────────────
from api.routers import register_routers
register_routers(app)


# ── MCP Server (optional) ─────────────────────────────────────────────────
try:
    from api.mcp_server import mount_mcp
    mount_mcp(app)
    print("[mcp] MCP Server mounted at /mcp")
except ImportError as e:
    print(f"[mcp] MCP not available (install 'mcp' package): {e}")
except Exception as e:
    print(f"[mcp] Failed to mount MCP server: {e}")


# ══════════════════════════════════════════════════════════════════════════
# Main entry point
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
