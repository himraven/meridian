"""
DuckDB Database Initialization

Called on FastAPI startup to:
  1. Initialize the DuckDB store singleton
  2. Run the initial refresh (load JSON → DuckDB tables)
  3. Start a background thread that watches for JSON file changes
     and refreshes tables automatically (every 60s mtime check)

Designed to be robust:
  - If DuckDB is unavailable, logs an error but does not crash the API
  - Multiple uvicorn workers: only one gets the write lock; others read-only
  - Refresh loop runs in a daemon thread (dies with the process)
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Files to watch for changes (subset from FILE_TABLES)
WATCHED_FILES = [
    "congress.json",
    "ark_trades.json",
    "insiders.json",
    "darkpool.json",
    "institutions.json",
    "short_interest.json",
    "superinvestors.json",
    "ranking_v3.json",
]

# How often to check for file changes (seconds)
REFRESH_INTERVAL = 60

# Global flag to track if background thread is already running
_refresh_thread_started = False
_thread_lock = threading.Lock()


def init_duckdb() -> bool:
    """
    Initialize DuckDB store and run initial data load.
    Returns True on success, False on failure.
    Called from FastAPI startup event.
    """
    try:
        from api.modules.duckdb_store import init_store
    except ImportError as e:
        logger.error(f"[duckdb] Cannot import duckdb_store: {e}. Is duckdb installed?")
        return False

    logger.info("[duckdb] Initializing DuckDB query layer...")

    try:
        store = init_store()
    except Exception as e:
        logger.error(f"[duckdb] Failed to create DuckDB store: {e}")
        return False

    # Initial refresh — load all JSON files into DuckDB tables
    try:
        counts = store.refresh_all()
        total = sum(counts.values())
        logger.info(f"[duckdb] Initial load complete: {total} rows across {len(counts)} tables")
        for table, count in sorted(counts.items()):
            logger.info(f"[duckdb]   {table}: {count} rows")
    except Exception as e:
        logger.error(f"[duckdb] Initial refresh failed: {e}", exc_info=True)
        # Non-fatal: API will fall back to JSON reads

    # Start background refresh thread (only once per process)
    _start_refresh_loop(store)

    return True


def _start_refresh_loop(store) -> None:
    """Start the background file-watcher / refresh loop (daemon thread)."""
    global _refresh_thread_started

    with _thread_lock:
        if _refresh_thread_started:
            logger.debug("[duckdb] Refresh thread already running, skipping")
            return
        _refresh_thread_started = True

    def _loop():
        """Watch JSON files for changes and refresh DuckDB when they change."""
        try:
            from api.config import DATA_DIR
            data_dir = Path(DATA_DIR)
        except ImportError:
            data_dir = Path("data")

        logger.info(f"[duckdb] Background refresh loop started (interval: {REFRESH_INTERVAL}s)")
        mtimes: Dict[str, float] = {}

        # Record initial mtimes
        for fname in WATCHED_FILES:
            path = data_dir / fname
            if path.exists():
                mtimes[fname] = path.stat().st_mtime

        while True:
            time.sleep(REFRESH_INTERVAL)
            try:
                changed_files = []
                for fname in WATCHED_FILES:
                    path = data_dir / fname
                    if not path.exists():
                        continue
                    mtime = path.stat().st_mtime
                    if mtimes.get(fname) != mtime:
                        mtimes[fname] = mtime
                        changed_files.append(fname)

                if changed_files:
                    logger.info(f"[duckdb] Detected changes in: {changed_files}. Refreshing...")
                    counts = store.refresh_all()
                    total = sum(counts.values())
                    logger.info(f"[duckdb] Auto-refresh complete: {total} rows")

            except Exception as e:
                logger.error(f"[duckdb] Background refresh error: {e}", exc_info=True)
                # Keep running despite errors

    thread = threading.Thread(target=_loop, daemon=True, name="duckdb-refresh")
    thread.start()


def trigger_refresh() -> Dict[str, int]:
    """
    Manually trigger a full DuckDB refresh.
    Called by API endpoints like /api/system/db-refresh.
    Returns {table: row_count}.
    """
    try:
        from api.modules.duckdb_store import get_store
        store = get_store()
        return store.refresh_all()
    except Exception as e:
        logger.error(f"[duckdb] Manual refresh failed: {e}")
        return {}
