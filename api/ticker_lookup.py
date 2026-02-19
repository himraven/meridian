"""
Ticker → Company Name Lookup

Builds a mapping from all internal data sources first, then fills gaps
from yfinance. Results are cached in ticker_names.json.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

DATA_DIR = Path("")
CACHE_FILE = DATA_DIR / "ticker_names.json"
CACHE_MAX_AGE = 7 * 24 * 3600  # 7 days


def _load_cache() -> dict:
    """Load cached ticker names."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                data = json.load(f)
            # Check age
            if time.time() - data.get("_updated", 0) < CACHE_MAX_AGE:
                return data.get("names", {})
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


def _save_cache(names: dict):
    """Save ticker names to cache."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"names": names, "_updated": time.time()}, f, indent=2)


def _build_from_internal_sources(smart_money_cache) -> dict:
    """Build mapping from ARK + Institutions data."""
    names = {}
    
    # ARK trades
    ark_data = smart_money_cache.read("ark_trades.json")
    for t in ark_data.get("trades", []):
        if t.get("company") and t.get("ticker"):
            names[t["ticker"]] = t["company"]
    
    # ARK holdings
    ark_h = smart_money_cache.read("ark_holdings.json")
    for h in ark_h.get("holdings", []):
        if h.get("company") and h.get("ticker") and h["ticker"] not in names:
            names[h["ticker"]] = h["company"]
    
    # Institution filings (nested holdings)
    inst = smart_money_cache.read("institutions.json")
    for filing in inst.get("filings", []):
        for h in filing.get("holdings", []):
            tk = h.get("ticker", "").strip()
            if tk and h.get("issuer") and tk not in names:
                names[tk] = h["issuer"]
    
    return names


def _fill_from_yfinance(tickers: list) -> dict:
    """Batch lookup missing tickers from yfinance."""
    if not tickers:
        return {}
    
    names = {}
    try:
        import yfinance as yf
        # Batch in groups of 20 to avoid timeouts
        for i in range(0, len(tickers), 20):
            batch = tickers[i:i+20]
            data = yf.Tickers(" ".join(batch))
            for t in batch:
                try:
                    info = data.tickers[t].info
                    name = info.get("shortName") or info.get("longName")
                    if name:
                        names[t] = name
                except Exception:
                    pass
    except ImportError:
        pass
    except Exception as e:
        print(f"[ticker_lookup] yfinance batch error: {e}")
    
    return names


class TickerNameLookup:
    """Ticker name lookup with multi-source caching."""
    
    def __init__(self, smart_money_cache=None):
        self._names = _load_cache()
        self._smart_money_cache = smart_money_cache
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy init: build from internal sources on first use."""
        if self._initialized:
            return
        self._initialized = True
        
        if self._smart_money_cache:
            internal = _build_from_internal_sources(self._smart_money_cache)
            # Merge: cache wins for existing, internal fills gaps
            for k, v in internal.items():
                if k not in self._names:
                    self._names[k] = v
    
    def get(self, ticker: str) -> Optional[str]:
        """Get company name for a ticker."""
        self._ensure_initialized()
        return self._names.get(ticker.upper())
    
    def get_or_fetch(self, ticker: str) -> Optional[str]:
        """Get company name, fetching from yfinance if needed."""
        name = self.get(ticker)
        if name:
            return name
        
        fetched = _fill_from_yfinance([ticker.upper()])
        if fetched:
            self._names.update(fetched)
            _save_cache(self._names)
            return fetched.get(ticker.upper())
        return None
    
    def enrich_list(self, items: list, ticker_field: str = "ticker", name_field: str = "company") -> list:
        """Add company names to a list of dicts."""
        self._ensure_initialized()
        for item in items:
            tk = item.get(ticker_field, "").upper()
            if tk and not item.get(name_field):
                name = self._names.get(tk)
                if name:
                    item[name_field] = name
        return items
    
    def bulk_resolve(self, tickers: list) -> dict:
        """Resolve a list of tickers, fetching missing from yfinance."""
        self._ensure_initialized()
        missing = [t for t in tickers if t.upper() not in self._names]
        
        if missing:
            fetched = _fill_from_yfinance(missing)
            self._names.update(fetched)
            if fetched:
                _save_cache(self._names)
        
        return {t: self._names.get(t.upper()) for t in tickers}
    
    def get_all(self) -> dict:
        """Return all ticker→name mappings."""
        self._ensure_initialized()
        return dict(self._names)

    @property
    def count(self) -> int:
        self._ensure_initialized()
        return len(self._names)
