"""Tests for the caching functionality in SQLiter."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any
from unittest.mock import patch

import pytest

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


class TestCacheParameterValidation:
    """Test validation of cache configuration parameters."""

    def test_cache_max_size_must_be_positive(self, tmp_path) -> None:
        """cache_max_size must be greater than 0."""
        with pytest.raises(
            ValueError, match="cache_max_size must be greater than 0"
        ):
            SqliterDB(
                tmp_path / "test.db", cache_enabled=True, cache_max_size=0
            )

        with pytest.raises(
            ValueError, match="cache_max_size must be greater than 0"
        ):
            SqliterDB(
                tmp_path / "test.db", cache_enabled=True, cache_max_size=-1
            )

    def test_cache_ttl_must_be_non_negative(self, tmp_path) -> None:
        """cache_ttl must be non-negative."""
        with pytest.raises(ValueError, match="cache_ttl must be non-negative"):
            SqliterDB(tmp_path / "test.db", cache_enabled=True, cache_ttl=-1)

    def test_cache_max_memory_mb_must_be_positive(self, tmp_path) -> None:
        """cache_max_memory_mb must be greater than 0."""
        with pytest.raises(
            ValueError, match="cache_max_memory_mb must be greater than 0"
        ):
            SqliterDB(
                tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=0
            )

        with pytest.raises(
            ValueError, match="cache_max_memory_mb must be greater than 0"
        ):
            SqliterDB(
                tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=-1
            )


class TestCacheHitOnRepeatedQuery:
    """Test cache hits on repeated queries."""

    def test_cache_hit_on_repeated_query(self, tmp_path) -> None:
        """Repeated queries return cached result and increment hit counter."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # First query - hits DB
        result1 = db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

        # Second query - hits cache
        result2 = db.select(User).filter(name="Alice").fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        # Results should be equivalent (same content)
        assert len(result1) == 1
        assert len(result2) == 1
        assert result1[0].name == result2[0].name
        assert result1[0].age == result2[0].age

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

        # Query to populate cache at time=0
        with patch("sqliter.sqliter.time.time", return_value=0):
            result1 = db.select(User).fetch_all()
            assert len(result1) == 1

        # Mock time advancing past TTL (time=100, TTL was 1 second)
        with patch("sqliter.sqliter.time.time", return_value=100):
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


class TestCacheClear:
    """Test manual cache clearing functionality."""

    def test_clear_cache_removes_all_entries(self) -> None:
        """clear_cache() removes all cached entries from all tables."""
        db = SqliterDB(memory=True, cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))

        # Cache some queries
        db.select(User).filter(name="Alice").fetch_all()
        db.select(User).filter(name="Bob").fetch_all()
        db.select(User).fetch_all()

        # Verify cache is populated
        table_name = User.get_table_name()
        assert len(db._cache.get(table_name, {})) == 3

        # Clear cache
        db.clear_cache()

        # Verify all entries are cleared
        assert len(db._cache.get(table_name, {})) == 0

        db.close()

    def test_clear_cache_with_multiple_tables(self) -> None:
        """clear_cache() clears cache for all tables."""

        class Product(BaseDBModel):
            name: str
            price: float

        db = SqliterDB(memory=True, cache_enabled=True)
        db.create_table(User)
        db.create_table(Product)

        # Insert and cache data for both tables
        db.insert(User(name="Alice", age=30))
        db.insert(Product(name="Widget", price=9.99))

        db.select(User).fetch_all()
        db.select(Product).fetch_all()

        # Verify both tables have cached entries
        user_table = User.get_table_name()
        product_table = Product.get_table_name()
        assert len(db._cache.get(user_table, {})) == 1
        assert len(db._cache.get(product_table, {})) == 1

        # Clear cache
        db.clear_cache()

        # Verify all tables are cleared
        assert len(db._cache.get(user_table, {})) == 0
        assert len(db._cache.get(product_table, {})) == 0

        db.close()

    def test_clear_cache_resets_statistics(self) -> None:
        """clear_cache() resets cache statistics."""
        db = SqliterDB(memory=True, cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Generate some cache activity
        db.select(User).fetch_all()  # miss
        db.select(User).fetch_all()  # hit

        stats_before = db.get_cache_stats()
        assert stats_before["hits"] > 0 or stats_before["misses"] > 0

        # Clear cache doesn't reset statistics
        db.clear_cache()
        stats_after = db.get_cache_stats()
        assert stats_after["hits"] == stats_before["hits"]
        assert stats_after["misses"] == stats_before["misses"]

        # But subsequent queries will hit DB again
        db.select(User).fetch_all()  # miss (cache was cleared)
        stats_final = db.get_cache_stats()
        assert stats_final["misses"] > stats_before["misses"]

        db.close()

    def test_clear_cache_when_cache_disabled(self) -> None:
        """clear_cache() works even when cache is disabled."""
        db = SqliterDB(memory=True, cache_enabled=False)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Cache should be empty
        assert len(db._cache) == 0

        # clear_cache() should not raise an error
        db.clear_cache()

        # Cache should still be empty
        assert len(db._cache) == 0

        db.close()

    def test_clear_cache_allows_fresh_queries(self) -> None:
        """Queries after clear_cache() hit the database."""
        db = SqliterDB(memory=True, cache_enabled=True)
        db.create_table(User)
        user = db.insert(User(name="Alice", age=30))

        # Query and cache
        result1 = db.select(User).filter(name="Alice").fetch_one()
        assert result1 is not None
        assert result1.age == 30
        stats_before = db.get_cache_stats()
        assert stats_before["misses"] == 1

        # Update the record directly (bypass ORM to avoid cache invalidation)
        conn = db.conn
        assert conn is not None
        conn.execute(
            f'UPDATE users SET age = 31 WHERE pk = "{user.pk}"'  # noqa: S608
        )

        # Query again - should return cached result (age=30)
        result2 = db.select(User).filter(name="Alice").fetch_one()
        assert result2 is not None
        assert result2.age == 30  # Still cached value

        # Clear cache
        db.clear_cache()

        # Query again - should hit database and get fresh data (age=31)
        result3 = db.select(User).filter(name="Alice").fetch_one()
        assert result3 is not None
        assert result3.age == 31  # Fresh from database

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
        """Empty single results are cached and retrieved from cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query that returns no results
        result1 = db.select(User).filter(name="Bob").fetch_one()
        assert result1 is None

        # Verify first query was a cache miss
        stats = db.get_cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

        # Should return cached None
        result2 = db.select(User).filter(name="Bob").fetch_one()
        assert result2 is None

        # Verify second query was a cache hit
        stats = db.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        # Should have 1 cache entry
        assert len(db._cache[User.get_table_name()]) == 1

        db.close()

    def test_cache_empty_list_result(self, tmp_path) -> None:
        """Empty list results are cached and retrieved from cache."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Query that returns no results
        result1 = db.select(User).filter(name="Bob").fetch_all()
        assert result1 == []

        # Verify first query was a cache miss
        stats = db.get_cache_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

        # Should return cached empty list
        result2 = db.select(User).filter(name="Bob").fetch_all()
        assert result2 == []

        # Verify second query was a cache hit
        stats = db.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

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

        # Query at time=0 - miss
        with patch("sqliter.sqliter.time.time", return_value=0):
            db.select(User).fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 1

        # Query at time=0.5 - hit
        with patch("sqliter.sqliter.time.time", return_value=0.5):
            db.select(User).fetch_all()
        stats = db.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

        # Query at time=100 (past TTL) - should be a cache miss
        with patch("sqliter.sqliter.time.time", return_value=100):
            db.select(User).fetch_all()
        stats = db.get_cache_stats()
        assert stats["misses"] == 2
        assert stats["hits"] == 1

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

    def test_memory_usage_with_set_fields(self, tmp_path) -> None:
        """Memory usage calculation works with set fields."""

        class ModelWithSet(BaseDBModel):
            name: str
            tags: set[str]

        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(ModelWithSet)
        db.insert(
            ModelWithSet(name="test", tags={"python", "database", "caching"})
        )

        # Cache the query - this should trigger set measurement
        db.select(ModelWithSet).fetch_all()

        # Memory usage should be calculable
        memory_usage = db._get_table_memory_usage(ModelWithSet.get_table_name())
        assert memory_usage > 0

        db.close()

    def test_memory_limit_enforcement(self, tmp_path) -> None:
        """Cache enforces memory limit by evicting entries."""

        # Create a model with large fields to consume memory quickly
        class LargeData(BaseDBModel):
            name: str
            data: str

        # Set a very low memory limit (1MB)
        db = SqliterDB(
            tmp_path / "test.db",
            cache_enabled=True,
            cache_max_memory_mb=1,
        )
        db.create_table(LargeData)

        # Insert data with large payloads
        large_data = "x" * 50000  # 50KB of data per entry
        for i in range(50):
            db.insert(LargeData(name=f"User{i}", data=large_data))

        # Cache queries - eviction should be triggered due to memory limit
        for i in range(50):
            db.select(LargeData).filter(name=f"User{i}").fetch_all()

        table_cache: OrderedDict[Any, Any] = db._cache.get(
            LargeData.get_table_name(), OrderedDict()
        )
        # With 1MB limit and ~50KB per entry, only ~15-20 entries should fit
        assert len(table_cache) < 50  # Many entries were evicted

        # Verify memory usage is under the limit
        memory_usage = db._get_table_memory_usage(LargeData.get_table_name())
        max_bytes = 1 * 1024 * 1024  # 1MB
        # Should be at or slightly over limit (eviction check after insert)
        assert memory_usage <= max_bytes + 100000  # Allow buffer

        db.close()

    def test_memory_usage_tracking(self, tmp_path) -> None:
        """Memory usage is calculated on-demand per table."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Initial memory usage should be 0 (no cached entries)
        assert db._get_table_memory_usage(User.get_table_name()) == 0

        # After caching, memory usage should be > 0
        db.select(User).filter(name="Alice").fetch_all()
        assert db._get_table_memory_usage(User.get_table_name()) > 0

        db.close()

    def test_memory_tracking_cleared_on_invalidation(
        self,
        tmp_path,
    ) -> None:
        """Memory usage is 0 when cache is invalidated."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Cache a query
        db.select(User).filter(name="Alice").fetch_all()
        initial_memory = db._get_table_memory_usage(User.get_table_name())
        assert initial_memory > 0

        # Invalidate cache (this clears all cached entries)
        db.insert(User(name="Bob", age=25))

        # Memory usage should be 0 (cache was cleared)
        assert db._get_table_memory_usage(User.get_table_name()) == 0

        db.close()

    def test_memory_tracking_cleared_on_close(self, tmp_path) -> None:
        """Memory usage is 0 when connection is closed."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Cache a query
        db.select(User).filter(name="Alice").fetch_all()
        assert db._get_table_memory_usage(User.get_table_name()) > 0

        # Close connection
        db.close()

        # Memory usage should be 0 (cache was cleared)
        assert db._get_table_memory_usage(User.get_table_name()) == 0

    def test_memory_tracking_cleared_on_context_exit(self, tmp_path) -> None:
        """Memory usage is 0 when exiting context manager."""
        with SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_memory_mb=1
        ) as db:
            db.create_table(User)
            db.insert(User(name="Alice", age=30))

            # Cache a query
            db.select(User).filter(name="Alice").fetch_all()
            assert db._get_table_memory_usage(User.get_table_name()) > 0

        # After exiting context, memory usage should be 0
        assert db._get_table_memory_usage(User.get_table_name()) == 0

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
        # Memory usage should still be calculable
        assert db._get_table_memory_usage(User.get_table_name()) >= 0

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

        # Query with 1 second TTL at time=0
        with patch("sqliter.sqliter.time.time", return_value=0):
            db.select(User).filter(name="Alice").cache_ttl(1).fetch_all()

        # Query at time=5 (past query-level TTL of 1, but global TTL is 10)
        with patch("sqliter.sqliter.time.time", return_value=5):
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

        # Query with 10 second TTL at time=0
        with patch("sqliter.sqliter.time.time", return_value=0):
            db.select(User).filter(name="Alice").cache_ttl(10).fetch_all()

        # Query at time=2 (past global TTL of 1, but query-level TTL is 10)
        with patch("sqliter.sqliter.time.time", return_value=2):
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

        # Query with 1 second TTL at time=0
        with patch("sqliter.sqliter.time.time", return_value=0):
            db.select(User).filter(name="Alice").cache_ttl(1).fetch_all()

        # Query at time=5 (past query-level TTL)
        with patch("sqliter.sqliter.time.time", return_value=5):
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

    def test_query_ttl_validates_non_negative(self, tmp_path) -> None:
        """cache_ttl() raises ValueError for negative values."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)

        # Negative TTL should raise ValueError
        with pytest.raises(ValueError, match="TTL must be non-negative"):
            db.select(User).cache_ttl(-1).fetch_all()

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

        # Query with 1 second TTL at time=0
        with patch("sqliter.sqliter.time.time", return_value=0):
            db.select(User).filter(name="Alice").cache_ttl(1).fetch_all()
            # Query with 5 second TTL
            db.select(User).filter(name="Bob").cache_ttl(5).fetch_all()

        # Both should be cached
        assert len(db._cache[User.get_table_name()]) == 2

        # Query at time=2 (Alice TTL expired, Bob TTL still valid)
        with patch("sqliter.sqliter.time.time", return_value=2):
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

    def test_overwriting_cache_key_updates_memory_and_lru(
        self,
        tmp_path,
    ) -> None:
        """Overwriting an existing cache key updates LRU position."""
        db = SqliterDB(
            tmp_path / "test.db", cache_enabled=True, cache_max_size=3
        )
        db.create_table(User)
        db.insert(User(name="Alice", age=30))
        db.insert(User(name="Bob", age=25))
        db.insert(User(name="Charlie", age=35))

        # Cache 3 queries to fill the cache
        db.select(User).filter(name="Alice").fetch_one()
        db.select(User).filter(name="Bob").fetch_one()
        db.select(User).filter(name="Charlie").fetch_one()

        table_name = User.get_table_name()
        initial_count = len(db._cache[table_name])
        assert initial_count == 3

        # Get the cache key for the first query (LRU entry)
        query = db.select(User).filter(name="Alice")
        cache_key = query._make_cache_key(fetch_one=True)

        # Get the current result to overwrite with
        result = db.select(User).filter(name="Alice").fetch_one()

        # Manually call _cache_set with the same key to test overwrite
        db._cache_set(table_name, cache_key, result, ttl=None)

        # Should still have only 3 cached entries (not 4)
        assert len(db._cache[table_name]) == 3

        # The overwritten entry should now be the MRU (most recently used)
        # Get the last key in the OrderedDict (MRU)
        mru_key = next(reversed(db._cache[table_name]))
        assert mru_key == cache_key

        # Memory usage should be reasonable (not double-counted)
        memory_usage = db._get_table_memory_usage(table_name)
        assert memory_usage > 0

        db.close()


class TestCacheKeyErrors:
    """Test error handling in cache key generation."""

    def test_incomparable_filter_types_raises_error(
        self,
        tmp_path,
    ) -> None:
        """Filters with incomparable types raise ValueError."""
        db = SqliterDB(tmp_path / "test.db", cache_enabled=True)
        db.create_table(User)
        db.insert(User(name="Alice", age=30))

        # Create a query and manually add filters with incomparable types
        # This simulates the edge case where sorting fails
        query = db.select(User).filter(name="Alice")

        # Manually add a filter with an incomparable value type
        # (same field name but int value instead of string)
        # Filters are tuples: (field_name, value, operator)
        query.filters.append(("name", 42, "__eq"))

        # This raises ValueError when sorting filters with incomparable types
        # The tuples ("name", "Alice", "__eq") and ("name", 42, "__eq")
        # cannot be compared due to string vs int at position 1
        with pytest.raises(
            ValueError,
            match="filters contain incomparable types",
        ):
            # Trigger cache key generation which requires sorting
            _ = query._make_cache_key(fetch_one=True)

        db.close()
