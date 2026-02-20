"""
Knowledge Hub API — serves educational articles about signal sources.

GET /api/knowledge        — list all articles (summary fields)
GET /api/knowledge/{slug} — full article including content_md

Content is loaded from JSON files in /app/content/knowledge/ (or KNOWLEDGE_DIR env).
Files are cached in memory and refreshed every 60s if mtime changes.
"""

import json
import os
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()

# ── Config ─────────────────────────────────────────────────────────────────
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", "/app/content/knowledge"))

# ── In-memory cache ────────────────────────────────────────────────────────
_cache: dict[str, dict[str, Any]] = {}        # slug → full article data
_file_mtimes: dict[str, float] = {}           # filename → last mtime seen
_last_scan: float = 0.0
_SCAN_INTERVAL = 60.0  # seconds between directory scans


def _scan_and_refresh() -> None:
    """Scan KNOWLEDGE_DIR for JSON files and refresh cache if any have changed."""
    global _last_scan

    now = time.time()
    if now - _last_scan < _SCAN_INTERVAL:
        return
    _last_scan = now

    if not KNOWLEDGE_DIR.exists():
        return

    for file_path in KNOWLEDGE_DIR.glob("*.json"):
        try:
            mtime = file_path.stat().st_mtime
        except OSError:
            continue

        if _file_mtimes.get(file_path.name) == mtime:
            continue  # unchanged

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            slug = data.get("slug") or file_path.stem
            _cache[slug] = data
            _file_mtimes[file_path.name] = mtime
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[knowledge] Failed to load {file_path.name}: {exc}")

    # Remove stale entries if files were deleted
    live_stems = {p.stem for p in KNOWLEDGE_DIR.glob("*.json")}
    stale = [slug for slug in list(_cache) if slug not in live_stems]
    for slug in stale:
        _cache.pop(slug, None)


def _get_all() -> list[dict[str, Any]]:
    """Return all articles, sorted by updated_at desc."""
    _scan_and_refresh()
    summaries = []
    for article in _cache.values():
        summaries.append({
            "slug": article.get("slug", ""),
            "title": article.get("title", ""),
            "subtitle": article.get("subtitle", ""),
            "category": article.get("category", ""),
            "signal_source": article.get("signal_source", ""),
            "layer": article.get("layer", "L1"),
            "parent_article": article.get("parent_article"),
            "tldr": article.get("tldr", ""),
            "hero_stat": article.get("hero_stat"),
            "key_takeaways": article.get("key_takeaways", []),
            "related_articles": article.get("related_articles", []),
            "updated_at": article.get("updated_at", ""),
        })
    summaries.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return summaries


def _get_one(slug: str) -> dict[str, Any] | None:
    """Return full article by slug."""
    _scan_and_refresh()
    return _cache.get(slug)


# ── Routes ──────────────────────────────────────────────────────────────────

@router.get("/api/knowledge")
def list_articles():
    """List all knowledge hub articles (summary fields only)."""
    articles = _get_all()
    return {
        "articles": articles,
        "count": len(articles),
    }


@router.get("/api/knowledge/{slug}")
def get_article(slug: str):
    """Get a full knowledge hub article by slug."""
    article = _get_one(slug)
    if article is None:
        raise HTTPException(
            status_code=404,
            detail=f"Article '{slug}' not found",
        )
    return article
