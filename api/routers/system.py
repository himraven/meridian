"""
System routes — Meridian (minimal: db-status only)
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/api/system/db-status")
def api_system_db_status():
    """DuckDB query layer status and table statistics."""
    try:
        from api.modules.duckdb_store import get_store
        store = get_store()
        if store is None:
            return {"status": "not_initialized", "tables": {}}
        return store.get_status()
    except ImportError:
        return {"status": "duckdb_not_installed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
