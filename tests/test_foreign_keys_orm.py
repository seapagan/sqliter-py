"""Test suite for Phase 2 ORM functionality.

Tests lazy loading, reverse relationships, and automatic setup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest

from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey, ModelRegistry
from sqliter.orm.fields import LazyLoader
from sqliter.orm.query import ReverseRelationship


@pytest.fixture
def db() -> SqliterDB:
    """Create a clean in-memory database for testing."""
    return SqliterDB(":memory:")


class Author(BaseDBModel):
    """Test model for an author."""

    name: str
    email: str


class Book(BaseDBModel):
    """Test model for a book with FK to author."""

    title: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")


class Publisher(BaseDBModel):
    """Test model for a publisher."""

    name: str


class Magazine(BaseDBModel):
    """Test model for a magazine with nullable FK."""

    title: str
    publisher: ForeignKey[Publisher] = ForeignKey(
        Publisher, on_delete="SET NULL", null=True
    )


class TestLazyLoading:
    """Test suite for lazy loading of foreign key relationships."""

    def test_lazy_load_single_object(self, db: SqliterDB) -> None:
        """Test lazy loading a related object."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="John", email="john@example.com"))
        book = db.insert(Book(title="My Book", author=author))

        # Access the FK field - should trigger lazy load
        assert book.author.name == "John"
        assert book.author.email == "john@example.com"

    def test_lazy_load_caching(self, db: SqliterDB) -> None:
        """Test that lazy loading caches the result."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Jane", email="jane@example.com"))
        book = db.insert(Book(title="Jane's Book", author=author))

        # First access triggers lazy load
        author1 = book.author
        # Second access should return cached object
        author2 = book.author

        assert author1 is author2
        assert author1.name == "Jane"

    def test_lazy_load_null_fk(self, db: SqliterDB) -> None:
        """Test lazy loading with null FK."""
        db.create_table(Publisher)
        db.create_table(Magazine)

        magazine = db.insert(Magazine(title="No Publisher", publisher=None))

        # Should return None for null FK
        assert magazine.publisher is None

    def test_lazy_load_with_id(self, db: SqliterDB) -> None:
        """Test creating object with ID instead of model instance."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Bob", email="bob@example.com"))
        book = db.insert(Book(title="Bob's Book", author=author.pk))

        # Should work with ID as well
        assert book.author.name == "Bob"

    def test_lazy_load_not_found(self, db: SqliterDB) -> None:
        """Test lazy loading when related object doesn't exist.

        With proper FK constraints, orphan records can't be created normally.
        This test verifies LazyLoader behavior when db.get returns None
        (simulating a missing record scenario like database corruption or
        race conditions).
        """
        db.create_table(Author)
        db.create_table(Book)

        # Create a valid author and book
        author = db.insert(Author(name="Test", email="test@example.com"))
        book = db.insert(Book(title="Orphan Book", author=author))

        # Simulate the author being missing by patching db.get to return None
        original_get = db.get

        def mock_get(model_class: type, pk: int) -> object:
            if model_class == Author:
                return None
            return original_get(model_class, pk)

        db.get = mock_get  # type: ignore[assignment]

        # Clear any cached loader
        if hasattr(book, "_fk_cache"):
            book._fk_cache.clear()

        # Accessing the author should raise AttributeError because
        # the LazyLoader returns None for the loaded object
        with pytest.raises(AttributeError):
            _ = book.author.name


class TestReverseRelationships:
    """Test suite for reverse relationships."""

    def test_reverse_relationship_fetch_all(self, db: SqliterDB) -> None:
        """Test fetching all related objects via reverse relationship."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Alice", email="alice@example.com"))
        db.insert(Book(title="Book 1", author=author))
        db.insert(Book(title="Book 2", author=author))

        # Fetch books via reverse relationship
        books = author.books.fetch_all()
        assert len(books) == 2
        assert {b.title for b in books} == {"Book 1", "Book 2"}

    def test_reverse_relationship_filter(self, db: SqliterDB) -> None:
        """Test filtering reverse relationship."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Charlie", email="charlie@example.com"))
        db.insert(Book(title="Book A", author=author))
        db.insert(Book(title="Book B", author=author))
        db.insert(Book(title="Book C", author=author))

        # Filter books by title
        books = author.books.filter(title__like="Book A%").fetch_all()
        assert len(books) == 1
        assert books[0].title == "Book A"

    def test_reverse_relationship_count(self, db: SqliterDB) -> None:
        """Test counting related objects."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Dave", email="dave@example.com"))
        db.insert(Book(title="Book 1", author=author))
        db.insert(Book(title="Book 2", author=author))
        db.insert(Book(title="Book 3", author=author))

        # Count books
        count = author.books.count()
        assert count == 3

    def test_reverse_relationship_exists(self, db: SqliterDB) -> None:
        """Test exists on reverse relationship."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Eve", email="eve@example.com"))
        assert not author.books.exists()

        db.insert(Book(title="Book 1", author=author))
        assert author.books.exists()

    def test_reverse_relationship_empty(self, db: SqliterDB) -> None:
        """Test reverse relationship with no related objects."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Frank", email="frank@example.com"))
        books = author.books.fetch_all()
        assert books == []

    def test_reverse_relationship_limit_offset(self, db: SqliterDB) -> None:
        """Test limit and offset on reverse relationship."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Grace", email="grace@example.com"))
        db.insert(Book(title="Book 1", author=author))
        db.insert(Book(title="Book 2", author=author))
        db.insert(Book(title="Book 3", author=author))
        db.insert(Book(title="Book 4", author=author))

        # Limit
        books = author.books.limit(2).fetch_all()
        assert len(books) == 2

        # Offset
        books = author.books.limit(2).offset(1).fetch_all()
        assert len(books) == 2

    def test_reverse_relationship_with_custom_related_name(
        self, db: SqliterDB
    ) -> None:
        """Test reverse relationship with custom related_name."""

        class Author(BaseDBModel):
            name: str

        class Book(BaseDBModel):
            title: str
            author: ForeignKey[Author] = ForeignKey(
                Author, on_delete="CASCADE", related_name="publications"
            )

        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Henry"))
        db.insert(Book(title="Book 1", author=author))
        db.insert(Book(title="Book 2", author=author))

        # Use custom related name
        books = author.publications.fetch_all()
        assert len(books) == 2


class TestModelRegistry:
    """Test suite for ModelRegistry."""

    def test_register_model(self) -> None:
        """Test registering models in the registry."""

        class TestModel(BaseDBModel):
            name: str

        table_name = TestModel.__name__.lower()
        assert ModelRegistry.get_model(table_name) is TestModel

    def test_register_foreign_key(self) -> None:
        """Test registering FK relationships."""
        # The FK should be registered during class creation
        assert Book.__name__.lower() in ModelRegistry._foreign_keys

    def test_get_foreign_keys(self) -> None:
        """Test getting FK relationships for a model."""
        fks = ModelRegistry.get_foreign_keys(Book.__name__.lower())
        assert len(fks) > 0
        assert fks[0]["to_model"] is Author

    def test_pending_reverse_relationships(self) -> None:
        """Test pending reverse relationships for forward references."""

        # Define Book first (Author doesn't exist yet)
        class _ForwardRefBook(BaseDBModel):
            title: str

        # Now define Author - pending relationship should be processed
        class _ForwardRefAuthor(BaseDBModel):
            name: str

        # The pending relationship should have been processed
        # (This is a basic test - the actual forward reference handling
        # would need more complex setup)


class TestDbContext:
    """Test suite for db_context functionality."""

    def test_db_context_set_on_insert(self, db: SqliterDB) -> None:
        """Test that db_context is set on insert."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Ian", email="ian@example.com"))
        assert author.db_context is db

    def test_db_context_set_on_get(self, db: SqliterDB) -> None:
        """Test that db_context is set on get."""
        db.create_table(Author)

        author1 = db.insert(Author(name="Jane", email="jane@example.com"))
        author2 = db.get(Author, author1.pk)
        assert author2
        assert author2.db_context is db

    def test_db_context_set_on_select(self, db: SqliterDB) -> None:
        """Test that db_context is set on select."""
        db.create_table(Author)

        db.insert(Author(name="Kate", email="kate@example.com"))
        db.insert(Author(name="Leo", email="leo@example.com"))

        authors = db.select(Author).fetch_all()
        assert all(author.db_context is db for author in authors)

    def test_db_context_for_lazy_loading(self, db: SqliterDB) -> None:
        """Test that db_context enables lazy loading."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Mike", email="mike@example.com"))
        book = db.insert(Book(title="Mike's Book", author=author))

        # db_context should enable lazy loading
        assert book.author.db_context is db


class TestCascadeDelete:
    """Test suite for cascade delete with ORM."""

    def test_cascade_delete_with_cached_objects(self, db: SqliterDB) -> None:
        """Test that cascade delete works with cached lazy-loaded objects."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Nina", email="nina@example.com"))
        book = db.insert(Book(title="Nina's Book", author=author))

        # Cache the author via lazy loading
        _ = book.author.name

        # Delete the author - should cascade delete the book
        db.delete(Author, author.pk)

        # Book should be deleted
        assert db.get(Book, book.pk) is None

    def test_cascade_delete_with_reverse_relationships(
        self, db: SqliterDB
    ) -> None:
        """Test that cascade delete updates reverse relationships."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Oliver", email="oliver@example.com"))
        db.insert(Book(title="Book 1", author=author))
        db.insert(Book(title="Book 2", author=author))

        # Get books via reverse relationship
        books = author.books.fetch_all()
        assert len(books) == 2

        # Delete author - should cascade delete books
        db.delete(Author, author.pk)

        # Books should be deleted
        assert db.select(Book).fetch_all() == []


class TestNestedLazyLoading:
    """Test suite for nested lazy loading."""

    def test_nested_lazy_loading(self, db: SqliterDB) -> None:
        """Test lazy loading through multiple levels."""

        class Country(BaseDBModel):
            name: str

        class City(BaseDBModel):
            name: str
            country: ForeignKey[Country] = ForeignKey(
                Country, on_delete="CASCADE"
            )

        class Person(BaseDBModel):
            name: str
            city: ForeignKey[City] = ForeignKey(City, on_delete="CASCADE")

        db.create_table(Country)
        db.create_table(City)
        db.create_table(Person)

        country = db.insert(Country(name="USA"))
        city = db.insert(City(name="New York", country=country))
        person = db.insert(Person(name="John", city=city))

        # Nested lazy loading
        assert person.city.country.name == "USA"


class TestLazyLoaderMethods:
    """Test suite for LazyLoader special methods."""

    def test_repr_unloaded(self, db: SqliterDB) -> None:
        """Test LazyLoader repr before loading."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Test", email="test@example.com"))
        book = db.insert(Book(title="Test Book", author=author))

        # Clear cache to get fresh LazyLoader
        if hasattr(book, "_fk_cache"):
            book._fk_cache.clear()

        # Get the LazyLoader without triggering load
        lazy = book.__dict__.get("_fk_cache", {}).get("author")
        if lazy is None:
            # Access to create the LazyLoader but check repr before load
            # Cast author_id since __getattribute__ returns object
            fk_id: int | None = book.author_id  # type: ignore[assignment]
            lazy = LazyLoader(
                instance=book,
                to_model=Author,
                fk_id=fk_id,
                db_context=db,
            )

        repr_str = repr(lazy)
        assert "LazyLoader" in repr_str
        assert "unloaded" in repr_str
        assert "Author" in repr_str

    def test_repr_loaded(self, db: SqliterDB) -> None:
        """Test LazyLoader repr after loading."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(
            Author(name="LoadedTest", email="loaded@example.com")
        )
        book = db.insert(Book(title="Loaded Book", author=author))

        # Access to trigger load
        _ = book.author.name

        # Get the cached LazyLoader
        lazy = book._fk_cache.get("author")
        assert lazy is not None

        repr_str = repr(lazy)
        assert "LazyLoader" in repr_str
        assert "loaded" in repr_str

    def test_equality_with_loaded_object(self, db: SqliterDB) -> None:
        """Test LazyLoader equality with loaded object."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="EqTest", email="eq@example.com"))
        book = db.insert(Book(title="Eq Book", author=author))

        # Get the LazyLoader
        lazy = book.author

        # Compare with the actual author
        assert lazy == author

    def test_equality_with_none_when_null(self, db: SqliterDB) -> None:
        """Test LazyLoader equality when FK is null returns None."""
        db.create_table(Publisher)
        db.create_table(Magazine)

        magazine = db.insert(Magazine(title="No Pub", publisher=None))

        # Create a LazyLoader with null FK ID and compare to None
        lazy = LazyLoader(
            instance=magazine,
            to_model=Publisher,
            fk_id=None,  # Null FK
            db_context=db,
        )

        # This triggers _load() which sets _cached = None, then returns True
        assert lazy == None  # noqa: E711

    def test_equality_different_objects(self, db: SqliterDB) -> None:
        """Test LazyLoader equality with different objects."""
        db.create_table(Author)
        db.create_table(Book)

        author1 = db.insert(Author(name="Author1", email="a1@example.com"))
        author2 = db.insert(Author(name="Author2", email="a2@example.com"))
        book = db.insert(Book(title="Book1", author=author1))

        # LazyLoader should not equal a different author
        assert book.author != author2

    def test_hash(self, db: SqliterDB) -> None:
        """Test LazyLoader can be hashed."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="HashTest", email="hash@example.com"))
        book = db.insert(Book(title="Hash Book", author=author))

        # Get the LazyLoader
        lazy = book.author

        # Should be hashable
        h = hash(lazy)
        assert isinstance(h, int)

        # Can be used in a set
        s = {lazy}
        assert len(s) == 1

    def test_db_error_handling(self, db: SqliterDB) -> None:
        """Test LazyLoader handles DB errors gracefully."""

        # Create a LazyLoader pointing to a non-existent table
        class FakeModel(BaseDBModel):
            name: str

        lazy = LazyLoader(
            instance=object(),
            to_model=FakeModel,
            fk_id=999,
            db_context=db,
        )

        # Accessing should raise AttributeError (not a DB error)
        with pytest.raises(AttributeError):
            _ = lazy.name

    def test_load_with_null_fk_id(self, db: SqliterDB) -> None:
        """Test LazyLoader._load() with null FK ID."""
        lazy = LazyLoader(
            instance=object(),
            to_model=Author,
            fk_id=None,
            db_context=db,
        )

        # Force _load to be called
        lazy._load()
        assert lazy._cached is None


class TestForeignKeyDescriptor:
    """Test suite for ForeignKey descriptor __set__ method.

    Note: Pydantic intercepts __setattr__, so we call the descriptor directly.
    The descriptor is stored in fk_descriptors, not __dict__.
    """

    def test_set_with_none(self, db: SqliterDB) -> None:
        """Test setting FK to None via descriptor."""
        db.create_table(Publisher)
        db.create_table(Magazine)

        publisher = db.insert(Publisher(name="Test Pub"))
        magazine = db.insert(Magazine(title="Test Mag", publisher=publisher))

        # Call descriptor directly via fk_descriptors
        Magazine.fk_descriptors["publisher"].__set__(magazine, None)
        assert magazine.publisher_id is None

    def test_set_with_int(self, db: SqliterDB) -> None:
        """Test setting FK with integer ID via descriptor."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="IntTest", email="int@example.com"))
        book = db.insert(Book(title="Int Book", author=author))

        # Create another author and set by ID via descriptor
        author2 = db.insert(Author(name="IntTest2", email="int2@example.com"))
        Book.fk_descriptors["author"].__set__(book, author2.pk)

        assert book.author_id == author2.pk

    def test_set_with_model_instance(self, db: SqliterDB) -> None:
        """Test setting FK with model instance via descriptor."""
        db.create_table(Author)
        db.create_table(Book)

        author1 = db.insert(Author(name="Model1", email="m1@example.com"))
        author2 = db.insert(Author(name="Model2", email="m2@example.com"))
        book = db.insert(Book(title="Model Book", author=author1))

        # Set with model instance via descriptor
        Book.fk_descriptors["author"].__set__(book, author2)
        assert book.author_id == author2.pk

    def test_set_with_invalid_type(self, db: SqliterDB) -> None:
        """Test setting FK with invalid type raises TypeError."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="Invalid", email="inv@example.com"))
        book = db.insert(Book(title="Invalid Book", author=author))

        # Setting with invalid type should raise TypeError
        with pytest.raises(TypeError, match="FK value must be"):
            Book.fk_descriptors["author"].__set__(book, "invalid string")

    def test_get_returns_lazy_loader(self, db: SqliterDB) -> None:
        """Test ForeignKey.__get__ returns LazyLoader when called directly.

        Note: The ORM model's __getattribute__ normally intercepts FK access,
        but we can call __get__ directly on the descriptor.
        """
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="GetTest", email="get@example.com"))
        book = db.insert(Book(title="Get Book", author=author))

        # Call __get__ directly on the descriptor
        descriptor = Book.fk_descriptors["author"]
        result = descriptor.__get__(book, Book)

        # Should return a LazyLoader
        assert isinstance(result, LazyLoader)


class TestReverseQueryMethods:
    """Test suite for ReverseQuery methods."""

    def test_fetch_one(self, db: SqliterDB) -> None:
        """Test fetch_one on reverse relationship."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="FetchOne", email="fo@example.com"))
        db.insert(Book(title="Book 1", author=author))
        db.insert(Book(title="Book 2", author=author))

        # fetch_one should return a single book
        book = author.books.fetch_one()
        assert book is not None
        assert book.title in {"Book 1", "Book 2"}

    def test_fetch_one_empty(self, db: SqliterDB) -> None:
        """Test fetch_one when no related objects exist."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="NoBooks", email="nb@example.com"))

        # fetch_one should return None
        book = author.books.fetch_one()
        assert book is None

    def test_fetch_all_no_db_context(self) -> None:
        """Test fetch_all returns empty list without db_context."""
        # Create instance without db_context
        author = Author(name="NoContext", email="nc@example.com")

        # Should return empty list
        books = author.books.fetch_all()
        assert books == []

    def test_count_no_db_context(self) -> None:
        """Test count returns 0 without db_context."""
        # Create instance without db_context
        author = Author(name="NoContext", email="nc@example.com")

        # Should return 0
        count = author.books.count()
        assert count == 0

    def test_count_with_filters(self, db: SqliterDB) -> None:
        """Test count with filters on reverse relationship."""
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="FilterCount", email="fc@example.com"))
        db.insert(Book(title="Python Book", author=author))
        db.insert(Book(title="Java Book", author=author))
        db.insert(Book(title="Python Guide", author=author))

        # Count with filter
        count = author.books.filter(title__like="Python%").count()
        assert count == 2


class TestReverseRelationshipDescriptor:
    """Test suite for ReverseRelationship descriptor."""

    def test_class_level_access(self) -> None:
        """Test accessing reverse relationship on class returns descriptor."""
        # Access on class, not instance
        descriptor = Author.books
        assert isinstance(descriptor, ReverseRelationship)

    def test_cannot_set_reverse_relationship(self, db: SqliterDB) -> None:
        """Test setting reverse relationship raises AttributeError.

        Pydantic intercepts __setattr__, so we call the descriptor directly.
        """
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="NoSet", email="ns@example.com"))

        # Call descriptor directly to bypass Pydantic's __setattr__
        with pytest.raises(
            AttributeError, match="Cannot set reverse relationship"
        ):
            Author.books.__set__(author, [])


class TestRegistryPendingRelationships:
    """Test suite for ModelRegistry pending relationships."""

    @pytest.fixture(autouse=True)
    def _clean_registry(self) -> Generator[None, None, None]:
        """Isolate ModelRegistry state for each test."""
        original_models = ModelRegistry._models.copy()
        original_fks = ModelRegistry._foreign_keys.copy()
        original_pending = ModelRegistry._pending_reverses.copy()

        ModelRegistry._models.clear()
        ModelRegistry._foreign_keys.clear()
        ModelRegistry._pending_reverses.clear()

        try:
            yield
        finally:
            ModelRegistry._models.clear()
            ModelRegistry._models.update(original_models)
            ModelRegistry._foreign_keys.clear()
            ModelRegistry._foreign_keys.update(original_fks)
            ModelRegistry._pending_reverses.clear()
            ModelRegistry._pending_reverses.update(original_pending)

    def test_forward_reference_pending_relationship(self) -> None:
        """Test FK to model defined later (forward reference)."""
        # Define a model that references another not-yet-defined model
        # Note: This is tricky because Python requires the class to exist
        # We'll test the pending mechanism by manually triggering it

        class TargetModel(BaseDBModel):
            """Model that will be referenced."""

            name: str

        # Define a model with FK to TargetModel
        # Since TargetModel is defined first, this won't trigger pending
        # But we can verify the mechanism works

        class _SourceModel(BaseDBModel):
            """Model with FK to target."""

            title: str
            target: ForeignKey[TargetModel] = ForeignKey(
                TargetModel,
                on_delete="CASCADE",
                related_name="sourcemodels",  # reverse relationship name
            )

        # Verify reverse relationship was set up
        assert hasattr(TargetModel, "sourcemodels")

    def test_pending_reverse_relationship_deferred(self) -> None:
        """Test that pending relationships are stored and processed later.

        This tests the scenario where a FK is defined before the target
        model is registered - the relationship is stored as pending and
        processed when the target model is registered.
        """

        # First define a target model (will be registered)
        class DeferredTarget(BaseDBModel):
            """Target model defined first but registered later."""

            name: str

        # Now manually simulate the pending mechanism by:
        # 1. Unregistering the target
        # 2. Adding a pending relationship
        # 3. Re-registering to trigger processing

        target_table = "deferredtarget"

        # Remove the model from registry (simulating it not being there yet)
        if target_table in ModelRegistry._models:
            del ModelRegistry._models[target_table]

        # Manually add a pending relationship
        ModelRegistry._pending_reverses[target_table] = [
            {
                "from_model": Book,  # Use existing Book class
                "to_model": DeferredTarget,
                "fk_field": "target",
                "related_name": "books",
            }
        ]

        # Now register the model - this should process pending relationships
        ModelRegistry.register_model(DeferredTarget)

        # Verify the pending list was processed and cleared
        assert target_table not in ModelRegistry._pending_reverses

        # Verify the reverse relationship was added
        assert hasattr(DeferredTarget, "books")

    def test_add_reverse_relationship_stores_pending(self) -> None:
        """Test add_reverse_relationship stores pending when model missing."""

        # Create a mock "to_model" that's not registered
        class UnregisteredModel(BaseDBModel):
            """Model that won't be in registry."""

            name: str

        # Remove it from registry
        unregistered_table = "unregisteredmodel"
        if unregistered_table in ModelRegistry._models:
            del ModelRegistry._models[unregistered_table]

        # Call add_reverse_relationship - should store as pending
        ModelRegistry.add_reverse_relationship(
            from_model=Book,
            to_model=UnregisteredModel,
            fk_field="unregistered",
            related_name="books",
        )

        # Verify it was stored as pending
        assert unregistered_table in ModelRegistry._pending_reverses
        assert len(ModelRegistry._pending_reverses[unregistered_table]) == 1
        pending = ModelRegistry._pending_reverses[unregistered_table][0]
        assert pending["from_model"] is Book
        assert pending["related_name"] == "books"


class TestUpdateWithORMForeignKey:
    """Test suite for SqliterDB.update() with ORM FK fields."""

    def test_update_fk_via_id_field(self, db: SqliterDB) -> None:
        """Test updating FK by modifying the _id field directly."""
        db.create_table(Author)
        db.create_table(Book)

        author1 = db.insert(Author(name="Author1", email="a1@example.com"))
        author2 = db.insert(Author(name="Author2", email="a2@example.com"))
        book = db.insert(Book(title="Update Book", author=author1))

        # Update by modifying the _id field and calling update
        book.author_id = author2.pk
        db.update(book)

        # Fetch and verify
        updated_book = db.get(Book, book.pk)
        assert updated_book is not None
        assert updated_book.author_id == author2.pk

    def test_update_nullable_fk_to_none(self, db: SqliterDB) -> None:
        """Test updating nullable FK to None."""
        db.create_table(Publisher)
        db.create_table(Magazine)

        publisher = db.insert(Publisher(name="Pub"))
        magazine = db.insert(Magazine(title="Update None", publisher=publisher))

        # Update by setting _id to None
        magazine.publisher_id = None
        db.update(magazine)

        # Fetch and verify
        updated_mag = db.get(Magazine, magazine.pk)
        assert updated_mag is not None
        assert updated_mag.publisher_id is None
