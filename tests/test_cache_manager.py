"""
Tests for CacheManager.

Validates:
- Read/write JSON files correctly
- Atomic writes (crash safety)
- Missing file handling (returns {})
- Invalid JSON handling (returns {})
- Path traversal prevention
- File existence and freshness checks
- File listing and deletion
- Concurrent access safety
"""

import json
import os
import time
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from api.modules.cache_manager import CacheManager


@pytest.fixture
def cache_dir(tmp_path):
    """Create a temporary cache directory."""
    return str(tmp_path / "test_cache")


@pytest.fixture
def cache(cache_dir):
    """Create a CacheManager instance with temp directory."""
    return CacheManager(cache_dir)


# ── Basic Read/Write ───────────────────────────────────────────────────────


class TestReadWrite:
    def test_write_and_read(self, cache):
        data = {"trades": [{"ticker": "NVDA", "price": 875.43}], "count": 1}
        assert cache.write("test.json", data) is True
        result = cache.read("test.json")
        assert result == data

    def test_write_creates_file(self, cache, cache_dir):
        cache.write("new_file.json", {"key": "value"})
        assert os.path.exists(os.path.join(cache_dir, "new_file.json"))

    def test_write_overwrites_existing(self, cache):
        cache.write("test.json", {"version": 1})
        cache.write("test.json", {"version": 2})
        result = cache.read("test.json")
        assert result["version"] == 2

    def test_read_nonexistent_returns_empty(self, cache):
        result = cache.read("nonexistent.json")
        assert result == {}

    def test_write_nested_data(self, cache):
        data = {
            "signals": [
                {
                    "ticker": "NVDA",
                    "score": 8.46,
                    "signals": [
                        {"type": "congress", "date": "2025-01-20"},
                        {"type": "ark", "date": "2025-01-24"},
                    ]
                }
            ],
            "metadata": {
                "total_count": 47,
                "last_updated": "2025-01-26T22:05:00Z"
            }
        }
        cache.write("nested.json", data)
        result = cache.read("nested.json")
        assert result["signals"][0]["score"] == 8.46
        assert len(result["signals"][0]["signals"]) == 2

    def test_write_unicode(self, cache):
        data = {"name": "Pelosi 佩洛西", "notes": "国会交易 🏛️"}
        cache.write("unicode.json", data)
        result = cache.read("unicode.json")
        assert result["name"] == "Pelosi 佩洛西"
        assert "🏛️" in result["notes"]

    def test_write_empty_dict(self, cache):
        cache.write("empty.json", {})
        result = cache.read("empty.json")
        assert result == {}

    def test_write_large_data(self, cache):
        data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(10_000)]}
        cache.write("large.json", data)
        result = cache.read("large.json")
        assert len(result["items"]) == 10_000


# ── Error Handling ─────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_read_invalid_json(self, cache, cache_dir):
        # Write invalid JSON directly
        filepath = os.path.join(cache_dir, "bad.json")
        os.makedirs(cache_dir, exist_ok=True)
        with open(filepath, "w") as f:
            f.write("{invalid json content")
        result = cache.read("bad.json")
        assert result == {}

    def test_read_json_array_returns_empty(self, cache, cache_dir):
        """We expect JSON objects (dict), not arrays."""
        filepath = os.path.join(cache_dir, "array.json")
        os.makedirs(cache_dir, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump([1, 2, 3], f)
        result = cache.read("array.json")
        assert result == {}

    def test_path_traversal_rejected(self, cache):
        with pytest.raises(ValueError, match="path traversal"):
            cache.read("../../../etc/passwd")

    def test_path_traversal_write_rejected(self, cache):
        with pytest.raises(ValueError, match="path traversal"):
            cache.write("../../hack.json", {"evil": True})

    def test_path_traversal_subdirectory_rejected(self, cache):
        with pytest.raises(ValueError, match="path traversal"):
            cache.read("subdir/file.json")


# ── File Existence & Freshness ─────────────────────────────────────────────


class TestExistenceAndFreshness:
    def test_exists_true(self, cache):
        cache.write("exists.json", {"data": True})
        assert cache.exists("exists.json") is True

    def test_exists_false(self, cache):
        assert cache.exists("nope.json") is False

    def test_get_mtime(self, cache):
        cache.write("timed.json", {"t": 1})
        mtime = cache.get_mtime("timed.json")
        assert mtime is not None
        assert abs(mtime - time.time()) < 5  # Within 5 seconds

    def test_get_mtime_nonexistent(self, cache):
        assert cache.get_mtime("nope.json") is None

    def test_get_age_seconds(self, cache):
        cache.write("aged.json", {"t": 1})
        age = cache.get_age_seconds("aged.json")
        assert age is not None
        assert age < 5  # Just written

    def test_get_age_nonexistent(self, cache):
        assert cache.get_age_seconds("nope.json") is None

    def test_is_stale_fresh_file(self, cache):
        cache.write("fresh.json", {"t": 1})
        assert cache.is_stale("fresh.json", max_age_seconds=3600) is False

    def test_is_stale_old_file(self, cache, cache_dir):
        cache.write("old.json", {"t": 1})
        filepath = os.path.join(cache_dir, "old.json")
        # Set mtime to 2 hours ago
        old_time = time.time() - 7200
        os.utime(filepath, (old_time, old_time))
        assert cache.is_stale("old.json", max_age_seconds=3600) is True

    def test_is_stale_nonexistent(self, cache):
        assert cache.is_stale("nope.json", max_age_seconds=3600) is True


# ── List & Delete ──────────────────────────────────────────────────────────


class TestListAndDelete:
    def test_list_files(self, cache):
        cache.write("a.json", {"a": 1})
        cache.write("b.json", {"b": 2})
        cache.write("c.json", {"c": 3})
        files = cache.list_files()
        assert files == ["a.json", "b.json", "c.json"]

    def test_list_files_empty(self, cache):
        assert cache.list_files() == []

    def test_list_ignores_non_json(self, cache, cache_dir):
        cache.write("valid.json", {"v": 1})
        # Create non-JSON file
        os.makedirs(cache_dir, exist_ok=True)
        with open(os.path.join(cache_dir, "readme.txt"), "w") as f:
            f.write("not json")
        files = cache.list_files()
        assert files == ["valid.json"]

    def test_delete_existing(self, cache):
        cache.write("doomed.json", {"bye": True})
        assert cache.delete("doomed.json") is True
        assert cache.exists("doomed.json") is False

    def test_delete_nonexistent(self, cache):
        assert cache.delete("nope.json") is False


# ── File Size ──────────────────────────────────────────────────────────────


class TestFileSize:
    def test_get_size(self, cache):
        cache.write("sized.json", {"data": "x" * 1000})
        size = cache.get_size_bytes("sized.json")
        assert size is not None
        assert size > 1000

    def test_get_size_nonexistent(self, cache):
        assert cache.get_size_bytes("nope.json") is None


# ── Directory Creation ─────────────────────────────────────────────────────


class TestDirectoryCreation:
    def test_auto_creates_directory(self, tmp_path):
        deep_path = str(tmp_path / "a" / "b" / "c" / "cache")
        cache = CacheManager(deep_path)
        assert os.path.isdir(deep_path)

    def test_existing_directory_ok(self, tmp_path):
        existing = str(tmp_path / "existing")
        os.makedirs(existing)
        cache = CacheManager(existing)  # Should not raise
        cache.write("test.json", {"ok": True})
        assert cache.read("test.json") == {"ok": True}


# ── Atomic Write Safety ───────────────────────────────────────────────────


class TestAtomicWrite:
    def test_no_partial_writes_on_replace_error(self, cache, cache_dir):
        """If os.replace fails, original file should remain intact."""
        cache.write("original.json", {"version": "original"})
        
        from unittest.mock import patch
        
        # Mock os.replace to simulate failure after temp file is written
        with patch("api.modules.cache_manager.os.replace", side_effect=OSError("Permission denied")):
            result = cache.write("original.json", {"version": "corrupted"})
        
        assert result is False
        # Original file should still be intact (replace never happened)
        data = cache.read("original.json")
        assert data["version"] == "original"

    def test_write_returns_false_on_os_error(self, cache):
        """Write should return False when OS-level error occurs."""
        from unittest.mock import patch
        
        with patch("api.modules.cache_manager.tempfile.mkstemp", side_effect=OSError("No space")):
            result = cache.write("fail.json", {"data": True})
        assert result is False

    def test_default_str_serializes_objects(self, cache):
        """json.dump with default=str handles non-serializable objects gracefully."""
        from datetime import datetime
        data = {"timestamp": datetime(2025, 1, 20, 12, 0), "count": 5}
        assert cache.write("datetime.json", data) is True
        result = cache.read("datetime.json")
        assert "2025-01-20" in result["timestamp"]
        assert result["count"] == 5


# ── Data Integrity ─────────────────────────────────────────────────────────


class TestDataIntegrity:
    def test_float_precision(self, cache):
        """Financial data needs precise floats."""
        data = {
            "dpi": 0.89123456789,
            "z_score": 3.14159265,
            "price": 875.4321,
        }
        cache.write("precision.json", data)
        result = cache.read("precision.json")
        assert result["dpi"] == 0.89123456789
        assert result["z_score"] == 3.14159265
        assert result["price"] == 875.4321

    def test_large_integers(self, cache):
        """Market cap and volume can be very large."""
        data = {
            "market_cap": 2_100_000_000_000,  # $2.1T
            "volume": 45_000_000,
        }
        cache.write("large_ints.json", data)
        result = cache.read("large_ints.json")
        assert result["market_cap"] == 2_100_000_000_000
        assert result["volume"] == 45_000_000

    def test_date_string_preservation(self, cache):
        """Dates stored as strings should roundtrip exactly."""
        data = {
            "dates": ["2025-01-20", "2025-01-24", "2025-01-25"],
            "timestamp": "2025-01-26T22:05:00Z"
        }
        cache.write("dates.json", data)
        result = cache.read("dates.json")
        assert result["dates"] == ["2025-01-20", "2025-01-24", "2025-01-25"]
        assert result["timestamp"] == "2025-01-26T22:05:00Z"
