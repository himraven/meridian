"""
Agent Discovery Routes — Meridian

Makes Meridian discoverable by AI agents and marketplaces:
  GET /api/health        — service health + capabilities summary (no auth)
  GET /api/stats         — data freshness + sample signals (no auth)
  GET /api/openapi.json  — OpenAPI spec for all 10 MCP tools (x-x402 pricing)

These endpoints are intentionally free and unauthenticated so agents can
evaluate the service before committing to paid calls.
"""

import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# ── Pricing table (USDC on Base L2) ───────────────────────────────────────
TOOL_PRICING = {
    "get_congress_trades": 0.05,
    "get_ark_trades": 0.03,
    "get_ark_holdings": 0.03,
    "get_insider_trades": 0.05,
    "get_13f_filings": 0.05,
    "get_darkpool_activity": 0.05,
    "get_short_interest": 0.03,
    "get_superinvestor_activity": 0.03,
    "get_confluence_signals": 0.10,
    "get_market_regime": 0.00,  # FREE
}

# REST v1 endpoint map: tool name → GET path (mirrors MCP tools)
V1_REST_PATHS = {
    "get_congress_trades":       "/api/v1/congress",
    "get_ark_trades":            "/api/v1/ark/trades",
    "get_ark_holdings":          "/api/v1/ark/holdings",
    "get_insider_trades":        "/api/v1/insiders",
    "get_13f_filings":           "/api/v1/13f",
    "get_darkpool_activity":     "/api/v1/darkpool",
    "get_short_interest":        "/api/v1/short-interest",
    "get_superinvestor_activity":"/api/v1/superinvestors",
    "get_confluence_signals":    "/api/v1/confluence",
    "get_market_regime":         "/api/v1/regime",
}

# ── Tool registry (ordered, mirrors mcp_server.py) ────────────────────────
TOOLS = [
    {
        "name": "get_congress_trades",
        "category": "Smart Money — Government",
        "description": "US Congress stock trading activity from STOCK Act disclosures",
        "parameters": {
            "party": "Democrat | Republican",
            "chamber": "House | Senate",
            "trade_type": "Purchase | Sale",
            "days": "int (default 30)",
            "limit": "int (default 100)",
        },
    },
    {
        "name": "get_ark_trades",
        "category": "Smart Money — Institutional",
        "description": "ARK Invest buy/sell trading activity across ARKK, ARKW, ARKG, ARKQ, ARKF, ARKX",
        "parameters": {
            "trade_type": "Buy | Sell",
            "etf": "ARKK | ARKG | ...",
            "days": "int (default 30)",
            "limit": "int (default 100)",
        },
    },
    {
        "name": "get_ark_holdings",
        "category": "Smart Money — Institutional",
        "description": "Current ARK ETF holdings with portfolio weights",
        "parameters": {
            "etf": "ARKK | ARKG | ...",
            "min_weight": "float (default 0.0)",
            "limit": "int (default 100)",
        },
    },
    {
        "name": "get_insider_trades",
        "category": "Smart Money — Insiders",
        "description": "SEC Form 4 insider trading — buys, sells, cluster buy detection",
        "parameters": {
            "transaction_type": "Buy | Sale",
            "ticker": "str (e.g. AAPL)",
            "days": "int (default 30)",
            "cluster_only": "bool (default false)",
            "limit": "int (default 100)",
        },
    },
    {
        "name": "get_13f_filings",
        "category": "Smart Money — Institutional",
        "description": "13F quarterly holdings from Berkshire, Bridgewater, Citadel, Soros, and ~80 others",
        "parameters": {
            "fund": "str partial match (e.g. berkshire)",
            "limit": "int (default 50)",
        },
    },
    {
        "name": "get_darkpool_activity",
        "category": "Smart Money — Dark Pool",
        "description": "FINRA off-exchange dark pool anomalies detected by Z-score analysis",
        "parameters": {
            "min_zscore": "float (default 2.0)",
            "min_dpi": "float (default 0.4)",
            "days": "int (default 7)",
            "limit": "int (default 100)",
        },
    },
    {
        "name": "get_short_interest",
        "category": "Smart Money — Short Selling",
        "description": "FINRA short interest data for 8,600+ tickers — shares short, days to cover, % float",
        "parameters": {
            "ticker": "str (e.g. GME)",
            "min_short_ratio": "float (e.g. 20.0)",
            "sort_by": "short_interest | short_ratio | days_to_cover",
            "limit": "int (default 50)",
        },
    },
    {
        "name": "get_superinvestor_activity",
        "category": "Smart Money — Superinvestors",
        "description": "Portfolio changes from ~80 legendary investors via 13F (Buffett, Soros, Ackman, Icahn...)",
        "parameters": {
            "manager": "str partial match (e.g. buffett)",
            "ticker": "str",
            "activity_type": "Buy | Sell | Add | Reduce",
            "limit": "int (default 100)",
        },
    },
    {
        "name": "get_confluence_signals",
        "category": "Signals — Multi-Source",
        "description": "Stocks with multi-source smart money consensus (Congress + ARK + Dark Pool + Insider + 13F)",
        "parameters": {
            "min_score": "float (default 6.0)",
            "sources": "str comma-separated (e.g. congress,ark,darkpool)",
            "days": "int (default 7)",
            "limit": "int (default 100)",
        },
    },
    {
        "name": "get_market_regime",
        "category": "Signals — Macro",
        "description": "Market regime: Green (risk-on) / Yellow (caution) / Red (defensive) via VIX + SPY MA + credit spreads",
        "parameters": {},
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────

def _file_age_hours(path: str) -> float | None:
    """Return file age in hours, or None if missing."""
    import time
    try:
        return round((time.time() - os.path.getmtime(path)) / 3600, 1)
    except Exception:
        return None


def _file_mtime_iso(path: str) -> str | None:
    """Return file mtime as ISO string, or None if missing."""
    import time
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except Exception:
        return None


def _count_tickers(*json_paths: tuple[str, str]) -> int:
    """Count unique tickers across multiple JSON files."""
    import json
    seen: set[str] = set()
    for path, key in json_paths:
        try:
            with open(path) as f:
                data = json.load(f)
            for item in data.get(key, []):
                t = (item.get("ticker") or "").strip().upper()
                if t:
                    seen.add(t)
        except Exception:
            pass
    return len(seen)


def _sample_confluence_signal() -> dict | None:
    """Return the top-ranked redacted confluence signal."""
    import json
    for fname in ("ranking_v3.json", "ranking_v2.json", "ranking.json"):
        path = f"/app/data/{fname}"
        try:
            with open(path) as f:
                data = json.load(f)
            signals = data.get("signals", [])
            if signals:
                top = signals[0]
                # Return preview — no full details, just enough to evaluate quality
                return {
                    "ticker": top.get("ticker", "?"),
                    "score": top.get("score"),
                    "direction": top.get("direction"),
                    "sources_count": len(top.get("sources", top.get("details", []))),
                    "signal_date": top.get("signal_date"),
                    "note": "Full signal available via get_confluence_signals",
                }
        except Exception:
            continue
    return None


# ── /api/health ────────────────────────────────────────────────────────────

@router.get("/api/health", tags=["discovery"])
def api_health():
    """
    Service health check — returns capabilities summary.

    Free endpoint, no auth required. Designed for agent health-checks
    and marketplace listings.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "tools_count": len(TOOLS),
        "mcp_url": "https://meridianfin.io/mcp",
        "api_base": "https://meridianfin.io",
        "payment": "x402 (USDC on Base L2)",
        "sources": [
            "SEC EDGAR (Form 4, 13F)",
            "STOCK Act (Congress)",
            "FINRA (Dark Pool, Short Interest)",
            "ARK Invest",
            "Dataroma (Superinvestors)",
            "Yahoo Finance / FRED (Macro)",
        ],
    }


# ── /api/stats ─────────────────────────────────────────────────────────────

@router.get("/api/stats", tags=["discovery"])
def api_stats():
    """
    Data freshness and coverage stats — free for agent evaluation.

    Returns:
    - Data source count and freshness
    - Total unique tickers tracked
    - Sample confluence signal (redacted preview)
    - Update cadence per source
    """
    DATA = "/app/data"

    # Freshness per source
    sources_freshness = {
        "congress_trades": {
            "last_updated": _file_mtime_iso(f"{DATA}/congress.json"),
            "age_hours": _file_age_hours(f"{DATA}/congress.json"),
            "schedule": "3x/day (STOCK Act)",
        },
        "ark_trades": {
            "last_updated": _file_mtime_iso(f"{DATA}/ark_trades.json"),
            "age_hours": _file_age_hours(f"{DATA}/ark_trades.json"),
            "schedule": "4x/day Mon-Fri",
        },
        "dark_pool": {
            "last_updated": _file_mtime_iso(f"{DATA}/darkpool.json"),
            "age_hours": _file_age_hours(f"{DATA}/darkpool.json"),
            "schedule": "Daily (FINRA, Tue-Sat)",
        },
        "insider_trades": {
            "last_updated": _file_mtime_iso(f"{DATA}/insiders.json"),
            "age_hours": _file_age_hours(f"{DATA}/insiders.json"),
            "schedule": "2x/day (SEC Form 4)",
        },
        "institutions_13f": {
            "last_updated": _file_mtime_iso(f"{DATA}/institutions.json"),
            "age_hours": _file_age_hours(f"{DATA}/institutions.json"),
            "schedule": "Weekly (SEC 13F)",
        },
        "confluence_signals": {
            "last_updated": _file_mtime_iso(f"{DATA}/ranking_v3.json")
                             or _file_mtime_iso(f"{DATA}/ranking.json"),
            "age_hours": _file_age_hours(f"{DATA}/ranking_v3.json")
                          or _file_age_hours(f"{DATA}/ranking.json"),
            "schedule": "2x/day",
        },
        "short_interest": {
            "last_updated": _file_mtime_iso(f"{DATA}/short_interest.json"),
            "age_hours": _file_age_hours(f"{DATA}/short_interest.json"),
            "schedule": "Bi-monthly (FINRA)",
        },
    }

    # Unique tickers across key sources
    total_tickers = _count_tickers(
        (f"{DATA}/congress.json", "trades"),
        (f"{DATA}/ark_trades.json", "trades"),
        (f"{DATA}/ark_holdings.json", "holdings"),
        (f"{DATA}/insiders.json", "trades"),
        (f"{DATA}/darkpool.json", "tickers"),
    )

    return {
        "service": "Meridian Smart Money Intelligence",
        "mcp_url": "https://meridianfin.io/mcp",
        "tools_count": len(TOOLS),
        "data_sources_count": len(sources_freshness),
        "total_tickers_tracked": total_tickers,
        "data_freshness": sources_freshness,
        "sample_signal": _sample_confluence_signal(),
        "pricing_preview": {
            "get_confluence_signals": "$0.10",
            "get_congress_trades": "$0.05",
            "get_market_regime": "FREE",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── /api/openapi.json ──────────────────────────────────────────────────────

def _build_openapi_spec() -> dict:
    """Build OpenAPI 3.1 spec covering both MCP tools and REST v1 endpoints."""

    _success_response = {
        "description": "Successful response",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "object"},
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "filtered": {"type": "integer"},
                                "source": {"type": "string"},
                            },
                        },
                    },
                }
            }
        },
    }

    _payment_required_response = {
        "description": "Payment required — send x402 PAYMENT-SIGNATURE header",
        "headers": {
            "PAYMENT-REQUIRED": {
                "description": "Base64-encoded JSON with payment instructions (x402 v2 protocol)",
                "schema": {"type": "string"},
            }
        },
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                    },
                }
            }
        },
    }

    def _build_query_params(params: dict) -> list:
        """Convert parameter description map to OpenAPI query parameter list."""
        result = []
        for param_name, param_desc in params.items():
            desc_lower = param_desc.lower()
            if "int" in desc_lower:
                schema: dict = {"type": "integer"}
            elif "float" in desc_lower:
                schema = {"type": "number"}
            elif "bool" in desc_lower:
                schema = {"type": "boolean"}
            else:
                schema = {"type": "string"}
            result.append({
                "name": param_name,
                "in": "query",
                "required": False,
                "description": param_desc,
                "schema": schema,
            })
        return result

    def _mcp_path(tool: dict) -> dict:
        """Build OpenAPI path entry for an MCP tool (POST to /mcp)."""
        price = TOOL_PRICING.get(tool["name"], 0.05)
        params = tool.get("parameters", {})

        properties: dict[str, Any] = {}
        for param_name, param_desc in params.items():
            desc_lower = param_desc.lower()
            if "int" in desc_lower:
                schema: dict = {"type": "integer"}
            elif "float" in desc_lower:
                schema = {"type": "number"}
            elif "bool" in desc_lower:
                schema = {"type": "boolean"}
            else:
                schema = {"type": "string"}
            schema["description"] = param_desc
            properties[param_name] = schema

        request_body = None
        if properties:
            request_body = {
                "required": False,
                "content": {
                    "application/json": {
                        "schema": {"type": "object", "properties": properties}
                    }
                },
            }

        x402_ext = {
            "price": price,
            "currency": "USDC",
            "network": "eip155:8453",
            "pay_to": "0xb8280cd9d2a2e7ac3be92c0b5b875c1ca7ab76f4",
            "facilitator": "https://x402.org/facilitator",
            "scheme": "exact",
        }
        if price == 0:
            x402_ext["free"] = True

        return {
            "post": {
                "operationId": f"mcp_{tool['name']}",
                "summary": f"[MCP] {tool['description']}",
                "description": tool["description"],
                "tags": [tool["category"]],
                "x-x402": x402_ext,
                **({"requestBody": request_body} if request_body else {}),
                "responses": {
                    "200": _success_response,
                    "402": _payment_required_response,
                },
            }
        }

    def _v1_path(tool: dict) -> dict:
        """Build OpenAPI path entry for a REST v1 GET endpoint."""
        price = TOOL_PRICING.get(tool["name"], 0.05)
        params = _build_query_params(tool.get("parameters", {}))

        x402_ext: dict = {
            "price": price,
            "currency": "USDC",
            "network": "eip155:8453",
            "pay_to": "0xb8280cd9d2a2e7ac3be92c0b5b875c1ca7ab76f4",
            "facilitator": "https://x402.org/facilitator",
            "scheme": "exact",
        }
        if price == 0:
            x402_ext["free"] = True

        response_codes: dict = {"200": _success_response}
        if price > 0:
            response_codes["402"] = _payment_required_response

        return {
            "get": {
                "operationId": f"v1_{tool['name']}",
                "summary": f"[REST v1] {tool['description']} — {'FREE' if price == 0 else f'${price:.2f}/call'}",
                "description": tool["description"],
                "tags": ["v1 — REST Endpoints"],
                "x-x402": x402_ext,
                **({"parameters": params} if params else {}),
                "responses": response_codes,
            }
        }

    paths = {}
    for tool in TOOLS:
        # MCP tool path (POST /mcp via MCP protocol)
        paths[f"/mcp/tools/{tool['name']}"] = _mcp_path(tool)
        # REST v1 path (GET /api/v1/*)
        v1_path = V1_REST_PATHS.get(tool["name"])
        if v1_path:
            paths[v1_path] = _v1_path(tool)

    # Collect unique tags/categories
    tags = list({t["category"] for t in TOOLS}) + ["v1 — REST Endpoints"]

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Meridian Smart Money Intelligence",
            "description": (
                "Real-time smart money intelligence across US markets. "
                "Tracks Congress trades, ARK Invest, dark pool anomalies, "
                "institutional 13F filings, insider trading, superinvestors, "
                "short interest, confluence signals, and market regime. "
                "Pay-per-call via x402 protocol (USDC on Base L2). No API keys needed."
            ),
            "version": "1.0.0",
            "contact": {
                "name": "Meridian",
                "url": "https://meridianfin.io",
            },
            "x-x402": {
                "payment_scheme": "exact",
                "currency": "USDC",
                "network": "base",
                "description": "Pay-per-call via x402 protocol. No API keys or subscriptions.",
            },
        },
        "servers": [
            {"url": "https://meridianfin.io", "description": "Production"},
        ],
        "tags": [{"name": t} for t in sorted(tags)],
        "paths": paths,
        "components": {
            "schemas": {
                "TradeMetadata": {
                    "type": "object",
                    "properties": {
                        "filtered": {"type": "integer"},
                        "buy_count": {"type": "integer"},
                        "sell_count": {"type": "integer"},
                        "source": {"type": "string", "enum": ["duckdb", "json"]},
                    },
                },
                "ConfluenceSignal": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "score": {"type": "number", "description": "0-100 confluence score"},
                        "direction": {"type": "string", "enum": ["bullish", "bearish"]},
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Contributing sources: congress, ark, darkpool, insider, 13f",
                        },
                        "signal_date": {"type": "string", "format": "date"},
                    },
                },
                "MarketRegime": {
                    "type": "object",
                    "properties": {
                        "regime": {"type": "string", "enum": ["green", "yellow", "red", "unknown"]},
                        "summary": {"type": "string"},
                        "components": {"type": "object"},
                    },
                },
            }
        },
    }


@router.get("/api/openapi.json", tags=["discovery"])
def api_openapi_spec():
    """
    OpenAPI 3.1 spec for all 10 Meridian MCP tools.

    Includes x-x402 extension with pricing info per tool.
    Suitable for agent marketplaces, tool registries, and automated discovery.
    """
    return JSONResponse(content=_build_openapi_spec())
