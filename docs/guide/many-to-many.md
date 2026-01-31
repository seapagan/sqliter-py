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

## Notes

- M2M operations require a `db_context`, which is set when instances are
  returned from `SqliterDB` methods like `insert()` and `get()`.
- Junction tables include `CASCADE` FK constraints, a unique pair
  constraint, and indexes on both FK columns.
