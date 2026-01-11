"""Tests for the caching functionality in SQLiter."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import patch

from sqliter import SqliterDB
from sqliter.model import BaseDBModel


class User(BaseDBModel):
    """Test model for caching tests."""

    name: str
    age: int


class TestCacheDisabledByDefault:
    """Test that caching is disabled by default."""

    def test_cache_disabled_by_default(self, tmp_path) -> None:
        """Verify caching is off unless explicitly enabled."""
        db = SqliterDB(tmp_path / "test.db")
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Cache should be disabled by default
        assert not db._cache_enabled

        # Queries should not be cached
        assert db._cache == {}

        db.close()


class TestCacheHitOnRepeatedQuery:
    """Test cache hits on repeated queries."""

    def test_cache_hit_on_repeated_query(self, tmp_path) -> None:
        """Same query returns cached result."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # First query - hits DB
        result1 = db.select(User).filter(name="Alice").fetch_all()

        # Second query - hits cache
        result2 = db.select(User).filter(name="Alice").fetch_all()

        # Should return same cached object
        assert result1 is result2
        assert len(result1) == 1
        assert result1[0].name == "Alice"

        db.close()


class TestCacheInvalidation:
    """Test cache invalidation on write operations."""

    def test_cache_invalidation_on_insert(self, tmp_path) -> None:
        """Insert clears table cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Cache the query
        result1 = db.select(User).fetch_all()
        assert len(result1) == 1

        # Insert new record
        db.insert(User(name="Bob", age=25))

        # Cache should be invalidated, should hit DB
        result2 = db.select(User).fetch_all()
        assert len(result2) == 2

        db.close()

    def test_cache_invalidation_on_update(self, tmp_path) -> None:
        """Update clears table cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        user = db.insert(User(name="Alice", age=30))

        # Cache the query
        result1 = db.select(User).filter(name="Alice").fetch_all()
        assert len(result1) == 1

        # Update the record
        user.age = 31
        db.update(user)

        # Cache should be invalidated
        result2 = db.select(User).filter(name="Alice").fetch_all()
        assert result2[0].age == 31

        db.close()

    def test_cache_invalidation_on_delete_by_pk(self, tmp_path) -> None:
        """Delete by primary key clears table cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        user = db.insert(User(name="Alice", age=30))

        # Cache the query
        result1 = db.select(User).fetch_all()
        assert len(result1) == 1

        # Delete the record
        db.delete(User, str(user.pk))

        # Cache should be invalidated
        result2 = db.select(User).fetch_all()
        assert len(result2) == 0

        db.close()

    def test_cache_invalidation_on_delete_by_query(self, tmp_path) -> None:
        """Delete by query clears table cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))

        # Cache the query
        result1 = db.select(User).fetch_all()
        assert len(result1) == 2

        # Delete records by query
        deleted_count = db.select(User).filter(age__gte=30).delete()
        assert deleted_count == 1

        # Cache should be invalidated
        result2 = db.select(User).fetch_all()
        assert len(result2) == 1

        db.close()


class TestCacheClearedOnClose:
    """Test that cache is cleared when connection is closed."""

    def test_cache_cleared_on_close(self, tmp_path) -> None:
        """Cache cleared when connection closed."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query to populate cache
        db.select(User).fetch_all()
        assert len(db._cache) > 0

        # Close connection
        db.close()

        # Cache should be cleared
        assert len(db._cache) == 0

    def test_cache_context_manager(self, tmp_path) -> None:
        """Cache cleared when using context manager."""
        with SqliterDB(tmp_path / "test.db", cache_enabled=True) as db:
            db.create_table(User)
            db.insert(User(name="Alice", age=30))

            # Query to populate cache
            db.select(User).fetch_all()
            assert len(db._cache) > 0

        # Cache should be cleared after exiting context
        assert len(db._cache) == 0


class TestCacheTtlExpiration:
    """Test TTL-based cache expiration."""

    def test_cache_ttl_expiration(self, tmp_path) -> None:
        """Entries expire after TTL."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True, cache_ttl=1)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query to populate cache
        result1 = db.select(User).fetch_all()
        assert len(result1) == 1

        # Wait for TTL to expire
        time.sleep(2)

        # Query should hit DB again (cache expired)
        result2 = db.select(User).fetch_all()
        assert len(result2) == 1

        db.close()


class TestCacheMaxSizeLru:
    """Test LRU eviction when cache is full."""

    def test_cache_max_size_lru(self, tmp_path) -> None:
        """Oldest entries evicted when max size reached."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_size=2
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))
        db.insert(User(name="Charlie", age=35))

        # Fill cache with 3 different queries (max is 2)
        db.select(User).filter(name="Alice").fetch_all()
        db.select(User).filter(name="Bob").fetch_all()
        db.select(User).filter(name="Charlie").fetch_all()

        # Cache should only have 2 entries (LRU eviction)
        assert len(db._cache[User.get_table_name()]) == 2

        db.close()


class TestCacheKeyVariations:
    """Test that different query parameters create different cache keys."""

    def test_cache_key_includes_filters(self, tmp_path) -> None:
        """Different filters create different cache entries."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))

        # Different filters should create different cache entries
        result1 = db.select(User).filter(name="Alice").fetch_all()
        result2 = db.select(User).filter(name="Bob").fetch_all()

        assert len(result1) == 1
        assert len(result2) == 1
        assert result1[0].name == "Alice"
        assert result2[0].name == "Bob"

        # Should have 2 cache entries for the table
        assert len(db._cache[User.get_table_name()]) == 2

        db.close()

    def test_cache_key_includes_limit_offset(self, tmp_path) -> None:
        """Different pagination creates different cache entries."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))
        db.insert(User(name="Charlie", age=35))

        # Different pagination should create different cache entries
        result1 = db.select(User).limit(1).fetch_all()
        result2 = db.select(User).limit(1).offset(1).fetch_all()

        assert len(result1) == 1
        assert len(result2) == 1

        # Should have 2 cache entries for the table
        assert len(db._cache[User.get_table_name()]) == 2

        db.close()

    def test_cache_key_includes_order_by(self, tmp_path) -> None:
        """Different order by creates different cache entries."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))
        db.insert(User(name="Charlie", age=35))

        # Different order by should create different cache entries
        result1 = db.select(User).order("age").fetch_all()
        result2 = db.select(User).order("age", reverse=True).fetch_all()

        assert len(result1) == 3
        assert len(result2) == 3
        assert result1[0].age == 25  # Ascending
        assert result2[0].age == 35  # Descending

        # Should have 2 cache entries for the table
        assert len(db._cache[User.get_table_name()]) == 2

        db.close()


class TestCacheEmptyResults:
    """Test caching of empty results."""

    def test_cache_empty_single_result(self, tmp_path) -> None:
        """Empty single results are cached."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query that returns no results
        result1 = db.select(User).filter(name="Bob").fetch_one()
        assert result1 is None

        # Should return cached None
        result2 = db.select(User).filter(name="Bob").fetch_one()
        assert result2 is None

        # Should have 1 cache entry
        assert len(db._cache[User.get_table_name()]) == 1

        db.close()

    def test_cache_empty_list_result(self, tmp_path) -> None:
        """Empty list results are cached."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query that returns no results
        result1 = db.select(User).filter(name="Bob").fetch_all()
        assert result1 == []

        # Should return cached empty list
        result2 = db.select(User).filter(name="Bob").fetch_all()
        assert result2 == []

        # Should have 1 cache entry
        assert len(db._cache[User.get_table_name()]) == 1

        db.close()


class TestCacheWithFields:
    """Test caching with field selection."""

    def test_cache_with_field_selection(self, tmp_path) -> None:
        """Different field selections create different cache entries."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query with specific fields
        result1 = db.select(User).only("name").fetch_all()
        result2 = db.select(User).fetch_all()

        assert len(result1) == 1
        assert len(result2) == 1
        # Fields should be different
        assert hasattr(result1[0], "name")
        assert hasattr(result2[0], "age")

        # Should have 2 cache entries for the table
        assert len(db._cache[User.get_table_name()]) == 2

        db.close()


class TestCacheStatistics:
    """Test cache statistics tracking."""

    def test_cache_stats_initial_state(self, tmp_path) -> None:
        """Cache stats start at zero."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)

        stats = db.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total"] == 0
        assert stats["hit_rate"] == 0.0

        db.close()

    def test_cache_stats_track_hits(self, tmp_path) -> None:
        """Cache stats track hits correctly."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # First query - cache miss
        db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

        # Second query - cache hit
        db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0

        db.close()

    def test_cache_stats_track_misses(self, tmp_path) -> None:
        """Cache stats track misses correctly."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Three different queries - all misses
        db.select(User).filter(name="Alice").fetch_all()
        db.select(User).filter(name="Bob").fetch_all()
        db.select(User).filter(age=30).fetch_all()

        stats = db.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 3
        assert stats["hit_rate"] == 0.0

        db.close()

    def test_cache_stats_with_invalidation(self, tmp_path) -> None:
        """Cache stats continue after invalidation."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query - miss
        db.select(User).fetch_all()
        # Query - hit
        db.select(User).fetch_all()

        stats_before = db.get_cache_stats()
        assert stats_before["hits"] == 1

        # Invalidate cache
        db.insert(User(name="Bob", age=25))

        # Query - miss again (was invalidated)
        db.select(User).fetch_all()

        stats_after = db.get_cache_stats()
        assert stats_after["hits"] == 1
        assert stats_after["misses"] == 2

        db.close()

    def test_cache_stats_disabled_cache(self, tmp_path) -> None:
        """Cache stats don't increment when cache is disabled."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=False)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Queries with cache disabled
        db.select(User).fetch_all()
        db.select(User).fetch_all()

        stats = db.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total"] == 0

        db.close()

    def test_cache_stats_with_ttl_expiration(self, tmp_path) -> None:
        """Expired cache entries count as misses."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True, cache_ttl=1)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query - miss
        db.select(User).fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 1

        # Wait for TTL to expire
        time.sleep(2)

        # Query after expiration - should be a cache miss
        db.select(User).fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 0

        db.close()

    def test_cache_stats_hit_rate_calculation(self, tmp_path) -> None:
        """Hit rate is calculated correctly."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Execute 10 queries: 1 unique, 9 repeats
        for _ in range(10):
            db.select(User).filter(name="Alice").fetch_all()

        stats = db.get_cache_stats()
        assert stats["total"] == 10
        assert stats["hits"] == 9
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 90.0

        db.close()


class TestCacheMemoryLimit:
    """Test memory-based cache limiting."""

    def test_memory_limit_enforcement(self, tmp_path) -> None:
        """Cache enforces memory limit by evicting entries."""

        # Create a model with large fields to consume memory quickly
        class LargeData(BaseDBModel):
            name: str
            data: str

        # Set a very low memory limit (1MB)
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        )
        db.create_table(LargeData)

        # Insert data
        for i in range(20):
            db.insert(LargeData(name=f"User{i}", data=f"data{i}"))

        # Mock _estimate_size to return large values to trigger eviction
        call_count = [0]

        def mock_estimate_size(obj) -> int:
            # Return 200KB for each object to force eviction
            call_count[0] += 1
            return 200_000

        # Patch and cache queries - eviction loop should be triggered
        with patch.object(db, "_estimate_size", side_effect=mock_estimate_size):
            for i in range(20):
                db.select(LargeData).filter(name=f"User{i}").fetch_all()

        # The eviction loop should have been triggered
        # With 1MB limit and 200KB per entry, only ~4-5 entries should fit
        table_cache: Any = db._cache.get(LargeData.get_table_name(), {})
        assert len(table_cache) < 20  # Many entries were evicted
        assert len(table_cache) >= 0  # Cache exists

        db.close()

    def test_memory_usage_tracking(self, tmp_path) -> None:
        """Memory usage is tracked per table."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Initial memory usage should be 0
        assert db._cache_memory_usage.get(User.get_table_name(), 0) == 0

        # After caching, memory usage should be tracked
        db.select(User).filter(name="Alice").fetch_all()
        assert db._cache_memory_usage.get(User.get_table_name(), 0) > 0

        db.close()

    def test_memory_tracking_cleared_on_invalidation(
        self,
        tmp_path,
    ) -> None:
        """Memory tracking is cleared when cache is invalidated."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Cache a query
        db.select(User).filter(name="Alice").fetch_all()
        initial_memory = db._cache_memory_usage.get(User.get_table_name(), 0)
        assert initial_memory > 0

        # Invalidate cache (this should also clear memory tracking)
        db.insert(User(name="Bob", age=25))

        # Memory tracking should be cleared
        assert db._cache_memory_usage.get(User.get_table_name(), 0) == 0

        db.close()

    def test_memory_tracking_cleared_on_close(self, tmp_path) -> None:
        """Memory tracking is cleared when connection is closed."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Cache a query
        db.select(User).filter(name="Alice").fetch_all()
        assert db._cache_memory_usage.get(User.get_table_name(), 0) > 0

        # Close connection
        db.close()

        # Memory tracking should be cleared
        assert db._cache_memory_usage.get(User.get_table_name(), 0) == 0

    def test_memory_tracking_cleared_on_context_exit(self, tmp_path) -> None:
        """Memory tracking is cleared when exiting context manager."""
        with SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        ) as db:
            db.create_table(User)
            db.insert(User(name="Alice", age=30))

            # Cache a query
            db.select(User).filter(name="Alice").fetch_all()
            assert db._cache_memory_usage.get(User.get_table_name(), 0) > 0

        # After exiting context, memory tracking should be cleared
        assert db._cache_memory_usage.get(User.get_table_name(), 0) == 0

    def test_memory_limit_with_both_limits(self, tmp_path) -> None:
        """Both cache_max_size and cache_max_memory_mb are respected."""
        # Set both limits: 10 entries OR 1MB (whichever hit first)
        db = SqliterDB(
            tmp_path / "test.db",
            cache_enabled=True,
            cache_max_size=10,
            cache_max_memory_mb=1,
        )
        db.create_table(User)

        # Insert 20 users
        for i in range(20):
            db.insert(User(name=f"User{i}", age=20 + i))

        # Cache 15 different queries
        for i in range(15):
            db.select(User).filter(name=f"User{i}").fetch_all()

        # Cache should be limited by both size and memory
        # Actual count depends on object sizes and memory pressure
        assert len(db._cache[User.get_table_name()]) <= 10

        db.close()

    def test_no_memory_limit_when_none(self, tmp_path) -> None:
        """When cache_max_memory_mb is None, only size limit applies."""
        db = SqliterDB(
            tmp_path / "test.db",
            cache_enabled=True,
            cache_max_size=5,
            cache_max_memory_mb=None,
        )
        db.create_table(User)

        # Insert all users first
        for i in range(10):
            db.insert(User(name=f"User{i}", age=20 + i))

        # Now cache multiple queries (each query is different)
        for i in range(10):
            db.select(User).filter(name=f"User{i}").fetch_all()

        # Should respect cache_max_size only (5 entries max)
        assert len(db._cache[User.get_table_name()]) == 5
        # Memory tracking should still work
        assert db._cache_memory_usage.get(User.get_table_name(), 0) >= 0

        db.close()


class TestQueryLevelBypass:
    """Test query-level cache bypass controls."""

    def test_bypass_cache_skips_cache_read(self, tmp_path) -> None:
        """bypass_cache() skips reading from cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # First query - hits DB and caches
        result1 = db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 1

        # Second query - hits cache
        db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 1

        # Third query with bypass - skips cache, hits DB
        result3 = (
            db.select(User).filter(name="Alice").bypass_cache().fetch_all()
        )
        stats = db.get_cache_stats()
        # Bypass doesn't increment hits or misses
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        # Fourth query - should still hit cache (bypass was one-time)
        result4 = db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1

        # All results should have the same data
        assert len(result1) == 1
        assert result1[0].name == "Alice"
        assert result3 == result4

        db.close()

    def test_bypass_cache_skips_cache_write(self, tmp_path) -> None:
        """bypass_cache() doesn't write to cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query with bypass - doesn't cache result
        db.select(User).filter(name="Alice").bypass_cache().fetch_all()

        # Cache should be empty (no table key created)
        assert len(db._cache.get(User.get_table_name(), {})) == 0

        # Normal query after bypass - should miss (nothing was cached)
        db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 1

        db.close()

    def test_bypass_cache_with_filter_chain(self, tmp_path) -> None:
        """bypass_cache() works with method chaining."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Bypass cache with method chaining
        result = (
            db.select(User)
            .filter(name="Alice")
            .order("age")
            .bypass_cache()
            .fetch_one()
        )

        assert result is not None
        assert result.name == "Alice"
        # Cache should be empty (no table key created)
        assert len(db._cache.get(User.get_table_name(), {})) == 0

        db.close()

    def test_bypass_cache_with_empty_result(self, tmp_path) -> None:
        """bypass_cache() works with empty results."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query that returns no result, with bypass
        result = db.select(User).filter(name="Bob").bypass_cache().fetch_one()

        assert result is None
        # Cache should be empty (no table key created)
        assert len(db._cache.get(User.get_table_name(), {})) == 0

        db.close()


class TestQueryLevelTtl:
    """Test query-level TTL controls."""

    def test_query_ttl_overrides_global_ttl(self, tmp_path) -> None:
        """Query-level TTL overrides global cache_ttl."""
        # Global TTL of 10 seconds
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True, cache_ttl=10)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query with 1 second TTL
        db.select(User).filter(name="Alice").cache_ttl(1).fetch_all()

        # Wait 2 seconds
        time.sleep(2)

        # Query should miss (query-level TTL expired)
        db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 2  # Initial miss + expiration miss

        db.close()

    def test_query_ttl_longer_than_global(self, tmp_path) -> None:
        """Query-level TTL can be longer than global TTL."""
        # Global TTL of 1 second
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True, cache_ttl=1)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query with 10 second TTL
        db.select(User).filter(name="Alice").cache_ttl(10).fetch_all()

        # Wait 2 seconds
        time.sleep(2)

        # Query should hit (query-level TTL still valid)
        db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 1  # Cache hit after 2 seconds

        db.close()

    def test_query_ttl_without_global_ttl(self, tmp_path) -> None:
        """Query-level TTL works without global TTL."""
        # No global TTL
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query with 1 second TTL
        db.select(User).filter(name="Alice").cache_ttl(1).fetch_all()

        # Wait 2 seconds
        time.sleep(2)

        # Query should miss (query-level TTL expired)
        db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 2

        db.close()

    def test_query_ttl_with_method_chaining(self, tmp_path) -> None:
        """cache_ttl() works with method chaining."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query with TTL and method chaining
        result = (
            db.select(User)
            .filter(name="Alice")
            .order("age")
            .cache_ttl(60)
            .fetch_one()
        )

        assert result is not None
        assert result.name == "Alice"

        db.close()

    def test_query_ttl_different_for_different_queries(
        self,
        tmp_path,
    ) -> None:
        """Different queries can have different TTLs."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True, cache_ttl=100)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))

        # Query with 1 second TTL
        db.select(User).filter(name="Alice").cache_ttl(1).fetch_all()

        # Query with 5 second TTL
        db.select(User).filter(name="Bob").cache_ttl(5).fetch_all()

        # Both should be cached
        assert len(db._cache[User.get_table_name()]) == 2

        # Wait 2 seconds
        time.sleep(2)

        # Alice query should miss, Bob query should hit
        db.select(User).filter(name="Alice").fetch_all()
        db.select(User).filter(name="Bob").fetch_all()
        stats = db.get_cache_stats()
        # Alice: initial miss + expiration miss = 2 misses
        # Bob: initial miss + hit = 1 hit
        assert stats["misses"] >= 2  # At least Alice's misses
        assert stats["hits"] >= 1  # At least Bob's hit

        db.close()


class TestFetchModeCacheKey:
    """Test that fetch_one and fetch_all use different cache keys."""

    def test_fetch_one_and_fetch_all_use_different_cache_keys(
        self,
        tmp_path,
    ) -> None:
        """fetch_one() and fetch_all() should generate different cache keys."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))

        # First, fetch_all - populates cache
        all_users = db.select(User).fetch_all()
        assert len(all_users) == 2

        # Verify we have 1 cached entry (fetch_all result)
        assert len(db._cache[User.get_table_name()]) == 1

        # Now fetch_one - should NOT hit the cache (different key)
        # This would have incorrectly returned the cached list before the fix
        one_user = db.select(User).filter(name="Alice").fetch_one()
        assert one_user is not None
        assert one_user.name == "Alice"

        # Should now have 2 cached entries (fetch_all and fetch_one)
        assert len(db._cache[User.get_table_name()]) == 2

        # Fetch the same fetch_one query again - should hit cache
        cached_user = db.select(User).filter(name="Alice").fetch_one()
        assert cached_user is not None
        assert cached_user.name == "Alice"

        # Verify cache stats show proper hit/miss counts
        stats = db.get_cache_stats()
        # Initial queries: 1 fetch_all (miss) + 1 fetch_one (miss) = 2 misses
        # Followed by: 1 fetch_one (hit)
        assert stats["misses"] >= 2
        assert stats["hits"] >= 1

        db.close()


class TestEmptyResultCaching:
    """Test that empty results (None and []) are cached and retrieved correctly.

    This tests the fix for the bug where falsy values (None, []) were not
    being returned from cache due to truthiness-based cache hit detection.
    """

    def test_empty_result_from_fetch_one_is_cached(self, tmp_path) -> None:
        """None result from fetch_one() should be cached and retrieved."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query that returns no result (filter doesn't match)
        result1 = db.select(User).filter(name="NonExistent").fetch_one()
        assert result1 is None

        # Should have 1 cached entry (the None result)
        assert len(db._cache[User.get_table_name()]) == 1

        # Query again - should hit cache and return None
        result2 = db.select(User).filter(name="NonExistent").fetch_one()
        assert result2 is None

        # Verify cache stats show 1 miss and 1 hit
        stats = db.get_cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 1

        db.close()

    def test_empty_result_from_fetch_all_is_cached(self, tmp_path) -> None:
        """Empty list [] from fetch_all() should be cached and retrieved."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query that returns no results (filter doesn't match)
        result1 = db.select(User).filter(age__gt=100).fetch_all()
        assert result1 == []

        # Should have 1 cached entry (the empty list result)
        assert len(db._cache[User.get_table_name()]) == 1

        # Query again - should hit cache and return empty list
        result2 = db.select(User).filter(age__gt=100).fetch_all()
        assert result2 == []

        # Verify cache stats show 1 miss and 1 hit
        stats = db.get_cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 1

        db.close()
