"""
System routes - health, VPS metrics, projects, todos, crons, admin
"""
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import psutil
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.shared import (
    PROJECTS_FILE, TODOS_FILE, SIGNAL_LOG, PORTFOLIO_FILE,
    HK_STATE_FILE, HK_ENTRY_EXIT_FILE, HK_MONTHLY_PICKS_FILE,
    ARK_DATA_DIR, CN_TREND_FILE, read_json, read_jsonl, file_mtime
)

router = APIRouter()

# ── Models ─────────────────────────────────────────────────────────────

class GatewayRestartRequest(BaseModel):
    action: str = "restart"  # restart | reset


class CronToggleRequest(BaseModel):
    id: str
    enabled: bool


class TodoCreate(BaseModel):
    text: str
    priority: str = "medium"
    status: str = "todo"
    project: str = "Other"
    tags: list[str] = []
    due_date: Optional[str] = None
    notes: Optional[str] = None


class TodoUpdate(BaseModel):
    text: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    project: Optional[str] = None
    tags: Optional[list[str]] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    blocked_reason: Optional[str] = None


class ReorderRequest(BaseModel):
    ids: list[str]


# ── Routes ─────────────────────────────────────────────────────────────

@router.get("/api/health")
def health_check():
    """Health check endpoint for monitoring and Docker healthcheck."""
    from api.config import DATA_DIR as SM_DATA_DIR
    data_files = {
        "congress": (SM_DATA_DIR / "congress.json").exists(),
        "institutions": (SM_DATA_DIR / "institutions.json").exists(),
        "darkpool": (SM_DATA_DIR / "darkpool.json").exists(),
        "ark_trades": (SM_DATA_DIR / "ark_trades.json").exists(),
    }
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - psutil.boot_time()),
        "data_sources": data_files,
        "version": "2.0.0",
    }

@router.get("/api/system/db")
def api_system_db():
    """Database status — table row counts and file size."""
    try:
        from api.database import engine
        from sqlalchemy import text
        from api.config import DATA_DIR as SM_DATA_DIR

        db_path = SM_DATA_DIR / "smartmoney.db"
        tables = {}
        with engine.connect() as conn:
            for table in ["congress_trades", "ark_trades", "ark_holdings",
                          "darkpool_data", "institution_filings",
                          "institution_holdings", "signals", "ticker_names",
                          "data_refresh_log"]:
                try:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    tables[table] = count
                except Exception:
                    tables[table] = -1

        return {
            "status": "ok",
            "database": str(db_path),
            "size_mb": round(db_path.stat().st_size / (1024 * 1024), 2) if db_path.exists() else 0,
            "tables": tables,
            "total_rows": sum(v for v in tables.values() if v > 0),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/api/system/db-status")
def api_system_db_status():
    """DuckDB query layer status — table row counts, last refresh, DB size."""
    try:
        from api.modules.duckdb_store import get_store
        store = get_store()
        status = store.get_status()
        return {"status": "ok", **status}
    except Exception as e:
        return {"status": "error", "error": str(e), "initialized": False}


@router.post("/api/system/db-refresh")
def api_system_db_refresh():
    """Manually trigger a DuckDB refresh from JSON files."""
    try:
        from api.modules.db_init import trigger_refresh
        counts = trigger_refresh()
        total = sum(counts.values())
        return {
            "status": "ok",
            "tables_refreshed": len(counts),
            "total_rows": total,
            "counts": counts,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/api/system/vps")
def api_system_vps():
    """VPS system metrics via psutil."""
    try:
        cpu_pct = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        boot_time = psutil.boot_time()
        uptime_secs = time.time() - boot_time

        # Format uptime
        days = int(uptime_secs // 86400)
        hours = int((uptime_secs % 86400) // 3600)
        mins = int((uptime_secs % 3600) // 60)
        if days > 0:
            uptime_str = f"{days}d {hours}h {mins}m"
        elif hours > 0:
            uptime_str = f"{hours}h {mins}m"
        else:
            uptime_str = f"{mins}m"

        return {
            "cpu_pct": cpu_pct,
            "cpu_count": psutil.cpu_count(),
            "ram_used_gb": round(mem.used / (1024**3), 1),
            "ram_total_gb": round(mem.total / (1024**3), 1),
            "ram_pct": mem.percent,
            "disk_used_gb": round(disk.used / (1024**3), 1),
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "disk_pct": round(disk.percent, 1),
            "uptime": uptime_str,
            "uptime_secs": int(uptime_secs),
            "hostname": os.uname().nodename,
            "os": f"{os.uname().sysname} {os.uname().release}",
            "load_avg": list(os.getloadavg()),
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/system/nova")
def api_system_nova():
    """Nova (Clawdbot) status — read from process list and gateway."""
    result = {
        "online": False,
        "model": "claude-opus-4-6",
        "gateway_running": False,
        "uptime": None,
        "pid": None,
    }

    try:
        # Method 1: Try HTTP health check to gateway (works inside Docker)
        import urllib.request
        gateway_port = os.environ.get("GATEWAY_PORT", "18789")
        # Try host.docker.internal (Docker) then localhost (bare-metal)
        for host in ["host.docker.internal", "localhost"]:
            try:
                url = f"http://{host}:{gateway_port}/"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        result["gateway_running"] = True
                        result["online"] = True
                        break
            except Exception:
                continue

        # Method 2: Check process list (works on bare-metal)
        if not result["online"]:
            for proc in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
                try:
                    name = proc.info["name"] or ""
                    if "clawdbot-gateway" in name:
                        result["gateway_running"] = True
                        result["online"] = True
                        result["pid"] = proc.info["pid"]
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        # Calculate uptime from session activity
        sessions_dir = Path.home() / ".clawdbot" / "agents" / "main" / "sessions"
        if result["online"] and sessions_dir.exists():
            latest_mtime = 0
            for f in sessions_dir.iterdir():
                if f.suffix == ".jsonl":
                    mt = f.stat().st_mtime
                    if mt > latest_mtime:
                        latest_mtime = mt
            if latest_mtime > 0:
                uptime_secs = time.time() - latest_mtime
                if uptime_secs < 300:  # Active in last 5 min
                    result["uptime"] = "Active now"
                else:
                    mins = int(uptime_secs // 60)
                    hours = int(mins // 60)
                    days = int(hours // 24)
                    if days > 0:
                        result["uptime"] = f"{days}d {hours%24}h ago"
                    elif hours > 0:
                        result["uptime"] = f"{hours}h {mins%60}m ago"
                    else:
                        result["uptime"] = f"{mins}m ago"

        # Try to get last activity from telegram session files
        tg_dir = Path.home() / ".clawdbot" / "telegram"
        if tg_dir.exists():
            latest_mtime = 0
            for f in tg_dir.iterdir():
                mt = f.stat().st_mtime
                if mt > latest_mtime:
                    latest_mtime = mt
            if latest_mtime > 0:
                result["last_activity"] = datetime.fromtimestamp(latest_mtime, tz=timezone.utc).isoformat()

        # Count active sessions from subagents dir
        sa_dir = Path.home() / ".clawdbot" / "subagents"
        if sa_dir.exists():
            active = sum(1 for f in sa_dir.iterdir() if f.is_file())
            result["active_sessions"] = active

    except Exception as e:
        result["error"] = str(e)

    return result

@router.get("/api/system/usage")
def api_system_usage():
    """API usage — parsed from session transcripts."""
    try:
        from api.modules.usage import get_usage_data
        return get_usage_data()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "today": {"cost": 0, "tokens_in": 0, "tokens_out": 0},
            "this_week": {"cost": 0, "tokens_in": 0, "tokens_out": 0},
            "this_month": {"cost": 0, "tokens_in": 0, "tokens_out": 0},
            "by_day": [],
            "by_model": {},
        }

@router.post("/api/system/gateway/restart")
def api_system_gateway_restart():
    """Restart the Clawdbot Gateway service."""
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "clawdbot-gateway"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return {"ok": True, "message": "Gateway restart initiated"}
        else:
            return JSONResponse(
                {"ok": False, "error": result.stderr.strip() or "Restart failed"},
                status_code=500
            )
    except subprocess.TimeoutExpired:
        return JSONResponse(
            {"ok": False, "error": "Restart command timed out"},
            status_code=504
        )
    except Exception as e:
        return JSONResponse(
            {"ok": False, "error": str(e)},
            status_code=500
        )

@router.get("/api/projects")
def api_projects():
    """Return projects from config file."""
    data = read_json(str(PROJECTS_FILE))
    if data is None:
        return []
    return data

@router.get("/api/projects/{project_id}")
def api_project_detail(project_id: str):
    """Return a single project by ID."""
    data = read_json(str(PROJECTS_FILE))
    if data is None:
        return JSONResponse({"error": "Projects data not available"}, status_code=500)
    for project in data:
        if project.get("id") == project_id:
            return project
    return JSONResponse({"error": "Project not found"}, status_code=404)

@router.get("/api/todos")
def api_todos(status: str = None, project: str = None):
    """Return todos from config file with optional filtering."""
    data = read_json(str(TODOS_FILE))
    if data is None:
        return []
    
    # Apply filters
    filtered = data
    if status:
        filtered = [t for t in filtered if t.get("status") == status]
    if project:
        filtered = [t for t in filtered if t.get("project") == project]
    
    return filtered


from pydantic import BaseModel
from typing import Optional

@router.post("/api/todos")
def api_create_todo(todo: TodoCreate):
    """Create a new todo."""
    try:
        import uuid
        from datetime import datetime, timezone
        
        data = read_json(str(TODOS_FILE))
        if data is None:
            data = []
        
        now = datetime.now(timezone.utc).isoformat()
        new_todo = {
            "id": str(uuid.uuid4()),
            "text": todo.text,
            "priority": todo.priority,
            "status": todo.status,
            "project": todo.project,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "blocked_reason": None,
            "tags": todo.tags,
            "due_date": todo.due_date,
            "notes": todo.notes,
        }
        
        data.append(new_todo)
        
        with open(TODOS_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return new_todo
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.put("/api/todos/{todo_id}")
def api_update_todo(todo_id: str, update: TodoUpdate):
    """Update any field of a todo."""
    try:
        from datetime import datetime, timezone
        
        data = read_json(str(TODOS_FILE))
        if data is None:
            return JSONResponse({"error": "Cannot read todos"}, status_code=500)
        
        # Find todo by ID
        todo_idx = None
        for i, t in enumerate(data):
            if t.get("id") == todo_id:
                todo_idx = i
                break
        
        if todo_idx is None:
            return JSONResponse({"error": "Todo not found"}, status_code=404)
        
        # Update fields
        now = datetime.now(timezone.utc).isoformat()
        for field, value in update.dict(exclude_unset=True).items():
            data[todo_idx][field] = value
        
        data[todo_idx]["updated_at"] = now
        
        # Handle status transitions
        if update.status == "done" and data[todo_idx].get("status") != "done":
            data[todo_idx]["completed_at"] = now
        elif update.status != "done":
            data[todo_idx]["completed_at"] = None
        
        with open(TODOS_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return data[todo_idx]
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/api/todos/{todo_id}")
def api_delete_todo(todo_id: str):
    """Delete a todo."""
    try:
        data = read_json(str(TODOS_FILE))
        if data is None:
            return JSONResponse({"error": "Cannot read todos"}, status_code=500)
        
        # Find and remove todo by ID
        original_len = len(data)
        data = [t for t in data if t.get("id") != todo_id]
        
        if len(data) == original_len:
            return JSONResponse({"error": "Todo not found"}, status_code=404)
        
        with open(TODOS_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"ok": True, "deleted": todo_id}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/todos/{todo_id}/toggle")
def api_toggle_todo(todo_id: str):
    """Quick toggle todo status between todo and done."""
    try:
        from datetime import datetime, timezone
        
        data = read_json(str(TODOS_FILE))
        if data is None:
            return JSONResponse({"error": "Cannot read todos"}, status_code=500)
        
        # Find todo by ID
        todo_idx = None
        for i, t in enumerate(data):
            if t.get("id") == todo_id:
                todo_idx = i
                break
        
        if todo_idx is None:
            return JSONResponse({"error": "Todo not found"}, status_code=404)
        
        now = datetime.now(timezone.utc).isoformat()
        current_status = data[todo_idx].get("status", "todo")
        
        if current_status == "done":
            data[todo_idx]["status"] = "todo"
            data[todo_idx]["completed_at"] = None
        else:
            data[todo_idx]["status"] = "done"
            data[todo_idx]["completed_at"] = now
        
        data[todo_idx]["updated_at"] = now
        
        with open(TODOS_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"ok": True, "id": todo_id, "status": data[todo_idx]["status"]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/api/todos/reorder")
def api_reorder_todos(req: ReorderRequest):
    """Reorder todos by ID list."""
    try:
        data = read_json(str(TODOS_FILE))
        if data is None:
            return JSONResponse({"error": "Cannot read todos"}, status_code=500)
        
        # Create a map of id -> todo
        todo_map = {t["id"]: t for t in data}
        
        # Reorder according to req.ids
        reordered = []
        for todo_id in req.ids:
            if todo_id in todo_map:
                reordered.append(todo_map[todo_id])
        
        # Add any todos not in the reorder list (shouldn't happen but safe)
        for t in data:
            if t["id"] not in req.ids:
                reordered.append(t)
        
        with open(TODOS_FILE, "w") as f:
            json.dump(reordered, f, ensure_ascii=False, indent=2)
        
        return {"ok": True, "count": len(reordered)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# Legacy endpoint (for backwards compatibility with index-based toggle)

@router.post("/api/todos/{index}/toggle")
def api_toggle_todo_legacy(index: int):
    """Toggle a todo's done status (legacy index-based endpoint)."""
    try:
        data = read_json(str(TODOS_FILE))
        if data is None:
            return JSONResponse({"error": "Cannot read todos"}, status_code=500)
        if index < 0 or index >= len(data):
            return JSONResponse({"error": "Index out of range"}, status_code=400)

        # Convert old 'done' to new 'status' model
        if "status" in data[index]:
            current_status = data[index]["status"]
            if current_status == "done":
                data[index]["status"] = "todo"
            else:
                data[index]["status"] = "done"
        else:
            # Legacy compatibility
            data[index]["done"] = not data[index].get("done", False)

        with open(TODOS_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"ok": True, "index": index, "done": data[index].get("done"), "status": data[index].get("status")}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/api/system/crons")
def api_system_crons():
    """Parse crontab and return structured cron job list."""
    crons = []
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    schedule = " ".join(parts[:5])
                    command = parts[5]
                    # Extract a friendly name from the command
                    name = command.split("/")[-1].split(";")[0].split("|")[0].strip()
                    if len(name) > 50:
                        name = name[:47] + "..."
                    crons.append({
                        "schedule": schedule,
                        "command": command,
                        "name": name,
                    })
    except Exception:
        pass
    return {"crons": crons}

@router.get("/api/system/signals")
def api_system_signals():
    """Recent signals from signal_log.jsonl."""
    signals = read_jsonl(SIGNAL_LOG, limit=20)
    # Return most recent first
    signals.reverse()
    return {"signals": signals}
