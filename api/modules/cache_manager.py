"""
Cache Manager — Thread-safe JSON cache read/write

Provides a simple interface for reading and writing JSON cache files.
All data flows through these cache files:
  Quiver API → Collectors → Cache (JSON) → API Endpoints → Frontend

Features:
- Atomic writes (write to tmp, then rename)
- File existence and freshness checks
- Thread-safe operations
- Automatic directory creation
"""

import json
import os
import tempfile
import time
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manage JSON cache files in a specified directory.
    
    Usage:
        cache = CacheManager("data")
        cache.write("congress.json", {"trades": [...]})
        data = cache.read("congress.json")
    """

    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _filepath(self, filename: str) -> Path:
        """Resolve filename to full path within cache directory."""
        # Prevent path traversal
        safe_name = Path(filename).name
        if safe_name != filename:
            raise ValueError(f"Invalid cache filename (path traversal detected): {filename}")
        return self.cache_dir / safe_name

    def read(self, filename: str) -> Dict[str, Any]:
        """
        Read a JSON cache file.
        
        Returns empty dict if file doesn't exist or is invalid JSON.
        Never raises on missing/corrupt files — caller gets {} and can handle it.
        """
        filepath = self._filepath(filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                logger.warning(f"Cache file {filename} is not a JSON object, got {type(data).__name__}")
                return {}
            return data
        except FileNotFoundError:
            logger.debug(f"Cache file not found: {filename}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            return {}
        except OSError as e:
            logger.error(f"OS error reading {filename}: {e}")
            return {}

    def write(self, filename: str, data: Dict[str, Any]) -> bool:
        """
        Write data to a JSON cache file atomically.
        
        Uses write-to-temp-then-rename pattern for crash safety.
        Returns True on success, False on failure.
        """
        filepath = self._filepath(filename)
        try:
            # Write to temp file in same directory (same filesystem for atomic rename)
            fd, tmp_path = tempfile.mkstemp(
                dir=str(self.cache_dir),
                prefix=f".{filename}.",
                suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str, ensure_ascii=False)
                # Atomic rename
                os.replace(tmp_path, str(filepath))
                logger.debug(f"Wrote cache file: {filename} ({filepath.stat().st_size} bytes)")
                return True
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except Exception as e:
            logger.error(f"Failed to write cache file {filename}: {e}")
            return False

    def exists(self, filename: str) -> bool:
        """Check if a cache file exists."""
        return self._filepath(filename).exists()

    def get_mtime(self, filename: str) -> Optional[float]:
        """
        Get modification time of a cache file (Unix timestamp).
        Returns None if file doesn't exist.
        """
        filepath = self._filepath(filename)
        try:
            return filepath.stat().st_mtime
        except FileNotFoundError:
            return None
        except OSError as e:
            logger.error(f"Error getting mtime for {filename}: {e}")
            return None

    def get_age_seconds(self, filename: str) -> Optional[float]:
        """
        Get age of cache file in seconds.
        Returns None if file doesn't exist.
        """
        mtime = self.get_mtime(filename)
        if mtime is None:
            return None
        return time.time() - mtime

    def is_stale(self, filename: str, max_age_seconds: float) -> bool:
        """
        Check if a cache file is older than max_age_seconds.
        Returns True if stale or if file doesn't exist.
        """
        age = self.get_age_seconds(filename)
        if age is None:
            return True  # Non-existent = stale
        return age > max_age_seconds

    def list_files(self) -> list[str]:
        """List all JSON files in the cache directory."""
        return sorted(
            f.name for f in self.cache_dir.iterdir()
            if f.is_file() and f.suffix == ".json"
        )

    def delete(self, filename: str) -> bool:
        """
        Delete a cache file.
        Returns True if deleted, False if not found or error.
        """
        filepath = self._filepath(filename)
        try:
            filepath.unlink()
            logger.info(f"Deleted cache file: {filename}")
            return True
        except FileNotFoundError:
            return False
        except OSError as e:
            logger.error(f"Error deleting {filename}: {e}")
            return False

    def get_size_bytes(self, filename: str) -> Optional[int]:
        """Get file size in bytes. Returns None if not found."""
        filepath = self._filepath(filename)
        try:
            return filepath.stat().st_size
        except (FileNotFoundError, OSError):
            return None
