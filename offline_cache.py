"""
Offline Cache System for ZEJZL.NET
Provides local caching capabilities for offline AI interactions
"""

import asyncio
import json
import logging
import sqlite3
import time
import hashlib
import gzip
import base64
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached response entry"""
    key: str
    content: str
    metadata: Dict[str, Any]
    created_at: float
    last_accessed: float
    access_count: int
    compressed: bool
    size_bytes: int
    ttl_seconds: Optional[int] = None

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl_seconds is None:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary"""
        return cls(**data)

class OfflineCache:
    """
    SQLite-based offline cache for AI responses and data
    Supports compression, TTL, and LRU eviction
    """

    def __init__(self, db_path: str = None, max_size_mb: int = 500, compression_threshold: int = 1024):
        """
        Initialize offline cache

        Args:
            db_path: Path to SQLite database file
            max_size_mb: Maximum cache size in MB
            compression_threshold: Minimum size for compression (bytes)
        """
        if db_path is None:
            # Default to user's home directory
            cache_dir = Path.home() / ".zejzl" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "offline_cache.db"

        self.db_path = Path(db_path)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.compression_threshold = compression_threshold

        # Thread pool for database operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cache")

        # Initialize database
        self._init_db()

        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compressions": 0,
            "total_requests": 0
        }

    def _init_db(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    compressed INTEGER DEFAULT 0,
                    size_bytes INTEGER NOT NULL,
                    ttl_seconds INTEGER
                )
            """)

            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_access_count ON cache_entries(access_count)")

            # Metadata table for cache statistics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            conn.commit()

    async def get(self, key: str, metadata_filter: Dict[str, Any] = None) -> Optional[str]:
        """
        Retrieve cached content by key

        Args:
            key: Cache key
            metadata_filter: Optional metadata filters

        Returns:
            Cached content or None if not found/expired
        """
        def _get():
            with sqlite3.connect(self.db_path) as conn:
                # Get entry
                cursor = conn.execute("""
                    SELECT content, metadata, compressed, ttl_seconds, created_at
                    FROM cache_entries WHERE key = ?
                """, (key,))

                row = cursor.fetchone()
                if not row:
                    self.stats["misses"] += 1
                    return None

                content_b64, metadata_json, compressed, ttl_seconds, created_at = row

                # Check TTL
                if ttl_seconds and time.time() - created_at > ttl_seconds:
                    # Remove expired entry
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                    conn.commit()
                    self.stats["misses"] += 1
                    return None

                # Parse metadata and check filters
                try:
                    metadata = json.loads(metadata_json)
                    if metadata_filter:
                        for filter_key, filter_value in metadata_filter.items():
                            if metadata.get(filter_key) != filter_value:
                                self.stats["misses"] += 1
                                return None
                except json.JSONDecodeError:
                    logger.warning(f"Invalid metadata JSON for key {key}")
                    self.stats["misses"] += 1
                    return None

                # Update access statistics
                conn.execute("""
                    UPDATE cache_entries
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE key = ?
                """, (time.time(), key))
                conn.commit()

                # Decompress if needed
                if compressed:
                    content_b64 = gzip.decompress(base64.b64decode(content_b64)).decode('utf-8')
                else:
                    content_b64 = base64.b64decode(content_b64).decode('utf-8')

                self.stats["hits"] += 1
                return content_b64

        self.stats["total_requests"] += 1
        return await asyncio.get_event_loop().run_in_executor(self.executor, _get)

    async def put(self, key: str, content: str, metadata: Dict[str, Any] = None,
                  ttl_seconds: int = None) -> bool:
        """
        Store content in cache

        Args:
            key: Cache key
            content: Content to cache
            metadata: Additional metadata
            ttl_seconds: Time to live in seconds

        Returns:
            True if stored successfully
        """
        def _put():
            try:
                # Compress if content is large enough
                original_content = content.encode('utf-8')
                should_compress = len(original_content) >= self.compression_threshold

                if should_compress:
                    compressed = gzip.compress(original_content)
                    content_b64 = base64.b64encode(compressed).decode('utf-8')
                    size_bytes = len(compressed)
                    self.stats["compressions"] += 1
                else:
                    content_b64 = base64.b64encode(original_content).decode('utf-8')
                    size_bytes = len(original_content)

                metadata_json = json.dumps(metadata or {})
                created_at = time.time()

                with sqlite3.connect(self.db_path) as conn:
                    # Check current cache size and evict if needed
                    self._evict_if_needed(conn, size_bytes)

                    # Insert or replace entry
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries
                        (key, content, metadata, created_at, last_accessed, compressed, size_bytes, ttl_seconds)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (key, content_b64, metadata_json, created_at, created_at,
                          1 if should_compress else 0, size_bytes, ttl_seconds))

                    conn.commit()
                    return True

            except Exception as e:
                logger.error(f"Failed to cache entry {key}: {e}")
                return False

        return await asyncio.get_event_loop().run_in_executor(self.executor, _put)

    def _evict_if_needed(self, conn: sqlite3.Connection, new_entry_size: int):
        """Evict old entries if cache is full (LRU strategy)"""
        # Check current size
        cursor = conn.execute("SELECT SUM(size_bytes) FROM cache_entries")
        current_size = cursor.fetchone()[0] or 0

        if current_size + new_entry_size <= self.max_size_bytes:
            return  # No eviction needed

        # Calculate how much to evict (aim for 80% of max size after eviction)
        target_size = int(self.max_size_bytes * 0.8)
        evict_size = current_size + new_entry_size - target_size

        if evict_size <= 0:
            return

        # Evict least recently used entries
        cursor = conn.execute("""
            SELECT key, size_bytes FROM cache_entries
            ORDER BY last_accessed ASC
        """)

        evicted_count = 0
        total_evicted_size = 0

        for row in cursor:
            key, size = row
            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            evicted_count += 1
            total_evicted_size += size
            self.stats["evictions"] += 1

            if total_evicted_size >= evict_size:
                break

        conn.commit()
        logger.info(f"Evicted {evicted_count} cache entries ({total_evicted_size} bytes)")

    async def delete(self, key: str) -> bool:
        """Delete cache entry by key"""
        def _delete():
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0

        return await asyncio.get_event_loop().run_in_executor(self.executor, _delete)

    async def clear(self) -> bool:
        """Clear all cache entries"""
        def _clear():
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache_entries")
                conn.commit()
                return True

        success = await asyncio.get_event_loop().run_in_executor(self.executor, _clear)
        if success:
            self.stats["evictions"] = 0  # Reset eviction count
        return success

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        def _get_stats():
            with sqlite3.connect(self.db_path) as conn:
                # Basic counts
                cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache_entries")
                count, total_size = cursor.fetchone()
                count = count or 0
                total_size = total_size or 0

                # Oldest and newest entries
                cursor = conn.execute("SELECT MIN(created_at), MAX(created_at) FROM cache_entries")
                oldest, newest = cursor.fetchone()

                # Compression stats
                cursor = conn.execute("SELECT COUNT(*) FROM cache_entries WHERE compressed = 1")
                compressed_count = cursor.fetchone()[0] or 0

                return {
                    "total_entries": count,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "max_size_mb": round(self.max_size_bytes / (1024 * 1024), 2),
                    "usage_percent": round((total_size / self.max_size_bytes) * 100, 1) if self.max_size_bytes > 0 else 0,
                    "compressed_entries": compressed_count,
                    "compression_ratio": round(compressed_count / count * 100, 1) if count > 0 else 0,
                    "oldest_entry": oldest,
                    "newest_entry": newest,
                    "cache_stats": self.stats.copy()
                }

        return await asyncio.get_event_loop().run_in_executor(self.executor, _get_stats)

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries"""
        def _cleanup():
            current_time = time.time()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM cache_entries
                    WHERE ttl_seconds IS NOT NULL
                    AND (? - created_at) > ttl_seconds
                """, (current_time,))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count

        return await asyncio.get_event_loop().run_in_executor(self.executor, _cleanup)

    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a consistent cache key from arguments"""
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())
        key_components = list(args) + [f"{k}:{v}" for k, v in sorted_kwargs]

        # Create hash of the components
        key_string = "|".join(str(component) for component in key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    async def warm_cache(self, queries: List[Tuple[str, Dict[str, Any]]]) -> int:
        """
        Warm cache with frequently used queries

        Args:
            queries: List of (query_text, metadata) tuples

        Returns:
            Number of queries cached
        """
        cached_count = 0

        for query_text, metadata in queries:
            # Try to get response for this query (this would normally hit the AI)
            # For now, we'll just mark it as cached if it doesn't exist
            cache_key = self.generate_cache_key("query", query_text=query_text)

            existing = await self.get(cache_key)
            if not existing:
                # In a real implementation, you'd execute the query here
                # For now, we'll just create a placeholder
                placeholder_response = f"[CACHED] Response for: {query_text}"
                await self.put(cache_key, placeholder_response, metadata, ttl_seconds=3600)  # 1 hour TTL
                cached_count += 1

        return cached_count

    async def close(self):
        """Clean shutdown"""
        self.executor.shutdown(wait=True)