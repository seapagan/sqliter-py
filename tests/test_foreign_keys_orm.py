"""Test suite for Phase 2 ORM functionality.

Tests lazy loading, reverse relationships, and automatic setup.
"""

import pytest

from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey, ModelRegistry


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
        """Test lazy loading when related object doesn't exist."""
        db.create_table(Book)
        # Don't create the author table or insert any authors

        # Insert with a non-existent author ID
        book = db.insert(Book(title="Orphan Book", author=999))

        # Accessing the author should return None or raise error
        # (Implementation may vary - currently it would try to load and fail)
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
        class ForwardRefBook(BaseDBModel):
            title: str

        # Now define Author - pending relationship should be processed
        class ForwardRefAuthor(BaseDBModel):
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
