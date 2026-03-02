"""Cache Manager for search results.

Provides persistent caching using DuckDB.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, List, Optional

import duckdb

logger = logging.getLogger(__name__)


class CacheManager:
    """Manage search result caching with DuckDB backend."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize cache manager.

        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory cache.
        """
        self.db_path = db_path or ":memory:"
        self._init_table()

    def _init_table(self):
        """Initialize cache table."""
        con = duckdb.connect(self.db_path)
        con.execute("""
            CREATE TABLE IF NOT EXISTS meta_cache (
                cache_key VARCHAR PRIMARY KEY,
                search_type VARCHAR,
                keywords VARCHAR,
                result TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        con.close()

    def get(self, search_type: str, keywords: List[str]) -> Optional[Any]:
        """Get cached result.

        Args:
            search_type: Type of search (e.g., 'mock_notes', 'als_filter')
            keywords: List of keywords

        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._hash(search_type, keywords)

        con = duckdb.connect(self.db_path)
        try:
            result = con.execute(
                """
                SELECT result FROM meta_cache
                WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
                """,
                [cache_key],
            ).fetchone()

            if result:
                logger.debug(f"Cache hit for {search_type}")
                return json.loads(result[0])
            else:
                logger.debug(f"Cache miss for {search_type}")
                return None
        finally:
            con.close()

    def set(
        self,
        search_type: str,
        keywords: List[str],
        result: Any,
        ttl_hours: int = 24,
    ):
        """Set cached result.

        Args:
            search_type: Type of search
            keywords: List of keywords
            result: Result to cache
            ttl_hours: Time to live in hours
        """
        cache_key = self._hash(search_type, keywords)
        keywords_json = json.dumps(sorted(keywords))
        result_json = json.dumps(result)

        now = datetime.now()
        expires_at = now + timedelta(hours=ttl_hours)

        con = duckdb.connect(self.db_path)
        try:
            con.execute(
                """
                INSERT OR REPLACE INTO meta_cache
                (cache_key, search_type, keywords, result, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [cache_key, search_type, keywords_json, result_json, now, expires_at],
            )
            logger.debug(f"Cached result for {search_type} (TTL: {ttl_hours}h)")
        finally:
            con.close()

    def clear_expired(self):
        """Remove expired cache entries."""
        con = duckdb.connect(self.db_path)
        try:
            con.execute(
                """
                DELETE FROM meta_cache
                WHERE expires_at <= CURRENT_TIMESTAMP
                """
            )
            logger.debug("Cleared expired cache entries")
        finally:
            con.close()

    def clear_all(self):
        """Remove all cache entries."""
        con = duckdb.connect(self.db_path)
        try:
            con.execute("DELETE FROM meta_cache")
            logger.debug("Cleared all cache entries")
        finally:
            con.close()

    def _hash(self, search_type: str, keywords: List[str]) -> str:
        """Generate cache key from search type and keywords.

        Args:
            search_type: Type of search
            keywords: List of keywords

        Returns:
            Hash string as cache key
        """
        key_string = f"{search_type}:{':'.join(sorted(keywords))}"
        return hashlib.sha256(key_string.encode()).hexdigest()
