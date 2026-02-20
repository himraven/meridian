"""
DuckDB Store — JSON → DuckDB Query Layer

Reads JSON cache files and loads them into a persistent DuckDB database,
providing a SQL query interface over the smart money data.

Architecture:
  JSON files (written by collectors)
    ↓ refresh_all() / background thread
  DuckDB tables (persistent, in data/smartmoney.duckdb)
    ↓ query()
  API routers (fast SQL queries with JSON fallback)

Thread safety:
  - Write connections use a process-level lock
  - Read queries use read_only=True connections (concurrent safe)
  - Multiple uvicorn workers: only one gets the write lock on startup

Tables:
  congress_trades      ← congress.json → trades[]
  ark_trades           ← ark_trades.json → trades[]
  insider_trades       ← insiders.json → trades[]
  insider_clusters     ← insiders.json → clusters[]
  darkpool_tickers     ← darkpool.json → tickers[]
  darkpool_anomalies   ← darkpool.json → anomalies[]
  institution_filings  ← institutions.json → filings[] (no nested holdings)
  institution_holdings ← institutions.json → filings[].holdings[] (flattened)
  short_interest       ← short_interest.json → tickers[]
  superinvestor_activity ← superinvestors.json → activity[]
  superinvestor_holdings ← superinvestors.json → holdings{} (flattened)
  ranking              ← ranking_v3.json → signals[]
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Global singleton ────────────────────────────────────────────────────────
_store: Optional["DuckDBStore"] = None
_store_lock = threading.Lock()


class DuckDBStore:
    """
    Thread-safe DuckDB store for smart money data.

    Usage:
        store = DuckDBStore(db_path="data/smartmoney.duckdb", data_dir="data")
        store.refresh_all()
        rows = store.query("SELECT * FROM congress_trades WHERE UPPER(ticker) = ?", ["AAPL"])
    """

    # Map: JSON filename → list of table names it produces
    FILE_TABLES: Dict[str, List[str]] = {
        "congress.json":      ["congress_trades"],
        "ark_trades.json":    ["ark_trades"],
        "insiders.json":      ["insider_trades", "insider_clusters"],
        "darkpool.json":      ["darkpool_tickers", "darkpool_anomalies"],
        "institutions.json":  ["institution_filings", "institution_holdings"],
        "short_interest.json": ["short_interest"],
        "superinvestors.json": ["superinvestor_activity", "superinvestor_holdings"],
        "ranking_v3.json":    ["ranking"],
    }

    def __init__(self, db_path: str = "data/smartmoney.duckdb", data_dir: str = "data"):
        self.db_path = str(db_path)
        self.data_dir = Path(data_dir)
        self._write_lock = threading.RLock()
        self._last_refresh: Optional[float] = None
        self._table_counts: Dict[str, int] = {}
        self._initialized = False

    # ── Connection helpers ──────────────────────────────────────────────────

    def _connect_write(self):
        """Open a write connection. May raise if another process holds the lock."""
        import duckdb
        return duckdb.connect(self.db_path, read_only=False)

    def _connect_read(self):
        """Open a read-only connection (concurrent-safe across processes)."""
        import duckdb
        return duckdb.connect(self.db_path, read_only=True)

    # ── Core refresh ────────────────────────────────────────────────────────

    def refresh_all(self) -> Dict[str, int]:
        """
        Reload all JSON files into DuckDB tables.
        Uses CREATE OR REPLACE TABLE to atomically swap data.
        Returns {table_name: row_count}.
        Thread-safe — only one process/thread refreshes at a time.
        """
        with self._write_lock:
            try:
                conn = self._connect_write()
            except Exception as e:
                # Another process has write lock — skip refresh, read-only mode
                logger.info(f"[duckdb] Cannot acquire write lock (another process writing): {e}")
                return self._table_counts

            counts: Dict[str, int] = {}
            try:
                for filename, tables in self.FILE_TABLES.items():
                    filepath = self.data_dir / filename
                    if not filepath.exists():
                        logger.debug(f"[duckdb] Skipping missing file: {filepath}")
                        continue
                    try:
                        file_counts = self._load_file(conn, filename, filepath)
                        counts.update(file_counts)
                    except Exception as e:
                        logger.error(f"[duckdb] Failed to load {filename}: {e}", exc_info=True)

                self._last_refresh = time.time()
                self._table_counts = counts
                self._initialized = True
                total = sum(counts.values())
                logger.info(f"[duckdb] Refresh complete: {total} rows in {len(counts)} tables")
                return counts
            finally:
                conn.close()

    def refresh_table(self, table_name: str) -> int:
        """
        Refresh a single table from its source JSON file.
        Returns the row count after refresh.
        """
        source_file = None
        for fname, tables in self.FILE_TABLES.items():
            if table_name in tables:
                source_file = fname
                break
        if not source_file:
            raise ValueError(f"Unknown table: {table_name}")

        filepath = self.data_dir / source_file
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")

        with self._write_lock:
            try:
                conn = self._connect_write()
            except Exception as e:
                logger.warning(f"[duckdb] Cannot acquire write lock for refresh_table: {e}")
                return self._table_counts.get(table_name, 0)

            try:
                data = json.loads(filepath.read_text(encoding="utf-8"))
                file_counts = self._load_file(conn, source_file, filepath)
                self._table_counts.update(file_counts)
                return file_counts.get(table_name, 0)
            finally:
                conn.close()

    # ── File loaders ────────────────────────────────────────────────────────

    def _load_file(self, conn, filename: str, filepath: Path) -> Dict[str, int]:
        """Dispatch to the correct loader based on filename."""
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"[duckdb] Cannot parse {filename}: {e}")
            return {}

        loaders = {
            "congress.json":       self._load_congress,
            "ark_trades.json":     self._load_ark_trades,
            "insiders.json":       self._load_insiders,
            "darkpool.json":       self._load_darkpool,
            "institutions.json":   self._load_institutions,
            "short_interest.json": self._load_short_interest,
            "superinvestors.json": self._load_superinvestors,
            "ranking_v3.json":     self._load_ranking,
        }
        loader = loaders.get(filename)
        if loader is None:
            logger.warning(f"[duckdb] No loader for {filename}")
            return {}
        return loader(conn, data)

    def _create_table_from_rows(self, conn, table: str, rows: List[Dict]) -> int:
        """
        Create (or replace) a DuckDB table from a list of dicts.
        Uses pandas DataFrame → DuckDB for reliable type inference.
        Returns row count.
        """
        if not rows:
            # Create empty table — drop if exists and recreate as empty
            conn.execute(f"DROP TABLE IF EXISTS {table}")
            logger.debug(f"[duckdb] {table}: 0 rows (empty source)")
            return 0

        try:
            import pandas as pd
            # Normalize: convert lists/dicts to JSON strings for non-scalar fields
            normalized = [_normalize_row(r) for r in rows]
            df = pd.DataFrame(normalized)

            # Register df as a view so DuckDB can see it
            conn.register(f"_tmp_{table}", df)
            conn.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM _tmp_{table}")
            conn.unregister(f"_tmp_{table}")

            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            logger.debug(f"[duckdb] {table}: {count} rows loaded")
            return count

        except Exception as e:
            logger.error(f"[duckdb] Failed to create table {table}: {e}", exc_info=True)
            return 0

    def _load_congress(self, conn, data: dict) -> Dict[str, int]:
        trades = data.get("trades", [])
        c = self._create_table_from_rows(conn, "congress_trades", trades)
        return {"congress_trades": c}

    def _load_ark_trades(self, conn, data: dict) -> Dict[str, int]:
        trades = data.get("trades", [])
        c = self._create_table_from_rows(conn, "ark_trades", trades)
        return {"ark_trades": c}

    def _load_insiders(self, conn, data: dict) -> Dict[str, int]:
        trades = data.get("trades", [])
        clusters = data.get("clusters", [])
        c1 = self._create_table_from_rows(conn, "insider_trades", trades)
        c2 = self._create_table_from_rows(conn, "insider_clusters", clusters)
        return {"insider_trades": c1, "insider_clusters": c2}

    def _load_darkpool(self, conn, data: dict) -> Dict[str, int]:
        tickers = data.get("tickers", [])
        anomalies = data.get("anomalies", [])
        c1 = self._create_table_from_rows(conn, "darkpool_tickers", tickers)
        c2 = self._create_table_from_rows(conn, "darkpool_anomalies", anomalies)
        return {"darkpool_tickers": c1, "darkpool_anomalies": c2}

    def _load_institutions(self, conn, data: dict) -> Dict[str, int]:
        filings = data.get("filings", [])

        # Top-level filing rows (strip nested holdings)
        filing_rows = []
        holding_rows = []

        for f in filings:
            row = {k: v for k, v in f.items() if k != "holdings"}
            filing_rows.append(row)

            # Flatten holdings with parent filing metadata
            for h in f.get("holdings", []):
                hr = dict(h)
                hr["cik"] = f.get("cik", "")
                hr["fund_name"] = f.get("fund_name", "")
                hr["filing_date"] = f.get("filing_date", "")
                hr["quarter"] = f.get("quarter", "")
                # Compute pct_portfolio if not present
                if "pct_portfolio" not in hr:
                    total_val = f.get("total_value", 0) or 1
                    hr["pct_portfolio"] = (hr.get("value", 0) / total_val * 100)
                holding_rows.append(hr)

        c1 = self._create_table_from_rows(conn, "institution_filings", filing_rows)
        c2 = self._create_table_from_rows(conn, "institution_holdings", holding_rows)
        return {"institution_filings": c1, "institution_holdings": c2}

    def _load_short_interest(self, conn, data: dict) -> Dict[str, int]:
        tickers = data.get("tickers", [])
        c = self._create_table_from_rows(conn, "short_interest", tickers)
        return {"short_interest": c}

    def _load_superinvestors(self, conn, data: dict) -> Dict[str, int]:
        activity = data.get("activity", [])

        # Flatten holdings: dict[code] → {manager, top_holdings: [...]}
        holdings_flat = []
        for code, h in data.get("holdings", {}).items():
            manager_meta = {
                "manager_code": code,
                "manager": h.get("manager", ""),
                "period": h.get("period", ""),
                "portfolio_date": h.get("portfolio_date", ""),
                "num_stocks": h.get("num_stocks", 0),
                "portfolio_value": h.get("portfolio_value", 0),
            }
            for th in h.get("top_holdings", []):
                row = dict(th)
                row.update(manager_meta)
                holdings_flat.append(row)

        c1 = self._create_table_from_rows(conn, "superinvestor_activity", activity)
        c2 = self._create_table_from_rows(conn, "superinvestor_holdings", holdings_flat)
        return {"superinvestor_activity": c1, "superinvestor_holdings": c2}

    def _load_ranking(self, conn, data: dict) -> Dict[str, int]:
        signals = data.get("signals", [])
        # Store sources list as both a list field and a comma-separated string
        rows = []
        for s in signals:
            row = dict(s)
            src = row.get("sources")
            if isinstance(src, list):
                row["sources_str"] = ",".join(src)
            else:
                row["sources_str"] = str(src or "")
            # Flatten v7_breakdown if present (nested dict — convert to JSON string)
            if isinstance(row.get("v7_breakdown"), dict):
                row["v7_breakdown"] = json.dumps(row["v7_breakdown"])
            if isinstance(row.get("details"), list):
                row["details"] = json.dumps(row["details"])
            rows.append(row)
        c = self._create_table_from_rows(conn, "ranking", rows)
        return {"ranking": c}

    # ── Query interface ────────────────────────────────────────────────────

    def query(self, sql: str, params: Optional[List] = None) -> List[Dict]:
        """
        Execute a SQL query and return a list of dicts.
        Uses a read-only connection for concurrent safety.
        Raises on error (callers should catch and fall back to JSON).
        """
        conn = self._connect_read()
        try:
            if params:
                result = conn.execute(sql, params)
            else:
                result = conn.execute(sql)
            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()

    def query_many(self, queries: List[tuple]) -> List[List[Dict]]:
        """
        Execute multiple SQL queries on a single read connection.
        Each element: (sql, params) or (sql,).
        Returns list of result-lists, one per query.
        Cuts per-query connection overhead from ~40ms to ~2ms.
        """
        conn = self._connect_read()
        try:
            results = []
            for q in queries:
                sql = q[0]
                params = q[1] if len(q) > 1 else None
                if params:
                    result = conn.execute(sql, params)
                else:
                    result = conn.execute(sql)
                columns = [desc[0] for desc in result.description]
                rows = result.fetchall()
                results.append([dict(zip(columns, row)) for row in rows])
            return results
        finally:
            conn.close()

    def query_one(self, sql: str, params: Optional[List] = None) -> Optional[Dict]:
        """Execute a SQL query and return the first row as a dict, or None."""
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def table_exists(self, table: str) -> bool:
        """Check if a table exists in the DuckDB file."""
        try:
            conn = self._connect_read()
            try:
                result = conn.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
                    [table]
                ).fetchone()
                return (result[0] > 0) if result else False
            finally:
                conn.close()
        except Exception:
            return False

    # ── Status ─────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return database status information."""
        try:
            size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        except OSError:
            size_bytes = 0

        # Try to get live row counts from DB
        live_counts = {}
        try:
            conn = self._connect_read()
            try:
                for table in [t for tables in self.FILE_TABLES.values() for t in tables]:
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                        live_counts[table] = count
                    except Exception:
                        live_counts[table] = -1
            finally:
                conn.close()
        except Exception:
            live_counts = self._table_counts

        return {
            "db_path": self.db_path,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "initialized": self._initialized,
            "last_refresh": self._last_refresh,
            "last_refresh_iso": (
                datetime.fromtimestamp(self._last_refresh, tz=timezone.utc).isoformat()
                if self._last_refresh else None
            ),
            "table_counts": live_counts,
            "total_rows": sum(v for v in live_counts.values() if v >= 0),
        }


# ── Helper ─────────────────────────────────────────────────────────────────

def _normalize_row(row: Dict) -> Dict:
    """
    Normalize a dict row for DuckDB insertion via pandas.
    Converts lists/dicts to JSON strings to avoid pandas object dtype issues.
    Scalar types (str, int, float, bool, None) are kept as-is.
    """
    out = {}
    for k, v in row.items():
        if isinstance(v, (list, dict)):
            out[k] = json.dumps(v, default=str, ensure_ascii=False)
        else:
            out[k] = v
    return out


# ── Singleton accessors ────────────────────────────────────────────────────

def init_store(db_path: Optional[str] = None, data_dir: Optional[str] = None) -> "DuckDBStore":
    """Initialize the global DuckDB store singleton."""
    global _store
    with _store_lock:
        if _store is not None:
            return _store
        try:
            from api.config import DATA_DIR
            if db_path is None:
                db_path = str(DATA_DIR / "smartmoney.duckdb")
            if data_dir is None:
                data_dir = str(DATA_DIR)
        except ImportError:
            if db_path is None:
                db_path = "data/smartmoney.duckdb"
            if data_dir is None:
                data_dir = "data"

        _store = DuckDBStore(db_path=db_path, data_dir=data_dir)
        return _store


def get_store() -> "DuckDBStore":
    """Get the global DuckDB store. Raises RuntimeError if not initialized."""
    global _store
    if _store is None:
        # Auto-initialize if not done yet (lazy init)
        return init_store()
    return _store
