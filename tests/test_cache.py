"""Tests for the caching functionality in SQLiter."""

from __future__ import annotations

import time

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
