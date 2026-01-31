"""Tests for many-to-many relationship support."""

from __future__ import annotations

import builtins
import sqlite3
import sys
from typing import TYPE_CHECKING, Any, cast

import pytest

from sqliter.exceptions import ManyToManyIntegrityError, TableCreationError
from sqliter.orm import BaseDBModel, ManyToMany
from sqliter.orm.m2m import (
    ManyToManyManager,
    ReverseManyToMany,
    create_junction_table,
)
from sqliter.orm.registry import ModelRegistry
from sqliter.sqliter import SqliterDB

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler

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

    def test_descriptor_set_raises_attribute_error(self, db: SqliterDB) -> None:
        """Descriptor __set__ raises AttributeError when called directly."""
        article = db.insert(Article(title="Test"))
        descriptor = Article.__dict__["tags"]
        with pytest.raises(AttributeError, match="Cannot assign"):
            descriptor.__set__(article, [])

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

    def test_create_junction_table_error(self) -> None:
        """create_junction_table raises TableCreationError on sqlite errors."""
        msg = "boom"

        class DummyDB(SqliterDB):
            def __init__(self) -> None:
                super().__init__(memory=True)

            def connect(self) -> sqlite3.Connection:
                raise sqlite3.Error(msg)

        with pytest.raises(TableCreationError, match="bad_table"):
            create_junction_table(DummyDB(), "bad_table", "a", "b")

    def test_junction_table_index_error_ignored(self) -> None:
        """Index creation errors are ignored."""
        msg = "index fail"

        class DummyCursor:
            def __init__(self, cursor: sqlite3.Cursor) -> None:
                self._cursor = cursor

            def execute(
                self, sql: str, params: tuple[object, ...] | None = None
            ) -> sqlite3.Cursor:
                if sql.startswith("CREATE INDEX"):
                    raise sqlite3.Error(msg)
                if params is None:
                    return self._cursor.execute(sql)
                return self._cursor.execute(sql, params)

        class DummyConn:
            def __init__(self) -> None:
                self._conn = sqlite3.connect(":memory:")

            def cursor(self) -> DummyCursor:
                return DummyCursor(self._conn.cursor())

            def commit(self) -> None:
                self._conn.commit()

        class DummyDB(SqliterDB):
            def __init__(self) -> None:
                super().__init__(memory=True)

            def connect(self) -> sqlite3.Connection:
                return cast("sqlite3.Connection", DummyConn())

        create_junction_table(DummyDB(), "articles_tags", "articles", "tags")


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

    def test_remove_rolls_back_on_error(self, db: SqliterDB) -> None:
        """remove() rolls back when a SQL error occurs."""
        article = db.insert(Article(title="Guide"))
        tag = db.insert(Tag(name="python"))
        article.tags.add(tag)

        conn = db.connect()
        conn.execute('DROP TABLE "articles_tags"')

        with pytest.raises(sqlite3.OperationalError):
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

    def test_count_no_pk_with_db_context(self, db: SqliterDB) -> None:
        """count() returns 0 when pk missing, even with db_context."""
        article = Article(title="Guide")
        article.db_context = db
        assert article.tags.count() == 0

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

    def test_reverse_set_handler_allows_noop(
        self, db: SqliterDB, monkeypatch
    ) -> None:
        """Reverse M2M handler returns True when __set__ does not raise."""
        tag = db.insert(Tag(name="python"))

        def noop_set(self, instance: object, value: object) -> None:
            return None

        monkeypatch.setattr(ReverseManyToMany, "__set__", noop_set)
        tag.articles = []

    def test_reverse_set_on_subclass_uses_mro(self, db: SqliterDB) -> None:
        """Reverse M2M assignment on subclass uses MRO lookup."""

        class TagChild(Tag):
            pass

        tag = TagChild(name="python")
        tag.db_context = db
        tag.pk = 1
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

    def test_custom_junction_table_columns_with_inflect(
        self, db_custom: SqliterDB
    ) -> None:
        """Custom junction table columns match inflect pluralization."""
        pytest.importorskip("inflect")
        conn = db_custom.connect()
        cursor = conn.cursor()
        cursor.execute('PRAGMA table_info("post_category_links")')
        columns = {row[1] for row in cursor.fetchall()}
        assert "id" in columns
        # Columns named by alphabetical sort of table names
        assert "categories_pk" in columns
        assert "posts_pk" in columns

    def test_custom_junction_table_columns_without_inflect(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Custom junction table columns match fallback pluralization."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()
        original_import = builtins.__import__

        def fake_import(
            name: str,
            globals_: dict[str, object] | None = None,
            locals_: dict[str, object] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> object:
            if name == "inflect":
                msg = "no inflect"
                raise ImportError(msg)
            return original_import(name, globals_, locals_, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        sys.modules.pop("inflect", None)

        try:

            class Category(BaseDBModel):
                label: str

            class Post(BaseDBModel):
                body: str
                categories: ManyToMany[Category] = ManyToMany(
                    Category,
                    through="post_category_links",
                )

            db = SqliterDB(memory=True)
            db.create_table(Category)
            db.create_table(Post)

            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute('PRAGMA table_info("post_category_links")')
            columns = {row[1] for row in cursor.fetchall()}
            assert "id" in columns
            # Fallback pluralization appends "s"
            assert "categorys_pk" in columns
            assert "posts_pk" in columns
        finally:
            ModelRegistry.restore(state)

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


# ── TestManyToManyEdgeCases ──────────────────────────────────────────


class TestManyToManyEdgeCases:
    """Tests for M2M edge cases and error conditions."""

    def test_manager_no_pk_error(self, db: SqliterDB) -> None:
        """ManyToManyManager raises error when instance has no pk."""
        # Create article without inserting (no pk)
        article = Article(title="Test")
        article.db_context = db

        # Try to use M2M manager without pk
        with pytest.raises(
            ManyToManyIntegrityError,
            match="Instance has no primary key",
        ):
            article.tags.add()

    def test_fetch_related_pks_no_db(self) -> None:
        """_fetch_related_pks returns empty list when no db_context."""
        # Create article without db_context
        article = Article(pk=1, title="Test")
        manager = article.tags
        # Should return empty list
        assert manager._fetch_related_pks() == []

    def test_fetch_related_pks_no_pk(self) -> None:
        """_fetch_related_pks returns empty list when no pk."""
        # Create article without pk but with db_context
        article = Article(title="Test")
        article.db_context = SqliterDB(memory=True)
        manager = article.tags
        # Should return empty list
        assert manager._fetch_related_pks() == []

    def test_pydantic_core_schema(self) -> None:
        """__get_pydantic_core_schema__ returns validator."""
        # Access the descriptor at class level
        descriptor = Article.tags
        # Get the schema - use cast to satisfy mypy
        handler = cast("GetCoreSchemaHandler", lambda x: x)
        schema: Any = descriptor.__get_pydantic_core_schema__(
            ManyToMany[Tag], handler
        )
        # Should return a validator schema
        assert schema is not None

    def test_inflect_fallback(self) -> None:
        """M2M related_name generation works (with or without inflect)."""
        # The related_name should be set (either via inflect or fallback)
        descriptor = Article.__dict__["tags"]
        assert descriptor.related_name is not None

    def test_string_forward_ref_resolves_when_target_exists(self) -> None:
        """String forward refs resolve when target is registered."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class Other(BaseDBModel):
                name: str

            class Referrer(BaseDBModel):
                name: str
                items: ManyToMany[Other] = ManyToMany("Other")

            descriptor = Referrer.__dict__["items"]
            assert descriptor.to_model is Other
        finally:
            ModelRegistry.restore(state)

    def test_string_forward_ref_resolves_when_target_defined_later(
        self,
    ) -> None:
        """String forward refs resolve when target is defined later."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class SourceLate(BaseDBModel):
                name: str
                targets: ManyToMany[TargetLate] = ManyToMany(
                    "TargetLate",
                    related_name="sources_late",
                )

            class TargetLate(BaseDBModel):
                name: str

            descriptor = SourceLate.__dict__["targets"]
            assert descriptor.to_model is TargetLate
            assert hasattr(TargetLate, "sources_late")
        finally:
            ModelRegistry.restore(state)

    def test_unresolved_string_forward_ref_raises_on_access(self) -> None:
        """Accessing unresolved forward refs raises a clear error."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class MissingTarget(BaseDBModel):
                name: str
                items: ManyToMany[Any] = ManyToMany("NeverDefined")

            instance = MissingTarget(name="missing")
            with pytest.raises(TypeError, match="unresolved"):
                _ = instance.items
        finally:
            ModelRegistry.restore(state)

    def test_inflect_import_error_fallback(self, monkeypatch) -> None:
        """Fallback related_name used when inflect import fails."""
        original_import = builtins.__import__

        def fake_import(
            name: str,
            globals_: dict[str, object] | None = None,
            locals_: dict[str, object] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> object:
            if name == "inflect":
                msg = "no inflect"
                raise ImportError(msg)
            return original_import(name, globals_, locals_, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        class AuthorFallback(BaseDBModel):
            name: str

        class BookFallback(BaseDBModel):
            title: str
            authors: ManyToMany[AuthorFallback] = ManyToMany(AuthorFallback)

        descriptor = BookFallback.__dict__["authors"]
        assert descriptor.related_name == "bookfallbacks"

    def test_junction_table_idempotent_creation(self, db: SqliterDB) -> None:
        """Creating junction table again doesn't raise error."""
        # Create junction table successfully
        create_junction_table(db, "articles_tags", "articles", "tags")

        # Try to create it again - should be idempotent
        create_junction_table(db, "articles_tags", "articles", "tags")

    def test_m2m_removed_from_model_fields_when_present(self) -> None:
        """_setup_orm_fields removes M2M fields from model_fields."""

        class TempTag(BaseDBModel):
            name: str

        class TempArticle(BaseDBModel):
            title: str
            tags: ManyToMany[TempTag] = ManyToMany(
                TempTag, related_name="temp_articles"
            )

        try:
            TempArticle.model_fields["tags"] = TempArticle.model_fields["title"]
            assert "tags" in TempArticle.model_fields
            TempArticle._setup_orm_fields()
            assert "tags" not in TempArticle.model_fields
        finally:
            TempArticle.model_fields.pop("tags", None)

    def test_invalid_through_table_name_raises(self) -> None:
        """Invalid through table name raises ValueError."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:
            with pytest.raises(ValueError, match="Invalid table name"):

                class BadThrough(BaseDBModel):  # pylint: disable=unused-variable
                    name: str
                    tags: ManyToMany[Any] = ManyToMany(
                        Tag,
                        through="bad-name",
                    )
        finally:
            ModelRegistry.restore(state)

    def test_create_m2m_junction_tables_import_error(self, monkeypatch) -> None:
        """ImportError in M2M setup is ignored."""
        original_import = builtins.__import__

        def fake_import(
            name: str,
            globals_: dict[str, object] | None = None,
            locals_: dict[str, object] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> object:
            if name in ("sqliter.orm.m2m", "sqliter.orm.registry"):
                msg = "no orm"
                raise ImportError(msg)
            return original_import(name, globals_, locals_, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        db = SqliterDB(memory=True)
        db._create_m2m_junction_tables(Article)

    def test_self_ref_symmetrical_relationship(self) -> None:
        """Self-referential symmetrical M2M works both directions."""
        state = ModelRegistry.snapshot()

        try:

            class Member(BaseDBModel):
                name: str
                friends: ManyToMany[Member] = ManyToMany(
                    "Member", symmetrical=True
                )

                class Meta:
                    table_name = "members_sym"

            db = SqliterDB(memory=True)
            db.create_table(Member)

            alice = db.insert(Member(name="Alice"))
            bob = db.insert(Member(name="Bob"))

            alice.friends.add(bob)

            assert {m.name for m in alice.friends.fetch_all()} == {"Bob"}
            assert {m.name for m in bob.friends.fetch_all()} == {"Alice"}

            bob.friends.add(alice)
            assert alice.friends.count() == 1
        finally:
            ModelRegistry.restore(state)

    def test_self_ref_symmetrical_remove(self) -> None:
        """Removing from either side works for symmetrical self-ref."""
        state = ModelRegistry.snapshot()

        try:

            class Person(BaseDBModel):
                name: str
                peers: ManyToMany[Person] = ManyToMany(
                    "Person", symmetrical=True
                )

                class Meta:
                    table_name = "people_sym"

            db = SqliterDB(memory=True)
            db.create_table(Person)

            a = db.insert(Person(name="A"))
            b = db.insert(Person(name="B"))
            a.peers.add(b)

            b.peers.remove(a)
            assert a.peers.count() == 0

            a.peers.add(b)
            a.peers.clear()
            assert b.peers.count() == 0
        finally:
            ModelRegistry.restore(state)

    def test_self_ref_reverse_accessor_directional(self) -> None:
        """Reverse accessor uses swapped columns for self-ref."""
        state = ModelRegistry.snapshot()

        try:

            class User(BaseDBModel):
                name: str
                follows: ManyToMany[User] = ManyToMany(
                    "User", related_name="followed_by"
                )

                class Meta:
                    table_name = "users_sym_dir"

            db = SqliterDB(memory=True)
            db.create_table(User)

            u1 = db.insert(User(name="U1"))
            u2 = db.insert(User(name="U2"))

            u1.follows.add(u2)
            assert {u.name for u in u2.followed_by.fetch_all()} == {"U1"}
            assert u2.follows.count() == 0
        finally:
            ModelRegistry.restore(state)

    def test_self_ref_symmetrical_skips_reverse_accessor(self) -> None:
        """Symmetrical self-ref ignores explicit related_name."""
        state = ModelRegistry.snapshot()

        try:

            class Contact(BaseDBModel):
                name: str
                links: ManyToMany[Contact] = ManyToMany(
                    "Contact", related_name="linked_to", symmetrical=True
                )

                class Meta:
                    table_name = "contacts_sym"

            assert not hasattr(Contact, "linked_to")
        finally:
            ModelRegistry.restore(state)


# ── TestManyToManyRegistry ───────────────────────────────────────────


class TestManyToManyRegistryEdgeCases:
    """Tests for M2M registration edge cases."""

    def test_pending_m2m_reverse_registration(self) -> None:
        """M2M reverse relationship registered when target becomes available."""
        # Save original state
        orig_models = ModelRegistry._models.copy()
        orig_m2m = ModelRegistry._m2m_relationships.copy()
        orig_pending = ModelRegistry._pending_m2m_reverses.copy()

        try:
            # Clear registry
            ModelRegistry._models.clear()
            ModelRegistry._m2m_relationships.clear()
            ModelRegistry._pending_m2m_reverses.clear()

            # Define models with unique names
            class TagPending(BaseDBModel):
                name: str

            class ArticlePending(BaseDBModel):
                title: str
                tags: ManyToMany[TagPending] = ManyToMany(
                    TagPending, related_name="articles_pending"
                )

            # Register Article first (Tag not registered yet)
            ModelRegistry.register_model(ArticlePending)

            # Now register Tag - should process pending M2M reverses
            ModelRegistry.register_model(TagPending)

            # Tag should now have the reverse accessor
            assert hasattr(TagPending, "articles_pending")
        finally:
            # Restore original state
            ModelRegistry._models = orig_models
            ModelRegistry._m2m_relationships = orig_m2m
            ModelRegistry._pending_m2m_reverses = orig_pending

    def test_pending_m2m_reverse_added_then_processed(self) -> None:
        """Pending reverse is stored then processed on register."""
        orig_models = ModelRegistry._models.copy()
        orig_m2m = ModelRegistry._m2m_relationships.copy()
        orig_pending = ModelRegistry._pending_m2m_reverses.copy()

        try:
            ModelRegistry._models.clear()
            ModelRegistry._m2m_relationships.clear()
            ModelRegistry._pending_m2m_reverses.clear()

            class TargetPending(BaseDBModel):
                name: str

            ModelRegistry._models.pop(TargetPending.get_table_name(), None)

            class SourcePending(BaseDBModel):
                title: str
                targets: ManyToMany[TargetPending] = ManyToMany(
                    TargetPending, related_name="sources_pending"
                )

            to_table = TargetPending.get_table_name()
            assert to_table in ModelRegistry._pending_m2m_reverses
            assert not hasattr(TargetPending, "sources_pending")

            ModelRegistry.register_model(TargetPending)
            assert hasattr(TargetPending, "sources_pending")
        finally:
            ModelRegistry._models = orig_models
            ModelRegistry._m2m_relationships = orig_m2m
            ModelRegistry._pending_m2m_reverses = orig_pending

    def test_reverse_accessor_conflict_raises(self) -> None:
        """Conflict on reverse accessor raises AttributeError."""
        orig_models = ModelRegistry._models.copy()
        orig_m2m = ModelRegistry._m2m_relationships.copy()
        orig_pending = ModelRegistry._pending_m2m_reverses.copy()

        try:
            ModelRegistry._models.clear()
            ModelRegistry._m2m_relationships.clear()
            ModelRegistry._pending_m2m_reverses.clear()

            class TargetConflict(BaseDBModel):
                name: str

            TargetConflict.conflict_attr = object()

            # Python 3.10 wraps __set_name__ errors in RuntimeError.
            with pytest.raises(
                (AttributeError, RuntimeError),
                match=r"Reverse M2M accessor|__set_name__",
            ) as exc_info:

                class SourceConflict(BaseDBModel):
                    title: str
                    targets: ManyToMany[TargetConflict] = ManyToMany(
                        TargetConflict, related_name="conflict_attr"
                    )

            if isinstance(exc_info.value, RuntimeError):
                assert isinstance(exc_info.value.__cause__, AttributeError)
        finally:
            ModelRegistry._models = orig_models
            ModelRegistry._m2m_relationships = orig_m2m
            ModelRegistry._pending_m2m_reverses = orig_pending

    def test_forward_ref_with_through_sets_junction_table(self) -> None:
        """String forward refs with through set junction table immediately."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class Source(BaseDBModel):
                name: str
                links: ManyToMany[Any] = ManyToMany(
                    "Target",
                    through="custom_links",
                )

            descriptor = Source.__dict__["links"]
            assert descriptor.junction_table == "custom_links"

            class Target(BaseDBModel):
                name: str

            assert descriptor.to_model is Target
            assert descriptor.junction_table == "custom_links"
        finally:
            ModelRegistry.restore(state)

    def test_junction_table_resolution_failure_raises(
        self, monkeypatch
    ) -> None:
        """If junction table can't be resolved, registration fails."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class TargetBad(BaseDBModel):
                name: str

            def bad_junction(self, owner: type[BaseDBModel]) -> None:
                _ = self
                _ = owner

            monkeypatch.setattr(
                ManyToMany, "_get_junction_table_name", bad_junction
            )

            with pytest.raises(
                (ValueError, RuntimeError),
                match=r"junction table|__set_name__",
            ) as exc_info:

                class SourceBad(BaseDBModel):  # pylint: disable=unused-variable
                    name: str
                    targets: ManyToMany[TargetBad] = ManyToMany(TargetBad)

            if isinstance(exc_info.value, RuntimeError):
                assert isinstance(exc_info.value.__cause__, ValueError)
        finally:
            ModelRegistry.restore(state)


class TestModelRegistry:
    """Tests for ModelRegistry helpers and pending resolution."""

    def test_add_reverse_relationship_pending_then_registered(self) -> None:
        """Pending reverse FK is processed on register."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class AuthorPending(BaseDBModel):
                name: str

            class BookPending(BaseDBModel):
                title: str

            table_name = AuthorPending.get_table_name()
            ModelRegistry._models.pop(table_name, None)

            ModelRegistry.add_reverse_relationship(
                from_model=BookPending,
                to_model=AuthorPending,
                fk_field="author",
                related_name="books",
            )

            assert table_name in ModelRegistry._pending_reverses
            ModelRegistry.register_model(AuthorPending)
            assert hasattr(AuthorPending, "books")
        finally:
            ModelRegistry.restore(state)

    def test_add_reverse_relationship_immediate(self) -> None:
        """Reverse FK added immediately when model is registered."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class AuthorNow(BaseDBModel):
                name: str

            class BookNow(BaseDBModel):
                title: str

            ModelRegistry.register_model(AuthorNow)
            ModelRegistry.add_reverse_relationship(
                from_model=BookNow,
                to_model=AuthorNow,
                fk_field="author",
                related_name="books_now",
            )

            assert hasattr(AuthorNow, "books_now")
        finally:
            ModelRegistry.restore(state)

    def test_reverse_relationship_conflict_raises(self) -> None:
        """Reverse FK conflict raises AttributeError."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class AuthorConflict(BaseDBModel):
                name: str

            class BookConflict(BaseDBModel):
                title: str

            AuthorConflict.conflict = object()
            ModelRegistry.register_model(AuthorConflict)

            with pytest.raises(AttributeError, match="Reverse relationship"):
                ModelRegistry.add_reverse_relationship(
                    from_model=BookConflict,
                    to_model=AuthorConflict,
                    fk_field="author",
                    related_name="conflict",
                )
        finally:
            ModelRegistry.restore(state)

    def test_register_foreign_key_and_getters(self) -> None:
        """Register FK and confirm getters behave."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class Parent(BaseDBModel):
                name: str

            class Child(BaseDBModel):
                name: str

            ModelRegistry.register_foreign_key(
                from_model=Child,
                to_model=Parent,
                fk_field="parent",
                on_delete="CASCADE",
                related_name="children",
            )

            assert ModelRegistry.get_model(Parent.get_table_name()) is Parent
            assert ModelRegistry.get_foreign_keys("missing") == []
            assert ModelRegistry.get_foreign_keys(Child.get_table_name())
        finally:
            ModelRegistry.restore(state)

    def test_pending_m2m_target_with_missing_junction_raises(self) -> None:
        """Pending M2M target resolution errors if junction table missing."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class Source(BaseDBModel):
                name: str

            class DescriptorMissing:
                def resolve_forward_ref(
                    self, model_class: type[BaseDBModel]
                ) -> None:
                    _ = model_class

                @property
                def junction_table(self) -> None:
                    return None

            ModelRegistry._pending_m2m_targets["TargetMissing"] = [
                {
                    "from_model": Source,
                    "m2m_field": "targets",
                    "related_name": "sources",
                    "symmetrical": False,
                    "descriptor": DescriptorMissing(),
                }
            ]

            with pytest.raises(ValueError, match="junction table"):

                class TargetMissing(BaseDBModel):  # pylint: disable=unused-variable
                    name: str
        finally:
            ModelRegistry.restore(state)

    def test_add_pending_m2m_existing_missing_junction_raises(self) -> None:
        """add_pending_m2m_relationship errors if junction table missing."""
        state = ModelRegistry.snapshot()
        ModelRegistry.reset()

        try:

            class TargetExists(BaseDBModel):  # pylint: disable=unused-variable
                name: str

            class SourceExists(BaseDBModel):
                name: str

            class DescriptorMissing:
                def resolve_forward_ref(
                    self, model_class: type[BaseDBModel]
                ) -> None:
                    _ = model_class

                @property
                def junction_table(self) -> None:
                    return None

            with pytest.raises(ValueError, match="junction table"):
                ModelRegistry.add_pending_m2m_relationship(
                    from_model=SourceExists,
                    to_model_name="TargetExists",
                    m2m_field="targets",
                    related_name="sources",
                    symmetrical=False,
                    descriptor=DescriptorMissing(),
                )
        finally:
            ModelRegistry.restore(state)
