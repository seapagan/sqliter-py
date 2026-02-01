# Many-to-Many Relationships

SQLiter supports many-to-many (M2M) relationships in ORM mode using the
`ManyToMany` descriptor. M2M relationships are backed by a junction
table that SQLiter creates automatically.

```python
from sqliter.orm import BaseDBModel, ManyToMany

class Tag(BaseDBModel):
    name: str

class Article(BaseDBModel):
    title: str
    tags: ManyToMany[Tag] = ManyToMany(Tag)
```

You can also use a string forward reference for `to_model` when the
target model is defined later. The relationship resolves when the target
model is registered.

```python
class Article(BaseDBModel):
    title: str
    tags: ManyToMany["Tag"] = ManyToMany("Tag")
```

## Creating and Querying Relationships

M2M access returns a `ManyToManyManager` that provides a small API:

```python
article = db.insert(Article(title="Guide"))
tag = db.insert(Tag(name="python"))

article.tags.add(tag)
article.tags.remove(tag)
article.tags.clear()
article.tags.set(tag)

tags = article.tags.fetch_all()
tag = article.tags.fetch_one()
count = article.tags.count()
exists = article.tags.exists()
```

`filter()` returns a `QueryBuilder` limited to related objects:

```python
results = article.tags.filter(name="python").fetch_all()
```

## Reverse Accessors

SQLiter adds a reverse accessor to the target model (unless suppressed).
The name is auto-generated from the source model name or can be
explicitly set with `related_name`.

```python
class Article(BaseDBModel):
    title: str
    tags: ManyToMany[Tag] = ManyToMany(Tag, related_name="articles")

tag = db.insert(Tag(name="python"))
articles = tag.articles.fetch_all()
```

!!! note "Type checkers and reverse accessors"
    Reverse accessors are injected dynamically at runtime, so tools like mypy
    cannot infer their type automatically. If you want strict typing, use
    `cast()` at the call site:

    ```python
    from typing import Any, cast

    articles = cast("Any", tag.articles).fetch_all()
    ```

## Custom Junction Table Name

Use `through` to control the junction table name:

```python
class Post(BaseDBModel):
    body: str
    categories: ManyToMany[Category] = ManyToMany(
        Category, through="post_category_links"
    )
```

## Self-Referential Symmetry

For self-referential relationships (e.g., friends), use
`symmetrical=True`. SQLiter stores a single row per pair and returns the
relationship from either side. No reverse accessor is created for
symmetrical self-references.

```python
class User(BaseDBModel):
    name: str
    friends: ManyToMany[User] = ManyToMany("User", symmetrical=True)

alice = db.insert(User(name="Alice"))
bob = db.insert(User(name="Bob"))

alice.friends.add(bob)
assert {u.name for u in bob.friends.fetch_all()} == {"Alice"}
```

## Eager Loading with prefetch_related()

When iterating over a queryset and accessing M2M relationships on each
instance, you can hit the N+1 query problem. `prefetch_related()` solves this
by fetching all related objects in a single extra query:

```python
# Without prefetch: 1 query for articles + N queries for tags
articles = db.select(Article).fetch_all()
for article in articles:
    tags = article.tags.fetch_all()  # hits the DB each time

# With prefetch: 1 query for articles + 1 query for tags (2 total)
articles = db.select(Article).prefetch_related("tags").fetch_all()
for article in articles:
    tags = article.tags.fetch_all()  # served from cache
```

### Forward and Reverse M2M

`prefetch_related()` works for both the forward side (where `ManyToMany` is
defined) and the reverse side:

```python
# Forward: articles with their tags
articles = db.select(Article).prefetch_related("tags").fetch_all()

# Reverse: tags with their articles
tags = db.select(Tag).prefetch_related("articles").fetch_all()
for tag in tags:
    print(f"{tag.name}: {tag.articles.count()} articles")
```

### Symmetrical Self-Referential M2M

`prefetch_related()` handles symmetrical self-referential M2M correctly.
Both directions of the relationship are resolved:

```python
people = db.select(User).prefetch_related("friends").fetch_all()
for person in people:
    print(f"{person.name}: {person.friends.count()} friends")
```

### Prefetched M2M Data API

Accessing a prefetched M2M relationship returns a `PrefetchedM2MResult` that
provides the same read interface as `ManyToManyManager`:

```python
article.tags.fetch_all()   # list of Tag instances
article.tags.fetch_one()   # first Tag or None
article.tags.count()       # number of tags
article.tags.exists()      # True if any tags exist
```

Write operations (`add`, `remove`, `clear`, `set`) are delegated to the real
`ManyToManyManager`, so they work exactly as expected:

```python
articles = db.select(Article).prefetch_related("tags").fetch_all()
guide = articles[0]

# Write operations still work through the prefetched wrapper
new_tag = db.insert(Tag(name="new"))
guide.tags.add(new_tag)
guide.tags.remove(new_tag)
```

Calling `filter()` on a prefetched M2M relationship falls back to a real
database query.

> [!TIP]
>
> For reverse FK relationships (e.g., `author.books`), `prefetch_related()`
> works the same way. See
> [ORM Foreign Keys](foreign-keys/orm.md#eager-loading-reverse-relationships-with-prefetch_related)
> for details.

## Notes

- M2M operations require a `db_context`, which is set when instances are
  returned from `SqliterDB` methods like `insert()` and `get()`.
- Junction tables include `CASCADE` FK constraints, a unique pair
  constraint, and indexes on both FK columns.
