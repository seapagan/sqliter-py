"""Mypy regression coverage for async M2M descriptor typing."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from sqliter.asyncio.orm import (
    AsyncBaseDBModel,
    AsyncManyToMany,
    AsyncManyToManyManager,
    AsyncPrefetchedM2MResult,
    AsyncReverseManyToMany,
)


class Tag(AsyncBaseDBModel):
    """Async tag model for typing checks."""

    name: str
    articles: ClassVar[AsyncReverseManyToMany]


class Article(AsyncBaseDBModel):
    """Async article model for typing checks."""

    title: str
    tags: AsyncManyToMany[Tag] = AsyncManyToMany(
        Tag,
        related_name="articles",
    )


if TYPE_CHECKING:
    article_field: AsyncManyToMany[Tag] = Article.tags
    article = Article(title="Guide")
    tag = Tag(name="python")

    article_rel: AsyncManyToManyManager[Tag] | AsyncPrefetchedM2MResult[Tag]
    article_rel = article.tags

    tag_field: AsyncReverseManyToMany = Tag.articles
    tag_rel: AsyncManyToManyManager[Article] | AsyncPrefetchedM2MResult[Article]
    tag_rel = tag.articles
