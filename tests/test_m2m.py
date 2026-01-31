"""Tests for many-to-many relationship support."""

from __future__ import annotations

import sqlite3

import pytest

from sqliter.exceptions import ManyToManyIntegrityError
from sqliter.orm import BaseDBModel, ManyToMany
from sqliter.orm.m2m import ManyToManyManager, ReverseManyToMany
from sqliter.orm.registry import ModelRegistry
from sqliter.sqliter import SqliterDB

# ── Test models ──────────────────────────────────────────────────────


class Tag(BaseDBModel):
    """Tag model for M2M tests."""

    name: str


class Article(BaseDBModel):
    """Article model with M2M relationship to Tag."""

    title: str
    tags: ManyToMany[Tag] = ManyToMany(Tag)


class Category(BaseDBModel):
    """Category model for custom through/related_name tests."""

    label: str


class Post(BaseDBModel):
    """Post model with custom M2M options."""

    body: str
    categories: ManyToMany[Category] = ManyToMany(
        Category,
        through="post_category_links",
        related_name="posts",
    )


# ── Helpers ──────────────────────────────────────────────────────────


@pytest.fixture
def db() -> SqliterDB:
    """Create an in-memory database with Article and Tag tables."""
    database = SqliterDB(memory=True)
    database.create_table(Tag)
    database.create_table(Article)
    return database


@pytest.fixture
def db_custom() -> SqliterDB:
    """Create an in-memory database with Post and Category tables."""
    database = SqliterDB(memory=True)
    database.create_table(Category)
    database.create_table(Post)
    return database


# ── TestManyToManyDescriptor ─────────────────────────────────────────


class TestManyToManyDescriptor:
    """Tests for ManyToMany descriptor behavior."""

    def test_class_access_returns_descriptor(self) -> None:
        """Accessing M2M on class returns the descriptor itself."""
        desc = Article.__dict__["tags"]
        assert isinstance(desc, ManyToMany)

    def test_instance_access_returns_manager(self, db: SqliterDB) -> None:
        """Accessing M2M on instance returns ManyToManyManager."""
        article = db.insert(Article(title="Test"))
        assert isinstance(article.tags, ManyToManyManager)

    def test_cannot_set_m2m_field(self, db: SqliterDB) -> None:
        """Direct assignment to M2M field raises AttributeError."""
        article = db.insert(Article(title="Test"))
        with pytest.raises(AttributeError, match="Cannot assign"):
            article.tags = []

    def test_m2m_not_in_model_fields(self) -> None:
        """M2M field should not appear in model_fields."""
        assert "tags" not in Article.model_fields

    def test_m2m_not_in_model_dump(self, db: SqliterDB) -> None:
        """M2M field should not appear in model_dump."""
        article = db.insert(Article(title="Test"))
        data = article.model_dump()
        assert "tags" not in data

    def test_no_db_column_created(self, db: SqliterDB) -> None:
        """M2M field should not create a column in the model table."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "tags" not in columns

    def test_custom_related_name(self) -> None:
        """Custom related_name is used for reverse accessor."""
        assert hasattr(Category, "posts")
        desc = Category.posts
        assert isinstance(desc, ReverseManyToMany)

    def test_custom_through_name(self) -> None:
        """Custom through name is used for junction table."""
        desc = Post.__dict__["categories"]
        assert isinstance(desc, ManyToMany)
        assert desc._junction_table == "post_category_links"

    def test_auto_related_name(self) -> None:
        """Auto-generated related_name on Tag for Article.tags."""
        assert hasattr(Tag, "articles")
        desc = Tag.articles
        assert isinstance(desc, ReverseManyToMany)


# ── TestJunctionTableCreation ────────────────────────────────────────


class TestJunctionTableCreation:
    """Tests for junction table creation."""

    def test_junction_table_exists(self, db: SqliterDB) -> None:
        """Junction table is created when create_table is called."""
        tables = db.table_names
        assert "articles_tags" in tables

    def test_junction_table_columns(self, db: SqliterDB) -> None:
        """Junction table has expected columns."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info("articles_tags")')
        columns = {row[1] for row in cursor.fetchall()}
        assert "id" in columns
        assert "articles_pk" in columns
        assert "tags_pk" in columns

    def test_junction_table_unique_constraint(self, db: SqliterDB) -> None:
        """Junction table enforces unique pair constraint."""
        tag = db.insert(Tag(name="python"))
        article = db.insert(Article(title="Guide"))

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO "articles_tags" '
            '("articles_pk", "tags_pk") VALUES (?, ?)',
            (article.pk, tag.pk),
        )
        # Second insert of same pair should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                'INSERT INTO "articles_tags" '
                '("articles_pk", "tags_pk") VALUES (?, ?)',
                (article.pk, tag.pk),
            )

    def test_junction_table_fk_constraints(self, db: SqliterDB) -> None:
        """Junction table has FK constraints to both sides."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute('PRAGMA foreign_key_list("articles_tags")')
        fks = cursor.fetchall()
        tables_referenced = {row[2] for row in fks}
        assert "articles" in tables_referenced
        assert "tags" in tables_referenced

    def test_junction_table_indexes(self, db: SqliterDB) -> None:
        """Junction table has indexes on both FK columns."""
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute('PRAGMA index_list("articles_tags")')
        indexes = cursor.fetchall()
        index_names = {row[1] for row in indexes}
        assert "idx_articles_tags_articles_pk" in index_names
        assert "idx_articles_tags_tags_pk" in index_names

    def test_alphabetical_naming(self) -> None:
        """Junction table name is alphabetically sorted."""
        # articles < tags alphabetically, so "articles_tags"
        desc = Article.__dict__["tags"]
        assert desc._junction_table == "articles_tags"

    def test_custom_through_junction_table(self, db_custom: SqliterDB) -> None:
        """Custom through name creates the right junction table."""
        tables = db_custom.table_names
        assert "post_category_links" in tables

    def test_idempotent_creation(self, db: SqliterDB) -> None:
        """Creating the table again does not raise an error."""
        db.create_table(Article)
        db.create_table(Tag)
        tables = db.table_names
        assert "articles_tags" in tables


# ── TestManyToManyAdd ────────────────────────────────────────────────


class TestManyToManyAdd:
    """Tests for ManyToManyManager.add()."""

    def test_add_single(self, db: SqliterDB) -> None:
        """Add a single related object."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        assert article.tags.count() == 1

    def test_add_multiple(self, db: SqliterDB) -> None:
        """Add multiple related objects at once."""
        article = db.insert(Article(title="Guide"))
        tag1 = db.insert(Tag(name="python"))
        tag2 = db.insert(Tag(name="tutorial"))
        article.tags.add(tag1, tag2)

        assert article.tags.count() == 2

    def test_add_duplicate_ignored(self, db: SqliterDB) -> None:
        """Adding the same object twice is silently ignored."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)
        article.tags.add(tag)

        assert article.tags.count() == 1

    def test_add_no_db_context_raises(self) -> None:
        """Adding without db_context raises ManyToManyIntegrityError."""
        article = Article(title="Guide")
        article.pk = 1
        tag = Tag(name="python")
        tag.pk = 1

        with pytest.raises(ManyToManyIntegrityError, match="context"):
            article.tags.add(tag)

    def test_add_unsaved_instance_raises(self, db: SqliterDB) -> None:
        """Adding an unsaved instance raises ManyToManyIntegrityError."""
        article = db.insert(Article(title="Guide"))
        tag = Tag(name="python")  # Not inserted

        with pytest.raises(ManyToManyIntegrityError, match="primary key"):
            article.tags.add(tag)


# ── TestManyToManyRemove ─────────────────────────────────────────────


class TestManyToManyRemove:
    """Tests for ManyToManyManager.remove()."""

    def test_remove_single(self, db: SqliterDB) -> None:
        """Remove a single related object."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)
        article.tags.remove(tag)

        assert article.tags.count() == 0

    def test_remove_multiple(self, db: SqliterDB) -> None:
        """Remove multiple related objects."""
        article = db.insert(Article(title="Guide"))
        tag1 = db.insert(Tag(name="python"))
        tag2 = db.insert(Tag(name="tutorial"))
        article.tags.add(tag1, tag2)
        article.tags.remove(tag1, tag2)

        assert article.tags.count() == 0

    def test_remove_nonexistent_is_noop(self, db: SqliterDB) -> None:
        """Removing a nonexistent relationship does nothing."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        # Never added, should not raise
        article.tags.remove(tag)
        assert article.tags.count() == 0

    def test_remove_no_db_context_raises(self) -> None:
        """Removing without db_context raises."""
        article = Article(title="Guide")
        article.pk = 1
        tag = Tag(name="python")
        tag.pk = 1

        with pytest.raises(ManyToManyIntegrityError, match="context"):
            article.tags.remove(tag)


# ── TestManyToManyClear ──────────────────────────────────────────────


class TestManyToManyClear:
    """Tests for ManyToManyManager.clear()."""

    def test_clear_removes_all(self, db: SqliterDB) -> None:
        """Clear removes all relationships."""
        article = db.insert(Article(title="Guide"))
        tag1 = db.insert(Tag(name="python"))
        tag2 = db.insert(Tag(name="tutorial"))
        article.tags.add(tag1, tag2)
        article.tags.clear()

        assert article.tags.count() == 0

    def test_clear_empty_is_noop(self, db: SqliterDB) -> None:
        """Clearing when no relationships exist does nothing."""
        article = db.insert(Article(title="Guide"))
        article.tags.clear()
        assert article.tags.count() == 0

    def test_clear_no_db_context_raises(self) -> None:
        """Clearing without db_context raises."""
        article = Article(title="Guide")
        article.pk = 1

        with pytest.raises(ManyToManyIntegrityError, match="context"):
            article.tags.clear()


# ── TestManyToManySet ────────────────────────────────────────────────


class TestManyToManySet:
    """Tests for ManyToManyManager.set()."""

    def test_set_replaces_existing(self, db: SqliterDB) -> None:
        """set() replaces existing relationships."""
        article = db.insert(Article(title="Guide"))
        tag1 = db.insert(Tag(name="python"))
        tag2 = db.insert(Tag(name="tutorial"))
        tag3 = db.insert(Tag(name="advanced"))

        article.tags.add(tag1, tag2)
        article.tags.set(tag2, tag3)

        tags = article.tags.fetch_all()
        tag_names = {t.name for t in tags}
        assert tag_names == {"tutorial", "advanced"}

    def test_set_empty_clears(self, db: SqliterDB) -> None:
        """set() with no arguments clears all."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)
        article.tags.set()

        assert article.tags.count() == 0


# ── TestManyToManyQuery ──────────────────────────────────────────────


class TestManyToManyQuery:
    """Tests for M2M query methods."""

    def test_fetch_all(self, db: SqliterDB) -> None:
        """fetch_all() returns all related objects."""
        article = db.insert(Article(title="Guide"))
        tag1 = db.insert(Tag(name="python"))
        tag2 = db.insert(Tag(name="tutorial"))
        article.tags.add(tag1, tag2)

        tags = article.tags.fetch_all()
        assert len(tags) == 2
        tag_names = {t.name for t in tags}
        assert tag_names == {"python", "tutorial"}

    def test_fetch_all_empty(self, db: SqliterDB) -> None:
        """fetch_all() returns empty list when no relationships."""
        article = db.insert(Article(title="Guide"))
        assert article.tags.fetch_all() == []

    def test_fetch_one(self, db: SqliterDB) -> None:
        """fetch_one() returns a single related object."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        result = article.tags.fetch_one()
        assert result is not None
        assert result.name == "python"

    def test_fetch_one_none(self, db: SqliterDB) -> None:
        """fetch_one() returns None when no relationships."""
        article = db.insert(Article(title="Guide"))
        assert article.tags.fetch_one() is None

    def test_count(self, db: SqliterDB) -> None:
        """count() returns correct number."""
        article = db.insert(Article(title="Guide"))
        tag1 = db.insert(Tag(name="python"))
        tag2 = db.insert(Tag(name="tutorial"))
        article.tags.add(tag1, tag2)

        assert article.tags.count() == 2

    def test_exists_true(self, db: SqliterDB) -> None:
        """exists() returns True when relationships exist."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        assert article.tags.exists() is True

    def test_exists_false(self, db: SqliterDB) -> None:
        """exists() returns False when no relationships."""
        article = db.insert(Article(title="Guide"))
        assert article.tags.exists() is False

    def test_no_db_context_returns_empty(self) -> None:
        """Query without db_context returns empty results."""
        article = Article(title="Guide")
        article.pk = 1
        # No db_context, should return empty
        assert article.tags.fetch_all() == []
        assert article.tags.fetch_one() is None
        assert article.tags.count() == 0
        assert article.tags.exists() is False

    def test_filter_chaining(self, db: SqliterDB) -> None:
        """filter() returns QueryBuilder for chaining."""
        article = db.insert(Article(title="Guide"))
        tag1 = db.insert(Tag(name="python"))
        tag2 = db.insert(Tag(name="tutorial"))
        article.tags.add(tag1, tag2)

        results = article.tags.filter(name="python").fetch_all()
        assert len(results) == 1
        assert results[0].name == "python"


# ── TestReverseManyToMany ────────────────────────────────────────────


class TestReverseManyToMany:
    """Tests for reverse M2M accessors."""

    def test_reverse_accessor_exists(self) -> None:
        """Reverse accessor is created on target model."""
        assert hasattr(Tag, "articles")

    def test_reverse_fetch_all(self, db: SqliterDB) -> None:
        """Reverse fetch_all() returns related objects."""
        article1 = db.insert(Article(title="Guide 1"))
        article2 = db.insert(Article(title="Guide 2"))
        tag = db.insert(Tag(name="python"))

        article1.tags.add(tag)
        article2.tags.add(tag)

        articles = tag.articles.fetch_all()
        assert len(articles) == 2
        titles = {a.title for a in articles}
        assert titles == {"Guide 1", "Guide 2"}

    def test_reverse_add(self, db: SqliterDB) -> None:
        """Can add from the reverse side."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))

        tag.articles.add(article)
        assert tag.articles.count() == 1
        # Also visible from the forward side
        assert article.tags.count() == 1

    def test_reverse_remove(self, db: SqliterDB) -> None:
        """Can remove from the reverse side."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))

        article.tags.add(tag)
        tag.articles.remove(article)

        assert tag.articles.count() == 0
        assert article.tags.count() == 0

    def test_reverse_clear(self, db: SqliterDB) -> None:
        """Can clear from the reverse side."""
        article1 = db.insert(Article(title="Guide 1"))
        article2 = db.insert(Article(title="Guide 2"))
        tag = db.insert(Tag(name="python"))

        article1.tags.add(tag)
        article2.tags.add(tag)
        tag.articles.clear()

        assert tag.articles.count() == 0

    def test_reverse_count(self, db: SqliterDB) -> None:
        """Reverse count() works correctly."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        assert tag.articles.count() == 1

    def test_reverse_cannot_set(self, db: SqliterDB) -> None:
        """Direct assignment to reverse M2M raises AttributeError."""
        tag = db.insert(Tag(name="python"))
        with pytest.raises(AttributeError, match="Cannot assign"):
            tag.articles = []


# ── TestManyToManyCascadeDelete ──────────────────────────────────────


class TestManyToManyCascadeDelete:
    """Tests for CASCADE delete behavior on junction table."""

    def test_delete_side_a_removes_junction_rows(self, db: SqliterDB) -> None:
        """Deleting the Article removes junction rows."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        db.delete(Article, article.pk)

        # Junction row should be gone
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM "articles_tags" WHERE "articles_pk" = ?',
            (article.pk,),
        )
        assert cursor.fetchone()[0] == 0

    def test_delete_side_b_removes_junction_rows(self, db: SqliterDB) -> None:
        """Deleting the Tag removes junction rows."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        db.delete(Tag, tag.pk)

        # Junction row should be gone
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM "articles_tags" WHERE "tags_pk" = ?',
            (tag.pk,),
        )
        assert cursor.fetchone()[0] == 0

    def test_delete_does_not_delete_related_model(self, db: SqliterDB) -> None:
        """Deleting one side does NOT delete the related model."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        db.delete(Article, article.pk)

        # Tag should still exist
        fetched_tag = db.get(Tag, tag.pk)
        assert fetched_tag is not None
        assert fetched_tag.name == "python"


# ── TestManyToManyRegistry ───────────────────────────────────────────


class TestManyToManyRegistry:
    """Tests for M2M registration in ModelRegistry."""

    def test_m2m_registered(self) -> None:
        """M2M relationship is registered in ModelRegistry."""
        rels = ModelRegistry.get_m2m_relationships("articles")
        assert len(rels) >= 1
        rel = next(r for r in rels if r["m2m_field"] == "tags")
        assert rel["junction_table"] == "articles_tags"
        assert rel["to_model"] is Tag

    def test_reverse_accessor_on_target(self) -> None:
        """Reverse accessor descriptor is on target model."""
        desc = Tag.articles
        assert isinstance(desc, ReverseManyToMany)

    def test_m2m_descriptors_classvar(self) -> None:
        """m2m_descriptors ClassVar is populated."""
        assert "tags" in Article.m2m_descriptors
        assert isinstance(Article.m2m_descriptors["tags"], ManyToMany)


# ── TestManyToManyCustomThrough ──────────────────────────────────────


class TestManyToManyCustomThrough:
    """Tests for custom through table name."""

    def test_custom_junction_table_columns(self, db_custom: SqliterDB) -> None:
        """Custom junction table has correct columns."""
        conn = db_custom.connect()
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info("post_category_links")')
        columns = {row[1] for row in cursor.fetchall()}
        assert "id" in columns
        # Columns named by alphabetical sort of table names
        assert "categories_pk" in columns
        assert "posts_pk" in columns

    def test_custom_through_operations(self, db_custom: SqliterDB) -> None:
        """M2M operations work with custom through table."""
        post = db_custom.insert(Post(body="Hello world"))
        cat = db_custom.insert(Category(label="Tech"))

        post.categories.add(cat)
        assert post.categories.count() == 1

        cats = post.categories.fetch_all()
        assert len(cats) == 1
        assert cats[0].label == "Tech"

        # Reverse
        assert cat.posts.count() == 1
