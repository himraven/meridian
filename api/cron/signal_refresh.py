#!/usr/bin/env python3
"""
Signal Refresh — Runs the CrossSignalEngine and writes data/ranking.json.

Called:
1. After each data collector completes
2. On manual refresh via /api/admin/refresh
3. As standalone cron job

Pipeline:
  Read data/*.json → Extract signals → Cluster → Score → Write ranking.json
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.config import DATA_DIR, CACHE_FILES
from api.modules.cache_manager import CacheManager
from api.modules.cross_signal_engine import CrossSignalEngine
from api.modules.cross_signal_engine_v2 import SmartMoneyEngineV2

logger = logging.getLogger(__name__)


def refresh_signals(
    cache_dir: str = str(DATA_DIR),
    min_score: float = 0,
    window_days: int = 7,
) -> dict:
    """
    Run the full signal refresh pipeline.
    
    1. Load all source data files
    2. Run CrossSignalEngine.generate_signals()
    3. Write ranking.json
    4. Return status report
    """
    cache = CacheManager(cache_dir)
    start_time = datetime.now()
    
    # Load source data
    source_data = {}
    source_status = {}
    
    for source, filename in [
        ("congress", "congress.json"),
        ("ark_trades", "ark_trades.json"),
        ("darkpool", "darkpool.json"),
        ("institutions", "institutions.json"),
        ("insiders", "insiders.json"),
        ("superinvestors", "superinvestors.json"),
        ("short_interest", "short_interest.json"),
    ]:
        if cache.exists(filename):
            data = cache.read(filename)
            source_data[source] = data
            age = cache.get_age_seconds(filename)
            source_status[source] = {
                "exists": True,
                "age_hours": round(age / 3600, 1) if age else 0,
                "records": len(data.get("trades", data.get("filings", data.get("tickers", [])))),
            }
        else:
            source_status[source] = {"exists": False}
            logger.warning(f"  {source}: MISSING ({filename})")

    # Run engine
    engine = CrossSignalEngine(
        window_days=window_days,
        min_score=min_score,
    )
    
    results = engine.generate_signals(
        congress_data=source_data.get("congress"),
        ark_data=source_data.get("ark_trades"),
        darkpool_data=source_data.get("darkpool"),
        institution_data=source_data.get("institutions"),
        insider_data=source_data.get("insiders"),
    )
    
    # Write ranking.json (v1 — kept for backward compat)
    output = engine.to_json(results)
    cache.write("ranking.json", output)
    
    # v2: Conviction-based scoring
    try:
        engine_v2 = SmartMoneyEngineV2()
        
        # Load ARK holdings for weight context
        ark_holdings = None
        if cache.exists("ark_holdings.json"):
            h_data = cache.read("ark_holdings.json")
            ark_holdings = h_data.get("holdings", h_data.get("data", []))
        
        v2_results = engine_v2.generate(
            congress_data=source_data.get("congress"),
            ark_data=source_data.get("ark_trades"),
            darkpool_data=source_data.get("darkpool"),
            institution_data=source_data.get("institutions"),
            insider_data=source_data.get("insiders"),
            superinvestor_data=source_data.get("superinvestors"),
            short_interest_data=source_data.get("short_interest"),
            ark_holdings=ark_holdings,
            min_score=0,
        )
        v2_output = {
            "signals": engine_v2.to_json(v2_results),
            "metadata": {
                "engine": "v2",
                "total": len(v2_results),
                "last_updated": datetime.now().isoformat(),
            }
        }
        cache.write("ranking_v2.json", v2_output)
        logger.info(f"v2 engine: {len(v2_results)} signals written")
    except Exception as e:
        logger.warning(f"v2 engine failed (v1 still saved): {e}")
    
    # Dual-write to SQLite
    try:
        from api.database import SessionLocal
        from api.crud import upsert_signals, log_refresh
        import time
        db = SessionLocal()
        t0 = time.time()
        count = upsert_signals(db, output.get("signals", []))
        ms = int((time.time() - t0) * 1000)
        log_refresh(db, "signals", "success", count, ms)
        db.close()
        logger.info(f"SQLite: {count} signals written ({ms}ms)")
    except Exception as e:
        logger.warning(f"SQLite write failed (JSON still saved): {e}")
    
    duration = (datetime.now() - start_time).total_seconds()
    
    result = {
        "status": "success",
        "signals_generated": len(results),
        "high_confidence": sum(1 for r in results if r.score >= 8),
        "avg_score": round(sum(r.score for r in results) / len(results), 2) if results else 0,
        "source_status": source_status,
        "duration_seconds": round(duration, 3),
        "timestamp": datetime.now().isoformat(),
    }
    
    logger.info(
        f"Signal refresh: {len(results)} signals "
        f"({result['high_confidence']} high confidence), "
        f"{duration:.2f}s"
    )
    
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = refresh_signals(min_score=0)
    
    print(f"\n{'='*50}")
    print(f"Signal Refresh Result:")
    print(f"  Signals: {result['signals_generated']}")
    print(f"  High confidence (≥8): {result['high_confidence']}")
    print(f"  Avg score: {result['avg_score']}")
    print(f"  Duration: {result['duration_seconds']}s")
    print(f"\nSource status:")
    for source, status in result['source_status'].items():
        if status['exists']:
            print(f"  ✅ {source}: {status['records']} records, {status['age_hours']}h old")
        else:
            print(f"  ❌ {source}: missing")
    
    # Show top signals
    with open(str(DATA_DIR / "ranking.json")) as f:
        signals = json.load(f)
    
    if signals["signals"]:
        print(f"\nTop 10 signals:")
        for s in signals["signals"][:10]:
            print(f"  {s['ticker']:6s} | score={s['score']:5.2f} | {s['sources']} | {s['signal_date']}")
