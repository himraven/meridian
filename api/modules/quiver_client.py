"""
Quiver Quantitative API Client — Rate-limited, retry-enabled wrapper.

Quiver API: https://api.quiverquant.com/beta
Free tier: 2000 req/day, ~30 req/min
Endpoints: Congress trading, Dark Pool (OTC), ARK trades

Features:
- Automatic rate limiting (configurable per-minute limit)
- Exponential backoff retry on transient errors
- API key loading from env or credentials file
- Response normalization to consistent dict format
"""

import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from api.config import (
    QUIVER_API_KEY,
    QUIVER_BASE_URL,
    QUIVER_RATE_LIMIT_PER_MIN,
    QUIVER_DAILY_LIMIT,
)

logger = logging.getLogger(__name__)


def _load_api_key() -> str:
    """Load Quiver API key from environment or credentials file."""
    key = QUIVER_API_KEY
    if key:
        return key

    # Try credentials file
    cred_path = Path.home() / ".credentials" / "quiver.env"
    if cred_path.exists():
        for line in cred_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("QUIVER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    return ""


class QuiverClientError(Exception):
    """Base exception for Quiver client errors."""
    pass


class QuiverRateLimitError(QuiverClientError):
    """Raised when rate limit is exceeded."""
    pass


class QuiverAuthError(QuiverClientError):
    """Raised on 401/403 authentication errors."""
    pass


class QuiverClient:
    """
    Rate-limited Quiver Quantitative API client.
    
    Usage:
        client = QuiverClient()
        trades = client.get_congress_trades(days=30)
        darkpool = client.get_darkpool_data(ticker="NVDA")
        ark = client.get_ark_trades(days=30)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = QUIVER_BASE_URL,
        rate_limit_per_min: int = QUIVER_RATE_LIMIT_PER_MIN,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        self.api_key = api_key or _load_api_key()
        self.base_url = base_url.rstrip("/")
        self.rate_limit_per_min = rate_limit_per_min
        self.max_retries = max_retries
        self.timeout = timeout

        # Rate limiting state
        self._request_timestamps: List[float] = []
        self._daily_count = 0
        self._daily_reset: Optional[datetime] = None

        # Session with connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SmartMoneyPlatform/2.0",
        })

        if not self.api_key:
            logger.warning("No Quiver API key configured. API calls will fail.")

    @property
    def is_configured(self) -> bool:
        """Check if API key is available."""
        return bool(self.api_key)

    def _wait_for_rate_limit(self):
        """Block until rate limit window allows a new request."""
        now = time.time()
        window = 60.0  # 1 minute

        # Clean old timestamps
        self._request_timestamps = [
            ts for ts in self._request_timestamps if now - ts < window
        ]

        if len(self._request_timestamps) >= self.rate_limit_per_min:
            oldest = self._request_timestamps[0]
            sleep_time = window - (now - oldest) + 0.1
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)

        # Check daily limit
        today = datetime.now().date()
        if self._daily_reset is None or self._daily_reset != today:
            self._daily_count = 0
            self._daily_reset = today

        if self._daily_count >= QUIVER_DAILY_LIMIT:
            raise QuiverRateLimitError(
                f"Daily limit of {QUIVER_DAILY_LIMIT} requests exceeded"
            )

    def _record_request(self):
        """Record a request for rate limiting."""
        self._request_timestamps.append(time.time())
        self._daily_count += 1

    def _request(
        self, method: str, endpoint: str, params: Optional[Dict] = None
    ) -> Any:
        """
        Make an authenticated API request with rate limiting and retries.
        
        Returns parsed JSON response.
        Raises QuiverClientError on failure after all retries.
        """
        if not self.api_key:
            raise QuiverAuthError("No API key configured")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            self._wait_for_rate_limit()

            try:
                resp = self._session.request(
                    method, url, headers=headers, params=params, timeout=self.timeout
                )
                self._record_request()

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 401:
                    raise QuiverAuthError("Invalid API key (401)")
                elif resp.status_code == 403:
                    raise QuiverAuthError("Access denied (403)")
                elif resp.status_code == 429:
                    wait = min(2 ** attempt * 5, 60)
                    logger.warning(f"Rate limited (429), waiting {wait}s (attempt {attempt})")
                    time.sleep(wait)
                    last_error = QuiverRateLimitError(f"429 on attempt {attempt}")
                    continue
                elif resp.status_code >= 500:
                    wait = min(2 ** attempt * 2, 30)
                    logger.warning(f"Server error {resp.status_code}, retrying in {wait}s")
                    time.sleep(wait)
                    last_error = QuiverClientError(f"Server error {resp.status_code}")
                    continue
                else:
                    raise QuiverClientError(
                        f"Unexpected status {resp.status_code}: {resp.text[:200]}"
                    )

            except (requests.ConnectionError, requests.Timeout) as e:
                wait = min(2 ** attempt * 2, 30)
                logger.warning(f"Connection error, retrying in {wait}s: {e}")
                time.sleep(wait)
                last_error = QuiverClientError(f"Connection error: {e}")
                continue

        raise last_error or QuiverClientError("Request failed after all retries")

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """GET request to Quiver API."""
        return self._request("GET", endpoint, params)

    # ── Congress Trading ───────────────────────────────────────────────

    def get_congress_trades(
        self, days: int = 30, page_size: int = 200
    ) -> List[Dict]:
        """
        Fetch recent Congress trades.
        
        Returns list of trade dicts with normalized field names.
        """
        data = self.get("live/congresstrading", {"page_size": page_size})
        if not isinstance(data, list):
            logger.warning(f"Unexpected congress response type: {type(data)}")
            return []

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = []

        for t in data:
            report_date = t.get("ReportDate", "")
            if report_date < cutoff:
                continue

            # Skip non-stock transactions
            if t.get("TickerType") not in ("Stock", None):
                continue

            ticker = t.get("Ticker", "")
            if not ticker or ticker == "--":
                continue

            trades.append({
                "ticker": ticker.upper().strip(),
                "representative": t.get("Representative", ""),
                "party": t.get("Party", ""),
                "chamber": t.get("House", ""),
                "trade_type": _normalize_trade_type(t.get("Transaction", "")),
                "amount_range": t.get("Range", t.get("Amount", "")),
                "transaction_date": t.get("TransactionDate", ""),
                "filing_date": report_date,
                "excess_return": t.get("ExcessReturn"),
                "price_change": t.get("PriceChange"),
                "spy_change": t.get("SPYChange"),
            })

        logger.info(f"Fetched {len(trades)} congress trades (last {days} days)")
        return trades

    # ── Dark Pool (Off-Exchange) ───────────────────────────────────────

    def get_darkpool_data(
        self, ticker: Optional[str] = None, days: int = 90
    ) -> List[Dict]:
        """
        Fetch dark pool (off-exchange) volume data.
        
        If ticker is None, fetches all tickers (expensive — many records).
        Prefer calling with a specific ticker.
        """
        endpoint = f"historical/offexchange/{ticker}" if ticker else "historical/offexchange"
        data = self.get(endpoint)
        if not isinstance(data, list):
            logger.warning(f"Unexpected darkpool response type: {type(data)}")
            return []

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        records = []

        for d in data:
            record_date = d.get("Date", "")
            if record_date < cutoff:
                continue

            records.append({
                "ticker": d.get("Ticker", ticker or "").upper().strip(),
                "date": record_date,
                "otc_short": int(d.get("ShortVolume", 0)),
                "otc_total": int(d.get("TotalVolume", 0)),
                "price": d.get("Price"),
            })

        logger.info(f"Fetched {len(records)} darkpool records" +
                     (f" for {ticker}" if ticker else ""))
        return records

    def get_darkpool_tickers(self) -> List[str]:
        """Get list of all tickers with dark pool data available."""
        try:
            data = self.get("historical/offexchange")
            if isinstance(data, list):
                return sorted(set(
                    d.get("Ticker", "").upper().strip()
                    for d in data if d.get("Ticker")
                ))
        except QuiverClientError as e:
            logger.error(f"Failed to get darkpool tickers: {e}")
        return []

    # ── ARK Trades ─────────────────────────────────────────────────────

    def get_ark_trades(self, days: int = 30) -> List[Dict]:
        """
        Fetch ARK ETF trades from Quiver.
        
        Returns normalized trade dicts.
        """
        data = self.get("live/ark")
        if not isinstance(data, list):
            logger.warning(f"Unexpected ARK response type: {type(data)}")
            return []

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        trades = []

        for t in data:
            trade_date = t.get("Date", "")
            if trade_date < cutoff:
                continue

            ticker = t.get("Ticker", "")
            if not ticker:
                continue

            trades.append({
                "ticker": ticker.upper().strip(),
                "etf": t.get("Fund", "").upper().strip(),
                "trade_type": "Buy" if t.get("Direction", "").lower() == "buy" else "Sell",
                "date": trade_date,
                "shares": int(t.get("Shares", 0)),
                "weight_pct": t.get("Weight"),
            })

        logger.info(f"Fetched {len(trades)} ARK trades (last {days} days)")
        return trades

    # ── Utility ────────────────────────────────────────────────────────

    @property
    def daily_requests_remaining(self) -> int:
        """Approximate daily requests remaining."""
        return max(0, QUIVER_DAILY_LIMIT - self._daily_count)

    def health_check(self) -> Dict[str, Any]:
        """Check API connectivity and key validity."""
        if not self.is_configured:
            return {"ok": False, "error": "No API key configured"}
        try:
            # Small request to verify key
            self.get("live/congresstrading", {"page_size": 1})
            return {
                "ok": True,
                "daily_remaining": self.daily_requests_remaining,
            }
        except QuiverAuthError as e:
            return {"ok": False, "error": str(e)}
        except QuiverClientError as e:
            return {"ok": False, "error": str(e)}


def _normalize_trade_type(raw: str) -> str:
    """Normalize transaction type to Purchase/Sale."""
    lower = raw.lower().strip()
    if "purchase" in lower or "buy" in lower:
        return "Buy"
    elif "sale" in lower or "sell" in lower:
        return "Sell"
    elif "exchange" in lower:
        return "Exchange"
    return raw


# ── Free API Fallbacks ─────────────────────────────────────────────────

HOUSE_FREE_API = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
SENATE_FREE_API = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"


def fetch_free_congress_trades(days: int = 30) -> List[Dict]:
    """
    Fallback: Fetch congress trades from free S3-hosted APIs.
    No API key required, but data quality is lower (no excess return, no party).
    """
    trades = []
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    session = requests.Session()
    session.headers["User-Agent"] = "SmartMoneyPlatform/2.0"

    # House trades
    try:
        resp = session.get(HOUSE_FREE_API, timeout=60)
        resp.raise_for_status()
        for t in resp.json():
            if t.get("transaction_date", "") >= cutoff:
                ticker = t.get("ticker", "")
                if ticker and ticker != "--":
                    trades.append({
                        "ticker": ticker.upper().strip(),
                        "representative": t.get("representative", ""),
                        "party": "",
                        "chamber": "House",
                        "trade_type": _normalize_trade_type(t.get("type", "")),
                        "amount_range": t.get("amount", ""),
                        "transaction_date": t.get("transaction_date", ""),
                        "filing_date": t.get("disclosure_date", ""),
                        "excess_return": None,
                        "price_change": None,
                        "spy_change": None,
                    })
        logger.info(f"Free House API: {sum(1 for t in trades if t['chamber']=='House')} trades")
    except Exception as e:
        logger.error(f"Free House API error: {e}")

    # Senate trades
    try:
        resp = session.get(SENATE_FREE_API, timeout=60)
        resp.raise_for_status()
        for t in resp.json():
            if t.get("transaction_date", "") >= cutoff:
                ticker = t.get("ticker", "")
                if ticker and ticker != "--":
                    trades.append({
                        "ticker": ticker.upper().strip(),
                        "representative": f"{t.get('first_name', '')} {t.get('last_name', '')}".strip(),
                        "party": "",
                        "chamber": "Senate",
                        "trade_type": _normalize_trade_type(t.get("type", "")),
                        "amount_range": t.get("amount", ""),
                        "transaction_date": t.get("transaction_date", ""),
                        "filing_date": t.get("disclosure_date", ""),
                        "excess_return": None,
                        "price_change": None,
                        "spy_change": None,
                    })
        logger.info(f"Free Senate API: {sum(1 for t in trades if t['chamber']=='Senate')} trades")
    except Exception as e:
        logger.error(f"Free Senate API error: {e}")

    return trades
