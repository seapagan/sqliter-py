# Foreign Key Support - Product Requirements Document

## Overview

Add comprehensive foreign key relationship support to SQLiter, enabling one-to-one, one-to-many, and many-to-many relationships between models with proper SQLite foreign key constraints and Python-level relationship management.

## Background

Currently, SQLiter provides robust model definition and querying capabilities but lacks built-in support for defining and managing relationships between models. This feature will enhance SQLiter's ORM capabilities to match common use cases in modern applications.

## Goals

1. Enable developers to define relationships between models using intuitive field types
2. Maintain SQLiter's current simplicity while adding powerful relationship features
3. Ensure proper SQLite foreign key constraint management
4. Provide efficient querying capabilities for related models

## Non-Goals

1. Supporting complex relationship features like polymorphic associations
2. Implementing advanced migration systems
3. Supporting databases other than SQLite

## Requirements

### 1. Relationship Field Types

#### 1.1 ForeignKeyField

```python
class ForeignKeyField:
    def __init__(
        self,
        to_model: type[BaseDBModel],
        on_delete: Literal["CASCADE", "SET NULL", "RESTRICT"] = "CASCADE",
        on_update: Literal["CASCADE", "SET NULL", "RESTRICT"] = "CASCADE",
        null: bool = False,
        unique: bool = False  # For one-to-one relationships
    )
```

#### 1.2 ManyToManyField

```python
class ManyToManyField:
    def __init__(
        self,
        to_model: type[BaseDBModel],
        through: Optional[str] = None,  # Custom junction table name
        related_name: Optional[str] = None
    )
```

### 2. Model Definition Examples

```python
class Author(BaseDBModel):
    name: str
    email: str

class Book(BaseDBModel):
    title: str
    author: ForeignKeyField[Author]  # One-to-many
    published_date: datetime.date

class Profile(BaseDBModel):
    user: ForeignKeyField[Author, unique=True]  # One-to-one
    bio: str

class Tag(BaseDBModel):
    name: str
    books: ManyToManyField[Book]  # Many-to-many
```

### 3. Query API Enhancements

#### 3.1 Relationship Loading

- Add `select_related()` for eager loading of foreign key relationships
- Add `prefetch_related()` for efficient loading of reverse relationships

```python
books = Book.objects.select_related("author").filter(published_date__gt="2023-01-01")
authors = Author.objects.prefetch_related("books").fetch_all()
```

#### 3.2 Relationship Access

- Direct attribute access for foreign keys
- Collection manager for reverse relationships

```python
book.author  # Returns Author instance
author.books  # Returns QueryManager for related Book instances
```

### 4. Database Schema Management

#### 4.1 Foreign Key Constraints

- Automatically create proper SQLite foreign key constraints
- Support ON DELETE and ON UPDATE actions
- Enable foreign key support in SQLite connection

#### 4.2 Junction Tables

- Automatic creation of junction tables for many-to-many relationships
- Support for custom junction table names
- Add appropriate indexes on foreign key columns

### 5. Data Operations

#### 5.1 Create & Update

- Cascade saves for nested relationships
- Validate relationship constraints

```python
book = Book(
    title="New Book",
    author=Author(name="New Author")  # Nested creation
)
book.save()  # Saves both book and author
```

#### 5.2 Delete

- Honor ON DELETE constraints
- Cascade deletes when specified
- Prevent deletion when RESTRICT is set

#### 5.3 Relationship Management

```python
# Many-to-many operations
book.tags.add(tag1, tag2)
book.tags.remove(tag1)
book.tags.clear()
```

## Technical Considerations

### 1. Schema Updates

- Add foreign key support to table creation SQL
- Implement junction table creation logic
- Add proper indexing for foreign key columns

### 2. Query Building

- Extend QueryBuilder to support JOIN operations
- Implement efficient prefetch logic
- Handle circular dependencies

### 3. Performance

- Lazy loading by default
- Efficient batch loading with prefetch_related
- Smart caching of related objects

### 4. Error Handling

- Add relationship-specific exceptions
- Proper validation of relationship definitions
- Clear error messages for constraint violations

## Migration Strategy

1. Implement as a new feature branch
2. Add comprehensive tests for all relationship types
3. Update documentation with relationship examples
4. Release as a major version update

## Testing Requirements

### 1. Unit Tests

- Test all relationship field types
- Test constraint enforcement
- Test cascade operations
- Test query performance

### 2. Integration Tests

- Test complex relationship scenarios
- Test data integrity
- Test migration scenarios

## Documentation Requirements

### 1. API Documentation

- Document all new field types
- Provide relationship definition examples
- Document query methods

### 2. Guides

- Add relationship modeling guide
- Add performance optimization guide
- Add migration guide for existing users

## Future Considerations

1. Support for more complex relationship types
2. Advanced prefetching strategies
3. Relationship-aware model validation
4. Schema migration tools

## Usage Examples

### 1. Basic Model Setup and Relationships

```python
from datetime import date
from sqliter import BaseDBModel, ForeignKeyField, ManyToManyField

# One-to-Many: Author -> Books
class Author(BaseDBModel):
    name: str
    email: str

class Book(BaseDBModel):
    title: str
    author: ForeignKeyField[Author]
    published_date: date

# One-to-One: User -> Profile
class User(BaseDBModel):
    username: str
    email: str

class Profile(BaseDBModel):
    user: ForeignKeyField[User, unique=True]  # unique=True makes it one-to-one
    bio: str
    avatar_url: str

# Many-to-Many: Books <-> Categories
class Category(BaseDBModel):
    name: str
    description: str
    books: ManyToManyField[Book]  # Creates a junction table
```

### 2. Creating Related Records

```python
# Creating records with relationships
author = Author(name="John Doe", email="john@example.com")
author.save()

# Create book with existing author
book = Book(
    title="Python Programming",
    author=author,  # Can assign the author instance directly
    published_date=date(2024, 1, 1)
)
book.save()

# Create book with new author (automatic save)
book2 = Book(
    title="Advanced Python",
    author=Author(name="Jane Smith", email="jane@example.com"),
    published_date=date(2024, 2, 1)
)
book2.save()  # This will save both the book and the new author

# One-to-one relationship
user = User(username="johndoe", email="john@example.com")
user.save()

profile = Profile(
    user=user,
    bio="Python developer and author",
    avatar_url="https://example.com/avatar.jpg"
)
profile.save()

# Many-to-many relationships
category = Category(name="Programming", description="Programming books")
category.save()

# Add books to category
category.books.add(book, book2)
# Or alternatively
book.categories.add(category)  # Reverse relationship is automatically available
```

### 3. Querying Related Records

```python
# Get all books by an author
books = Book.objects.filter(author=author).fetch_all()

# Get author's books using reverse relationship
author_books = author.books.fetch_all()  # Automatically available

# Get book with author data in one query
book = Book.objects.select_related("author").fetch_first()
print(book.author.name)  # No additional query needed

# Get all authors with their books in one query
authors = Author.objects.prefetch_related("books").fetch_all()
for author in authors:
    for book in author.books.fetch_all():  # No additional queries
        print(f"{author.name}: {book.title}")

# Filter on related fields
books = Book.objects.filter(author__name="John Doe").fetch_all()

# Complex queries
recent_books = (
    Book.objects
    .select_related("author")
    .filter(
        published_date__gt=date(2023, 1, 1),
        author__email__contains="example.com"
    )
    .order("published_date", reverse=True)
    .fetch_all()
)

# One-to-one relationships
user = User.objects.select_related("profile").fetch_first()
print(user.profile.bio)

# Get user from profile
profile = Profile.objects.select_related("user").fetch_first()
print(profile.user.username)

# Many-to-many queries
programming_books = Category.objects.get(name="Programming").books.fetch_all()

# Books in multiple categories
books = (
    Book.objects
    .filter(categories__name__in=["Programming", "Python"])
    .fetch_all()
)
```

### 4. Updating Related Records

```python
# Update author's email and all their books' publication dates
author = Author.objects.fetch_first()
author.email = "newemail@example.com"
author.save()

for book in author.books.fetch_all():
    book.published_date = date(2024, 3, 1)
    book.save()

# Update one-to-one relationship
user = User.objects.fetch_first()
user.profile.bio = "Updated bio"
user.profile.save()

# Update many-to-many relationships
category = Category.objects.fetch_first()
category.books.remove(book)  # Remove one book
category.books.add(new_book)  # Add new book
category.books.clear()  # Remove all books
```

### 5. Deleting Related Records

```python
# Delete author (cascade behavior based on on_delete setting)
author = Author.objects.fetch_first()
author.delete()  # Will delete or update related books based on on_delete

# Delete specific books
author.books.filter(published_date__lt=date(2023, 1, 1)).delete()

# Delete profile (one-to-one)
user.profile.delete()

# Clean up many-to-many relationships
category.books.clear()  # Remove all associations without deleting books
category.delete()  # Delete category (books remain unaffected)
```

### 6. Advanced Usage

```python
# Custom junction table name
class Tag(BaseDBModel):
    name: str
    books: ManyToManyField[Book, through="book_tags"]

# Nested prefetch
authors = (
    Author.objects
    .prefetch_related("books__categories")  # Prefetch books and their categories
    .fetch_all()
)

# Complex filtering on related fields
books = (
    Book.objects
    .select_related("author")
    .filter(
        author__name__startswith="John",
        categories__name__in=["Python", "Programming"],
        published_date__gt=date(2023, 1, 1)
    )
    .order("author__name", "title")
    .fetch_all()
)

# Aggregate queries on related records
total_books = author.books.count()
latest_book = author.books.order("published_date", reverse=True).fetch_first()
```

## Implementation Phases

### Phase 1: Basic Foreign Key Support

- Implement ForeignKeyField class with basic functionality
- Add foreign key constraint support to table creation
- Implement basic relationship querying
- Add ON DELETE and ON UPDATE support
- Add validation for foreign key constraints
- Unit tests for basic functionality
- Documentation for ForeignKeyField usage

### Phase 2: Many-to-Many Relationships

- Implement ManyToManyField class
- Add automatic junction table creation and management
- Implement relationship manager for many-to-many operations
- Add support for custom junction table names
- Implement reverse relationship handling
- Unit tests for many-to-many functionality
- Documentation for ManyToManyField usage

### Phase 3: Advanced Features and Optimization

- Implement eager loading (select_related, prefetch_related)
- Add support for complex queries on related fields
- Implement caching for related objects
- Add support for nested prefetch operations
- Performance optimization for bulk operations
- Comprehensive integration tests
- Advanced usage documentation and examples
- Performance benchmarking

## Success Metrics

1. Zero regression in existing functionality
2. Query performance within 10% of direct SQL
3. Positive developer feedback on API design
4. Comprehensive test coverage
