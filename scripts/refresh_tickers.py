#!/usr/bin/env python3
import sys
sys.path.insert(0, "")
from api.ticker_lookup import TickerNameLookup, _save_cache
t = TickerNameLookup()
t._ensure_initialized()
_save_cache(t._names)
print(f"Ticker names: {len(t._names)} entries")
