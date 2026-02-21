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


# ── Health Check ───────────────────────────────────────────────────────────
@app.get("/health")
@app.get("/api/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "meridian-api"}


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
